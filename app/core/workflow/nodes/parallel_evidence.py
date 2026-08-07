"""并发证据采集节点（多异常扇出）。

设计（2026-08-05 用户拍板）：
- layer 检出的异常组 > 阈值（默认 2）时走本节点；≤ 阈值走原单 context evidence。
- 每个异常组一条独立的 EvidenceCollectorNode 流水线（全新 context + 完整
  max_steps 预算），只做证据采集 + 单组分析；结果落盘（每组独立归档
  {run_id}-gN）并产出摘要。
- 不做全局 RCA：每组的"单独分析"就是该组的根因分析；本节点之后直达
  conclusion，由其确定性拼接结构化真实数据 + LLM 读各组摘要写结论。

N 阶梯实测依据：单 context evidence 在 N=5 降级、N=10 完全塌缩
（35 项计划 0 执行）；每组独立 context 是唯一不随 N 退化的路径。
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.group_evidence import aggregate_group_evidence
from app.core.workflow.schemas import GroupDiagnosisSummaryOutput
from app.core.workflow.state import WorkflowState
from app.core.prompts import GROUP_EVIDENCE_SUMMARY_PROMPT

logger = logging.getLogger(__name__)

# 单组摘要注入 conclusion 的字符上限（摘要必须紧凑，N 份合计才装得下）
_GROUP_SUMMARY_CHAR_LIMIT = 1600


def extract_abnormal_groups(layer_handoff: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从 layer_handoff 提取异常组列表；无 issue_groups 时按 Pod 逐个成组。"""
    handoff = layer_handoff or {}
    groups = [
        g for g in (handoff.get("issue_groups") or handoff.get("abnormal_groups") or [])
        if isinstance(g, dict) and (g.get("entities") or g.get("status_keywords"))
    ]
    if groups:
        return groups
    # 回退：每个 abnormal_pod 单独一组
    fallback = []
    for i, pod in enumerate(handoff.get("abnormal_pods") or [], start=1):
        if not isinstance(pod, dict) or not pod.get("name"):
            continue
        fallback.append({
            "group_id": f"g{i}",
            "status_keywords": [pod.get("status")] if pod.get("status") else [],
            "pod_abnormal_type": "",
            "entities": [{
                "kind": "Pod",
                "namespace": pod.get("namespace", ""),
                "name": pod.get("name", ""),
            }],
            "possible_scenarios": [],
        })
    return fallback


class ParallelEvidenceNode(WorkflowNode):
    """多异常并发采集：每组一个独立 evidence context，采集+分析+落盘+摘要。"""

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

    @property
    def node_id(self) -> str:
        return "parallel_evidence"

    @property
    def node_name(self) -> str:
        return "并发证据采集"

    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]

    # ------------------------------------------------------------------
    def _max_concurrency(self) -> int:
        wf = self._get_workflow_config()
        evidence = wf.get("evidence", {}) if isinstance(wf, dict) else {}
        parallel = evidence.get("parallel", {}) if isinstance(evidence, dict) else {}
        try:
            value = int(parallel.get("max_concurrency"))
            return max(1, min(value, 8))
        except (TypeError, ValueError):
            return 3

    def execute(self, state: WorkflowState) -> WorkflowState:
        new_state: WorkflowState = {"current_node": self.node_id}
        question = state.get("question", "")
        run_id = state.get("run_id", "") or getattr(self, "current_run_id", "")
        handoff = state.get("layer_handoff") or {}
        groups = extract_abnormal_groups(handoff)

        logger.info(
            "🚀 [parallel_evidence] 多异常并发采集: %d 组, 并发度=%d",
            len(groups), self._max_concurrency(),
        )

        if not groups:
            new_state.setdefault("errors", []).append(
                "parallel_evidence: layer_handoff 无异常组，无法并发采集"
            )
            new_state["group_results"] = []
            self._save_thinking(state, new_state, [])
            return new_state

        results: List[Optional[Dict[str, Any]]] = [None] * len(groups)
        merged_thinking: List[Dict[str, Any]] = []

        def run_group(index: int, group: Dict[str, Any]) -> Dict[str, Any]:
            gid = str(group.get("group_id") or f"g{index + 1}")
            collector = self._build_group_collector(gid, run_id)
            scoped_state = self._build_group_state(
                question=question,
                state=state,
                handoff=handoff,
                group=group,
                gid=gid,
            )
            logger.info("📍 [parallel_evidence:%s] 开始采集 | 实体=%s",
                        gid, self._group_entity_labels(group))
            group_state = collector.execute(scoped_state)
            result = self._build_group_result(gid, group, group_state, run_id)
            self._attach_structured_diagnosis(result, group)
            return result

        max_workers = min(self._max_concurrency(), len(groups))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(run_group, i, g): i for i, g in enumerate(groups)
            }
            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                    logger.info(
                        "✅ [parallel_evidence:%s] 完成 | 摘要 %d 字符",
                        results[i]["group_id"], len(results[i].get("summary") or ""),
                    )
                except Exception as exc:  # noqa: BLE001
                    gid = str(groups[i].get("group_id") or f"g{i + 1}")
                    logger.error("❌ [parallel_evidence:%s] 组采集失败: %s", gid, exc)
                    results[i] = {
                        "group_id": gid,
                        "pod_abnormal_type": groups[i].get("pod_abnormal_type", ""),
                        "entities": groups[i].get("entities") or [],
                        "status_keywords": groups[i].get("status_keywords") or [],
                        "error": str(exc),
                        "summary": f"该组采集失败: {exc}",
                        "evidence_analysis": "{}",
                        "thinking_events": [],
                        "archive_run_id": f"{run_id}-{gid}" if run_id else "",
                    }

        group_results = [r for r in results if r is not None]
        # 各组 thinking 事件合并进主流（带组标记），保证归档与展示可追溯
        for r in group_results:
            for ev in r.get("thinking_events") or []:
                merged_thinking.append({**ev, "group_id": r["group_id"]})
            # thinking 事件已合并到主 state，组结果里只留必要字段
            r["thinking_events"] = [
                ev for ev in (r.get("thinking_events") or [])
                if ev.get("type") == "tool_result"
            ]

        new_state["group_results"] = group_results
        # 兼容下游统计口径：合并各组 evidence 完整度的简单平均
        completeness = [
            r.get("completeness") for r in group_results
            if isinstance(r.get("completeness"), (int, float))
        ]
        if completeness:
            new_state["evidence_completeness"] = sum(completeness) / len(completeness)

        self._save_thinking(state, new_state, merged_thinking)
        logger.info(
            "🎉 [parallel_evidence] 全部完成: %d/%d 组成功",
            sum(1 for r in group_results if not r.get("error")), len(groups),
        )
        return new_state

    # ------------------------------------------------------------------
    def _build_group_collector(self, gid: str, run_id: str) -> EvidenceCollectorNode:
        """为一个组构建独立的 evidence 采集器（共享服务，隔离归档）。"""
        collector = EvidenceCollectorNode(
            self.holmes_service, self.metrics, self.runbook_catalog,
        )
        collector.ai_call = getattr(self, "ai_call", None)
        collector.tools = getattr(self, "tools", []) or []
        collector.workflow_config_override = getattr(self, "workflow_config_override", None)
        collector.cancel_event = getattr(self, "cancel_event", None)
        # 每组独立归档目录 {run_id}-gN，避免并发工具序号冲突
        collector.current_run_id = f"{run_id}-{gid}" if run_id else ""
        # 共享事件队列：各组 thinking 实时流出（事件天然带 tool_args 可辨识组）
        queue = getattr(self, "_event_queue", None)
        if queue is not None:
            collector.set_event_queue(queue)
        return collector

    @staticmethod
    def _group_entity_labels(group: Dict[str, Any]) -> str:
        labels = []
        for e in (group.get("entities") or [])[:4]:
            if isinstance(e, dict):
                labels.append(f"{e.get('namespace', '')}/{e.get('name', '')}")
        return ",".join(labels) or "?"

    def _build_group_state(
        self,
        *,
        question: str,
        state: WorkflowState,
        handoff: Dict[str, Any],
        group: Dict[str, Any],
        gid: str,
    ) -> WorkflowState:
        """构建单组 scoped 状态：handoff 只含该组，采集范围钉死在组实体上。"""
        entities = group.get("entities") or []
        primary = entities[0] if entities and isinstance(entities[0], dict) else {}
        status_keywords = [s for s in (group.get("status_keywords") or []) if s]
        scoped_handoff = {
            "diagnosis_scope": "single_group",
            "layer": handoff.get("layer", "ABNORMAL"),
            "confidence": handoff.get("confidence", 0.5),
            "primary_problem": (
                f"[{gid}] {primary.get('namespace', '')}/{primary.get('name', '')} "
                f"{'/'.join(status_keywords)} {group.get('pod_abnormal_type', '')}"
            ).strip(),
            "abnormal_pods": [
                {
                    "name": e.get("name", ""),
                    "namespace": e.get("namespace", ""),
                    "status": (status_keywords[0] if status_keywords else None),
                }
                for e in entities if isinstance(e, dict)
            ],
            "issue_groups": [group],
            "abnormal_groups": [group],
            "pod_status_keyword": (status_keywords[0] if status_keywords else ""),
            "pod_abnormal_type": group.get("pod_abnormal_type", ""),
            "possible_scenarios": group.get("possible_scenarios") or [],
            "matched_runbooks": handoff.get("matched_runbooks") or [],
            "must_verify": [
                f"只诊断本组实体 {self._group_entity_labels(group)}，"
                "不要采集其他 namespace/Pod 的证据",
            ],
            "current_abnormal_summary": {
                "source": "parallel_evidence_group_scope",
                "status_counts": {k: 1 for k in status_keywords} or {},
                "total_abnormal": len(entities),
                "selected_rows": [],
            },
        }
        scoped_question = (
            f"{question}\n（本组诊断目标：{self._group_entity_labels(group)}，"
            f"异常状态 {'/'.join(status_keywords) or '未知'}）"
        )
        return {
            "question": scoped_question,
            "run_id": state.get("run_id", ""),
            "layer": state.get("layer"),
            "layer_analysis": json.dumps(scoped_handoff, ensure_ascii=False),
            "layer_handoff": scoped_handoff,
            "possible_scenarios": group.get("possible_scenarios") or [],
            # key_entities 必须是 dict（evidence planner 对每项调 .get('type')/.get('value')）
            "key_entities": [
                {
                    "type": e.get("kind", "Pod"),
                    "value": f"{e.get('namespace', '')}/{e.get('name', '')}",
                }
                for e in entities if isinstance(e, dict)
            ],
            "context_archive_ref": state.get("context_archive_ref", ""),
            "layer_archive_ref": state.get("layer_archive_ref") or {},
            "thinking_events": [],
            "errors": [],
            "warnings": [],
        }

    @staticmethod
    def _build_group_result(
        gid: str,
        group: Dict[str, Any],
        group_state: Dict[str, Any],
        run_id: str,
    ) -> Dict[str, Any]:
        """从组的 evidence 执行结果提炼落盘引用 + 摘要。"""
        evidence_analysis = group_state.get("evidence_analysis") or "{}"
        summary = ""
        legacy_text_fallback = False
        collection_summary = ""
        completeness = None
        try:
            parsed = json.loads(evidence_analysis) if isinstance(evidence_analysis, str) else evidence_analysis
            if isinstance(parsed, dict):
                summary = str(parsed.get("llm_analysis") or "").strip()
                collection_summary = str(parsed.get("collection_summary") or "").strip()
                completeness = parsed.get("plan_completeness")
        except (ValueError, TypeError):
            pass
        if not summary:
            # 回退：用最后一条 ai_message 作为组分析
            for ev in reversed(group_state.get("thinking_events") or []):
                full = str(ev.get("full_content") or "").strip()
                preview = str(ev.get("content") or "").strip()
                if ev.get("type") == "ai_message" and (full or preview):
                    summary = full or preview
                    legacy_text_fallback = True
                    break
        summary = summary[:_GROUP_SUMMARY_CHAR_LIMIT]

        dimension_evidence = aggregate_group_evidence(
            group.get("entities") or [],
            group_state.get("thinking_events") or [],
            status_keywords=group.get("status_keywords") or [],
        )

        return {
            "group_id": gid,
            "pod_abnormal_type": group.get("pod_abnormal_type", ""),
            "status_keywords": group.get("status_keywords") or [],
            "entities": group.get("entities") or [],
            "summary": summary,
            "legacy_text_fallback": legacy_text_fallback,
            "entity_summaries": [],
            "dimension_evidence_by_entity": dimension_evidence,
            "collection_summary": collection_summary,
            "completeness": completeness,
            "evidence_analysis": evidence_analysis,
            "thinking_events": group_state.get("thinking_events") or [],
            "archive_run_id": f"{run_id}-{gid}" if run_id else "",
            "error": None,
        }

    @staticmethod
    def _deterministic_entity_summary(
        entity: Dict[str, Any],
        group: Dict[str, Any],
        dimensions: Dict[str, Any],
    ) -> Dict[str, Any]:
        facts = [
            fact
            for dimension in dimensions.values()
            for fact in (dimension.get("facts") or [])
            if isinstance(fact, dict)
        ]
        phenomenon = str(facts[0].get("value") or "") if facts else "未采集到可用于归因的真实事实"
        return {
            "namespace": str(entity.get("namespace") or ""),
            "name": str(entity.get("name") or ""),
            "status": "/".join(group.get("status_keywords") or []),
            "phenomenon": phenomenon,
            "root_cause": "证据不足",
            "causal_chain": [],
            "confidence": 0.0,
            "supporting_fact_ids": [],
            "contradicting_fact_ids": [],
            "unknowns": ["结构化单组分析不可用，请查看各维度真实事实和归档"],
        }

    def _attach_structured_diagnosis(
        self,
        result: Dict[str, Any],
        group: Dict[str, Any],
    ) -> None:
        """Extract one fact-linked diagnosis per entity and validate its scope."""
        entities = [item for item in (group.get("entities") or []) if isinstance(item, dict)]
        dimensions_by_entity = result.get("dimension_evidence_by_entity") or {}
        allowed_entities = {
            f"{item.get('namespace', '')}/{item.get('name', '')}": item
            for item in entities
        }
        allowed_fact_ids = {
            key: {
                str(fact.get("fact_id"))
                for dimension in (dimensions_by_entity.get(key) or {}).values()
                for fact in (dimension.get("facts") or [])
                if isinstance(fact, dict) and fact.get("fact_id")
            }
            for key in allowed_entities
        }

        parsed = None
        ai_call = getattr(self, "ai_call", None)
        if ai_call is not None and hasattr(ai_call, "call_structured"):
            prompt_payload = {
                "group_id": result.get("group_id"),
                "entities": entities,
                "dimension_evidence_by_entity": dimensions_by_entity,
            }
            try:
                parsed, _raw = ai_call.call_structured(
                    system_prompt=GROUP_EVIDENCE_SUMMARY_PROMPT,
                    question=json.dumps(prompt_payload, ensure_ascii=False, default=str),
                    schema=GroupDiagnosisSummaryOutput,
                    node_id=self.node_id,
                    run_id=result.get("archive_run_id") or "",
                    max_tokens=2048,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "⚠️ [parallel_evidence:%s] 结构化单组分析失败，使用确定性回退: %s",
                    result.get("group_id"), exc,
                )

        by_key: Dict[str, Dict[str, Any]] = {}
        if parsed is not None:
            for item in parsed.entities:
                data = item.model_dump(mode="json")
                key = f"{data.get('namespace', '')}/{data.get('name', '')}"
                if key not in allowed_entities or key in by_key:
                    continue
                valid_ids = allowed_fact_ids.get(key, set())
                data["supporting_fact_ids"] = [
                    fact_id for fact_id in data.get("supporting_fact_ids") or []
                    if fact_id in valid_ids
                ]
                data["contradicting_fact_ids"] = [
                    fact_id for fact_id in data.get("contradicting_fact_ids") or []
                    if fact_id in valid_ids
                ]
                if not data["supporting_fact_ids"]:
                    data["root_cause"] = "证据不足"
                    data["confidence"] = 0.0
                    data.setdefault("unknowns", []).append("模型结论没有当前实体的有效 fact_id 支撑")
                by_key[key] = data

        for key, entity in allowed_entities.items():
            if key not in by_key:
                by_key[key] = self._deterministic_entity_summary(
                    entity,
                    group,
                    dimensions_by_entity.get(key) or {},
                )
        result["entity_summaries"] = [by_key[key] for key in allowed_entities]
