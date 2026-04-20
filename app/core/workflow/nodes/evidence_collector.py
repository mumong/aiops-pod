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
from app.core.prompts import get_workflow_prompt

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
            # 优先使用阶段1完整分析文本（含工具输出），回退到结构化 JSON
            layer_full_analysis = state.get("layer_full_analysis", "") or layer_analysis
            possible_scenarios = state.get("possible_scenarios", [])
            key_entities = state.get("key_entities", [])

            logger.info(f"📋 证据采集: 层级={layer}, 可能场景={possible_scenarios}")
            logger.debug(f"📋 [DEBUG] 证据采集输入: question={question[:100]}, "
                        f"layer_analysis长度={len(layer_full_analysis)}, "
                        f"key_entities={key_entities}")
            self._early_stop_state = {
                "triggered": False,
                "reason": "",
                "required_levels": ["critical", "important"],
            }

            # 1. 调用 LLM 规划证据采集计划
            evidence_plan, thinking_events, llm_result_text = self._plan_evidence_with_llm(
                question=question,
                layer=layer,
                possible_scenarios=possible_scenarios,
                key_entities=key_entities,
                layer_analysis=layer_full_analysis
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

    def _plan_evidence_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict],
        layer_analysis: str = ""
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

            # 注入上游 layer 节点的分析结果，避免 evidence 重复分析
            if layer_analysis:
                system_prompt += f"\n\n# 上游问题定位结果（已完成，不要重复分析或重新获取 runbook）\n{layer_analysis}\n"
                system_prompt += "\n请直接基于以上定位结果采集证据。如果上游分析中发现的实际问题与定位层级不符（例如上游发现 Pod 被驱逐是 L0 问题但定位为 L1），应按实际问题采集证据。\n"

            # 添加 entities 信息到 prompt
            if entities_str:
                system_prompt += f"\n\n# 已提取的关键实体\n{entities_str}\n"

            response, thinking_events = self._call_llm(
                question,
                system_prompt,
                stop_checker=self._should_stop_collection_early,
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
            return json.loads(response_text)
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
            if ev.get("type") == "tool_result" and ev.get("status") == "success"
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
    _NON_EVIDENCE_TOOLS = {"todowrite", "todo_write", "todo"}

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
            if ev.get("type") == "tool_result" and ev.get("status") == "success":
                successful_tools.append({
                    "tool_name": ev.get("tool_name", ""),
                    "result": ev.get("result", ev.get("result_preview", "")),
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
            elif level_str == "optional":
                level = EvidenceLevel.OPTIONAL

            matched = False
            matched_result = None
            for ti, tool in enumerate(successful_tools):
                if ti in matched_tool_indices:
                    continue
                tn = tool["tool_name"].lower()
                if (plan_tool and plan_tool == tn) or \
                   (plan_tool and plan_tool in tn) or \
                   (plan_tool and tn in plan_tool) or \
                   (plan_cmd and tn in plan_cmd) or \
                   (plan_cmd and any(kw in tn for kw in plan_cmd.split()[:3])) or \
                   (plan_tool and plan_tool.replace("_", "") == tn.replace("_", "")):
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
                preview = ev.get("result_preview", "")
                status = ev.get("status", "")
                if preview and status == "success":
                    tool_data.append({
                        "tool": tool_name,
                        "data": preview,
                        "duration_s": ev.get("duration_seconds", 0),
                    })
        return tool_data
