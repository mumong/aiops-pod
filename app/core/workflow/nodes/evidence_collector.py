"""
节点2：证据链采集

职责：
- 调用 LLM 规划需要采集的证据
- 调用工具实际采集证据
- 记录 LLM 调用和工具调用统计
- 详细的输出，详细的给证据具有逻辑性
- 输出：evidence_items, evidence_analysis, evidence_completeness, tool_results

设计：
- 有自己的专用 prompt
- 调用 LLM 进行证据规划（使用和 HolmesService 相同的方式）
- 支持使用 runbooks 和 tools
- 统计 LLM 调用和工具调用次数
"""

import json
import logging
import re
import shlex
from typing import Any, Dict, List, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import EvidenceCollectionOutput, EvidenceMatchOutput, EvidencePlanOutput, QueryResult
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer, EvidenceItem, EvidenceLevel
from app.core.prompts import get_workflow_prompt, get_query_evidence_normalization_prompt

logger = logging.getLogger(__name__)


class EvidenceCollectorNode(WorkflowNode):
    """
    证据链采集节点

    每次执行都会：
    1. 调用 LLM 规划需要采集的证据
    2. 调用工具实际采集证据
    3. 统计 LLM 调用和工具调用次数
    4. 计算证据完整度
    """

    def __init__(
        self,
        holmes_service: Any = None,
        metrics: Any = None,
        runbook_catalog: Any = None,
        plan_match_adjudicator: Any = None,
    ):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 和工具调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog
        self.plan_match_adjudicator = plan_match_adjudicator
        self._plan_match_adjudication_enabled = bool(plan_match_adjudicator)
        self._logged_evidence_user_prompt = False
        self._early_stop_state = {
            "triggered": False,
            "reason": "",
            "required_levels": ["critical", "important"],
        }

    @property
    def node_id(self) -> str:
        return "evidence"

    @property
    def node_name(self) -> str:
        return "证据链采集"

    def _get_prompt_language(self) -> str:
        if self.holmes_service and hasattr(self.holmes_service, "get_prompt_language"):
            return self.holmes_service.get_prompt_language()
        return "zh"

    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]

    def _use_agent_structured_output(self) -> bool:
        runtime_enabled = self._is_structured_runtime_enabled(default=True)
        cfg = self._get_workflow_config()
        node_cfg = cfg.get("evidence", {}) if isinstance(cfg, dict) else {}
        if isinstance(node_cfg, dict):
            if "agent_structured_output" in node_cfg:
                return self._parse_bool_config(node_cfg.get("agent_structured_output"), runtime_enabled)
            structured_cfg = node_cfg.get("structured_output")
            if isinstance(structured_cfg, dict) and "enabled" in structured_cfg:
                return self._parse_bool_config(structured_cfg.get("enabled"), runtime_enabled)
        return runtime_enabled

    def _allow_plan_precall_fallback(self) -> bool:
        runtime_fallback = self._is_structured_runtime_fallback_enabled(default=True)
        cfg = self._get_workflow_config()
        node_cfg = cfg.get("evidence", {}) if isinstance(cfg, dict) else {}
        if isinstance(node_cfg, dict):
            if "plan_precall_fallback" in node_cfg:
                return self._parse_bool_config(node_cfg.get("plan_precall_fallback"), runtime_fallback)
            structured_cfg = node_cfg.get("structured_output")
            if isinstance(structured_cfg, dict) and "plan_precall_fallback" in structured_cfg:
                return self._parse_bool_config(structured_cfg.get("plan_precall_fallback"), runtime_fallback)
        return runtime_fallback

    @staticmethod
    def _has_successful_tool_results(thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result" and ev.get("status") == "success"
            for ev in (thinking_events or [])
        )

    @staticmethod
    def _has_semantic_tool_success(thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and ev.get("semantic_success", True) is not False
            for ev in (thinking_events or [])
        )

    @classmethod
    def _has_effective_tool_evidence(cls, thinking_events: List[Dict[str, Any]]) -> bool:
        """A tool result is effective when it is positive evidence or a diagnostic failure.

        Some probes intentionally fail when the cluster dependency is broken,
        e.g. `curl registry-1.docker.io` timing out. Those must count as
        collected evidence instead of triggering a retry.
        """
        return cls._has_semantic_tool_success(thinking_events) or cls._has_diagnostic_negative_tool_result(thinking_events)

    @classmethod
    def _has_diagnostic_negative_tool_result(cls, thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and cls._is_diagnostic_negative_tool_result(
                ev.get("tool_name", ""),
                ev.get("result", ev.get("result_preview", "")),
                ev.get("structured") or {},
            )
            for ev in (thinking_events or [])
        )

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行证据采集逻辑

        流程：
        1. 调用 LLM 规划需要采集的证据
        2. 根据规划调用工具采集证据
        3. 解析工具输出，标记哪些证据已采集
        4. 计算证据完整度
        5. 记录 LLM 调用和工具调用次数到 metrics
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            question = state.get("question", "")
            layer = state.get("layer")
            layer_analysis = state.get("layer_analysis", "{}")
            layer_handoff = state.get("layer_handoff") or self._parse_layer_handoff(layer_analysis)
            possible_scenarios = state.get("possible_scenarios", [])
            key_entities = state.get("key_entities", [])

            logger.info(f"📋 证据采集: 层级={layer}, 可能场景={possible_scenarios}")
            logger.debug(f"📋 [DEBUG] 证据采集输入: question={question[:100]}, "
                        f"layer_handoff长度={len(json.dumps(layer_handoff, ensure_ascii=False, default=str))}, "
                        f"key_entities={key_entities}")
            self._early_stop_state = {
                "triggered": False,
                "reason": "",
                "required_levels": ["critical", "important"],
            }
            self._plan_match_adjudication_enabled = bool(getattr(self, "plan_match_adjudicator", None))
            self._logged_evidence_user_prompt = False

            # 1. 调用 LLM 规划证据采集计划
            evidence_plan, thinking_events, llm_result_text = self._plan_evidence_with_llm(
                question=question,
                layer=layer,
                possible_scenarios=possible_scenarios,
                key_entities=key_entities,
                layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
                context_archive_ref=state.get("context_archive_ref", ""),
                layer_archive_ref=state.get("layer_archive_ref") or {},
            )
            retry_reason = self._get_plan_protocol_failure_reason(
                evidence_plan=evidence_plan,
                thinking_events=thinking_events,
            )
            if retry_reason:
                retry_existing_plan = (
                    evidence_plan
                    if self._plan_exists_without_tool_results(retry_reason)
                    else None
                )
                logger.warning("⚠️ [evidence] 首轮结果违反采证协议：%s；发起一次重试", retry_reason)
                evidence_plan, thinking_events, llm_result_text = self._plan_evidence_with_llm(
                    question=question,
                    layer=layer,
                    possible_scenarios=possible_scenarios,
                    key_entities=key_entities,
                    layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
                    context_archive_ref=state.get("context_archive_ref", ""),
                    layer_archive_ref=state.get("layer_archive_ref") or {},
                    strict_mode=retry_existing_plan is None,
                    failure_reason=(
                        "上一轮 evidence_plan 已有效，本轮不要重新输出 evidence_plan；"
                        "请直接按既有计划调用至少一个 critical 或 important 级真实工具。"
                        if retry_existing_plan
                        else retry_reason
                    ),
                    existing_plan=retry_existing_plan,
                )

            # 2. 构建证据项列表（基于 thinking_events 中 AICall 真实工具调用）
            tool_results = []
            evidence_items = self._build_evidence_items_from_thinking(
                evidence_plan=evidence_plan,
                thinking_events=thinking_events,
            )
            upstream_evidence_items = self._build_upstream_evidence_items(
                evidence_plan=evidence_plan,
                thinking_events=state.get("thinking_events", []),
            )
            if not self._early_stop_state.get("triggered"):
                self._early_stop_state = self._derive_early_stop_state(evidence_plan, evidence_items)

            # 2.1 回退：evidence 节点没采集到证据时，从 layer 阶段的 thinking_events 统计
            if not evidence_items and not upstream_evidence_items:
                layer_thinking = state.get("thinking_events", [])
                layer_tool_events = [
                    ev for ev in layer_thinking
                    if ev.get("type") == "tool_result"
                    and ev.get("status") == "success"
                    and ev.get("node") == "layer"
                    and ev.get("tool_name", "").lower() not in self._NON_EVIDENCE_TOOLS
                ]
                if layer_tool_events:
                    logger.info("📊 [evidence] evidence 节点未采集新证据，"
                                "回退到 layer 阶段的 %d 个工具调用", len(layer_tool_events))
                    for ti, ev in enumerate(layer_tool_events):
                        evidence_items.append(EvidenceItem(
                            id=f"layer_{ti}",
                            description=f"上游采集: {ev.get('tool_name', '')}",
                            level=EvidenceLevel.IMPORTANT,
                            weight=0.2,
                            collected=True,
                            value=(ev.get("result", "") or ev.get("result_preview", ""))[:500],
                            source="layer_fallback",
                        ))

            # 3. 计算完整度
            combined_evidence_items = self._merge_evidence_items(evidence_items, upstream_evidence_items)
            completeness = self._calculate_completeness(combined_evidence_items)

            # 4. 更新 metrics（记录 LLM 调用和工具调用次数）
            self._update_metrics(evidence_plan, tool_results)

            # 5. 从 thinking_events 提取 MCP 工具的真实输出数据
            tool_data_from_llm = self._extract_tool_data_from_thinking(thinking_events)
            evidence_tool_stats = self._calculate_evidence_tool_stats(
                evidence_plan=evidence_plan,
                thinking_events=[*(state.get("thinking_events", []) or []), *(thinking_events or [])],
                evidence_items=evidence_items,
                upstream_evidence_items=upstream_evidence_items,
            )

            # 6. 构建证据清单（真实数据，供 conclusion LLM 引用）
            # plan_total 保持与模型输出的 evidence_plan 对齐；environment_total
            # 只统计真实环境证据。报告同时展示两个口径，避免用户看到
            # evidence_plan=4 项但“证据完整度 3/3”这种不直观结果。
            measurable_items = self._measurable_evidence_items(combined_evidence_items)
            plan_stats = self._calculate_plan_completeness(evidence_items, upstream_evidence_items)
            plan_collected = plan_stats["plan_collected"]
            plan_total = plan_stats["plan_total"]
            collected = sum(1 for e in measurable_items if e.collected)
            total = len(measurable_items)
            not_collected = [e for e in measurable_items if not e.collected]
            plan_completeness = plan_stats["plan_completeness"]
            evidence_facts = self._build_evidence_facts(combined_evidence_items)
            evidence_conflicts = self._build_evidence_conflicts(tool_data_from_llm, layer_handoff)
            missing_evidence = [
                {"id": e.id, "description": e.description, "level": e.level.value if hasattr(e.level, "value") else str(e.level)}
                for e in not_collected
            ]

            plan_by_id = {
                str(item.get("id", "")): item
                for item in evidence_plan
                if isinstance(item, dict)
            }
            evidence_inventory = []
            for e in combined_evidence_items:
                plan_item = plan_by_id.get(str(e.id), {})
                evidence_inventory.append({
                    "id": e.id,
                    "description": e.description,
                    "level": e.level.value if hasattr(e.level, 'value') else str(e.level),
                    "tool": plan_item.get("tool", ""),
                    "command": plan_item.get("command", ""),
                    "purpose": plan_item.get("purpose", ""),
                    "collected": e.collected,
                    "source": getattr(e, 'source', ''),
                    "outcome": getattr(e, 'outcome', 'unknown'),
                })

            # 未采集原因说明
            missing_reasons = []
            for e in not_collected:
                source = getattr(e, 'source', '')
                if source == "planned":
                    missing_reasons.append(f"{e.id}({e.description}): 已规划但工具执行失败或无匹配结果")
                else:
                    missing_reasons.append(f"{e.id}({e.description}): 未采集")

            collection_output = self._build_evidence_collection_output(
                evidence_plan=evidence_plan,
                tool_results=tool_results,
                tool_data=tool_data_from_llm,
                llm_result_text=llm_result_text,
                plan_total=plan_total,
                plan_collected=plan_collected,
                plan_completeness=plan_completeness,
                environment_total=total,
                environment_collected=collected,
                environment_completeness=completeness,
                evidence_inventory=evidence_inventory,
                missing_reasons=missing_reasons,
                early_stop=dict(self._early_stop_state),
                executed_tool_count=evidence_tool_stats["executed_tool_count"],
                matched_tool_count=evidence_tool_stats["matched_tool_count"],
                unplanned_tool_count=evidence_tool_stats["unplanned_tool_count"],
            )

            new_state.update({
                "evidence_items": combined_evidence_items,
                "evidence_analysis": collection_output.model_dump_json(),
                "evidence_completeness": completeness,
                "tool_results": tool_results,
                "evidence_facts": evidence_facts,
                "evidence_conflicts": evidence_conflicts,
                "missing_evidence": missing_evidence,
                "query_result": self._build_query_result(
                    question=question,
                    layer=layer,
                    evidence_plan=evidence_plan,
                    evidence_inventory=evidence_inventory,
                    tool_data=tool_data_from_llm,
                    collection_summary=f"计划 {total} 项，实际采集 {collected} 项，未采集 {total - collected} 项，完整度 {completeness:.0%}",
                    missing_reasons=missing_reasons,
                ) if layer == Layer.QUERY else None,
            })

            logger.info(f"✅ 证据采集完成: {collected}/{total} 项, 完整度 {completeness:.0%}")
            if self._early_stop_state.get("triggered"):
                logger.info("🛑 [evidence] 动态提前停止: %s",
                            self._early_stop_state.get("reason", "critical 和 important 级证据均已满足"))
            if missing_reasons:
                logger.info(f"   未采集证据 ({len(missing_reasons)} 项):")
                for reason in missing_reasons:
                    logger.info(f"     - {reason}")
            logger.info(f"   LLM 调用: 1 次, 工具调用: {len(tool_results)} 次")

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

        except Exception as e:
            logger.error(f"证据采集失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "evidence_items": [],
                "evidence_analysis": "{}",
                "evidence_completeness": 0.0,
                "tool_results": [],
            })
            self._save_thinking(state, new_state, [])

        return new_state

    @staticmethod
    def _parse_layer_handoff(layer_analysis: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(layer_analysis) if layer_analysis else {}
            if isinstance(parsed, dict):
                return {
                    "layer": parsed.get("layer"),
                    "confidence": parsed.get("confidence"),
                    "primary_problem": parsed.get("reasoning", ""),
                    "active_entities": parsed.get("key_entities", []),
                    "possible_scenarios": parsed.get("possible_scenarios", []),
                    "must_verify": ["基于真实 tool_result 重新验证上游定位"],
                }
        except (json.JSONDecodeError, TypeError):
            pass
        return {}

    @staticmethod
    def _build_evidence_facts(evidence_items: List[EvidenceItem]) -> List[Dict[str, Any]]:
        facts = []
        for item in evidence_items:
            if not item.collected:
                continue
            facts.append({
                "id": item.id,
                "description": item.description,
                "level": item.level.value if hasattr(item.level, "value") else str(item.level),
                "value": (item.value or "")[:500],
                "source": getattr(item, "source", ""),
            })
        return facts

    @staticmethod
    def _build_evidence_collection_output(
        evidence_plan: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        tool_data: List[Dict[str, Any]],
        llm_result_text: str,
        plan_total: int,
        plan_collected: int,
        plan_completeness: float,
        environment_total: int,
        environment_collected: int,
        environment_completeness: float,
        evidence_inventory: List[Dict[str, Any]],
        missing_reasons: List[str],
        early_stop: Dict[str, Any],
        executed_tool_count: int = 0,
        matched_tool_count: int = 0,
        unplanned_tool_count: int = 0,
    ) -> EvidenceCollectionOutput:
        return EvidenceCollectionOutput.model_validate({
            "evidence_plan": evidence_plan,
            "tool_results": [r.get("summary", "") for r in tool_results],
            "tool_data": tool_data,
            "llm_analysis": llm_result_text[:3000] if llm_result_text else "",
            "collection_summary": (
                f"计划 {plan_total} 项，实际采集 {plan_collected} 项，"
                f"未采集 {plan_total - plan_collected} 项，完整度 {plan_completeness:.0%}；"
                f"其中真实环境证据 {environment_collected}/{environment_total} 项，完整度 {environment_completeness:.0%}；"
                f"实际执行工具 {executed_tool_count} 个，匹配计划 {matched_tool_count} 个，未规划证据 {unplanned_tool_count} 个"
            ),
            "plan_total": plan_total,
            "plan_collected": plan_collected,
            "plan_completeness": plan_completeness,
            "environment_evidence_total": environment_total,
            "environment_evidence_collected": environment_collected,
            "environment_evidence_completeness": environment_completeness,
            "executed_tool_count": executed_tool_count,
            "matched_tool_count": matched_tool_count,
            "unplanned_tool_count": unplanned_tool_count,
            "evidence_inventory": evidence_inventory,
            "missing_reasons": missing_reasons,
            "early_stop": early_stop,
        })

    @staticmethod
    def _build_evidence_conflicts(
        tool_data: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        conflicts = []
        abnormal_pods = (layer_handoff or {}).get("abnormal_pods") or []
        abnormal_pod_keys = {
            (str(pod.get("namespace") or ""), str(pod.get("name") or ""))
            for pod in abnormal_pods
            if isinstance(pod, dict) and pod.get("name")
        }
        for item in tool_data:
            data = item.get("data", "") or ""
            if re.search(r"no events found|no resources found|notfound|not found|command failed|error from server", data, re.IGNORECASE):
                missing_pod = EvidenceCollectorNode._extract_missing_abnormal_pod(data, abnormal_pod_keys)
                object_missing = bool(missing_pod)
                conflict = {
                    "tool": item.get("tool", "unknown"),
                    "reason": data[:300],
                    "severity": "critical" if object_missing else "warning",
                    "object_missing": object_missing,
                }
                if object_missing:
                    conflict["object"] = {
                        "kind": "Pod",
                        "name": missing_pod[1],
                        "namespace": missing_pod[0],
                    }
                    conflict["message"] = (
                        "异常 Pod 当前不存在；历史事件或归档摘要不能继续作为该 Pod 当前异常的正向证据"
                    )
                conflicts.append(conflict)
        return conflicts

    @staticmethod
    def _extract_missing_abnormal_pod(
        data: str,
        abnormal_pod_keys: set[tuple[str, str]],
    ) -> Optional[tuple[str, str]]:
        if not data or not abnormal_pod_keys:
            return None
        for namespace, pod_name in abnormal_pod_keys:
            name = re.escape(pod_name)
            patterns = (
                rf"(?:^|:\s*)pods?\s+[\"']{name}[\"']\s+(?:not\s*found|notfound)\b",
                rf"\bpods?/{name}\s+(?:not\s*found|notfound)\b",
            )
            if any(re.search(pattern, data or "", re.IGNORECASE) for pattern in patterns):
                return namespace, pod_name
        return None

    def _build_query_result(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_plan: List[Dict[str, Any]],
        evidence_inventory: List[Dict[str, Any]],
        tool_data: List[Dict[str, Any]],
        collection_summary: str,
        missing_reasons: List[str],
    ) -> Dict[str, Any]:
        """QUERY 模式下将真实工具结果归一化为 Pydantic QueryResult，供 conclusion 纯渲染。"""
        if layer != Layer.QUERY:
            return {}

        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)
        if not hasattr(ai_call, "call_structured"):
            logger.warning("⚠️ [evidence] ai_call 不支持 call_structured，使用 QUERY 通用回退")
            return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)

        prompt = get_query_evidence_normalization_prompt(self._get_prompt_language())
        payload = {
            "question": question,
            "collection_summary": collection_summary,
            "evidence_plan": evidence_plan,
            "evidence_inventory": evidence_inventory,
            "tool_data": tool_data,
            "missing_reasons": missing_reasons,
        }

        try:
            normalized, _ = ai_call.call_structured(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False),
                schema=QueryResult,
                node_id="query_result_normalize",
                run_id=getattr(self, "current_run_id", ""),
            )
            if normalized:
                result = normalized.model_dump()
                result.setdefault("query_target", question)
                result.setdefault("collection_summary", collection_summary)
                return QueryResult.model_validate(result).model_dump()
        except Exception as exc:
            logger.warning("⚠️ [evidence] QUERY 结果归一化失败，使用通用回退: %s", exc)

        return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)

    @staticmethod
    def _build_query_result_fallback(
        question: str,
        tool_data: List[Dict[str, Any]],
        collection_summary: str,
        missing_reasons: List[str],
    ) -> Dict[str, Any]:
        rows = []
        for item in tool_data[:10]:
            rows.append({
                "tool": item.get("tool", "unknown"),
                "result": item.get("data", "")[:200] or "未获取到",
            })

        notes = list(missing_reasons[:5])
        if not rows:
            notes.append("未能从工具结果中归一化出更细粒度的数据表。")

        return QueryResult.model_validate({
            "query_target": question,
            "collection_summary": collection_summary,
            "columns": [
                {"key": "tool", "label": "工具"},
                {"key": "result", "label": "结果摘要"},
            ],
            "rows": rows,
            "notes": notes,
            "missing": [{"field": "result", "reason": reason} for reason in missing_reasons[:5]],
            "sources": [],
        }).model_dump()

    def _plan_evidence_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict],
        layer_analysis: str = "",
        context_archive_ref: str = "",
        layer_archive_ref: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
        failure_reason: str = "",
        existing_plan: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple:
        """
        调用 LLM 规划证据采集

        Returns:
            (evidence_plan_list, intermediate_events_list, llm_result_text)
            llm_result_text: LLM 的完整输出文本（包含工具调用结果和分析）
        """
        if getattr(self, 'ai_call', None) is None:
            logger.warning("⚠️ [evidence] ai_call 未设置，无法生成 Pydantic evidence_plan")
            return [], [], ""
        try:
            layer_str = layer.value if layer else "L2"
            # possible_scenarios 可能是 str 列表或 dict 列表（含 scenario/probability 字段）
            if possible_scenarios:
                parts = []
                for s in possible_scenarios:
                    if isinstance(s, dict):
                        parts.append(s.get("scenario", str(s)))
                    else:
                        parts.append(str(s))
                scenarios_str = ", ".join(parts)
            else:
                scenarios_str = "未知"

            # 构建 entities 信息用于 prompt
            entities_str = ""
            if key_entities:
                entities_str = "\n".join([
                    f"  - {e.get('type', '')}: {e.get('value', '')}"
                    for e in key_entities[:10]
                ])

            # 构建完整的 system prompt
            system_prompt = get_workflow_prompt(
                "evidence",
                prompt_language=self._get_prompt_language(),
            ).format(
                layer=layer_str,
                possible_scenarios=scenarios_str
            )

            # 添加 entities 信息到 prompt
            if entities_str:
                system_prompt += f"\n\n# 已提取的关键实体\n{entities_str}\n"

            if strict_mode:
                system_prompt += (
                    "\n\n# 上一轮结果被系统拒绝（必须遵守）\n"
                    f"- 失败原因：{failure_reason or '上一轮只返回计划，没有执行工具'}\n"
                    "- 本轮至少执行一条 critical 或 important 级工具调用后，系统才会接受你的结果。\n"
                    "- 在出现真实 tool_result 之前，禁止输出任何“采集完成/证据充分/可以下结论”的表述。\n"
                    "- 计划不是证据，工具名不是证据，command 字段不是证据；只有 tool_result 才是证据。\n"
                    "- 禁止只输出 evidence_plan 就结束。\n"
                    "- 在没有真实 tool_result 之前，不要声称“已采集完成”“完整度 100%”或“证据充分”。\n"
                )

            user_message = self._build_evidence_user_message(
                question=question,
                layer=layer_str,
                layer_handoff=layer_analysis,
                context_archive_ref=context_archive_ref,
                layer_archive_ref=layer_archive_ref or {},
                strict_mode=strict_mode,
                failure_reason=failure_reason,
                existing_plan=existing_plan,
                plan_mode="dynamic_collection",
            )
            if not getattr(self, "_logged_evidence_user_prompt", False):
                logger.info(
                    "📨 [evidence] LLM user prompt | chars=%d strict=%s\n%s",
                    len(user_message),
                    strict_mode,
                    user_message,
                )
                self._logged_evidence_user_prompt = True
            self._archive_node_input(
                {
                    "node": self.node_id,
                    "strict_mode": strict_mode,
                    "question": question,
                    "user_message": user_message,
                    "layer": layer_str,
                    "layer_handoff": layer_analysis,
                    "system_prompt_chars": len(system_prompt),
                    "user_message_chars": len(user_message),
                }
            )

            if existing_plan is not None:
                evidence_plan = self._normalize_evidence_plan(
                    existing_plan,
                    layer_handoff=self._parse_handoff_json(layer_analysis),
                )
                if not evidence_plan:
                    logger.warning("⚠️ [evidence] 既有 evidence_plan 为空，拒绝执行自由文本采证")
                    return [], [], ""
                return self._execute_existing_evidence_plan(
                    question=question,
                    layer=layer,
                    possible_scenarios=possible_scenarios,
                    key_entities=key_entities,
                    layer_analysis=layer_analysis,
                    context_archive_ref=context_archive_ref,
                    layer_archive_ref=layer_archive_ref,
                    evidence_plan=evidence_plan,
                    failure_reason=failure_reason or "沿用既有 Pydantic evidence_plan 执行采证",
                )

            evidence_plan, plan_raw = self._generate_structured_evidence_plan(
                system_prompt=system_prompt,
                user_message=user_message,
                layer_str=layer_str,
            )
            evidence_plan = self._normalize_evidence_plan(
                evidence_plan,
                layer_handoff=self._parse_handoff_json(layer_analysis),
            )
            if not evidence_plan:
                logger.warning("LLM 未返回有效 evidence_plan Pydantic 结构，拒绝进入工具执行")
                return [], [], plan_raw

            return self._execute_existing_evidence_plan(
                question=question,
                layer=layer,
                possible_scenarios=possible_scenarios,
                key_entities=key_entities,
                layer_analysis=layer_analysis,
                context_archive_ref=context_archive_ref,
                layer_archive_ref=layer_archive_ref,
                evidence_plan=evidence_plan,
                failure_reason="Pydantic evidence_plan 已生成，本轮只执行既有计划",
            )

        except Exception as e:
            logger.warning(f"LLM Pydantic evidence_plan 生成或执行失败: {e}")
            return [], [], ""

    def _execute_dynamic_structured_evidence_agent(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict],
        layer_analysis: str,
        context_archive_ref: str,
        layer_archive_ref: Dict[str, Any],
        system_prompt: str,
        user_message: str,
        layer_str: str,
        strict_mode: bool = False,
        failure_reason: str = "",
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        dynamic_message = (
            user_message
            + "\n\n# 动态结构化采证模式\n"
            "- 本轮只有一次 evidence agent 调用。\n"
            "- 你必须根据 layer_handoff 在内部形成最小采证意图。\n"
            "- 然后直接调用必要的真实只读工具采证，不要等待下一轮。\n"
            "- 最后输出简短自然语言采证摘要；结构化收口由后续非流式 Pydantic 调用完成。\n"
        )
        if strict_mode:
            dynamic_message += (
                "\n# 严格重试约束\n"
                f"- 失败原因：{failure_reason or '上一轮没有有效工具证据'}\n"
                "- 本轮至少调用一个 critical 或 important 意图的真实工具。\n"
            )

        early_stop_enabled = self._is_early_stop_enabled(default=True)
        logger.info("🧭 [evidence] early_stop=%s", early_stop_enabled)
        self._active_evidence_plan = []
        try:
            response, thinking_events = self._call_llm(
                dynamic_message,
                system_prompt,
                stop_checker=self._should_stop_collection_early if early_stop_enabled else None,
            )
        finally:
            self._active_evidence_plan = None

        evidence_plan = []
        llm_text = (response.result or "") if response else ""

        return evidence_plan, thinking_events, llm_text

    @staticmethod
    def _structured_evidence_from_response(response: Any) -> Optional[EvidenceCollectionOutput]:
        from app.core.workflow.structured_runtime import StructuredAgentRuntime

        return StructuredAgentRuntime.extract_structured_response(response, EvidenceCollectionOutput)

    def _generate_structured_evidence_plan(
        self,
        system_prompt: str,
        user_message: str,
        layer_str: str,
    ) -> tuple[List[Dict[str, Any]], str]:
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None or not hasattr(ai_call, "call_structured"):
            logger.warning("⚠️ [evidence] ai_call 不支持 call_structured，无法生成 Pydantic evidence_plan")
            return [], ""

        plan_prompt = (
            system_prompt.rstrip()
            + "\n\n# 结构化计划生成模式\n"
            + "- 只生成 evidence_plan，不调用工具。\n"
            + "- 必须使用 Pydantic 结构化输出契约 EvidencePlanOutput。\n"
            + "- 不要输出自然语言总结，不要把工具结果当证据。\n"
        )
        structured, raw = ai_call.call_structured(
            system_prompt=plan_prompt,
            question=user_message,
            schema=EvidencePlanOutput,
            node_id="evidence_plan",
            run_id=getattr(self, "current_run_id", ""),
            max_tokens=2048,
        )
        if structured is None:
            return [], raw
        output = structured.model_dump()
        output.setdefault("layer", layer_str)
        return [item.model_dump() for item in structured.evidence_plan], raw

    def _execute_existing_evidence_plan(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict],
        layer_analysis: str,
        context_archive_ref: str,
        layer_archive_ref: Optional[Dict[str, Any]],
        evidence_plan: List[Dict[str, Any]],
        failure_reason: str,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        layer_str = layer.value if layer else "L2"
        if possible_scenarios:
            parts = []
            for s in possible_scenarios:
                if isinstance(s, dict):
                    parts.append(s.get("scenario", str(s)))
                else:
                    parts.append(str(s))
            scenarios_str = ", ".join(parts)
        else:
            scenarios_str = "未知"

        system_prompt = get_workflow_prompt(
            "evidence",
            prompt_language=self._get_prompt_language(),
        ).format(
            layer=layer_str,
            possible_scenarios=scenarios_str,
        )
        if key_entities:
            entities_str = "\n".join([
                f"  - {e.get('type', '')}: {e.get('value', e.get('name', ''))}"
                for e in key_entities[:10]
            ])
            system_prompt += f"\n\n# 已提取的关键实体\n{entities_str}\n"

        user_message = self._build_evidence_user_message(
            question=question,
            layer=layer_str,
            layer_handoff=layer_analysis,
            context_archive_ref=context_archive_ref,
            layer_archive_ref=layer_archive_ref or {},
            strict_mode=False,
            failure_reason=failure_reason,
            existing_plan=evidence_plan,
            plan_mode="preplanned_execution",
        )

        early_stop_enabled = self._is_early_stop_enabled(default=True)
        logger.info("🧭 [evidence] early_stop=%s", early_stop_enabled)
        self._active_evidence_plan = evidence_plan
        try:
            response, thinking_events = self._call_llm(
                user_message,
                system_prompt,
                stop_checker=self._should_stop_collection_early if early_stop_enabled else None,
            )
        finally:
            self._active_evidence_plan = None

        llm_text = (response.result or "") if response else ""
        if self._has_effective_tool_evidence(thinking_events):
            logger.info("📋 [evidence] 使用 Pydantic evidence_plan 执行采证: %d 项", len(evidence_plan))
            return evidence_plan, thinking_events, llm_text
        logger.warning("⚠️ [evidence] Pydantic evidence_plan 已生成，但执行阶段未产生有效工具结果")
        return evidence_plan, thinking_events, llm_text

    def _archive_node_input(self, payload: Dict) -> None:
        run_id = getattr(self, "current_run_id", "")
        if not run_id:
            return
        try:
            from app.core.context.archive import ContextArchive

            ContextArchive(run_id=run_id).write_node_artifacts(
                node_id=self.node_id,
                input_payload=payload,
            )
        except Exception as exc:
            logger.warning("⚠️ [evidence] 写入 node input archive 失败: %s", exc)

    @staticmethod
    def _build_evidence_user_message(
        question: str,
        layer: str,
        layer_handoff: str,
        context_archive_ref: str = "",
        layer_archive_ref: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
        failure_reason: str = "",
        existing_plan: Optional[List[Dict[str, Any]]] = None,
        plan_mode: str = "dynamic_collection",
    ) -> str:
        strict_section = ""
        if existing_plan:
            plan_lines = ["# 既有 evidence_plan（系统注入，禁止重写）"]
            for item in existing_plan:
                if not isinstance(item, dict):
                    continue
                plan_lines.append(
                    "- {id}: level={level}, tool={tool}, command={command}, tool_args={tool_args}, purpose={purpose}".format(
                        id=item.get("id", ""),
                        level=item.get("level", ""),
                        tool=item.get("tool", ""),
                        command=item.get("command", ""),
                        tool_args=json.dumps(item.get("tool_args") or {}, ensure_ascii=False, default=str),
                        purpose=item.get("purpose", ""),
                    )
                )
            strict_section = f"""

# 既有 evidence_plan（本轮不要重写）
上一轮已生成有效 Pydantic evidence_plan，但没有执行真实工具。本轮必须沿用下列计划，直接调用工具采证，不要重新输出 evidence_plan。
{chr(10).join(plan_lines)}
- {failure_reason or '请直接按既有计划执行工具'}
"""
        elif strict_mode:
            strict_section = f"""

# 上一轮结果被系统拒绝
- 失败原因：{failure_reason or '上一轮只返回计划，没有执行工具'}
- 本轮必须先调用至少一个 critical 或 important 级真实工具。
- 没有 tool_result 前禁止输出“证据充分/采集完成/完整度 100%”。
"""
        archive_refs = layer_archive_ref or {}
        archive_lines = []
        context_root = (context_archive_ref or "").strip()
        if context_root:
            archive_lines.extend([
                "# context archive",
                "- context archive 已落盘，仅供人工排障；evidence 默认不要读取归档。",
                "- 归档不是当前环境证据，不要把读取归档写入 evidence_plan。",
            ])
        if archive_refs.get("handoff_ref"):
            archive_lines.append("- layer handoff 已由上方 layer_handoff 注入；不要重复读取归档。")
        archive_section = "\n".join(archive_lines).strip() if archive_lines else "无"
        if existing_plan:
            plan_protocol = """- 本轮已有 Pydantic evidence_plan，禁止重新输出或改写 evidence_plan。
- 直接按既有 evidence_plan 调用至少一个 critical 或 important 级真实工具。
- 如果计划项提供 tool_args，必须按 tool_args 调用 MCP 工具；不要从 command 文本重新猜 MCP 参数。
- LLM 必须自己决定并调用工具；计划不是证据。
- 工具调用必须尽量逐项完成既有计划，最终消息不要新增未写入 plan 的“已采集计划项”。
- evidence_plan 中的 tool 字段必须是 Available tools 中真实存在的工具名。不要自行创造 kubectl_logs 等不存在的工具；需要执行未封装的只读 kubectl 命令时使用 run_bash_command。"""
        elif plan_mode == "preplanned_execution":
            plan_protocol = """- 采证计划已由 `EvidencePlanOutput` Pydantic schema 单独生成；执行阶段不要重写 evidence_plan。
- 如果本轮进入工具执行，必须调用至少一个 critical 或 important 级真实工具。
- LLM 必须自己决定并调用工具；计划不是证据。
- 后续工具调用必须尽量逐项完成 Pydantic plan 中的项目，最终消息不要新增未写入 plan 的“已采集计划项”。
- evidence_plan 中的 tool 字段必须是 Available tools 中真实存在的工具名。不要自行创造 kubectl_logs 等不存在的工具；需要执行未封装的只读 kubectl 命令时使用 run_bash_command。"""
        else:
            plan_protocol = """- 本轮使用普通工具 agent 采集真实证据；采证计划由 `EvidencePlanOutput` Pydantic schema 单独生成。
- 必须先在内部形成最小采证意图，再直接调用真实工具；必须调用至少一个 critical 或 important 级真实工具。
- LLM 必须自己决定并调用工具；计划不是证据。
- evidence_plan 中的 tool 字段必须是 Available tools 中真实存在的工具名。不要自行创造 kubectl_logs 等不存在的工具；需要执行未封装的只读 kubectl 命令时使用 run_bash_command。"""
        handoff_obj = EvidenceCollectorNode._parse_handoff_json(layer_handoff)
        compact_handoff = EvidenceCollectorNode._compact_layer_handoff_for_prompt(handoff_obj, layer_handoff)
        abnormal_summary_section = EvidenceCollectorNode._format_current_abnormal_summary_for_prompt(handoff_obj)
        return f"""# 用户原始问题
{question}

# 上游定位结构化结果 layer_handoff
{compact_handoff}

{abnormal_summary_section}

# Runbook 语义匹配要求
- 根据 Available Runbooks/catalog 的 description、runbook_id、状态关键字与 layer_handoff 中的 abnormal_groups、pod_status_keyword、pod_abnormal_type、active_signals 做语义匹配。
- 如果某个 Pod 异常 runbook 明显匹配当前 Pod 异常状态，evidence_plan 必须包含一条 level=reference、tool=fetch_runbook 的参考步骤；多个当前异常类型可以获取多个明显匹配的 runbook。
- 匹配到 runbook 时，fetch_runbook 必须在真实环境工具前执行。先读 runbook，再把 runbook 的关键检查点转化为 kubectl/prometheus 等真实环境验证步骤。
- 不要依赖代码注入的 runbook 推荐字段；是否调用 runbook 必须由你根据 catalog 描述和当前异常信号自主判断。
- runbook 是参考知识，不是真实环境证据；fetch_runbook 后仍必须调用 kubectl/prometheus 等真实环境工具验证关键事实。
- 如果你在分析中认为“应该查看/参考某个 runbook”，必须把它写入 evidence_plan 并实际调用 fetch_runbook；禁止只在思考中提到 runbook 却不调用。
- 只有当 catalog 中没有明显匹配项，或上游判断为 HEALTHY/QUERY，才允许不调用 fetch_runbook；这种情况下最终消息必须说明“未发现明显匹配的 Pod 异常 runbook”。

# 归档上下文（非采证主线）
{archive_section}

# 当前节点职责
你是 evidence 节点。核心任务是找证据：为上游定位出的 Pod 异常状态的证据提供真实环境验证。你必须以 layer_handoff 的 abnormal_groups、issue_groups、abnormal_pods、current_abnormal_summary 为覆盖基准调用真实只读工具采集证据。

# 强约束
{plan_protocol}
- 如果 layer_handoff 提供 abnormal_groups/issue_groups，evidence_plan 应优先覆盖每个当前异常组的最小关键证据；不要只围绕单个 Pod 而完全忽略其他异常组。
- 影响范围最大的异常组做完整验证；其他异常组做最小验证。单个 Pod 不能替代 abnormal_pods/abnormal_groups 的覆盖要求。
- 对非主要影响面的 issue_group 只做最小验证：当前状态 + 一个最关键配置/事件信号即可，不要展开成长链路。
- 必须把 current_abnormal_summary.status_counts 作为审查核心；非 Running/Completed/Succeeded/Ready/Bound/Active 的状态都需要至少最小验证。
- 必须优先围绕影响范围最大的异常组验证它为什么进入当前 pod_status_keyword / pod_abnormal_type；不要把采证范围收缩成单个 Pod，也不要先做大范围无关集群扫描。
- 必须保持 namespace、Pod、Service、Node、资源类型不漂移。
- 如果工具结果显示对象不存在、namespace 不匹配、事件为空、命令失败，必须把它视为冲突或负向证据，不能当作成功验证。
- 如果 Available Runbooks/catalog 中存在明显匹配当前 Pod 异常状态的 runbook，应先执行 fetch_runbook 参考步骤；但不能只 fetch_runbook 后结束，必须继续调用真实环境工具。reference/runbook 步骤不是证据，不计入 critical/important 完整度。存在明显匹配 runbook 却未调用 fetch_runbook 时，本轮采证视为不完整。
- 不要把 context_archive_ref、archive_ref、raw_ref、summary_ref、structured_ref 等路径当作采证任务；默认不要计划读取归档文件。
{strict_section}
# 输出
{"直接执行既有 Pydantic evidence_plan 中的必要工具，最后输出简短证据结论。" if existing_plan else "调用必要真实工具后输出简短证据结论；不要手写 EvidenceCollectionOutput。"}"""

    @staticmethod
    def _parse_handoff_json(layer_handoff: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(layer_handoff) if layer_handoff else {}
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _compact_layer_handoff_for_prompt(handoff: Dict[str, Any], raw_handoff: str) -> str:
        if not handoff:
            return raw_handoff or "{}"

        keep_keys = {
            "layer",
            "derived_layer",
            "confidence",
            "primary_problem",
            "reasoning",
            "abnormal_pods",
            "abnormal_groups",
            "pod_status_keyword",
            "pod_abnormal_type",
            "status_category",
            "active_entities",
            "active_signals",
            "possible_scenarios",
            "must_verify",
            "issue_groups",
            "current_abnormal_summary",
        }
        compact = {
            key: EvidenceCollectorNode._strip_archive_refs(handoff[key])
            for key in keep_keys
            if key in handoff
        }
        summary = compact.get("current_abnormal_summary")
        if isinstance(summary, dict):
            compact["current_abnormal_summary"] = {
                key: summary[key]
                for key in ("source", "status_counts", "total_abnormal", "selected_rows")
                if key in summary
            }
        return json.dumps(compact, ensure_ascii=False, default=str)

    @staticmethod
    def _strip_archive_refs(value: Any) -> Any:
        archive_keys = {
            "archive_ref",
            "context_archive_ref",
            "raw_ref",
            "summary_ref",
            "structured_ref",
            "handoff_ref",
            "input_ref",
            "output_ref",
            "full_analysis_ref",
        }
        if isinstance(value, dict):
            return {
                key: EvidenceCollectorNode._strip_archive_refs(item)
                for key, item in value.items()
                if key not in archive_keys
            }
        if isinstance(value, list):
            return [EvidenceCollectorNode._strip_archive_refs(item) for item in value]
        return value

    @staticmethod
    def _format_current_abnormal_summary_for_prompt(handoff: Dict[str, Any]) -> str:
        summary = handoff.get("current_abnormal_summary") if isinstance(handoff, dict) else {}
        issue_groups = handoff.get("issue_groups") if isinstance(handoff, dict) else []
        lines = ["# 当前异常结构化摘要（必须优先审查）"]

        status_counts = summary.get("status_counts") if isinstance(summary, dict) else {}
        if isinstance(status_counts, dict) and status_counts:
            lines.append("status_counts:")
            for status, count in status_counts.items():
                lines.append(f"- {status}: {count}")
        else:
            lines.append("status_counts: 未提供；从 issue_groups/abnormal_pods 进行最小覆盖。")

        selected_rows = summary.get("selected_rows") if isinstance(summary, dict) else []
        if isinstance(selected_rows, list) and selected_rows:
            lines.append("selected_rows:")
            for row in selected_rows[:10]:
                lines.append(f"- {row}")

        if isinstance(issue_groups, list) and issue_groups:
            lines.append("issue_groups:")
            for idx, group in enumerate(issue_groups[:8], start=1):
                if not isinstance(group, dict):
                    continue
                group_id = group.get("group_id") or f"g{idx}"
                statuses = ", ".join(str(s) for s in group.get("status_keywords", []) if s)
                abnormal_type = group.get("pod_abnormal_type", "")
                layers = ", ".join(str(l) for l in group.get("compatible_layers", []) if l)
                entities = group.get("entities") or group.get("primary_entities") or []
                entity_texts = []
                if isinstance(entities, list):
                    for entity in entities[:5]:
                        if not isinstance(entity, dict):
                            continue
                        namespace = entity.get("namespace", "")
                        name = entity.get("name", "")
                        kind = entity.get("kind", "Pod")
                        entity_texts.append(f"{kind}/{namespace}/{name}" if namespace else f"{kind}/{name}")
                lines.append(
                    f"- {group_id}: statuses={statuses or 'unknown'}, "
                    f"type={abnormal_type or 'unknown'}, layers={layers or 'unknown'}, "
                    f"entities={', '.join(entity_texts) or 'unknown'}"
                )

        lines.append(
            "要求：非 Running/Completed/Succeeded/Ready/Bound/Active 的状态都需要至少最小验证；"
            "主异常组做完整验证，非主异常组验证当前状态 + 一个最关键事件/配置/依赖信号。"
        )
        return "\n".join(lines)

    def _get_plan_protocol_failure_reason(
        self,
        evidence_plan: List[Dict],
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        """检查 evidence 是否遵守了先 plan 后执行的协议。"""
        if evidence_plan:
            if not self._has_effective_tool_evidence(thinking_events):
                return "上一轮只返回 evidence_plan，没有任何有效工具证据，系统已拒绝该结果"
            return ""

        return "上一轮没有可用的 Pydantic evidence_plan，系统已拒绝该结果"

    @staticmethod
    def _plan_exists_without_tool_results(reason: str) -> bool:
        return "只返回 evidence_plan" in (reason or "")

    @staticmethod
    def _validate_evidence_plan_payload(parsed: Any) -> List[Dict]:
        if isinstance(parsed, dict) and "evidence_plan" in parsed:
            try:
                output = EvidencePlanOutput.model_validate(parsed)
            except Exception as exc:
                logger.warning("⚠️ [evidence] evidence_plan 结构化校验失败: %s", exc)
                return []
            return [item.model_dump() for item in output.evidence_plan]
        if isinstance(parsed, list):
            try:
                output = EvidencePlanOutput.model_validate({
                    "layer": "",
                    "evidence_plan": parsed,
                    "collection_strategy": "",
                })
            except Exception as exc:
                logger.warning("⚠️ [evidence] evidence_plan 列表结构化校验失败: %s", exc)
                return []
            return [item.model_dump() for item in output.evidence_plan]
        return []

    @classmethod
    def _normalize_evidence_plan(
        cls,
        evidence_plan: List[Dict[str, Any]],
        layer_handoff: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Bound and deduplicate LLM-generated evidence plans.

        This keeps dynamic planning but removes repeated variants for the same
        evidence dimension, e.g. curl/telnet/nc against the same registry.
        """
        normalized: List[Dict[str, Any]] = []
        seen_signatures: set[tuple[str, str, str]] = set()
        max_items = 10

        for item in evidence_plan or []:
            if not isinstance(item, dict):
                continue
            item = cls._normalize_plan_tool_args(item)
            signature = cls._evidence_plan_signature(item)
            if signature in seen_signatures:
                logger.info(
                    "♻️ [evidence] 跳过重复采证计划: id=%s tool=%s command=%s",
                    item.get("id", ""),
                    item.get("tool", ""),
                    item.get("command", ""),
                )
                continue
            seen_signatures.add(signature)
            normalized.append(item)
            if len(normalized) >= max_items:
                logger.info("✂️ [evidence] evidence_plan 超过 %d 项，已截断", max_items)
                break

        return cls._ensure_abnormal_group_plan_coverage(normalized, layer_handoff or {})

    @classmethod
    def _normalize_plan_tool_args(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(item)
        if isinstance(normalized.get("tool_args"), dict) and normalized["tool_args"]:
            return normalized

        tool = cls._normalize_plan_text(normalized.get("tool"))
        command = str(normalized.get("command") or "")
        if tool == "kubectl_events":
            tool_args = cls._derive_kubectl_events_tool_args(command)
            if tool_args:
                normalized["tool_args"] = tool_args
        return normalized

    @staticmethod
    def _derive_kubectl_events_tool_args(command: str) -> Dict[str, str]:
        text = command or ""
        namespace = ""
        namespace_match = re.search(r"(?:^|\s)-n\s+([^\s]+)|(?:^|\s)--namespace(?:=|\s+)([^\s]+)", text)
        if namespace_match:
            namespace = namespace_match.group(1) or namespace_match.group(2) or ""

        resource_name = ""
        name_match = re.search(r"involvedObject\.name=([^,\s]+)", text)
        if name_match:
            resource_name = name_match.group(1)
        if not resource_name:
            object_match = re.search(r"\b(?:pod|pods)/([A-Za-z0-9_.-]+)", text, re.IGNORECASE)
            if object_match:
                resource_name = object_match.group(1)

        args: Dict[str, str] = {}
        if resource_name:
            args["resource_type"] = "pod"
            args["resource_name"] = resource_name
        if namespace:
            args["namespace"] = namespace
        return args

    @classmethod
    def _ensure_abnormal_group_plan_coverage(
        cls,
        evidence_plan: List[Dict[str, Any]],
        layer_handoff: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Ensure every abnormal group has at least one countable plan intent.

        The LLM can still choose the plan, but coverage is a deterministic
        contract: if current state contains multiple abnormal groups, a plan
        that only covers one group is incomplete and must be normalized before
        execution.
        """
        groups = layer_handoff.get("abnormal_groups") or layer_handoff.get("issue_groups") or []
        if not isinstance(groups, list) or not groups:
            return evidence_plan

        normalized = list(evidence_plan or [])
        covered_scopes = {
            str(item.get("target_scope") or "").strip().lower()
            for item in normalized
            if isinstance(item, dict)
            and item.get("counts_for_completeness", True) is not False
            and str(item.get("target_scope") or "").strip()
        }
        existing_ids = {
            str(item.get("id") or "")
            for item in normalized
            if isinstance(item, dict)
        }

        for index, group in enumerate(groups, start=1):
            if not isinstance(group, dict):
                continue
            group_id = str(group.get("group_id") or f"g{index}")
            scope = f"group:{group_id}".lower()
            if scope in covered_scopes:
                continue

            item = cls._build_minimal_group_plan_item(group=group, group_id=group_id, existing_ids=existing_ids)
            if not item:
                continue
            normalized.append(item)
            existing_ids.add(item["id"])
            covered_scopes.add(scope)

        return normalized

    @classmethod
    def _build_minimal_group_plan_item(
        cls,
        group: Dict[str, Any],
        group_id: str,
        existing_ids: set[str],
    ) -> Dict[str, Any]:
        entities = group.get("entities") or group.get("primary_entities") or []
        entity = next((item for item in entities if isinstance(item, dict) and item.get("name")), {})
        if not entity:
            return {}

        name = cls._normalize_plan_text(entity.get("name"))
        namespace = cls._normalize_plan_text(entity.get("namespace"))
        abnormal_type = str(group.get("pod_abnormal_type") or "")
        statuses = ", ".join(str(s) for s in group.get("status_keywords", []) if s) or "Unknown"
        base_id = f"auto_{group_id}_coverage"
        item_id = base_id
        suffix = 2
        while item_id in existing_ids:
            item_id = f"{base_id}_{suffix}"
            suffix += 1

        if abnormal_type == "TerminatingStuck":
            return {
                "id": item_id,
                "description": f"最小验证异常组 {group_id}: {namespace}/{name} 是否仍处于 {statuses}，并检查 deletionTimestamp/finalizers",
                "level": "important",
                "tool": "kubectl_get_yaml",
                "command": f"kubectl get pod {name} -n {namespace} -o yaml",
                "tool_args": {"resource_type": "pod", "resource_name": name, "namespace": namespace},
                "purpose": "覆盖 TerminatingStuck 异常组，确认当前状态和 finalizer 删除阻塞信号",
                "evidence_type": "pod_lifecycle",
                "target_scope": f"group:{group_id}",
                "acceptable_tools": ["kubectl_get_yaml", "kubectl_describe", "kubectl_get_by_name"],
                "counts_for_completeness": True,
            }

        return {
            "id": item_id,
            "description": f"最小验证异常组 {group_id}: {namespace}/{name} 的当前 {statuses} 事件/状态",
            "level": "important",
            "tool": "kubectl_events",
            "command": f"kubectl get events -n {namespace} --field-selector involvedObject.name={name}",
            "tool_args": {"resource_type": "pod", "resource_name": name, "namespace": namespace},
            "purpose": "覆盖当前异常组，确认代表 Pod 的关键事件或当前异常状态",
            "evidence_type": "pod_events",
            "target_scope": f"group:{group_id}",
            "acceptable_tools": ["kubectl_events", "kubectl_describe", "kubectl_get_by_name", "kubectl_get_by_kind_in_cluster"],
            "counts_for_completeness": True,
        }

    @classmethod
    def _evidence_plan_signature(cls, item: Dict[str, Any]) -> tuple[str, str, str]:
        tool = cls._normalize_plan_text(item.get("tool"))
        command = cls._normalize_plan_text(item.get("command"))
        purpose = cls._normalize_plan_text(item.get("purpose"), item.get("description"))
        target = cls._extract_plan_target(command)
        intent = cls._classify_plan_intent(command, purpose)

        if intent in {"registry_connectivity", "dns_connectivity"} and target:
            return ("connectivity", intent, target)
        if intent == "runtime_info":
            return (tool, intent, target or "runtime")
        if intent and target:
            return (tool, intent, target)
        return (tool, intent or purpose[:80], command[:160])

    @staticmethod
    def _normalize_plan_text(*values: Any) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return " ".join(value.lower().split())
        return ""

    @staticmethod
    def _extract_plan_target(command: str) -> str:
        text = command or ""
        resource_target = EvidenceCollectorNode._extract_plan_resource_target(text)
        if resource_target:
            kind = resource_target.get("kind", "")
            namespace = resource_target.get("namespace", "")
            name = resource_target.get("name", "")
            if namespace:
                return f"{kind}/{namespace}/{name}"
            return f"{kind}/{name}"

        url_match = re.search(r"https?://([^/\s:]+)", text, re.IGNORECASE)
        if url_match:
            return url_match.group(1).lower()

        host_match = re.search(
            r"\b([a-z0-9][a-z0-9.-]*\.(?:io|com|net|org|cn|local))\b",
            text,
            re.IGNORECASE,
        )
        if host_match:
            return host_match.group(1).lower()

        node_match = re.search(r"\bnode\s+([a-z0-9]([-a-z0-9]*[a-z0-9])?)\b", text, re.IGNORECASE)
        if node_match:
            return f"node/{node_match.group(1)}"

        return ""

    @staticmethod
    def _extract_plan_resource_target(command: str) -> Dict[str, str]:
        """Extract a concrete kubectl resource target from common command forms.

        Supported examples:
        - kubectl describe pod name -n ns
        - kubectl describe pod -n ns name
        - kubectl get pod/name -n ns -o yaml
        - kubectl get pod -n ns name -o yaml
        """
        text = command or ""
        if "kubectl" not in text and not re.search(r"\b(get|describe)\s+", text, re.IGNORECASE):
            return {}

        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
        if not tokens:
            return {}

        namespace = ""
        cleaned: List[str] = []
        skip_next = False
        for idx, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue
            lower = token.lower()
            if lower in {"-n", "--namespace"}:
                if idx + 1 < len(tokens):
                    namespace = tokens[idx + 1].strip("'\"")
                    skip_next = True
                continue
            if lower.startswith("--namespace="):
                namespace = token.split("=", 1)[1].strip("'\"")
                continue
            cleaned.append(token)

        verbs = {"get", "describe", "logs", "events"}
        kind_aliases = {
            "pod": "pod",
            "pods": "pod",
            "po": "pod",
            "node": "node",
            "nodes": "node",
            "no": "node",
            "secret": "secret",
            "secrets": "secret",
            "configmap": "configmap",
            "configmaps": "configmap",
            "cm": "configmap",
            "pvc": "pvc",
            "pvcs": "pvc",
            "persistentvolumeclaim": "pvc",
            "persistentvolumeclaims": "pvc",
            "service": "service",
            "services": "service",
            "svc": "service",
            "deployment": "deployment",
            "deployments": "deployment",
            "replicaset": "replicaset",
            "replicasets": "replicaset",
            "rs": "replicaset",
            "daemonset": "daemonset",
            "daemonsets": "daemonset",
            "ds": "daemonset",
            "statefulset": "statefulset",
            "statefulsets": "statefulset",
            "sts": "statefulset",
            "event": "event",
            "events": "event",
            "networkpolicy": "networkpolicy",
            "networkpolicies": "networkpolicy",
        }
        value_flags = {
            "-o",
            "--output",
            "-l",
            "--selector",
            "--field-selector",
            "--sort-by",
            "--container",
            "-c",
            "--since",
            "--tail",
        }
        boolean_flags = {
            "-A",
            "--all-namespaces",
            "--show-labels",
            "--previous",
            "--watch",
            "-w",
            "--ignore-not-found",
        }

        verb_index = next((i for i, token in enumerate(cleaned) if token.lower() in verbs), -1)
        if verb_index < 0:
            return {}

        i = verb_index + 1
        while i < len(cleaned):
            token = cleaned[i]
            lower = token.lower()
            if lower in boolean_flags:
                i += 1
                continue
            if lower in value_flags:
                i += 2
                continue
            if lower.startswith("-"):
                i += 1
                continue
            if "/" in lower:
                kind_part, name_part = lower.split("/", 1)
                kind = kind_aliases.get(kind_part)
                if kind and name_part:
                    return {"kind": kind, "namespace": namespace.lower(), "name": name_part.strip("'\"").lower()}
            kind = kind_aliases.get(lower)
            if kind:
                j = i + 1
                while j < len(cleaned):
                    candidate = cleaned[j]
                    candidate_lower = candidate.lower()
                    if candidate_lower in boolean_flags:
                        j += 1
                        continue
                    if candidate_lower in value_flags:
                        j += 2
                        continue
                    if candidate_lower.startswith("-"):
                        j += 1
                        continue
                    if candidate_lower in kind_aliases:
                        return {"kind": kind, "namespace": namespace.lower(), "name": ""}
                    if re.match(r"^[a-z0-9]([-a-z0-9.]*[a-z0-9])?$", candidate_lower):
                        return {"kind": kind, "namespace": namespace.lower(), "name": candidate_lower.strip("'\"")}
                    break
                return {"kind": kind, "namespace": namespace.lower(), "name": ""}
            i += 1

        return {}

    @staticmethod
    def _classify_plan_intent(command: str, purpose: str) -> str:
        text = f"{command}\n{purpose}"
        if re.search(r"\b(curl|wget|telnet|nc|ping)\b|连通|可达|访问|registry|docker\.io|镜像仓库", text, re.IGNORECASE):
            if re.search(r"dns|nslookup|dig|解析", text, re.IGNORECASE):
                return "dns_connectivity"
            return "registry_connectivity"
        if re.search(r"\bdescribe\s+(pod|po)\b|events?|事件", text, re.IGNORECASE):
            return "pod_events"
        if re.search(r"\b(docker|containerd|crictl|runtime)\b.*\b(info|version|status)\b|容器运行时|docker 守护进程", text, re.IGNORECASE):
            return "runtime_info"
        if re.search(r"\bget\s+(pod|po)\b.*-o\s+yaml|yaml|imagepullsecrets?|镜像|配置", text, re.IGNORECASE):
            return "pod_config"
        if re.search(r"\b(secret|imagepullsecret|dockerconfigjson)\b", text, re.IGNORECASE):
            return "secret_config"
        if re.search(r"\b(logs?)\b|日志", text, re.IGNORECASE):
            return "pod_logs"
        if re.search(r"\bdescribe\s+node\b|kubelet|节点", text, re.IGNORECASE):
            return "node_state"
        return ""

    def _should_stop_collection_early(self, thinking_events: list) -> bool:
        """
        动态采证提前停止条件：
        - 已解析到 evidence_plan
        - 至少已有一次成功工具调用
        - 所有 critical + important 级计划证据都已被当前工具结果满足
        或者
        - 没有 critical/important 项时，全部计划项都已满足
        """
        evidence_plan = getattr(self, "_active_evidence_plan", None)
        if not evidence_plan:
            return False

        successful_tools = [
            ev for ev in thinking_events
            if ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and (
                ev.get("semantic_success", True) is not False
                or self._is_diagnostic_negative_tool_result(
                    ev.get("tool_name", ""),
                    ev.get("result", ev.get("result_preview", "")),
                    ev.get("structured") or {},
                )
            )
        ]
        if not successful_tools:
            return False

        evidence_items = self._build_evidence_items_from_thinking(evidence_plan, thinking_events)
        planned_items = [
            e for e in evidence_items
            if getattr(e, "source", "") in ("thinking_match", "thinking_negative_match", "planned")
        ]
        required_items = [
            e for e in planned_items
            if e.level in (EvidenceLevel.CRITICAL, EvidenceLevel.IMPORTANT)
        ]

        if required_items:
            missing_required = [e.description for e in required_items if not e.collected]
            if missing_required:
                return False

            self._early_stop_state = {
                "triggered": True,
                "reason": "critical 和 important 级证据均已满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }
            return True

        all_collected = bool(planned_items) and all(e.collected for e in planned_items)
        if all_collected:
            self._early_stop_state = {
                "triggered": True,
                "reason": "计划中的证据已全部满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }
        return all_collected

    def _derive_early_stop_state(self, evidence_plan: List[Dict], evidence_items: List[EvidenceItem]) -> Dict[str, Any]:
        """根据计划和采集结果后验推导提前停止状态，保证输出字段稳定。"""
        planned_items = [
            e for e in evidence_items
            if getattr(e, "source", "") in ("thinking_match", "thinking_negative_match", "planned")
        ]
        required_items = [
            e for e in planned_items
            if e.level in (EvidenceLevel.CRITICAL, EvidenceLevel.IMPORTANT)
        ]

        if required_items and all(e.collected for e in required_items):
            return {
                "triggered": True,
                "reason": "critical 和 important 级证据均已满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }

        if planned_items and all(e.collected for e in planned_items):
            return {
                "triggered": True,
                "reason": "计划中的证据已全部满足，提前停止后续采集",
                "required_levels": ["critical", "important"],
            }

        return {
            "triggered": False,
            "reason": "",
            "required_levels": ["critical", "important"],
        }

    # 非证据类工具（LLM 自用的辅助工具），不计入证据统计
    _NON_EVIDENCE_TOOLS = {
        "todowrite",
        "todo_write",
        "todo",
        # Archive reads are auxiliary context lookups. They can point the model
        # to raw files, but they are not fresh cluster observations and must not
        # become positive evidence by themselves.
        "read_context_archive",
        "fetch_runbook",
    }

    def _build_evidence_items_from_thinking(
        self,
        evidence_plan: List[Dict],
        thinking_events: list,
    ) -> List[EvidenceItem]:
        """
        从 thinking_events（AICall agent loop 真实工具调用）构建证据项列表。

        匹配逻辑：
        1. 有 plan 时：plan item 与工具调用匹配，未匹配的工具作为额外采集
        2. 无 plan 但有工具调用时：从工具调用反向构建证据项（过滤非证据工具）
        3. 无 plan 且无工具调用时：返回空列表（completeness 由 _calculate_completeness 处理）
        """
        evidence_items = []

        # 从 thinking_events 提取可用于证据匹配的工具调用。部分只读探测
        # 命令的失败结果本身就是诊断证据，例如 curl registry 超时。
        successful_tools = []
        for ev in thinking_events:
            if (
                ev.get("type") == "tool_result"
                and ev.get("status") == "success"
            ):
                result = ev.get("result", ev.get("result_preview", ""))
                structured = ev.get("structured") or {}
                semantic_success = ev.get("semantic_success", True) is not False
                diagnostic_negative = self._is_diagnostic_negative_tool_result(
                    ev.get("tool_name", ""),
                    result,
                    structured,
                )
                if not semantic_success and not diagnostic_negative:
                    continue
                successful_tools.append({
                    "tool_name": ev.get("tool_name", ""),
                    "result": result,
                    "tool_args": ev.get("tool_args") or {},
                    "structured": structured,
                    "raw_ref": ev.get("raw_ref"),
                    "summary_ref": ev.get("summary_ref"),
                    "diagnostic_negative": diagnostic_negative,
                })

        # ── 无 plan 时：从工具调用反向构建证据项 ──
        if not evidence_plan and successful_tools:
            real_tools = [
                t for t in successful_tools
                if t["tool_name"].lower() not in self._NON_EVIDENCE_TOOLS
            ]
            skipped = len(successful_tools) - len(real_tools)
            if skipped:
                logger.debug("📊 [evidence] 过滤 %d 个非证据工具 (TodoWrite 等)", skipped)

            for ti, tool in enumerate(real_tools):
                evidence_items.append(EvidenceItem(
                    id=f"auto_{ti}",
                    description=f"工具采集: {tool['tool_name']}",
                    level=EvidenceLevel.IMPORTANT,
                    weight=0.2,
                    collected=True,
                    value=tool["result"][:500] if tool["result"] else None,
                    source="thinking_auto",
                ))

            logger.info("📊 [evidence] 证据统计(无plan模式): "
                        "thinking_tools=%d 个成功调用, 有效证据=%d, 过滤=%d",
                        len(successful_tools), len(real_tools), skipped)
            return evidence_items

        # ── 有 plan 时：正常匹配流程 ──
        matched_tool_indices = set()
        adjudicated_matches = self._adjudicate_plan_tool_matches(evidence_plan, successful_tools)

        for plan_item in evidence_plan:
            plan_tool = (plan_item.get("tool") or "").lower()
            plan_cmd = (plan_item.get("command") or "").lower()
            plan_desc = (plan_item.get("description") or "").lower()
            plan_intent = str(plan_item.get("evidence_type") or "").lower()
            acceptable_tools = [
                str(tool or "").lower()
                for tool in (plan_item.get("acceptable_tools") or [])
            ]
            item_id = plan_item.get("id", f"ev_{len(evidence_items)}")

            level_str = plan_item.get("level", "important")
            level = EvidenceLevel.IMPORTANT
            if level_str == "critical":
                level = EvidenceLevel.CRITICAL
            elif level_str in {"optional", "reference"}:
                level = EvidenceLevel.OPTIONAL

            matched = False
            matched_result = None
            matched_tool = None
            if adjudicated_matches is not None:
                adjudicated_index = adjudicated_matches.get(str(item_id))
                if adjudicated_index is not None and 0 <= adjudicated_index < len(successful_tools):
                    matched = True
                    matched_tool = successful_tools[adjudicated_index]
                    matched_result = matched_tool["result"]
                    matched_tool_indices.add(adjudicated_index)
                else:
                    for ti, tool in enumerate(successful_tools):
                        if ti in matched_tool_indices or not tool.get("diagnostic_negative"):
                            continue
                        tn = tool["tool_name"].lower()
                        if self._tool_result_matches_plan(
                            plan_tool=plan_tool,
                            plan_cmd=plan_cmd,
                            plan_desc=plan_desc,
                            tool_name=tn,
                            result=tool.get("result", ""),
                            structured=tool.get("structured") or {},
                            tool_args=tool.get("tool_args") or {},
                            plan_intent=plan_intent,
                            acceptable_tools=acceptable_tools,
                        ):
                            matched = True
                            matched_tool = tool
                            matched_result = tool["result"]
                            matched_tool_indices.add(ti)
                            break
            else:
                for ti, tool in enumerate(successful_tools):
                    if ti in matched_tool_indices:
                        continue
                    tn = tool["tool_name"].lower()
                    if self._tool_result_matches_plan(
                        plan_tool=plan_tool,
                        plan_cmd=plan_cmd,
                        plan_desc=plan_desc,
                        tool_name=tn,
                        result=tool.get("result", ""),
                        structured=tool.get("structured") or {},
                        tool_args=tool.get("tool_args") or {},
                        plan_intent=plan_intent,
                        acceptable_tools=acceptable_tools,
                    ):
                        matched = True
                        matched_tool = tool
                        matched_result = tool["result"]
                        matched_tool_indices.add(ti)
                        break

            outcome = "positive"
            source = "thinking_match" if matched else "planned"
            if matched_tool and matched_tool.get("diagnostic_negative"):
                outcome = "negative"
                source = "thinking_negative_match"
            elif not matched:
                outcome = "unknown"

            evidence_items.append(EvidenceItem(
                id=item_id,
                description=plan_item.get("description", "未知证据"),
                level=level,
                weight=0.2,
                collected=matched,
                value=matched_result,
                source=source,
                outcome=outcome,
            ))

        # 有 plan 时，最终 evidence_items 必须与 plan 对齐。
        # 未规划但实际执行的工具结果保留在 tool_data/thinking_events 中，不能混入
        # evidence_items，否则前端展示的 plan 与最终完整度口径会漂移。
        unplanned_tool_count = sum(
            1 for ti, tool in enumerate(successful_tools)
            if ti not in matched_tool_indices
            and tool["tool_name"].lower() not in self._NON_EVIDENCE_TOOLS
        )
        logger.info("📊 [evidence] 证据统计: plan=%d 项, "
                    "thinking_tools=%d 个成功调用, "
                    "matched=%d, unplanned=%d",
                    len(evidence_plan), len(successful_tools),
                    len(matched_tool_indices),
                    unplanned_tool_count)

        return evidence_items

    def _calculate_evidence_tool_stats(
        self,
        evidence_plan: List[Dict],
        thinking_events: list,
        evidence_items: List[EvidenceItem],
        upstream_evidence_items: List[EvidenceItem],
    ) -> Dict[str, int]:
        """Calculate transparent tool/evidence counts from structured objects.

        Completeness is plan-item based. Tool counts are diagnostic metadata:
        executed tools can be greater than matched plan items when the agent
        performs extra probes, and matched can be lower than planned when some
        Pydantic plan intents were not satisfied.
        """
        planned_ids = {
            str(item.get("id", ""))
            for item in evidence_plan or []
            if isinstance(item, dict) and item.get("id")
        }
        matched_ids = {
            str(item.id)
            for item in [*(evidence_items or []), *(upstream_evidence_items or [])]
            if item.collected
            and str(item.id) in planned_ids
            and str(getattr(item, "source", "") or "") in {
                "thinking_match",
                "thinking_negative_match",
                "layer_verified",
            }
        }

        evidence_tool_events = self._extract_evidence_tool_events(thinking_events)
        executed_tool_count = len(evidence_tool_events)
        matched_tool_count = len(matched_ids)
        unplanned_tool_count = max(0, executed_tool_count - matched_tool_count)

        return {
            "executed_tool_count": executed_tool_count,
            "matched_tool_count": matched_tool_count,
            "unplanned_tool_count": unplanned_tool_count,
        }

    def _extract_evidence_tool_events(self, thinking_events: list) -> List[Dict[str, Any]]:
        """Return successful/diagnostic tool observations that count as evidence attempts."""
        evidence_events: List[Dict[str, Any]] = []
        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            tool_name = str(ev.get("tool_name", "") or "").lower()
            if tool_name in self._NON_EVIDENCE_TOOLS:
                continue

            result = ev.get("result", ev.get("result_preview", "")) or ""
            structured = ev.get("structured") or {}
            semantic_success = ev.get("semantic_success", True) is not False
            diagnostic_negative = self._is_diagnostic_negative_tool_result(tool_name, result, structured)
            if not semantic_success and not diagnostic_negative:
                continue
            evidence_events.append(ev)
        return evidence_events

    def _build_upstream_evidence_items(
        self,
        evidence_plan: List[Dict],
        thinking_events: list,
    ) -> List[EvidenceItem]:
        """Convert upstream layer tool results into collected evidence items.

        Layer observations are real environment evidence when they are scoped to
        current abnormal objects. They should be visible and countable, but kept
        separate from evidence-plan execution with source=layer_verified.
        """
        layer_events = [
            ev for ev in thinking_events or []
            if ev.get("type") == "tool_result"
            and ev.get("node") == "layer"
            and ev.get("status") == "success"
            and str(ev.get("tool_name", "")).lower() not in self._NON_EVIDENCE_TOOLS
            and str(ev.get("tool_name", "")).lower() not in {"fetch_runbook", "read_context_archive"}
        ]
        if not layer_events:
            return []

        items: List[EvidenceItem] = []
        matched_plan_items = self._build_evidence_items_from_thinking(evidence_plan, layer_events) if evidence_plan else []
        for item in matched_plan_items:
            if item.collected:
                item.source = "layer_verified"
                items.append(item)

        matched_count = len(items)
        for index, ev in enumerate(layer_events, start=1):
            result = ev.get("result", "") or ev.get("result_preview", "")
            if not result:
                continue
            items.append(EvidenceItem(
                id=f"layer_{index}",
                description=f"上游已验证工具结果: {ev.get('tool_name', '')}",
                level=EvidenceLevel.IMPORTANT,
                weight=0.2,
                collected=True,
                value=result[:500],
                source="layer_verified",
                outcome="negative" if self._is_diagnostic_negative_tool_result(
                    ev.get("tool_name", ""),
                    result,
                    ev.get("structured") or {},
                ) else "positive",
            ))

        logger.info(
            "📊 [evidence] 纳入上游 layer 证据: layer_tools=%d plan_matched=%d total_added=%d",
            len(layer_events),
            matched_count,
            len(items),
        )
        return items

    @staticmethod
    def _merge_evidence_items(
        evidence_items: List[EvidenceItem],
        upstream_items: List[EvidenceItem],
    ) -> List[EvidenceItem]:
        if not upstream_items:
            return evidence_items

        merged: List[EvidenceItem] = list(evidence_items or [])
        by_id = {str(item.id): idx for idx, item in enumerate(merged)}
        for item in upstream_items:
            item_id = str(item.id)
            if item_id in by_id:
                existing = merged[by_id[item_id]]
                if not existing.collected and item.collected:
                    existing.collected = True
                    existing.value = item.value
                    existing.source = item.source
                    existing.outcome = getattr(item, "outcome", getattr(existing, "outcome", "positive"))
                continue
            merged.append(item)
            by_id[item_id] = len(merged) - 1
        return merged

    def _calculate_plan_completeness(
        self,
        evidence_items: List[EvidenceItem],
        upstream_items: List[EvidenceItem],
    ) -> Dict[str, Any]:
        """Calculate completeness from countable planned items only.

        Extra layer_verified observations remain visible in inventory, but they
        must not inflate plan completeness unless they satisfy a planned item by
        id.
        """
        planned_items = self._measurable_evidence_items([
            item for item in evidence_items or []
            if str(getattr(item, "source", "") or "") in {
                "thinking_match",
                "thinking_negative_match",
                "planned",
                "layer_verified",
            }
            and not str(item.id).startswith("layer_")
        ])
        if not planned_items:
            return {"plan_total": 0, "plan_collected": 0, "plan_completeness": 0.0}

        planned_by_id = {str(item.id): item for item in planned_items}
        for item in upstream_items or []:
            item_id = str(item.id)
            if item_id in planned_by_id and item.collected:
                planned_by_id[item_id].collected = True

        total = len(planned_items)
        collected = sum(1 for item in planned_items if item.collected)
        return {
            "plan_total": total,
            "plan_collected": collected,
            "plan_completeness": collected / total if total else 0.0,
        }

    def _adjudicate_plan_tool_matches(
        self,
        evidence_plan: List[Dict],
        successful_tools: List[Dict[str, Any]],
    ) -> Optional[Dict[str, int]]:
        if not getattr(self, "_plan_match_adjudication_enabled", False):
            return None
        if not evidence_plan or not successful_tools:
            return None

        candidates = []
        for index, tool in enumerate(successful_tools):
            if tool["tool_name"].lower() in self._NON_EVIDENCE_TOOLS:
                continue
            candidates.append({
                "index": index,
                "tool_name": tool.get("tool_name", ""),
                "tool_args": tool.get("tool_args") or {},
                "structured": tool.get("structured") or {},
                "result_preview": (tool.get("result") or "")[:1200],
                "raw_ref": tool.get("raw_ref"),
                "summary_ref": tool.get("summary_ref"),
            })

        if not candidates:
            return None

        adjudicator = getattr(self, "plan_match_adjudicator", None)
        if not adjudicator:
            return None

        try:
            data = adjudicator(evidence_plan, candidates)
        except Exception as exc:
            logger.warning("⚠️ [evidence] evidence_plan 对齐扩展失败，回退规则匹配: %s", exc)
            return None

        matches = data.get("matches") if isinstance(data, dict) else None
        if not isinstance(matches, list):
            return None

        matched: Dict[str, int] = {}
        used_tool_indices: set[int] = set()
        for item in matches:
            if not isinstance(item, dict) or item.get("matched") is not True:
                continue
            plan_id = str(item.get("plan_id") or "")
            if not plan_id:
                continue
            try:
                tool_index = int(item.get("tool_result_index"))
            except (TypeError, ValueError):
                continue
            if tool_index < 0 or tool_index >= len(successful_tools) or tool_index in used_tool_indices:
                continue
            confidence = item.get("confidence", 0)
            try:
                if float(confidence) < 0.5:
                    continue
            except (TypeError, ValueError):
                continue
            matched[plan_id] = tool_index
            used_tool_indices.add(tool_index)

        if matched:
            logger.info("📊 [evidence] 扩展 plan/tool 对齐命中 %d 项", len(matched))
        return matched

    def _call_plan_match_llm(
        self,
        evidence_plan: List[Dict],
        tool_candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            return {}

        prompt = """你是 Kubernetes 诊断证据对齐裁判。
任务：判断 evidence_plan 中每个计划项是否被某个真实 tool_result 满足。

判定原则：
- 不要只看 tool 名；必须同时比较对象类型、资源名、namespace、命令意图、结果内容。
- 如果计划查 NetworkPolicy，但结果是 Secret/PVC/Node 表，必须判定不匹配。
- 如果计划查某个 Pod/namespace，但结果属于其他对象或其他 namespace，必须判定不匹配。
- 失败、空结果、无关资源不能作为已采集证据。
- 一个 tool_result 最多匹配一个 plan item。

结构化裁判结果由 `EvidenceMatchOutput` Pydantic schema 生成和校验；不要手写结构化对象。
"""
        payload = {
            "evidence_plan": evidence_plan,
            "tool_candidates": tool_candidates,
        }
        if hasattr(ai_call, "call_structured"):
            parsed, _ = ai_call.call_structured(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False, default=str),
                schema=EvidenceMatchOutput,
                node_id="evidence_plan_match",
                max_tokens=2048,
            )
            return parsed.model_dump() if parsed is not None else {}

        logger.warning("⚠️ [evidence] ai_call 不支持 call_structured，跳过 Pydantic 证据对齐裁判")
        return {}

    @staticmethod
    def _tool_result_matches_plan(
        plan_tool: str,
        plan_cmd: str,
        plan_desc: str,
        tool_name: str,
        result: str,
        structured: Dict[str, Any],
        tool_args: Optional[Dict[str, Any]] = None,
        plan_intent: str = "",
        acceptable_tools: Optional[List[str]] = None,
    ) -> bool:
        if not result or not result.strip():
            return False
        if (structured or {}).get("status") in {"invalid_tool", "command_failed", "extract_failed"}:
            return False
        if not plan_intent and not EvidenceCollectorNode._namespace_scope_matches(plan_cmd, result):
            return False

        combined = f"{plan_cmd}\n{plan_desc}"
        has_structured_intent = bool(plan_intent)
        intent = plan_intent or EvidenceCollectorNode._classify_plan_intent(plan_cmd, plan_desc)
        tool_match = EvidenceCollectorNode._tool_is_compatible_with_plan(
            plan_tool=plan_tool,
            plan_cmd=plan_cmd,
            intent=intent,
            tool_name=tool_name,
            acceptable_tools=acceptable_tools,
        )
        if not tool_match:
            return False

        lower_result = result.lower()
        plan_target = EvidenceCollectorNode._extract_plan_resource_target(plan_cmd)
        if plan_target and not plan_intent:
            result_target = EvidenceCollectorNode._extract_result_resource_target(
                result=result,
                structured=structured or {},
                tool_args=tool_args or {},
            )
            if not EvidenceCollectorNode._resource_target_matches(plan_target, result_target):
                return False

        if (structured or {}).get("diagnostic_negative") or EvidenceCollectorNode._is_diagnostic_negative_tool_result(tool_name, result, structured or {}):
            return (
                intent in {"registry_connectivity", "dns_connectivity"}
                or EvidenceCollectorNode._negative_result_answers_plan(combined, lower_result)
            )

        if has_structured_intent:
            if intent in {"pod_status", "pod_events"}:
                return EvidenceCollectorNode._result_answers_pod_status(result, structured or {})
            if intent in {"pod_spec", "pod_config", "pod_lifecycle"}:
                return EvidenceCollectorNode._result_answers_pod_spec_or_lifecycle(result, structured or {}, intent)
            if intent in {"secret_config"}:
                return structured.get("resource_kind") == "Secret" or structured.get("kind") == "Secret" or "secret" in lower_result
        if "run_bash_command" in tool_name and intent in {"registry_connectivity", "dns_connectivity"}:
            probe_markers = (
                "curl",
                "wget",
                "telnet",
                "nc ",
                "ping",
                "registry",
                "docker.io",
                "resolve",
                "nslookup",
                "dig ",
                "connected",
                "connection",
                "timeout",
                "timed out",
            )
            return any(marker in lower_result for marker in probe_markers)
        if "run_bash_command" in tool_name and intent == "node_state":
            node_name = plan_target.get("name", "") if plan_target.get("kind") == "node" else ""
            return bool(node_name and node_name in lower_result and re.search(r"\bready\b|kubelet|containerd|runtime", lower_result))

        if "events" in combined or "事件" in combined:
            return (
                "kubectl_events" in tool_name
                or ("kubectl_describe" in tool_name and re.search(r"\b(status|reason|events?)\b|状态|事件", lower_result))
                or structured.get("status") == "events_found"
                or "last seen" in lower_result
                or "reason" in lower_result and "object" in lower_result
                or "failed to pull image" in lower_result
                or "back-off pulling image" in lower_result
            )

        if "logs" in combined or "日志" in combined:
            return (
                "kubectl_logs" in tool_name
                or "run_bash_command" in tool_name
                or not (structured.get("kind") == "Pod" and "kubectl_get_yaml" in tool_name)
            )

        if "configmap" in combined:
            return structured.get("kind") == "ConfigMap" or "configmap" in lower_result

        if "secret" in combined or "imagepullsecret" in combined:
            return (
                structured.get("resource_kind") == "Secret"
                or structured.get("kind") == "Secret"
                or "secret" in lower_result
                or "dockerconfigjson" in lower_result
            )

        if "describe" in combined:
            return "kubectl_describe" in tool_name

        if "get pod" in plan_cmd or "describe pod" in plan_cmd:
            return structured.get("kind") == "Pod" or "pod" in lower_result

        return True

    @staticmethod
    def _tool_is_compatible_with_plan(
        plan_tool: str,
        plan_cmd: str,
        intent: str,
        tool_name: str,
        acceptable_tools: Optional[List[str]] = None,
    ) -> bool:
        """Treat LLM generated `tool` as a weak hint and command intent as truth.

        Smaller models often put a broad kubectl wrapper in the plan while the
        agent executes a more specific helper, e.g. plan says
        kubectl_get_by_kind_in_cluster but command is `kubectl describe pod`
        and the real tool is kubectl_describe. Hard-failing that case makes
        real evidence show as 0/N.
        """
        plan_tool = (plan_tool or "").lower()
        tool_name = (tool_name or "").lower()
        plan_cmd = (plan_cmd or "").lower()
        acceptable = {
            str(tool or "").lower()
            for tool in (acceptable_tools or [])
            if str(tool or "").strip()
        }

        if acceptable:
            return any(
                tool_name == tool
                or tool_name in tool
                or tool in tool_name
                or tool_name.replace("_", "") == tool.replace("_", "")
                for tool in acceptable
            )

        if (
            (plan_tool and plan_tool == tool_name)
            or (plan_tool and plan_tool in tool_name)
            or (plan_tool and tool_name in plan_tool)
            or (plan_tool and plan_tool.replace("_", "") == tool_name.replace("_", ""))
        ):
            return True

        if "kubectl" in plan_cmd:
            if re.search(r"\bdescribe\s+", plan_cmd):
                return "kubectl_describe" in tool_name or "run_bash_command" in tool_name
            if re.search(r"\bget\s+", plan_cmd):
                return (
                    "kubectl_get" in tool_name
                    or "kubectl_describe" in tool_name
                    or "run_bash_command" in tool_name
                )
            if re.search(r"\blogs\s+", plan_cmd):
                return "run_bash_command" in tool_name or "kubectl_logs" in tool_name
            if re.search(r"\b(exec|curl|wget|nc|telnet|ping)\b", plan_cmd):
                return "run_bash_command" in tool_name

        if intent in {"registry_connectivity", "dns_connectivity", "pod_logs", "runtime_info"}:
            return "run_bash_command" in tool_name or "kubectl_run_image" in tool_name
        if intent in {"pod_status", "pod_events", "pod_config", "pod_spec", "pod_lifecycle", "secret_config", "node_state"}:
            return (
                tool_name.startswith("kubectl_")
                or "run_bash_command" in tool_name
            )

        return False

    @staticmethod
    def _result_answers_pod_status(result: str, structured: Dict[str, Any]) -> bool:
        text = (result or "").lower()
        if structured.get("kind") == "Pod" or structured.get("resource_kind") == "Pod":
            return True
        if structured.get("status") in {"describe_summarized", "events_found", "kept_small_output"}:
            return True
        return any(
            marker in text
            for marker in (
                "imagepullbackoff",
                "errimagepull",
                "crashloopbackoff",
                "terminating",
                "oomkilled",
                "failed",
                "reason:",
                "status",
                "ready",
            )
        )

    @staticmethod
    def _result_answers_pod_spec_or_lifecycle(
        result: str,
        structured: Dict[str, Any],
        intent: str,
    ) -> bool:
        text = (result or "").lower()
        if structured.get("kind") == "Pod" or structured.get("resource_kind") == "Pod":
            return True
        if intent == "pod_lifecycle":
            return any(marker in text for marker in ("deletiontimestamp", "finalizers", "terminating"))
        return any(marker in text for marker in ("kind: pod", "image:", "imagepullsecrets", "containers:"))

    @staticmethod
    def _extract_result_resource_target(
        result: str,
        structured: Dict[str, Any],
        tool_args: Dict[str, Any],
    ) -> Dict[str, str]:
        kind = EvidenceCollectorNode._normalize_resource_kind(
            structured.get("kind")
            or structured.get("resource_kind")
            or structured.get("resource_type")
            or tool_args.get("kind")
            or tool_args.get("resource_kind")
            or tool_args.get("resource_type")
        )
        name = str(
            structured.get("name")
            or structured.get("resource_name")
            or tool_args.get("name")
            or tool_args.get("resource_name")
            or ""
        ).strip("'\"").lower()
        namespace = str(
            structured.get("namespace")
            or tool_args.get("namespace")
            or ""
        ).strip("'\"").lower()

        text = result or ""
        if not name:
            match = re.search(r"(?im)^\s*name:\s*([^\s]+)\s*$", text)
            if match:
                name = match.group(1).strip("'\"").lower()
        if not namespace:
            match = re.search(r"(?im)^\s*namespace:\s*([^\s]+)\s*$", text)
            if match:
                namespace = match.group(1).strip("'\"").lower()
        if not kind:
            match = re.search(r"(?im)^\s*kind:\s*([^\s]+)\s*$", text)
            if match:
                kind = EvidenceCollectorNode._normalize_resource_kind(match.group(1))
        if not kind and re.search(r"\bpod/", text, re.IGNORECASE):
            kind = "pod"

        return {"kind": kind, "namespace": namespace, "name": name}

    @staticmethod
    def _normalize_resource_kind(value: Any) -> str:
        text = str(value or "").strip().lower()
        aliases = {
            "pods": "pod",
            "po": "pod",
            "nodes": "node",
            "no": "node",
            "secrets": "secret",
            "configmaps": "configmap",
            "cm": "configmap",
            "persistentvolumeclaim": "pvc",
            "persistentvolumeclaims": "pvc",
            "pvcs": "pvc",
            "services": "service",
            "svc": "service",
            "deployments": "deployment",
            "replicasets": "replicaset",
            "rs": "replicaset",
            "daemonsets": "daemonset",
            "ds": "daemonset",
            "statefulsets": "statefulset",
            "sts": "statefulset",
            "events": "event",
            "networkpolicies": "networkpolicy",
        }
        return aliases.get(text, text)

    @staticmethod
    def _resource_target_matches(plan_target: Dict[str, str], result_target: Dict[str, str]) -> bool:
        plan_kind = (plan_target or {}).get("kind", "")
        plan_name = (plan_target or {}).get("name", "")
        plan_namespace = (plan_target or {}).get("namespace", "")
        result_kind = (result_target or {}).get("kind", "")
        result_name = (result_target or {}).get("name", "")
        result_namespace = (result_target or {}).get("namespace", "")

        if not result_kind and not result_name and not result_namespace:
            return True

        if plan_kind and result_kind and plan_kind != result_kind:
            return False
        if plan_name:
            if result_name and plan_name != result_name:
                return False
        if plan_namespace:
            if result_namespace and plan_namespace != result_namespace:
                return False
        return True

    @staticmethod
    def _is_diagnostic_negative_tool_result(
        tool_name: str,
        result: str,
        structured: Dict[str, Any],
    ) -> bool:
        """Return True when a failed probe is itself useful diagnostic evidence."""
        tool = (tool_name or "").lower()
        if not any(name in tool for name in ("run_bash_command", "kubectl_run_image")):
            return False

        text = " ".join([
            str(result or ""),
            str((structured or {}).get("stderr_preview") or ""),
            str((structured or {}).get("stdout_preview") or ""),
            str((structured or {}).get("stderr") or ""),
            str((structured or {}).get("stdout") or ""),
            " ".join(str(signal) for signal in ((structured or {}).get("signals") or [])),
        ]).lower()
        negative_markers = (
            "connection reset",
            "connection refused",
            "i/o timeout",
            "timed out",
            "timeout",
            "命令执行超时",
            "执行超时",
            "could not resolve host",
            "no route to host",
            "network is unreachable",
            "recv failure",
            "curl:",
            "wget:",
            "tls handshake timeout",
        )
        return any(marker in text for marker in negative_markers)

    @staticmethod
    def _negative_result_answers_plan(combined_plan_text: str, lower_result: str) -> bool:
        plan = (combined_plan_text or "").lower()
        intent_markers = (
            "连通",
            "网络",
            "访问",
            "可达",
            "docker.io",
            "registry",
            "镜像仓库",
            "仓库",
            "curl",
            "wget",
            "dns",
            "tls",
            "timeout",
        )
        result_markers = (
            "connection reset",
            "connection refused",
            "i/o timeout",
            "timed out",
            "timeout",
            "命令执行超时",
            "执行超时",
            "could not resolve host",
            "no route to host",
            "network is unreachable",
            "recv failure",
            "curl:",
            "wget:",
            "tls handshake timeout",
        )
        return (
            any(marker in plan for marker in intent_markers)
            and any(marker in lower_result for marker in result_markers)
        )

    @staticmethod
    def _namespace_scope_matches(plan_cmd: str, result: str) -> bool:
        """Reject obvious namespace drift for tabular outputs."""
        match = re.search(r"(?:^|\s)(?:-n|--namespace(?:=|\s+))\s*([^\s]+)", plan_cmd or "")
        if not match:
            return True

        expected_namespace = match.group(1).strip("'\"").lower()
        if not expected_namespace:
            return True

        lower_result = (result or "").lower()
        if f"namespace: {expected_namespace}" in lower_result or f"namespace={expected_namespace}" in lower_result:
            return True

        lines = [line.strip() for line in (result or "").splitlines() if line.strip()]
        header_index = next(
            (
                idx for idx, line in enumerate(lines[:5])
                if "namespace" in line.lower().split()
            ),
            None,
        )
        if header_index is None:
            return True

        columns = lines[header_index].lower().split()
        try:
            namespace_index = columns.index("namespace")
        except ValueError:
            return True

        rows = lines[header_index + 1:]
        if not rows:
            return True

        namespaces = {
            parts[namespace_index].strip("'\"").lower()
            for row in rows
            if (parts := row.split()) and len(parts) > namespace_index
        }
        return not namespaces or expected_namespace in namespaces

    def _calculate_completeness(self, evidence_items: List[EvidenceItem]) -> float:
        """计算真实环境证据采集率，reference/runbook 不计入分母。"""
        measurable_items = self._measurable_evidence_items(evidence_items)
        if not measurable_items:
            return 0.0

        total = len(measurable_items)
        collected = sum(1 for e in measurable_items if e.collected)

        return collected / total

    def _measurable_evidence_items(self, evidence_items: List[EvidenceItem]) -> List[EvidenceItem]:
        """Return evidence items that should count toward collection completeness."""
        measurable: List[EvidenceItem] = []
        for item in evidence_items or []:
            level_value = item.level.value if hasattr(item.level, "value") else str(item.level)
            if str(level_value).lower() in {"optional", "reference"}:
                continue
            desc = (item.description or "").lower()
            source = str(getattr(item, "source", "") or "").lower()
            if source in {"reference", "archive"}:
                continue
            if "fetch_runbook" in desc or "read_context_archive" in desc:
                continue
            measurable.append(item)
        return measurable

    def _update_metrics(
        self,
        evidence_plan: List[Dict],
        tool_results: List[Dict]
    ):
        """更新 metrics 统计"""
        if not self.metrics:
            return

        # LLM 调用已经在 _plan_evidence_with_llm 中记录了
        # 这里只补充统计（如果有额外调用）

        # 记录工具调用统计
        for tool_result in tool_results:
            duration_ms = tool_result.get("duration_ms", 0)
            success = tool_result.get("success", True)
            self.metrics.record_tool_call(
                tool_name=tool_result.get("tool", "kubectl"),
                duration_ms=duration_ms,
                success=success
            )

    def _extract_tool_data_from_thinking(self, thinking_events: list) -> List[Dict]:
        """
        从 thinking_events 中提取 MCP 工具的真实输出数据

        这些数据来自 LLM agentic loop 中的工具调用（kubectl, prometheus 等），
        是下游节点（rca, conclusion）生成准确报告的关键数据源。
        """
        tool_data = []
        for ev in thinking_events:
            if ev.get("type") == "tool_result":
                tool_name = ev.get("tool_name", "")
                result_text = ev.get("result", "") or ev.get("result_preview", "")
                status = ev.get("status", "")
                if result_text and status == "success":
                    tool_data.append({
                        "tool": tool_name,
                        "data": result_text,
                        "duration_s": ev.get("duration_seconds", 0),
                        "semantic_success": ev.get("semantic_success", True),
                        "raw_ref": ev.get("raw_ref"),
                        "structured_ref": ev.get("structured_ref"),
                        "summary_ref": ev.get("summary_ref"),
                    })
        return tool_data
