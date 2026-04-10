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
from app.core.prompts import LAYER_CLASSIFIER_PROMPT, LAYER_EXTRACT_PROMPT

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
            # 如果有 HolmesService，使用 LLM 分析
            if self.holmes_service and self.holmes_service.ai:
                layer_result, thinking_events = self._analyze_with_llm(question)
            else:
                # 回退到规则匹配
                logger.info("⚠️ 无 LLM 服务，使用规则匹配")
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
        """使用 LLM 分析问题层级（两阶段架构）

        阶段1: HolmesGPT agentic loop — 调用工具收集数据，输出自然语言分析
        阶段2: litellm 直接调用 — 基于分析文本+工具数据，提取结构化 JSON

        Returns:
            (layer_result_dict, intermediate_events_list)
        """
        try:
            # ── 阶段1：工具调用，收集集群状态 ──
            logger.debug("📍 [layer] 阶段1开始 | ai_call=%s tools=%d",
                         type(getattr(self, 'ai_call', None)).__name__,
                         len(getattr(self, 'tools', [])))
            response, thinking_events = self._call_llm(question, LAYER_CLASSIFIER_PROMPT)

            if not (response and response.result):
                return self._analyze_with_rules(question), thinking_events

            # 尝试从 response.result 直接解析 JSON（偶尔 LLM 会直接输出 JSON）
            result = self._try_parse_json(response.result)
            if result and result.get("possible_scenarios") and result.get("confidence", 0) > 0.6:
                logger.info(f"✅ 阶段1直接输出了合法 JSON: layer={result.get('layer')}")
                return result, thinking_events

            # ── 阶段2：结构化提取（始终执行） ──
            logger.info("📋 阶段2: 使用 litellm 从分析文本中提取结构化分类")
            enriched_text = self._build_extraction_input(response.result, thinking_events)
            extracted = self._extract_classification_with_litellm(enriched_text)
            if extracted:
                # 关键：把阶段1的完整分析文本注入结果，供下游 evidence/rca 使用
                extracted["full_analysis"] = enriched_text
                return extracted, thinking_events

            # 阶段2 也失败 → 最终兜底
            logger.warning("⚠️ 阶段2 litellm 提取失败，使用层级关键词兜底")
            fallback = self._extract_from_text(response.result)
            fallback["full_analysis"] = enriched_text
            return fallback, thinking_events

        except Exception as e:
            logger.warning(f"LLM 分析失败，回退到规则: {e}")
            return self._analyze_with_rules(question), []

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
    def _build_extraction_input(llm_text: str, thinking_events: list) -> str:
        """构建阶段2的输入：LLM 分析文本 + 工具返回的原始数据"""
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

    def _extract_classification_with_litellm(self, analysis_text: str) -> Optional[Dict]:
        """用 litellm 从工具调用后的分析文本中提取结构化 JSON 分类"""
        try:
            # Use ai_call.call_simple if available (aicall path)
            ai_call = getattr(self, 'ai_call', None)
            if ai_call:
                content = ai_call.call_simple(
                    system_prompt=LAYER_EXTRACT_PROMPT,
                    question=analysis_text,
                )
            else:
                # Legacy litellm path
                from litellm import completion

                model = self.holmes_service.ai.llm.model
                api_key = getattr(self.holmes_service.ai.llm, 'api_key', None)
                api_base = getattr(self.holmes_service.ai.llm, 'api_base', None)

                completion_kwargs = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": LAYER_EXTRACT_PROMPT},
                        {"role": "user", "content": analysis_text},
                    ],
                    "temperature": 0.1,
                }
                if api_key:
                    completion_kwargs["api_key"] = api_key
                if api_base:
                    completion_kwargs["api_base"] = api_base

                resp = completion(**completion_kwargs)
                content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

            if content:
                result = self._try_parse_json(content)
                if result and result.get("layer") and result.get("confidence", 0) > 0.5:
                    logger.info(f"✅ litellm 提取分类成功: layer={result['layer']}, confidence={result.get('confidence')}")
                    return result
                elif content:
                    logger.warning(f"litellm 返回内容无法解析为 JSON: {content[:200]}")

        except Exception as e:
            logger.warning(f"litellm 提取分类失败: {e}")
        return None


    def _extract_from_text(self, text: str) -> Dict:
        """从非 JSON 文本中提取层级信息（最终兜底，仅匹配 L0-L4）

        注意：HEALTHY/QUERY 的判断完全交给 _extract_classification_with_litellm，
        这里不做 HEALTHY/QUERY 的硬编码判断，避免误判。
        """
        result = {
            "layer": "L2",
            "layer_name": "工作负载层",
            "confidence": 0.5,
            "reasoning": text[:200],
            "key_entities": [],
            "possible_scenarios": []
        }

        # 提取层级（按根因优先级排序，L0 最优先）
        layer_patterns = [
            (r'L0|基础设施|Evicted|volume.?limit|emptyDir|sizeLimit|disk.?pressure|ENOSPC|磁盘|驱逐', "L0", "基础设施层"),
            (r'L1|NotReady|kubelet|taint|节点.*不可调度', "L1", "集群与节点层"),
            (r'L2|OOMKilled|CrashLoop|Exit.?Code.?137|容器.*重启', "L2", "工作负载层"),
            (r'L3|ImagePull|DNS|NetworkPolicy|服务.*网络', "L3", "服务与网络层"),
            (r'L4|应用.*错误|依赖.*503|upstream', "L4", "应用层"),
        ]

        for pattern, layer, name in layer_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result["layer"] = layer
                result["layer_name"] = name
                break

        return result
    
    def _analyze_with_rules(self, question: str) -> Dict:
        """使用规则匹配分析（回退方案）"""
        q_lower = question.lower()

        # 优先检测：是否为直接查询（非故障诊断）
        query_keywords = [
            "使用率", "用了多少", "占用", "cpu", "内存", "memory", "磁盘",
            "多少", "状态", "列表", "有哪些", "pod列表", "节点列表",
            "查询", "查看", "获取", "统计", "概况", "概览", "情况",
        ]
        diagnosis_keywords = [
            "故障", "问题", "异常", "报错", "错误", "失败", "不通",
            "重启", "crash", "oom", "排查", "诊断", "为什么",
            "不正常", "不可用", "挂了", "宕机",
        ]

        has_query = any(kw in q_lower for kw in query_keywords)
        has_diagnosis = any(kw in q_lower for kw in diagnosis_keywords)

        # 有查询关键词且无诊断关键词 → QUERY
        if has_query and not has_diagnosis:
            return {
                "layer": "QUERY",
                "layer_name": "直接查询",
                "confidence": 0.9,
                "reasoning": "检测到数据查询关键词，无故障诊断关键词，判定为直接查询",
                "key_entities": [],
                "possible_scenarios": [{"scenario": "用户直接查询", "probability": "高", "reason": "数据请求，非故障"}]
            }

        # 规则匹配：关键词 -> 层级映射
        layer_rules = {
            # L0: 基础设施层
            "disk": ("L0", "基础设施层", 0.9, "检测到磁盘相关关键词"),
            "enospc": ("L0", "基础设施层", 0.95, "检测到 ENOSPC 错误"),
            "no space": ("L0", "基础设施层", 0.9, "检测到磁盘空间不足"),
            "磁盘": ("L0", "基础设施层", 0.9, "检测到磁盘相关关键词"),
            
            # L1: 集群与节点层
            "kubelet": ("L1", "集群与节点层", 0.9, "检测到 Kubelet 相关关键词"),
            "notready": ("L1", "集群与节点层", 0.9, "检测到 Node NotReady 状态"),
            "证书": ("L1", "集群与节点层", 0.85, "检测到证书相关关键词"),
            
            # L2: 工作负载层
            "oom": ("L2", "工作负载层", 0.95, "检测到 OOM 相关关键词"),
            "oomkilled": ("L2", "工作负载层", 0.95, "检测到 OOMKilled 状态"),
            "137": ("L2", "工作负载层", 0.9, "检测到退出码 137（OOM）"),
            "crashloop": ("L2", "工作负载层", 0.9, "检测到 CrashLoopBackOff 状态"),
            "重启": ("L2", "工作负载层", 0.85, "检测到重启相关关键词"),
            "pod": ("L2", "工作负载层", 0.8, "检测到 Pod 相关关键词"),
            
            # L3: 服务与网络层
            "dns": ("L3", "服务与网络层", 0.9, "检测到 DNS 相关关键词"),
            "coredns": ("L3", "服务与网络层", 0.9, "检测到 CoreDNS 相关关键词"),
            "网络": ("L3", "服务与网络层", 0.85, "检测到网络相关关键词"),
            
            # L4: 应用层
            "503": ("L4", "应用层", 0.9, "检测到 503 错误码"),
            "依赖": ("L4", "应用层", 0.8, "检测到依赖服务相关关键词"),
        }
        
        # 匹配规则
        matched = []
        for keyword, (layer, name, conf, reason) in layer_rules.items():
            if keyword in q_lower:
                matched.append((layer, name, conf, reason))
        
        if matched:
            # 按置信度排序
            matched.sort(key=lambda x: x[2], reverse=True)
            layer, name, conf, reason = matched[0]
            
            return {
                "layer": layer,
                "layer_name": name,
                "confidence": conf * 0.9 if len(matched) > 1 else conf,
                "reasoning": reason + (f"（同时匹配到 {len(matched)} 个关键词）" if len(matched) > 1 else ""),
                "key_entities": [],
                "possible_scenarios": []
            }
        
        # 默认
        return {
            "layer": "L2",
            "layer_name": "工作负载层",
            "confidence": 0.5,
            "reasoning": "未匹配到明确关键词，默认判定为工作负载层",
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
