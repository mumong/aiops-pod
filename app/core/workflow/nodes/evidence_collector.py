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
from typing import Any, Dict, List, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import EvidenceCollectionOutput, EvidenceMatchOutput, EvidencePlanOutput
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
        self._plan_match_adjudication_enabled = True
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
            self._plan_match_adjudication_enabled = layer != Layer.QUERY
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
            if not self._early_stop_state.get("triggered"):
                self._early_stop_state = self._derive_early_stop_state(evidence_plan, evidence_items)

            # 2.1 回退：evidence 节点没采集到证据时，从 layer 阶段的 thinking_events 统计
            if not evidence_items:
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
            completeness = self._calculate_completeness(evidence_items)

            # 4. 更新 metrics（记录 LLM 调用和工具调用次数）
            self._update_metrics(evidence_plan, tool_results)

            # 5. 从 thinking_events 提取 MCP 工具的真实输出数据
            tool_data_from_llm = self._extract_tool_data_from_thinking(thinking_events)

            # 6. 构建证据清单（真实数据，供 conclusion LLM 引用）
            # plan_total 保持与模型输出的 evidence_plan 对齐；environment_total
            # 只统计真实环境证据。报告同时展示两个口径，避免用户看到
            # evidence_plan=4 项但“证据完整度 3/3”这种不直观结果。
            measurable_items = self._measurable_evidence_items(evidence_items)
            plan_collected = sum(1 for e in evidence_items if e.collected)
            plan_total = len(evidence_items)
            collected = sum(1 for e in measurable_items if e.collected)
            total = len(measurable_items)
            not_collected = [e for e in measurable_items if not e.collected]
            plan_completeness = (plan_collected / plan_total) if plan_total else 0.0
            evidence_facts = self._build_evidence_facts(evidence_items)
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
            for e in evidence_items:
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
            )

            new_state.update({
                "evidence_items": evidence_items,
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
    ) -> EvidenceCollectionOutput:
        return EvidenceCollectionOutput.model_validate({
            "evidence_plan": evidence_plan,
            "tool_results": [r.get("summary", "") for r in tool_results],
            "tool_data": tool_data,
            "llm_analysis": llm_result_text[:3000] if llm_result_text else "",
            "collection_summary": (
                f"计划 {plan_total} 项，实际采集 {plan_collected} 项，"
                f"未采集 {plan_total - plan_collected} 项，完整度 {plan_completeness:.0%}；"
                f"其中真实环境证据 {environment_collected}/{environment_total} 项，完整度 {environment_completeness:.0%}"
            ),
            "plan_total": plan_total,
            "plan_collected": plan_collected,
            "plan_completeness": plan_completeness,
            "environment_evidence_total": environment_total,
            "environment_evidence_collected": environment_collected,
            "environment_evidence_completeness": environment_completeness,
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
        primary_pod = (layer_handoff or {}).get("primary_pod") or {}
        primary_name = str(primary_pod.get("name") or "")
        primary_namespace = str(primary_pod.get("namespace") or "")
        for item in tool_data:
            data = item.get("data", "") or ""
            if re.search(r"no events found|no resources found|notfound|not found|command failed|error from server", data, re.IGNORECASE):
                object_missing = bool(
                    primary_name
                    and re.search(r"notfound|not found|error from server", data, re.IGNORECASE)
                    and primary_name in data
                )
                conflict = {
                    "tool": item.get("tool", "unknown"),
                    "reason": data[:300],
                    "severity": "critical" if object_missing else "warning",
                    "object_missing": object_missing,
                }
                if object_missing:
                    conflict["object"] = {
                        "kind": "Pod",
                        "name": primary_name,
                        "namespace": primary_namespace,
                    }
                    conflict["message"] = (
                        "primary_pod 当前不存在；历史事件或归档摘要不能继续作为该 Pod 当前异常的正向证据"
                    )
                conflicts.append(conflict)
        return conflicts

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
        """QUERY 模式下将真实工具结果归一化为结构化 JSON，供 conclusion 纯渲染。"""
        if layer != Layer.QUERY:
            return {}

        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
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
            normalized, _ = ai_call.call_simple_json(
                system_prompt=prompt,
                question=json.dumps(payload, ensure_ascii=False),
                validator=lambda data: isinstance(data, dict),
            )
            if normalized:
                normalized.setdefault("query_target", question)
                normalized.setdefault("collection_summary", collection_summary)
                normalized.setdefault("notes", [])
                normalized.setdefault("missing", [])
                normalized.setdefault("sources", [])
                normalized.setdefault("columns", [])
                normalized.setdefault("rows", [])
                return normalized
        except Exception as exc:
            logger.warning("⚠️ [evidence] QUERY 结果归一化失败，使用通用回退: %s", exc)

        return self._build_query_result_fallback(question, tool_data, collection_summary, missing_reasons)

    @staticmethod
    def _parse_query_result(text: str) -> Optional[Dict[str, Any]]:
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None

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

        return {
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
        }

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
            logger.warning("⚠️ [evidence] ai_call 未设置，使用规则规划")
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

            early_stop_enabled = self._is_early_stop_enabled(default=True)
            logger.info("🧭 [evidence] early_stop=%s", early_stop_enabled)
            response, thinking_events = self._call_llm(
                user_message,
                system_prompt,
                stop_checker=self._should_stop_collection_early if early_stop_enabled else None,
            )

            llm_text = (response.result or "") if response else ""

            # 从 thinking_events 的 ai_message full_content 中搜索 JSON 证据计划
            # response.result 是最后一条 AI 消息（通常是总结），JSON 计划在早期消息中
            evidence_plan = self._extract_plan_from_thinking(thinking_events)
            if not evidence_plan:
                # 回退：尝试从 response.result 解析
                if response and response.result:
                    evidence_plan = self._parse_llm_evidence_plan(response.result)
            if not evidence_plan and existing_plan and self._has_semantic_tool_success(thinking_events):
                evidence_plan = existing_plan

            if evidence_plan:
                logger.info(f"📋 [evidence] 从 LLM 输出解析到 {len(evidence_plan)} 项证据计划")
                return evidence_plan, thinking_events, llm_text

            logger.warning("LLM 未返回有效证据计划，使用规则规划")
            return [], thinking_events, llm_text

        except Exception as e:
            logger.warning(f"LLM 规划失败，回退到规则: {e}")
            return [], [], ""

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
    ) -> str:
        strict_section = ""
        if existing_plan:
            strict_section = f"""

# 既有 evidence_plan（本轮不要重写）
上一轮已输出有效 evidence_plan，但没有执行真实工具。本轮必须沿用下列计划，直接调用工具采证，不要重新输出 evidence_plan。
```json
{json.dumps({"evidence_plan": existing_plan}, ensure_ascii=False)}
```
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
                "# context archive 引用",
                f"- context_archive_ref: {context_root}",
                "- 该引用仅用于人工排障和必要时追溯上游摘要；evidence 节点默认应基于 layer_handoff 与真实环境工具采证。",
                "- 不要因为存在 archive 引用而计划读取归档；归档内容不是当前环境证据。",
            ])
        if archive_refs.get("handoff_ref"):
            archive_lines.append("- layer handoff 已由上方 layer_handoff 注入；不要重复读取归档。")
        archive_section = "\n".join(archive_lines).strip() if archive_lines else "无"
        if existing_plan:
            plan_protocol = """- 本轮已有 evidence_plan，禁止重新输出 evidence_plan JSON。
- 直接按既有 evidence_plan 调用至少一个 critical 或 important 级真实工具。
- LLM 必须自己决定并调用工具；计划不是证据。
- 工具调用必须尽量逐项完成既有计划，最终消息不要新增未写入 plan 的“已采集计划项”。
- evidence_plan 中的 tool 字段必须是 Available tools 中真实存在的工具名。不要自行创造 kubectl_logs 等不存在的工具；需要执行未封装的只读 kubectl 命令时使用 run_bash_command。"""
        else:
            plan_protocol = """- 第一条 assistant 消息必须只输出 evidence_plan JSON，不能附加解释文本。
- 在输出 evidence_plan JSON 之前，禁止调用任何工具。
- 输出 evidence_plan 后不能结束，必须继续调用至少一个 critical 或 important 级真实工具。
- LLM 必须自己决定并调用工具；计划不是证据。
- evidence_plan 就是本轮计划采集清单；后续工具调用必须尽量逐项完成 plan 中的项目，最终消息不要新增未写入 plan 的“已采集计划项”。
- evidence_plan 中的 tool 字段必须是 Available tools 中真实存在的工具名。不要自行创造 kubectl_logs 等不存在的工具；需要执行未封装的只读 kubectl 命令时使用 run_bash_command。"""
        return f"""# 用户原始问题
{question}

# 上游定位结构化结果 layer_handoff
{layer_handoff or '{}'}

# Runbook 语义匹配要求
- 根据 Available Runbooks/catalog 的 description、runbook_id、状态关键字与 layer_handoff 中的 pod_status_keyword、pod_abnormal_type、primary_pod、active_signals 做语义匹配。
- 如果某个 Pod 异常 runbook 明显匹配当前 Pod 异常状态，evidence_plan 必须包含一条 level=reference、tool=fetch_runbook 的参考步骤；多个当前异常类型可以获取多个明显匹配的 runbook。
- 匹配到 runbook 时，fetch_runbook 必须在真实环境工具前执行。先读 runbook，再把 runbook 的关键检查点转化为 kubectl/prometheus 等真实环境验证步骤。
- 不要依赖代码注入的 runbook 推荐字段；是否调用 runbook 必须由你根据 catalog 描述和当前异常信号自主判断。
- runbook 是参考知识，不是真实环境证据；fetch_runbook 后仍必须调用 kubectl/prometheus 等真实环境工具验证关键事实。
- 如果你在分析中认为“应该查看/参考某个 runbook”，必须把它写入 evidence_plan 并实际调用 fetch_runbook；禁止只在思考中提到 runbook 却不调用。
- 只有当 catalog 中没有明显匹配项，或上游判断为 HEALTHY/QUERY，才允许不调用 fetch_runbook；这种情况下最终消息必须说明“未发现明显匹配的 Pod 异常 runbook”。

# 归档上下文（非采证主线）
{archive_section}

# 当前节点职责
你是 evidence 节点。核心任务是找证据：为上游定位出的 Pod 异常状态的证据提供真实环境验证。你必须基于 layer_handoff 的 issue_groups、primary_pod、abnormal_pods、pod_status_keyword、pod_abnormal_type、active_entities、active_signals、possible_scenarios 和 must_verify 调用真实只读工具采集证据。

# 强约束
{plan_protocol}
- 如果 layer_handoff 提供 issue_groups，evidence_plan 应优先覆盖每个当前异常组的最小关键证据；不要只围绕 primary_pod 而完全忽略其他异常组。
- 对非 primary 的 issue_group 只做最小验证：当前状态 + 一个最关键配置/事件信号即可，不要展开成长链路。
- 必须优先围绕 primary_pod 验证它为什么进入当前 pod_status_keyword / pod_abnormal_type；不要先做大范围集群扫描。
- 必须保持 namespace、Pod、Service、Node、资源类型不漂移。
- 如果工具结果显示对象不存在、namespace 不匹配、事件为空、命令失败，必须把它视为冲突或负向证据，不能当作成功验证。
- 如果 Available Runbooks/catalog 中存在明显匹配当前 Pod 异常状态的 runbook，应先执行 fetch_runbook 参考步骤；但不能只 fetch_runbook 后结束，必须继续调用真实环境工具。reference/runbook 步骤不是证据，不计入 critical/important 完整度。存在明显匹配 runbook 却未调用 fetch_runbook 时，本轮采证视为不完整。
- 不要把 context_archive_ref、archive_ref、raw_ref、summary_ref、structured_ref 等路径当作采证任务；默认不要计划读取归档文件。
{strict_section}
# 输出
{"直接执行既有 evidence_plan 中的必要工具，最后输出简短证据结论。" if existing_plan else "先输出 evidence_plan JSON，再执行必要工具调用，最后再输出简短证据结论。"}"""

    def _get_plan_protocol_failure_reason(
        self,
        evidence_plan: List[Dict],
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        """检查 evidence 是否遵守了先 plan 后执行的协议。"""
        timeline = self._analyze_plan_timeline(thinking_events)
        has_plan = bool(evidence_plan) or bool(timeline["has_plan"])
        if not has_plan:
            return "上一轮没有输出有效 evidence_plan JSON，系统已拒绝该结果"
        if timeline["tool_activity_before_plan"]:
            return "上一轮在 evidence_plan 前就开始调用工具，违反先计划后执行约束，系统已拒绝该结果"
        if evidence_plan and not self._has_semantic_tool_success(thinking_events):
            return "上一轮只返回 evidence_plan，没有任何成功工具调用，系统已拒绝该结果"
        return ""

    @staticmethod
    def _plan_exists_without_tool_results(reason: str) -> bool:
        return "只返回 evidence_plan" in (reason or "")

    def _analyze_plan_timeline(self, thinking_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析 plan 与 tool 调用的先后顺序。"""
        first_plan_index = None
        first_tool_index = None

        for idx, ev in enumerate(thinking_events or []):
            ev_type = ev.get("type")
            if first_tool_index is None and ev_type in {"tool_start", "tool_result"}:
                first_tool_index = idx
            if ev_type != "ai_message":
                continue
            text = ev.get("full_content") or ev.get("content") or ""
            if not text or "evidence_plan" not in text:
                continue
            plan = self._parse_llm_evidence_plan(text)
            if plan:
                first_plan_index = idx
                break

        return {
            "has_plan": first_plan_index is not None,
            "first_plan_index": first_plan_index,
            "first_tool_index": first_tool_index,
            "tool_activity_before_plan": (
                first_tool_index is not None
                and (first_plan_index is None or first_tool_index < first_plan_index)
            ),
        }
    def _extract_plan_from_thinking(self, thinking_events: list) -> List[Dict]:
        """
        从 thinking_events 的 ai_message 中提取 JSON 证据计划。

        LLM 在 agent loop 中先输出 JSON 计划，再调用工具执行。
        JSON 计划在早期的 ai_message 中，而 response.result 是最后一条消息。
        """
        for ev in thinking_events:
            if ev.get("type") != "ai_message":
                continue
            # 优先用 full_content（完整文本），回退到 content（截断到 500 字）
            text = ev.get("full_content") or ev.get("content") or ""
            if not text or "evidence_plan" not in text:
                continue
            plan = self._parse_llm_evidence_plan(text)
            if plan and len(plan) > 0:
                logger.debug(f"📋 [evidence] 从 thinking ai_message 解析到 {len(plan)} 项计划")
                return plan
        return []

    def _parse_llm_evidence_plan(self, response_text: str) -> List[Dict]:
        """
        解析 LLM 返回的证据计划

        Args:
            response_text: LLM 返回的文本

        Returns:
            证据计划列表
        """
        try:
            # 尝试提取 JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                return self._validate_evidence_plan_payload(parsed)
            parsed = json.loads(response_text)
            return self._validate_evidence_plan_payload(parsed)
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试提取命令列表
            return self._extract_commands_from_text(response_text)

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

    def _extract_commands_from_text(self, text: str) -> List[Dict]:
        """
        从文本中提取 kubectl 命令

        Args:
            text: LLM 返回的文本

        Returns:
            命令列表
        """
        commands = []
        # 提取 kubectl 命令
        kubectl_pattern = r'kubectl\s+(?:get|describe|logs|top|exec|apply|delete)[^\n]+'
        for match in re.finditer(kubectl_pattern, text, re.MULTILINE):
            cmd = match.group(0).strip()
            commands.append({
                "id": f"cmd_{len(commands)}",
                "description": f"执行命令: {cmd}",
                "level": "critical" if "describe" in cmd or "get events" in cmd else "important",
                "command": cmd,
                "tool": "kubectl",
                "purpose": "获取集群状态或资源信息"
            })
        return commands

    def _should_stop_collection_early(self, thinking_events: list) -> bool:
        """
        动态采证提前停止条件：
        - 已解析到 evidence_plan
        - 至少已有一次成功工具调用
        - 所有 critical + important 级计划证据都已被当前工具结果满足
        或者
        - 没有 critical/important 项时，全部计划项都已满足
        """
        evidence_plan = self._extract_plan_from_thinking(thinking_events)
        if not evidence_plan:
            return False

        successful_tools = [
            ev for ev in thinking_events
            if ev.get("type") == "tool_result"
            and ev.get("status") == "success"
            and ev.get("semantic_success", True) is not False
        ]
        if not successful_tools:
            return False

        evidence_items = self._build_evidence_items_from_thinking(evidence_plan, thinking_events)
        planned_items = [e for e in evidence_items if getattr(e, "source", "") in ("thinking_match", "planned")]
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
        planned_items = [e for e in evidence_items if getattr(e, "source", "") in ("thinking_match", "planned")]
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

        # 从 thinking_events 提取成功的工具调用
        successful_tools = []
        for ev in thinking_events:
            if (
                ev.get("type") == "tool_result"
                and ev.get("status") == "success"
                and ev.get("semantic_success", True) is not False
            ):
                successful_tools.append({
                    "tool_name": ev.get("tool_name", ""),
                    "result": ev.get("result", ev.get("result_preview", "")),
                    "tool_args": ev.get("tool_args") or {},
                    "structured": ev.get("structured") or {},
                    "raw_ref": ev.get("raw_ref"),
                    "summary_ref": ev.get("summary_ref"),
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
            item_id = plan_item.get("id", f"ev_{len(evidence_items)}")

            level_str = plan_item.get("level", "important")
            level = EvidenceLevel.IMPORTANT
            if level_str == "critical":
                level = EvidenceLevel.CRITICAL
            elif level_str in {"optional", "reference"}:
                level = EvidenceLevel.OPTIONAL

            matched = False
            matched_result = None
            if adjudicated_matches is not None:
                adjudicated_index = adjudicated_matches.get(str(item_id))
                if adjudicated_index is not None and 0 <= adjudicated_index < len(successful_tools):
                    matched = True
                    matched_result = successful_tools[adjudicated_index]["result"]
                    matched_tool_indices.add(adjudicated_index)
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
                    ):
                        matched = True
                        matched_result = tool["result"]
                        matched_tool_indices.add(ti)
                        break

            evidence_items.append(EvidenceItem(
                id=item_id,
                description=plan_item.get("description", "未知证据"),
                level=level,
                weight=0.2,
                collected=matched,
                value=matched_result,
                source="thinking_match" if matched else "planned",
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

    def _adjudicate_plan_tool_matches(
        self,
        evidence_plan: List[Dict],
        successful_tools: List[Dict[str, Any]],
    ) -> Optional[Dict[str, int]]:
        if not getattr(self, "_plan_match_adjudication_enabled", True):
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
        try:
            if adjudicator:
                data = adjudicator(evidence_plan, candidates)
            else:
                data = self._call_plan_match_llm(evidence_plan, candidates)
        except Exception as exc:
            logger.warning("⚠️ [evidence] evidence_plan LLM 对齐失败，回退规则匹配: %s", exc)
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
            logger.info("📊 [evidence] LLM plan/tool 对齐命中 %d 项", len(matched))
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

只输出 JSON，不要解释。格式：
{
  "matches": [
    {
      "plan_id": "e1",
      "tool_result_index": 0,
      "matched": true,
      "confidence": 0.0,
      "reason": "简短中文原因"
    }
  ],
  "unmatched_plan_ids": [],
  "unplanned_tool_result_indexes": []
}
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

        parsed, _ = ai_call.call_simple_json(
            system_prompt=prompt,
            question=json.dumps(payload, ensure_ascii=False, default=str),
            validator=lambda data: isinstance(data, dict) and isinstance(data.get("matches"), list),
            node_id="evidence_plan_match",
            max_tokens=2048,
        )
        return parsed or {}

    @staticmethod
    def _tool_result_matches_plan(
        plan_tool: str,
        plan_cmd: str,
        plan_desc: str,
        tool_name: str,
        result: str,
        structured: Dict[str, Any],
    ) -> bool:
        if not result or not result.strip():
            return False
        if (structured or {}).get("status") in {"invalid_tool", "command_failed", "extract_failed"}:
            return False
        if not EvidenceCollectorNode._namespace_scope_matches(plan_cmd, result):
            return False

        tool_match = (
            (plan_tool and plan_tool == tool_name)
            or (plan_tool and plan_tool in tool_name)
            or (plan_tool and tool_name in plan_tool)
            or (plan_tool and plan_tool.replace("_", "") == tool_name.replace("_", ""))
        )
        if not tool_match:
            return False

        combined = f"{plan_cmd}\n{plan_desc}"
        lower_result = result.lower()

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
