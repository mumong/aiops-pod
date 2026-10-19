"""
工作流图构建

公开入口使用 auto：RequestRouter 选择轻量查询、深度诊断、修复或澄清/终止。
- focused → query_collect
- full_diagnosis → layer →（parallel_evidence | evidence → rca）→ conclusion
- remediation → remediation
direct 模式仅包含 query_collect，供内部直接查询。
"""

import logging
import time
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from app.core.log_context import log_context
from app.core.workflow.nodes.query_answer import QueryCollectNode, QueryConclusionNode
from app.core.workflow.nodes.request_router import RequestRouterNode
from app.core.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


def _wrap_node_execute(node: Any):
    """为节点执行注入生命周期事件，便于 executor 做精确计时。"""

    def execute_with_lifecycle(state: WorkflowState):
        event_queue = getattr(node, "_event_queue", None)
        start_ts = time.time()

        if event_queue is not None:
            event_queue.put(
                (
                    "node_lifecycle",
                    {
                        "phase": "start",
                        "node": node.node_id,
                        "node_name": node.node_name,
                        "ts": start_ts,
                    },
                )
            )

        try:
            with log_context(node=node.node_id):
                new_state = node.execute(state)
        except Exception as exc:
            if event_queue is not None:
                event_queue.put(
                    (
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
                    )
                )
            raise

        if event_queue is not None:
            event_queue.put(
                (
                    "node_lifecycle",
                    {
                        "phase": "end",
                        "node": node.node_id,
                        "node_name": node.node_name,
                        "ts": time.time(),
                        "success": True,
                        "state_update": new_state,
                    },
                )
            )

        return new_state

    return execute_with_lifecycle


def build_diagnosis_workflow(
    holmes_service: Any = None,
    metrics: Any = None,
    runbook_catalog: Any = None,
    node_config: Optional[Dict[str, bool]] = None,
    query_mode: str = "auto",
    parallel_config: Optional[Dict[str, Any]] = None,
) -> tuple:
    """
    构建工作流图。

    Args:
        holmes_service: HolmesService 实例
        metrics: WorkflowMetrics 实例
        runbook_catalog: RunbookCatalog 实例
        node_config: 兼容旧调用方的节点开关；auto/direct 图不使用
        query_mode: "auto"（默认）或 "direct"
        parallel_config: {"enabled": bool, "max_workers": int}；enabled 控制 layer 是否分组，
            max_workers 限制 parallel_evidence 同时运行的 lane 数

    Returns:
        (compiled_workflow, node_instances)
    """
    if query_mode == "direct":
        workflow = StateGraph(WorkflowState)
        nodes = [QueryCollectNode(holmes_service, metrics, runbook_catalog)]
        for node in nodes:
            workflow.add_node(node.node_id, _wrap_node_execute(node))
        workflow.set_entry_point(nodes[0].node_id)
        workflow.add_edge(nodes[0].node_id, END)
        return workflow.compile(), nodes

    if query_mode != "auto":
        logger.warning("未知 query_mode=%s，按 auto 构建工作流", query_mode)

    from app.core.workflow.nodes.autonomous_diagnosis import (
        DiagnosisEvidenceNode,
        DiagnosisRootCauseNode,
        DiagnosisStageNode,
    )
    from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode
    from app.core.workflow.nodes.remediation import RemediationNode

    workflow = StateGraph(WorkflowState)
    nodes = [
        cls(holmes_service, metrics, runbook_catalog)
        for cls in (
            RequestRouterNode,
            QueryCollectNode,
            DiagnosisStageNode,
            DiagnosisEvidenceNode,
            DiagnosisRootCauseNode,
            AutonomousParallelNode,
            QueryConclusionNode,
            RemediationNode,
        )
    ]
    for node in nodes:
        if node.node_id == "layer":
            node.autonomous_parallel_enabled = (parallel_config or {}).get("enabled", True)
        if node.node_id == "parallel_evidence":
            node.autonomous_parallel_workers = (parallel_config or {}).get("max_workers")
        workflow.add_node(node.node_id, _wrap_node_execute(node))
    workflow.set_entry_point("request_router")
    workflow.add_conditional_edges(
        "request_router",
        lambda state: state["request_route"],
        {
            "focused": "query_collect",
            "full_diagnosis": "layer",
            "clarify": END,
            "stop": END,
            "remediation": "remediation",
        },
    )
    workflow.add_edge("remediation", END)
    workflow.add_edge("query_collect", END)
    from app.core.workflow.pod_detection import after_location

    workflow.add_conditional_edges(
        "layer",
        after_location,
        {
            "parallel_evidence": "parallel_evidence",
            "evidence": "evidence",
            "conclusion": "conclusion",
        },
    )
    workflow.add_edge("parallel_evidence", "conclusion")
    workflow.add_edge("evidence", "rca")
    workflow.add_edge("rca", "conclusion")
    workflow.add_edge("conclusion", END)
    return workflow.compile(), nodes
