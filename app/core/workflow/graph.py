"""
工作流图构建

设计原则：
- 节点顺序：layer → evidence → rca → conclusion
- 节点可通过 config.yaml 的 workflow.nodes 启用/禁用
- QUERY 模式走简化路径（保留 evidence，跳过 rca）
- HEALTHY 模式直接到 conclusion
- conclusion 始终保留（最终输出节点）
- 每个节点独立，易于替换/扩展
"""

import logging
import time
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, END
from app.core.workflow.state import WorkflowState
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.skills.models import Layer

logger = logging.getLogger(__name__)

# 节点定义注册表：id → (类, 显示名)
NODE_REGISTRY = {
    "layer": (LayerClassifierNode, "问题定位"),
    "evidence": (EvidenceCollectorNode, "证据采集"),
    "rca": (RootCauseAnalyzerNode, "根因分析"),
    "conclusion": (ConclusionFormatterNode, "汇总总结"),
}

# 默认节点执行顺序
DEFAULT_NODE_ORDER = ["layer", "evidence", "rca", "conclusion"]


def _wrap_node_execute(node: Any):
    """为节点执行注入生命周期事件，便于 executor 做精确计时。"""
    def execute_with_lifecycle(state: WorkflowState):
        event_queue = getattr(node, "_event_queue", None)
        start_ts = time.time()

        if event_queue is not None:
            event_queue.put((
                "node_lifecycle",
                {
                    "phase": "start",
                    "node": node.node_id,
                    "node_name": node.node_name,
                    "ts": start_ts,
                },
            ))

        try:
            new_state = node.execute(state)
        except Exception as exc:
            if event_queue is not None:
                event_queue.put((
                    "node_lifecycle",
                    {
                        "phase": "end",
                        "node": node.node_id,
                        "node_name": node.node_name,
                        "ts": time.time(),
                        "success": False,
                        "error": str(exc),
                        "state_update": {},
                    },
                ))
            raise

        if event_queue is not None:
            event_queue.put((
                "node_lifecycle",
                {
                    "phase": "end",
                    "node": node.node_id,
                    "node_name": node.node_name,
                    "ts": time.time(),
                    "success": True,
                    "state_update": new_state,
                },
            ))

        return new_state

    return execute_with_lifecycle


def _get_enabled_nodes(node_config: Optional[Dict[str, bool]] = None) -> list:
    """根据配置返回启用的节点列表（保持顺序，conclusion 强制启用）"""
    if not node_config:
        return list(DEFAULT_NODE_ORDER)

    enabled = []
    for node_id in DEFAULT_NODE_ORDER:
        if node_id == "conclusion":
            enabled.append(node_id)  # conclusion 不可禁用
        elif node_config.get(node_id, True):
            enabled.append(node_id)
        else:
            logger.info(f"⏭️ 节点 [{node_id}] 已禁用，跳过")
    return enabled


def build_diagnosis_workflow(
    holmes_service: Any = None,
    metrics: Any = None,
    runbook_catalog: Any = None,
    node_config: Optional[Dict[str, bool]] = None,
) -> tuple:
    """
    构建诊断工作流图（支持节点启用/禁用）

    Args:
        holmes_service: HolmesService 实例
        metrics: WorkflowMetrics 实例
        runbook_catalog: RunbookCatalog 实例
        node_config: 节点启用配置，如 {"layer": False, "rca": False}

    Returns:
        (compiled_workflow, node_instances) — 编译后的工作流图 + 节点实例列表
    """
    enabled = _get_enabled_nodes(node_config)
    logger.info(f"🔧 工作流节点: {' → '.join(enabled)}")

    workflow = StateGraph(WorkflowState)

    # 创建并添加启用的节点
    node_instances = []
    for node_id in enabled:
        cls, display_name = NODE_REGISTRY[node_id]
        node = cls(holmes_service, metrics, runbook_catalog)
        node_instances.append(node)
        workflow.add_node(node_id, _wrap_node_execute(node))

    # 设置入口点
    workflow.set_entry_point(enabled[0])

    # 构建边
    layer_enabled = "layer" in enabled
    for i, node_id in enumerate(enabled[:-1]):
        next_node = enabled[i + 1]

        if node_id == "layer" and layer_enabled:
            # layer 节点有条件路由：HEALTHY 直达 conclusion，QUERY 进入 evidence
            workflow.add_conditional_edges(
                "layer",
                _make_layer_router(enabled),
                _make_layer_route_map(enabled),
            )
        else:
            workflow.add_edge(node_id, next_node)

    # 终点
    workflow.add_edge(enabled[-1], END)

    return workflow.compile(), node_instances


def _make_layer_router(enabled: list):
    """创建 layer 节点的条件路由函数"""
    def router(state: WorkflowState) -> str:
        layer = state.get("layer")
        if layer == Layer.HEALTHY:
            logger.info("🚀 HEALTHY 模式：直接到 conclusion")
            return "conclusion"
        if layer == Layer.QUERY:
            idx = enabled.index("layer")
            next_node = enabled[idx + 1] if idx + 1 < len(enabled) else "conclusion"
            logger.info("🚀 QUERY 模式：进入 %s", next_node)
            return next_node
        # 找 layer 之后的下一个节点
        idx = enabled.index("layer")
        return enabled[idx + 1] if idx + 1 < len(enabled) else "conclusion"
    return router


def _make_layer_route_map(enabled: list) -> dict:
    """创建 layer 路由的目标映射"""
    route_map = {"conclusion": "conclusion"}
    idx = enabled.index("layer")
    if idx + 1 < len(enabled):
        next_node = enabled[idx + 1]
        route_map[next_node] = next_node
    return route_map


def build_simple_workflow(holmes_service=None, metrics=None, runbook_catalog=None):
    """构建简化工作流（仅 layer + conclusion）"""
    return build_diagnosis_workflow(
        holmes_service, metrics, runbook_catalog,
        node_config={"layer": True, "evidence": False, "rca": False, "conclusion": True},
    )
