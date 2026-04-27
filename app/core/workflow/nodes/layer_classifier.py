"""
节点1：问题定位（初步定层）

职责：
- 从用户问题中提取关键实体（Pod、Node、Service 等）
- 调用 LLM 判断问题层级（L0-L4）
- 输出：layer, layer_confidence, layer_reasoning, layer_analysis

设计：
- 有自己的专用 prompt
- 调用 LLM 进行独立分析（使用和 HolmesService 相同的方式）
- 支持使用 runbooks 和 tools
- 输出结构化的分析结果供下游节点使用
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.context.archive import ContextArchive
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer
from app.core.prompts import get_workflow_prompt

logger = logging.getLogger(__name__)


class LayerClassifierNode(WorkflowNode):
    """
    问题定位节点

    每次执行都会调用 LLM 进行独立分析
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog
    
    @property
    def node_id(self) -> str:
        return "layer"
    
    @property
    def node_name(self) -> str:
        return "问题定位"

    def _get_prompt_language(self) -> str:
        if self.holmes_service and hasattr(self.holmes_service, "get_prompt_language"):
            return self.holmes_service.get_prompt_language()
        return "zh"

    def should_inject_runbook_catalog(self) -> bool:
        # /query direct 模式下只做轻量真实取数，不注入大段 runbook catalog 干扰本地模型工具决策。
        return not self._is_direct_query_mode()

    def _get_query_mode(self) -> str:
        wf_config = getattr(self, "workflow_config_override", None) or {}
        return str(wf_config.get("query_mode", "full")).strip().lower() or "full"

    def _is_direct_query_mode(self) -> bool:
        return self._get_query_mode() == "direct"

    def _get_layer_prompt(self) -> str:
        if self._is_direct_query_mode():
            return get_workflow_prompt("layer_query_direct", prompt_language=self._get_prompt_language())
        return get_workflow_prompt("layer", prompt_language=self._get_prompt_language())

    def _get_layer_extract_prompt(self) -> str:
        if self._is_direct_query_mode():
            return get_workflow_prompt("layer_query_direct_extract", prompt_language=self._get_prompt_language())
        return get_workflow_prompt("layer_extract", prompt_language=self._get_prompt_language())

    @staticmethod
    def _has_successful_tool_results(thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result" and ev.get("status") == "success"
            for ev in (thinking_events or [])
        )

    def _is_usable_query_result(
        self,
        result: Optional[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> bool:
        if not self._is_structured_layer_result(result):
            return False

        if result.get("layer") != "QUERY":
            return True

        query_result = result.get("query_result")
        if not isinstance(query_result, dict):
            return False

        if not self._has_successful_tool_results(thinking_events):
            return False

        rows = query_result.get("rows", []) or []
        missing = query_result.get("missing", []) or []
        sources = query_result.get("sources", []) or []
        return bool(sources) and bool(rows or missing)

    def _get_query_retry_prompt(self) -> str:
        return (
            self._get_layer_prompt()
            + "\n\n# 上一轮结果被系统拒绝\n"
              "- 原因：你输出了 QUERY JSON，但没有提供足够的真实工具执行结果。\n"
              "- 本轮必须先执行工具，再输出最终 JSON。\n"
              "- 在出现至少一次成功的 tool_result 之前，禁止输出最终答案。\n"
              "- 你的最后一条消息必须建立在真实工具结果之上，而不是工具计划之上。\n"
              "- 如果没有至少一次成功的 tool_result，系统会再次拒绝你的输出。\n"
              "- `query_result.rows` 为空且 `missing` 也为空，视为无效结果。\n"
              "- `collection_summary`、`sources`、`rows` 只能基于真实工具结果填写，禁止编造“已采集 100%”。\n"
        )

    def _build_query_direct_failure_result(
        self,
        question: str,
        full_analysis_text: str,
        failure_reason: str,
    ) -> Dict[str, Any]:
        return {
            "layer": "QUERY",
            "layers": ["QUERY"],
            "layer_name": "查询请求",
            "confidence": 0.3,
            "reasoning": failure_reason,
            "key_entities": [],
            "possible_scenarios": [],
            "query_result": {
                "query_target": question,
                "collection_summary": "计划 0 项，实际采集 0 项，未采集 1 项，完整度 0%",
                "columns": [
                    {"key": "status", "label": "状态"},
                    {"key": "reason", "label": "原因"},
                ],
                "rows": [],
                "notes": ["未获得足够的真实工具结果，已拒绝模型直接生成的伪结构化答案。"],
                "missing": [{"field": "query_result", "reason": failure_reason}],
                "sources": [],
            },
            "full_analysis": full_analysis_text,
        }
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行定层逻辑

        1. 构建专用 prompt
        2. 调用 LLM 分析
        3. 解析输出，提取层级信息
        """
        question = state.get("question", "")

        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            # 如果有 AICall，统一使用 LLM 做 QUERY / HEALTHY / L0-L4 判断
            ai_call = getattr(self, 'ai_call', None)
            if ai_call is not None:
                layer_result, thinking_events = self._analyze_with_llm(question)
            else:
                # 无 LLM 时仅使用低置信度兜底，避免人工关键词主导分类
                logger.info("⚠️ 无 LLM 服务，使用低置信度兜底分类")
                layer_result = self._analyze_with_rules(question)
                thinking_events = []

            # 解析层级
            layer = self._parse_layer(layer_result.get("layer", "L2"))

            # 解析多层级（多问题并存）
            raw_layers = layer_result.get("layers", [])
            layers = [self._parse_layer(l) for l in raw_layers if l] if raw_layers else [layer]

            # 提取阶段1的完整分析文本（包含工具调用数据），只归档，不再作为大字段传递给下游
            full_analysis = layer_result.pop("full_analysis", "")
            query_result = layer_result.pop("query_result", None)
            layer_handoff = self._build_layer_handoff(
                question=question,
                layer_result=layer_result,
                layer=layer,
                layers=layers,
                thinking_events=thinking_events,
            )
            archive_refs = self._archive_layer_outputs(
                run_id=state.get("run_id", ""),
                full_analysis=full_analysis,
                handoff=layer_handoff,
            )
            if archive_refs.get("full_analysis_ref"):
                layer_handoff["archive_ref"] = archive_refs["full_analysis_ref"]

            new_state.update({
                "layer": layer,
                "layers": layers,
                "layer_confidence": layer_result.get("confidence", 0.5),
                "layer_reasoning": layer_result.get("reasoning", ""),
                # 保存结构化分类结果
                "layer_analysis": json.dumps(layer_result, ensure_ascii=False),
                # 大文本只落盘；下游使用 layer_handoff
                "layer_full_analysis": None,
                "layer_handoff": layer_handoff,
                "layer_archive_ref": archive_refs,
                "context_archive_ref": archive_refs.get("run_root"),
                "key_entities": layer_result.get("key_entities", []),
                "possible_scenarios": layer_result.get("possible_scenarios", []),
            })
            if layer == Layer.QUERY and self._is_direct_query_mode() and isinstance(query_result, dict):
                new_state["query_result"] = query_result

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

            logger.info(f"✅ 问题定位完成: {layer} (置信度: {layer_result.get('confidence', 0):.0%})")

        except Exception as e:
            logger.error(f"问题定位失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            rescue_result = self._extract_with_lite_llm(
                question=question,
                full_analysis_text=f"# layer 节点执行异常\n{str(e)}",
                failure_reason=f"layer 节点执行异常: {str(e)}",
            )
            if rescue_result is None:
                raise

            layer = self._parse_layer(rescue_result.get("layer", "HEALTHY"))
            raw_layers = rescue_result.get("layers", [])
            layers = [self._parse_layer(l) for l in raw_layers if l] if raw_layers else [layer]
            full_analysis = rescue_result.pop("full_analysis", "")
            query_result = rescue_result.pop("query_result", None)
            layer_handoff = self._build_layer_handoff(
                question=question,
                layer_result=rescue_result,
                layer=layer,
                layers=layers,
                thinking_events=[],
            )
            archive_refs = self._archive_layer_outputs(
                run_id=state.get("run_id", ""),
                full_analysis=full_analysis,
                handoff=layer_handoff,
            )
            if archive_refs.get("full_analysis_ref"):
                layer_handoff["archive_ref"] = archive_refs["full_analysis_ref"]

            new_state.update({
                "layer": layer,
                "layers": layers,
                "layer_confidence": rescue_result.get("confidence", 0.5),
                "layer_reasoning": rescue_result.get("reasoning", ""),
                "layer_analysis": json.dumps(rescue_result, ensure_ascii=False),
                "layer_full_analysis": None,
                "layer_handoff": layer_handoff,
                "layer_archive_ref": archive_refs,
                "context_archive_ref": archive_refs.get("run_root"),
                "key_entities": rescue_result.get("key_entities", []),
                "possible_scenarios": rescue_result.get("possible_scenarios", []),
            })
            if layer == Layer.QUERY and self._is_direct_query_mode() and isinstance(query_result, dict):
                new_state["query_result"] = query_result
            self._save_thinking(state, new_state, [])

        return new_state

    def _archive_layer_outputs(
        self,
        run_id: str,
        full_analysis: str,
        handoff: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Archive full layer text and compact handoff; keep only refs in state."""
        if not run_id:
            return {}
        try:
            archive = ContextArchive(run_id=run_id)
            refs = archive.write_layer_artifacts(full_analysis or "", handoff or {})
            refs["run_root"] = str(archive.root)
            return refs
        except Exception as exc:
            logger.warning("⚠️ [layer] 写入 context archive 失败: %s", exc)
            return {}

    def _build_layer_handoff(
        self,
        question: str,
        layer_result: Dict[str, Any],
        layer: Layer,
        layers: List[Layer],
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a compact structured handoff for downstream nodes."""
        active_entities = self._normalize_entities(layer_result.get("key_entities", []))
        active_signals = []
        matched_runbooks = []

        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            tool_name = ev.get("tool_name", "unknown")
            if tool_name == "fetch_runbook":
                rb_id = self._extract_runbook_id(ev)
                if rb_id and rb_id not in matched_runbooks:
                    matched_runbooks.append(rb_id)

            signal = ev.get("result", "") or ev.get("result_preview", "")
            if signal:
                active_signals.append({
                    "source": tool_name,
                    "signal": self._compact_signal(signal),
                    "raw_ref": ev.get("raw_ref"),
                    "summary_ref": ev.get("summary_ref"),
                })

        layer_value = layer.value if hasattr(layer, "value") else str(layer)
        return {
            "diagnosis_scope": "current_state_only" if "之前" in question or "当前" in question or "现在" in question else "question_scope",
            "layer": layer_value,
            "layers": [l.value if hasattr(l, "value") else str(l) for l in layers],
            "confidence": layer_result.get("confidence", 0.5),
            "primary_problem": layer_result.get("reasoning", ""),
            "active_entities": active_entities,
            "active_signals": active_signals[:12],
            "possible_scenarios": layer_result.get("possible_scenarios", []),
            "matched_runbooks": matched_runbooks,
            "must_verify": [
                "确认 active_entities 中的对象当前仍存在于指定 namespace",
                "确认 active_signals 仍能被真实工具结果验证",
                "如果工具返回 NotFound、空事件或 namespace 不匹配，记录为冲突/负向证据",
            ],
            "do_not_change": [
                "不要把上游 namespace、Pod、Service、Node 名称改写成其他对象",
                "不要把历史 event 当成当前故障",
                "不要把计划或工具名当成证据，必须基于 tool_result",
            ],
        }

    @staticmethod
    def _normalize_entities(entities: Any) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        current_namespace = ""
        if not isinstance(entities, list):
            return normalized
        for entity in entities:
            if isinstance(entity, dict):
                etype = entity.get("type", "")
                value = entity.get("value") or entity.get("name") or ""
                namespace = entity.get("namespace", "")
                item = {"type": etype, "name": value}
                if namespace:
                    item["namespace"] = namespace
                normalized.append(item)
                if etype.lower() == "namespace" and value:
                    current_namespace = value
            else:
                normalized.append({"type": "Unknown", "name": str(entity)})
        if current_namespace:
            for item in normalized:
                if item.get("type", "").lower() != "namespace" and "namespace" not in item:
                    item["namespace"] = current_namespace
        return normalized

    @staticmethod
    def _compact_signal(text: str, limit: int = 500) -> str:
        compact = " ".join((text or "").split())
        return compact[:limit] + ("..." if len(compact) > limit else "")

    @staticmethod
    def _extract_runbook_id(event: Dict[str, Any]) -> str:
        raw = (event.get("result", "") or event.get("result_preview", "") or "")
        match = re.search(r"\[([a-z0-9][a-z0-9-]+)\]|runbook_id[:=]\s*([a-z0-9-]+)", raw, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2) or ""
        return ""

    def _analyze_with_llm(self, question: str) -> tuple:
        """使用 LLM 分析问题层级（单阶段架构）

        阶段1: AICall (LangChain create_agent) — 调用工具收集数据，并直接输出结构化 JSON

        Returns:
            (layer_result_dict, intermediate_events_list)
        """
        thinking_events = []
        try:
            # ── 阶段1：工具调用，收集集群状态 ──
            logger.info("📍 [layer] 阶段1: AICall 工具调用开始 | tools=%d",
                        len(getattr(self, 'tools', [])))
            response, thinking_events = self._call_llm(
                question,
                self._get_layer_prompt(),
                expect_json=True,
                json_validator=self._is_structured_layer_result,
            )

            if not (response and response.result):
                logger.warning("⚠️ [layer] 阶段1 无输出，转入 lite 提取")
                full_analysis_text = self._build_full_analysis("", thinking_events)
                extracted = self._extract_with_lite_llm(
                    question=question,
                    full_analysis_text=full_analysis_text,
                    failure_reason="LLM 未返回有效结果，转入无工具结构化提取",
                )
                if extracted is None:
                    raise RuntimeError("layer_extract 未能从现有分析文本中生成合法 JSON")
                return extracted, thinking_events

            logger.debug("📋 [layer] 阶段1 输出: %s", response.result[:200])

            full_analysis_text = self._build_full_analysis(response.result, thinking_events)

            # 压缩 enriched_text（可能含大量工具原始输出，50-100K chars）
            # 压缩后传给下游 evidence/rca/conclusion，避免 token overflow
            compact_threshold = 30000
            if len(full_analysis_text) > compact_threshold:
                logger.info("📦 [layer] enriched_text 过大 (%d chars)，执行 LLM 压缩",
                            len(full_analysis_text))
                enriched_text_for_downstream = self._compact_context(
                    full_analysis_text, max_chars=compact_threshold
                )
            else:
                enriched_text_for_downstream = full_analysis_text

            # 阶段1必须直接输出结构化 JSON
            result = self._try_parse_json(response.result)
            if self._is_structured_layer_result(result):
                if self._is_direct_query_mode() and result.get("layer") == "QUERY":
                    if not self._is_usable_query_result(result, thinking_events):
                        logger.warning("⚠️ [layer] QUERY direct 输出缺少真实工具结果或有效 rows，发起一次严格重试")
                        retry_response, retry_events = self._call_llm(
                            question,
                            self._get_query_retry_prompt(),
                            expect_json=True,
                            json_validator=self._is_structured_layer_result,
                        )
                        thinking_events = (thinking_events or []) + (retry_events or [])
                        retry_text = retry_response.result if retry_response else ""
                        full_analysis_text = self._build_full_analysis(retry_text, thinking_events)
                        if len(full_analysis_text) > compact_threshold:
                            enriched_text_for_downstream = self._compact_context(
                                full_analysis_text, max_chars=compact_threshold
                            )
                        else:
                            enriched_text_for_downstream = full_analysis_text

                        retry_result = self._try_parse_json(retry_text)
                        if self._is_usable_query_result(retry_result, thinking_events):
                            logger.info("✅ [layer] QUERY direct 严格重试后获得真实工具结果")
                            retry_result["full_analysis"] = enriched_text_for_downstream
                            return retry_result, thinking_events

                        failure_reason = "QUERY 请求未获得任何可用的真实工具结果，拒绝直接返回伪结构化结果"
                        logger.warning("⚠️ [layer] %s", failure_reason)
                        return self._build_query_direct_failure_result(
                            question=question,
                            full_analysis_text=enriched_text_for_downstream,
                            failure_reason=failure_reason,
                        ), thinking_events
                logger.info("✅ [layer] 阶段1直接输出合法 JSON: layer=%s, confidence=%.2f",
                           result.get('layer'), result.get('confidence', 0))
                result["full_analysis"] = enriched_text_for_downstream
                return result, thinking_events

            # 阶段1失败 → 使用无工具 lite 提取基于已收集上下文做结构化分类
            logger.warning("⚠️ [layer] 阶段1未返回合法 JSON，转入 lite 提取")
            extracted = self._extract_with_lite_llm(
                question=question,
                full_analysis_text=enriched_text_for_downstream,
                failure_reason="LLM 未返回合法 JSON，转入无工具结构化提取",
            )
            if extracted is None:
                raise RuntimeError("layer_extract 未能从现有分析文本中生成合法 JSON")
            return extracted, thinking_events

        except Exception as e:
            logger.warning(f"[layer] LLM 分析失败，转入 lite 提取: {e}")
            full_analysis_text = self._build_full_analysis("", thinking_events)
            extracted = self._extract_with_lite_llm(
                question=question,
                full_analysis_text=full_analysis_text or f"# layer 阶段1异常\n{str(e)}",
                failure_reason=f"LLM 定层失败，转入无工具结构化提取: {str(e)}",
            )
            if extracted is None:
                raise
            return extracted, thinking_events

    def _extract_with_lite_llm(
        self,
        question: str,
        full_analysis_text: str,
        failure_reason: str = "",
    ) -> Optional[Dict[str, Any]]:
        """当 agent 未直接产出合法 JSON 时，基于已收集内容再做一次无工具结构化提取。"""
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            logger.warning("⚠️ [layer] 无 ai_call，无法执行 lite 提取")
            return None

        extract_prompt = self._get_layer_extract_prompt()
        extract_input = (
            f"# 用户问题\n{question}\n\n"
            f"# 失败原因\n{failure_reason or '未提供'}\n\n"
            f"# 分析文本\n{full_analysis_text or '无'}"
        )
        parsed, raw = ai_call.call_simple_json(
            extract_prompt,
            extract_input,
            validator=self._is_structured_layer_result,
            max_tokens=2048,
        )
        if parsed is None:
            logger.warning("⚠️ [layer] lite 提取仍未返回合法 JSON | raw=%s", (raw or "")[:500])
            return None

        parsed["full_analysis"] = full_analysis_text
        logger.info("✅ [layer] lite 提取成功: layer=%s confidence=%.2f",
                    parsed.get("layer"), parsed.get("confidence", 0.0))
        return parsed

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Dict]:
        """尝试从文本中提取 JSON，失败返回 None"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def _is_structured_layer_result(result: Optional[Dict]) -> bool:
        """判断阶段1输出是否已是可用的结构化定层结果。"""
        if not isinstance(result, dict):
            return False

        layer = result.get("layer")
        confidence = result.get("confidence")
        reasoning = result.get("reasoning")

        if not isinstance(layer, str) or not layer.strip():
            return False
        if not isinstance(reasoning, str) or not reasoning.strip():
            return False
        if not isinstance(confidence, (int, float)):
            return False

        return True

    @staticmethod
    def _build_full_analysis(llm_text: str, thinking_events: list) -> str:
        """构建阶段1完整分析文本：LLM 输出 + 工具返回的原始数据。"""
        parts = [llm_text]

        tool_data = []
        for ev in thinking_events:
            # 收集工具调用结果
            if ev.get("type") == "tool_result" and ev.get("status") == "success":
                tool_name = ev.get("tool_name", "unknown")
                # 优先用完整结果，回退到 preview
                result_text = ev.get("result", "") or ev.get("result_preview", "")
                if result_text:
                    tool_data.append(f"[{tool_name}]\n{result_text}")

        if tool_data:
            parts.append("\n\n# 工具返回的原始数据（以此为准）")
            parts.extend(tool_data)

        return "\n".join(parts)

    def _analyze_with_rules(self, question: str) -> Dict:
        """无 LLM 时的低置信度兜底分类，避免使用人工关键词规则主导分类。"""
        return {
            "layer": "L2",
            "layer_name": "工作负载层",
            "confidence": 0.1,
            "reasoning": "LLM 不可用，无法完成基于问题和环境的可靠定层，使用低置信度默认层级兜底",
            "key_entities": [],
            "possible_scenarios": []
        }

    def _parse_layer(self, layer_str: str) -> Layer:
        """解析层级字符串为 Layer 枚举"""
        layer_map = {
            "HEALTHY": Layer.HEALTHY,
            "QUERY": Layer.QUERY,
            "L0": Layer.L0,
            "L1": Layer.L1,
            "L2": Layer.L2,
            "L3": Layer.L3,
            "L4": Layer.L4,
        }
        return layer_map.get(layer_str.upper(), Layer.L2)
