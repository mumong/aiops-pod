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

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
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
                logger.warning("⚠️ [evidence] 首轮结果违反采证协议：%s；发起一次严格重试", retry_reason)
                evidence_plan, thinking_events, llm_result_text = self._plan_evidence_with_llm(
                    question=question,
                    layer=layer,
                    possible_scenarios=possible_scenarios,
                    key_entities=key_entities,
                    layer_analysis=json.dumps(layer_handoff, ensure_ascii=False),
                    context_archive_ref=state.get("context_archive_ref", ""),
                    layer_archive_ref=state.get("layer_archive_ref") or {},
                    strict_mode=True,
                    failure_reason=retry_reason,
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
            collected = sum(1 for e in evidence_items if e.collected)
            total = len(evidence_items)
            not_collected = [e for e in evidence_items if not e.collected]
            evidence_facts = self._build_evidence_facts(evidence_items)
            evidence_conflicts = self._build_evidence_conflicts(tool_data_from_llm, layer_handoff)
            missing_evidence = [
                {"id": e.id, "description": e.description, "level": e.level.value if hasattr(e.level, "value") else str(e.level)}
                for e in not_collected
            ]

            evidence_inventory = []
            for e in evidence_items:
                evidence_inventory.append({
                    "id": e.id,
                    "description": e.description,
                    "level": e.level.value if hasattr(e.level, 'value') else str(e.level),
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

            new_state.update({
                "evidence_items": evidence_items,
                "evidence_analysis": json.dumps({
                    "evidence_plan": evidence_plan,
                    "tool_results": [r.get("summary", "") for r in tool_results],
                    "tool_data": tool_data_from_llm,
                    "llm_analysis": llm_result_text[:3000] if llm_result_text else "",
                    "collection_summary": f"计划 {total} 项，实际采集 {collected} 项，未采集 {total - collected} 项，完整度 {completeness:.0%}",
                    "evidence_inventory": evidence_inventory,
                    "missing_reasons": missing_reasons,
                    "early_stop": dict(self._early_stop_state),
                }, ensure_ascii=False),
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
    ) -> str:
        strict_section = ""
        if strict_mode:
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
                "# 可读取的 context archive 入口",
                f"- context_archive_ref: {context_root}",
                f"- 可按需读取: {context_root}/budget/layer.json",
                f"- 可按需读取: {context_root}/budget/evidence.json",
                f"- 可按需读取: {context_root}/handoff/layer-to-evidence.json",
                f"- 可按需读取: {context_root}/layer/full_analysis.md",
                f"- 可按需读取: {context_root}/layer/handoff.json",
                f"- 可按需读取: {context_root}/node_inputs/evidence.input.json",
                f"- 可按需读取: {context_root}/node_outputs/layer.output.json",
                f"- 可按需读取: {context_root}/tools/ 下的 *.raw.txt / *.structured.json / *.summary.txt",
            ])
        if archive_refs.get("full_analysis_ref"):
            archive_lines.append(f"- layer full_analysis_ref: {archive_refs.get('full_analysis_ref')}")
        if archive_refs.get("handoff_ref"):
            archive_lines.append(f"- layer handoff_ref: {archive_refs.get('handoff_ref')}")
        archive_section = "\n".join(archive_lines).strip() if archive_lines else "无"
        return f"""# 用户原始问题
{question}

# 上游定位结构化结果 layer_handoff
{layer_handoff or '{}'}

# Runbook 语义匹配要求
- 根据 Available Runbooks/catalog 的 description、runbook_id、状态关键字与 layer_handoff 中的 pod_status_keyword、pod_abnormal_type、primary_pod、active_signals 做语义匹配。
- 如果某个 Pod 异常 runbook 明显匹配当前 Pod 异常状态，evidence_plan 必须包含一条 level=reference、tool=fetch_runbook 的参考步骤；多个当前异常类型可以获取多个明显匹配的 runbook。
- 不要依赖代码注入的 runbook 推荐字段；是否调用 runbook 必须由你根据 catalog 描述和当前异常信号自主判断。
- runbook 是参考知识，不是真实环境证据；fetch_runbook 后仍必须调用 kubectl/prometheus 等真实环境工具验证关键事实。
- 如果你在分析中认为“应该查看/参考某个 runbook”，必须把它写入 evidence_plan 并实际调用 fetch_runbook；禁止只在思考中提到 runbook 却不调用。

# 可选归档上下文
{archive_section}

# 当前节点职责
你是 evidence 节点。核心任务是找证据：为上游定位出的 Pod 异常状态的证据提供真实环境验证。你必须基于 layer_handoff 的 primary_pod、pod_status_keyword、pod_abnormal_type、active_entities、active_signals、possible_scenarios 和 must_verify 调用真实只读工具采集证据。

# 强约束
- 第一条 assistant 消息必须只输出 evidence_plan JSON，不能附加解释文本。
- 在输出 evidence_plan JSON 之前，禁止调用任何工具。
- 输出 evidence_plan 后不能结束，必须继续调用至少一个 critical 或 important 级真实工具。
- LLM 必须自己决定并调用工具；计划不是证据。
- 必须优先围绕 primary_pod 验证它为什么进入当前 pod_status_keyword / pod_abnormal_type；不要先做大范围集群扫描。
- 必须保持 namespace、Pod、Service、Node、资源类型不漂移。
- 如果工具结果显示对象不存在、namespace 不匹配、事件为空、命令失败，必须把它视为冲突或负向证据，不能当作成功验证。
- 如果 Available Runbooks/catalog 中存在明显匹配当前 Pod 异常状态的 runbook，应先执行 fetch_runbook 参考步骤；但不能只 fetch_runbook 后结束，必须继续调用真实环境工具。reference/runbook 步骤不是证据，不计入 critical/important 完整度。
- 如果输入里给出了 raw_ref、summary_ref、structured_ref、archive_ref、handoff_ref、input_ref、output_ref 等路径，而你需要查看其内容，必须调用 read_context_archive 工具；模型不能直接访问本地文件。
{strict_section}
# 输出
先输出 evidence_plan JSON，再执行必要工具调用，最后再输出简短证据结论。"""

    def _get_plan_protocol_failure_reason(
        self,
        evidence_plan: List[Dict],
        thinking_events: List[Dict[str, Any]],
    ) -> str:
        """检查 evidence 是否遵守了先 plan 后执行的协议。"""
        timeline = self._analyze_plan_timeline(thinking_events)
        if not timeline["has_plan"]:
            return "上一轮没有输出有效 evidence_plan JSON，系统已拒绝该结果"
        if timeline["tool_activity_before_plan"]:
            return "上一轮在 evidence_plan 前就开始调用工具，违反先计划后执行约束，系统已拒绝该结果"
        if evidence_plan and not self._has_semantic_tool_success(thinking_events):
            return "上一轮只返回 evidence_plan，没有任何成功工具调用，系统已拒绝该结果"
        return ""

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
                if "evidence_plan" in parsed:
                    return parsed["evidence_plan"]
            parsed = json.loads(response_text)
            if isinstance(parsed, dict) and "evidence_plan" in parsed:
                return parsed["evidence_plan"]
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试提取命令列表
            return self._extract_commands_from_text(response_text)

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

        # 未匹配到 plan 的成功工具调用作为额外采集（过滤非证据工具）
        for ti, tool in enumerate(successful_tools):
            if ti in matched_tool_indices:
                continue
            if tool["tool_name"].lower() in self._NON_EVIDENCE_TOOLS:
                continue
            evidence_items.append(EvidenceItem(
                id=f"extra_{ti}",
                description=f"工具采集: {tool['tool_name']}",
                level=EvidenceLevel.IMPORTANT,
                weight=0.15,
                collected=True,
                value=tool["result"][:500] if tool["result"] else None,
                source="thinking_extra",
            ))

        logger.info("📊 [evidence] 证据统计: plan=%d 项, "
                    "thinking_tools=%d 个成功调用, "
                    "matched=%d, extra=%d",
                    len(evidence_plan), len(successful_tools),
                    len(matched_tool_indices),
                    sum(1 for e in evidence_items if getattr(e, 'source', '') == 'thinking_extra'))

        return evidence_items

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
            return "kubectl_logs" in tool_name or not (
                structured.get("kind") == "Pod" and "kubectl_get_yaml" in tool_name
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

    def _calculate_completeness(self, evidence_items: List[EvidenceItem]) -> float:
        """计算证据采集率：已采集数 / 总数（计划 + 额外）"""
        if not evidence_items:
            return 0.0

        total = len(evidence_items)
        collected = sum(1 for e in evidence_items if e.collected)

        return collected / total

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
