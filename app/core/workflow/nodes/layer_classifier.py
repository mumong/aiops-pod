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

    def _get_layer_prompt(self) -> str:
        return get_workflow_prompt("layer", prompt_language=self._get_prompt_language())
    
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

            # 提取阶段1的完整分析文本（包含工具调用数据），单独传递给下游
            full_analysis = layer_result.pop("full_analysis", "")

            new_state.update({
                "layer": layer,
                "layers": layers,
                "layer_confidence": layer_result.get("confidence", 0.5),
                "layer_reasoning": layer_result.get("reasoning", ""),
                # 保存结构化分类结果
                "layer_analysis": json.dumps(layer_result, ensure_ascii=False),
                # 保存阶段1完整分析文本（含工具输出），供 evidence/rca 使用
                "layer_full_analysis": full_analysis,
                "key_entities": layer_result.get("key_entities", []),
                "possible_scenarios": layer_result.get("possible_scenarios", []),
            })

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

            logger.info(f"✅ 问题定位完成: {layer} (置信度: {layer_result.get('confidence', 0):.0%})")

        except Exception as e:
            logger.error(f"问题定位失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            # 失败时使用默认值
            new_state.update({
                "layer": Layer.L2,
                "layer_confidence": 0.3,
                "layer_reasoning": f"定层失败，使用默认值（错误: {str(e)}）",
                "layer_analysis": "{}",
            })
            self._save_thinking(state, new_state, [])

        return new_state

    def _analyze_with_llm(self, question: str) -> tuple:
        """使用 LLM 分析问题层级（单阶段架构）

        阶段1: AICall (LangChain create_agent) — 调用工具收集数据，并直接输出结构化 JSON

        Returns:
            (layer_result_dict, intermediate_events_list)
        """
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
                logger.warning("⚠️ [layer] 阶段1 无输出，使用通用低置信度兜底")
                return self._build_llm_fallback(
                    reason="LLM 未返回有效结果，无法完成可靠定层",
                ), thinking_events

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
                logger.info("✅ [layer] 阶段1直接输出合法 JSON: layer=%s, confidence=%.2f",
                           result.get('layer'), result.get('confidence', 0))
                result["full_analysis"] = enriched_text_for_downstream
                return result, thinking_events

            # 阶段1失败 → 使用通用低置信度兜底，不再做规则/正则提层
            logger.warning("⚠️ [layer] 阶段1未返回合法 JSON，使用通用低置信度兜底")
            fallback = self._build_llm_fallback(
                reason="LLM 未返回合法 JSON，无法完成可靠定层",
                full_analysis=enriched_text_for_downstream,
            )
            return fallback, thinking_events

        except Exception as e:
            logger.warning(f"[layer] LLM 分析失败，使用通用低置信度兜底: {e}")
            return self._build_llm_fallback(
                reason=f"LLM 定层失败: {str(e)}",
            ), []

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

    @staticmethod
    def _build_llm_fallback(reason: str, full_analysis: str = "") -> Dict:
        """LLM 不可用或未返回结构化结果时的通用低置信度回退。"""
        result = {
            "layer": "L2",
            "layers": ["L2"],
            "layer_name": "工作负载层",
            "confidence": 0.1,
            "reasoning": reason,
            "key_entities": [],
            "possible_scenarios": [],
        }
        if full_analysis:
            result["full_analysis"] = full_analysis
        return result
    
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
