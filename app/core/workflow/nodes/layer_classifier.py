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
from app.core.prompts import LAYER_CLASSIFIER_PROMPT

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

            new_state.update({
                "layer": layer,
                "layer_confidence": layer_result.get("confidence", 0.5),
                "layer_reasoning": layer_result.get("reasoning", ""),
                # 保存完整的 LLM 分析结果供下游使用
                "layer_analysis": json.dumps(layer_result, ensure_ascii=False),
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
        """使用 LLM 分析问题层级

        Returns:
            (layer_result_dict, intermediate_events_list)
        """
        try:
            response, thinking_events = self._call_llm(question, LAYER_CLASSIFIER_PROMPT)

            if response and response.result:
                return self._parse_llm_response(response.result), thinking_events

            return self._analyze_with_rules(question), thinking_events

        except Exception as e:
            logger.warning(f"LLM 分析失败，回退到规则: {e}")
            return self._analyze_with_rules(question), []

    # def _log_available_tools(self, tool_executor: Any):
    #     """输出可用的工具信息"""
    #     if not tool_executor:
    #         logger.info("🔧 可用工具: 无 tool_executor")
    #         return

    #     # 分类工具
    #     builtin_tools = []
    #     mcp_tools = []
    #     mcp_servers = []

    #     for toolset in tool_executor.toolsets:
    #         toolset_class = toolset.__class__.__name__
    #         toolset_name = getattr(toolset, "name", str(toolset))
    #         is_enabled = getattr(toolset, "enabled", False)

    #         # 判断是否是 MCP 工具
    #         is_mcp = "mcp" in toolset_class.lower() or (
    #             hasattr(toolset, "type") and str(toolset.type).lower() == "mcp"
    #         )

    #         if is_mcp:
    #             mcp_servers.append({
    #                 "name": toolset_name,
    #                 "enabled": is_enabled,
    #             })
    #         else:
    #             # 内置工具
    #             if hasattr(toolset, "tools") and toolset.tools:
    #                 tool_count = 0
    #                 for t in toolset.tools:
    #                     if hasattr(t, "name"):
    #                         tool_count += 1
    #                         builtin_tools.append(getattr(t, "name", str(t)))

    #     # 输出日志
    #     if mcp_servers:
    #         logger.info(f"🌐 MCP 工具集: {len(mcp_servers)} 个")
    #         for server in mcp_servers:
    #             status = "✅ 启用" if server["enabled"] else "❌ 禁用"
    #             logger.info(f"   {status} {server['name']}")
    #     else:
    #         logger.info("🌐 MCP 工具集: 无")

    #     if builtin_tools:
    #         logger.info(f"🔧 内置工具: {len(builtin_tools)} 个")
    #         for tool in builtin_tools[:20]:  # 最多显示20个
    #             logger.info(f"   • {tool}")
    #         if len(builtin_tools) > 20:
    #             logger.info(f"   ... 还有 {len(builtin_tools) - 20} 个工具")

    # def _log_available_runbooks(self, runbook_catalog: Any):
    #     """输出可用的 runbooks 信息"""
    #     if not runbook_catalog:
    #         logger.info("📚 Runbook 知识库: 无")
    #         return

    #     catalog = runbook_catalog.catalog if hasattr(runbook_catalog, "catalog") else []
    #     if not catalog:
    #         logger.info("📚 Runbook 知识库: 0 个")
    #         return

    #     logger.info(f"📚 Runbook 知识库: {len(catalog)} 个")
    #     for entry in catalog[:10]:  # 最多显示10个
    #         if hasattr(entry, "title"):
    #             title = entry.title
    #         elif isinstance(entry, dict):
    #             title = entry.get("title", "Unknown")
    #         else:
    #             title = str(entry)
    #         logger.info(f"   • {title}")
    #     if len(catalog) > 10:
    #         logger.info(f"   ... 还有 {len(catalog) - 10} 个 runbook")
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """解析 LLM 的 JSON 响应"""
        try:
            # 提取 JSON 块
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 尝试直接解析
            return json.loads(response_text)
        
        except json.JSONDecodeError:
            # 解析失败，从文本中提取关键信息
            return self._extract_from_text(response_text)
    
    def _extract_from_text(self, text: str) -> Dict:
        """从非 JSON 文本中提取信息"""
        result = {
            "layer": "L2",
            "layer_name": "工作负载层",
            "confidence": 0.5,
            "reasoning": text[:200],
            "key_entities": [],
            "possible_scenarios": []
        }

        # 优先检测 QUERY 模式
        query_indicators = [
            r'"layer"\s*:\s*"QUERY"',
            r'QUERY',
            r'直接查询',
            r'查询结果',
            r'query_results',
        ]
        # 同时检测是否有诊断指标
        diagnosis_indicators = [
            r'故障', r'异常', r'报错', r'重启', r'crash', r'oom',
            r'排查', r'诊断',
        ]
        text_lower = text.lower()
        has_query_indicator = any(re.search(p, text, re.IGNORECASE) for p in query_indicators)
        has_diagnosis_indicator = any(re.search(p, text_lower) for p in diagnosis_indicators)

        if has_query_indicator and not has_diagnosis_indicator:
            result["layer"] = "QUERY"
            result["layer_name"] = "直接查询"
            result["confidence"] = 0.9
            result["possible_scenarios"] = [{"scenario": "用户直接查询", "probability": "高", "reason": "数据请求"}]
            return result

        # 提取层级
        layer_patterns = [
            (r'L0|基础设施', "L0", "基础设施层"),
            (r'L1|集群.*节点', "L1", "集群与节点层"),
            (r'L2|工作负载|Pod|容器', "L2", "工作负载层"),
            (r'L3|服务.*网络|DNS', "L3", "服务与网络层"),
            (r'L4|应用|依赖', "L4", "应用层"),
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
            "QUERY": Layer.QUERY,
            "L0": Layer.L0,
            "L1": Layer.L1,
            "L2": Layer.L2,
            "L3": Layer.L3,
            "L4": Layer.L4,
        }
        return layer_map.get(layer_str.upper(), Layer.L2)
