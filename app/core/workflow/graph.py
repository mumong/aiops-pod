"""
工作流图构建

设计原则：
- 节点顺序：layer → evidence → rca → conclusion
- 节点可通过 config.yaml 的 workflow.nodes 启用/禁用
- QUERY 模式走轻量查询路径（layer 轻量路由 → evidence 归一化 → conclusion 渲染）
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
from app.core.workflow.nodes.parallel_evidence import (
    ParallelEvidenceNode,
    expand_groups_to_entity_lanes,
    extract_abnormal_groups,
)
from app.core.skills.models import Layer

logger = logging.getLogger(__name__)

# 节点定义注册表：id → (类, 显示名)
NODE_REGISTRY = {
    "layer": (LayerClassifierNode, "问题定位"),
    "evidence": (EvidenceCollectorNode, "证据采集"),
    "parallel_evidence": (ParallelEvidenceNode, "并发证据采集"),
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
    query_mode: str = "full",
    parallel_config: Optional[Dict[str, Any]] = None,
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

    # Pod 诊断 lane 扇出配置。默认 threshold=0，使单异常与多异常共享
    # 同一条「每 Pod 一 lane」事实/RCA/归档契约；保留正数 threshold 仅用于
    # 需要兼容旧共享 evidence 路径的部署。
    parallel_cfg = parallel_config or {}
    parallel_enabled = (
        bool(parallel_cfg.get("enabled", True))
        and "evidence" in enabled
        and "layer" in enabled
    )
    parallel_threshold = 0
    try:
        parallel_threshold = max(0, int(parallel_cfg.get("threshold", 0)))
    except (TypeError, ValueError):
        pass

    # 创建并添加启用的节点
    node_instances = []
    for node_id in enabled:
        cls, display_name = NODE_REGISTRY[node_id]
        node = cls(holmes_service, metrics, runbook_catalog)
        node_instances.append(node)
        workflow.add_node(node_id, _wrap_node_execute(node))

    if parallel_enabled:
        parallel_node = ParallelEvidenceNode(holmes_service, metrics, runbook_catalog)
        node_instances.append(parallel_node)
        workflow.add_node("parallel_evidence", _wrap_node_execute(parallel_node))
        # 并发采集完成后直达 conclusion（每组的单独分析即该组 RCA，跳过全局 rca）
        workflow.add_edge("parallel_evidence", "conclusion")

    # 设置入口点
    workflow.set_entry_point(enabled[0])

    # 构建边
    layer_enabled = "layer" in enabled
    evidence_enabled = "evidence" in enabled
    for i, node_id in enumerate(enabled[:-1]):
        next_node = enabled[i + 1]

        if node_id == "layer" and layer_enabled:
            # layer 节点有条件路由：HEALTHY 直达 conclusion；异常 Pod 默认
            # 全部走 parallel_evidence，每个 Pod 一条 lane。
            workflow.add_conditional_edges(
                "layer",
                _make_layer_router(
                    enabled,
                    query_mode=query_mode,
                    parallel_enabled=parallel_enabled,
                    parallel_threshold=parallel_threshold,
                ),
                _make_layer_route_map(enabled, parallel_enabled=parallel_enabled),
            )
        elif node_id == "evidence" and evidence_enabled:
            # evidence 节点有条件路由：QUERY 直达 conclusion，其余进入下一个分析节点
            workflow.add_conditional_edges(
                "evidence",
                _make_evidence_router(enabled),
                _make_evidence_route_map(enabled),
            )
        else:
            workflow.add_edge(node_id, next_node)

    # 终点
    workflow.add_edge(enabled[-1], END)

    return workflow.compile(), node_instances


def _make_layer_router(
    enabled: list,
    query_mode: str = "full",
    parallel_enabled: bool = False,
    parallel_threshold: int = 0,
):
    """创建 layer 节点的条件路由函数"""
    def router(state: WorkflowState) -> str:
        layer = state.get("layer")
        if layer == Layer.QUERY:
            if str(query_mode or "full").strip().lower() == "direct":
                logger.info("🚀 QUERY direct 模式：直接到 conclusion")
                return "conclusion"
            idx = enabled.index("layer")
            next_node = enabled[idx + 1] if idx + 1 < len(enabled) else "conclusion"
            logger.info("🚀 QUERY 模式：进入 %s", next_node)
            return next_node
        # Explicit diagnosis targets define an N-target total-fan-in contract,
        # even when one instantaneous lookup is healthy. Route them before the
        # general HEALTHY fast path so requested targets cannot disappear.
        handoff = state.get("layer_handoff") or {}
        if parallel_enabled and handoff.get("explicit_pod_targets"):
            groups = extract_abnormal_groups(handoff)
            lane_count = len(expand_groups_to_entity_lanes(groups))
            if lane_count > parallel_threshold:
                logger.info(
                    "🚀 显式 Pod 并发模式：%d 个目标 lanes > 阈值 %d，进入 parallel_evidence",
                    lane_count,
                    parallel_threshold,
                )
                return "parallel_evidence"
        if layer == Layer.HEALTHY:
            logger.info("🚀 HEALTHY 模式：直接到 conclusion")
            return "conclusion"
        # 按原子 Pod lane 数量判断，避免粗粒度 Layer 分组把多个 Pod 压成
        # 一组；默认阈值 0，因此 N=1/3/5/10 使用同一诊断路径。
        if parallel_enabled:
            groups = extract_abnormal_groups(state.get("layer_handoff"))
            lane_count = len(expand_groups_to_entity_lanes(groups))
            if lane_count > parallel_threshold:
                logger.info(
                    "🚀 多异常并发模式：检出 %d 组/%d Pod lanes > 阈值 %d，进入 parallel_evidence",
                    len(groups), lane_count, parallel_threshold,
                )
                return "parallel_evidence"
        # 找 layer 之后的下一个节点
        idx = enabled.index("layer")
        return enabled[idx + 1] if idx + 1 < len(enabled) else "conclusion"
    return router


def _make_layer_route_map(enabled: list, parallel_enabled: bool = False) -> dict:
    """创建 layer 路由的目标映射"""
    route_map = {"conclusion": "conclusion"}
    idx = enabled.index("layer")
    if idx + 1 < len(enabled):
        next_node = enabled[idx + 1]
        route_map[next_node] = next_node
    if parallel_enabled:
        route_map["parallel_evidence"] = "parallel_evidence"
    return route_map


def _make_evidence_router(enabled: list):
    """创建 evidence 节点的条件路由函数"""
    def router(state: WorkflowState) -> str:
        idx = enabled.index("evidence")
        return enabled[idx + 1] if idx + 1 < len(enabled) else "conclusion"

    return router


def _make_evidence_route_map(enabled: list) -> dict:
    """创建 evidence 路由的目标映射"""
    route_map = {"conclusion": "conclusion"}
    idx = enabled.index("evidence")
    if idx + 1 < len(enabled):
        next_node = enabled[idx + 1]
        route_map[next_node] = next_node
    return route_map


def build_simple_workflow(holmes_service=None, metrics=None, runbook_catalog=None):
    """构建简化工作流（仅 layer + conclusion）"""
    return build_diagnosis_workflow(
        holmes_service, metrics, runbook_catalog,
        node_config={"layer": True, "evidence": False, "rca": False, "conclusion": True},
        query_mode="direct",
    )
