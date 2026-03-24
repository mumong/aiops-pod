"""
工作流图构建

设计原则：
- 节点顺序：layer → evidence → rca → conclusion
- QUERY 模式走简化路径：layer → conclusion（跳过 evidence + rca）
- 诊断模式走完整路径：layer → evidence → rca → conclusion
- 每个节点独立，易于替换/扩展
"""

import logging
from typing import Any
from langgraph.graph import StateGraph, END
from app.core.workflow.state import WorkflowState
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.skills.models import Layer

logger = logging.getLogger(__name__)


def _route_after_layer(state: WorkflowState) -> str:
    """
    layer 节点后的条件路由

    - QUERY 模式：跳过 evidence + rca，直接到 conclusion
    - 诊断模式（L0-L4）：走完整流程 evidence → rca → conclusion
    """
    layer = state.get("layer")
    if layer == Layer.QUERY:
        logger.info("🚀 QUERY 模式：跳过 evidence + rca，直接到 conclusion")
        return "conclusion"
    return "evidence"


def build_diagnosis_workflow(
    holmes_service: Any = None,
    metrics: Any = None,
    runbook_catalog: Any = None
) -> StateGraph:
    """
    构建诊断工作流图（带条件路由）

    路由逻辑：
    - QUERY 模式：layer → conclusion（2 节点，快速响应）
    - 诊断模式：layer → evidence → rca → conclusion（4 节点，完整诊断）

    Args:
        holmes_service: HolmesService 实例（用于 LLM 调用）
        metrics: WorkflowMetrics 实例（用于记录统计）
        runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）

    Returns:
        编译后的工作流图
    """
    workflow = StateGraph(WorkflowState)

    # 创建节点实例（传递 holmes_service、metrics 和 runbook_catalog）
    layer_node = LayerClassifierNode(holmes_service, metrics, runbook_catalog)
    evidence_node = EvidenceCollectorNode(holmes_service, metrics, runbook_catalog)
    rca_node = RootCauseAnalyzerNode(holmes_service, metrics, runbook_catalog)
    conclusion_node = ConclusionFormatterNode(holmes_service, metrics, runbook_catalog)

    # 添加节点
    workflow.add_node("layer", layer_node.execute)
    workflow.add_node("evidence", evidence_node.execute)
    workflow.add_node("rca", rca_node.execute)
    workflow.add_node("conclusion", conclusion_node.execute)

    # 定义边（条件路由）
    workflow.set_entry_point("layer")

    # layer 节点后根据结果条件路由
    workflow.add_conditional_edges("layer", _route_after_layer, {
        "conclusion": "conclusion",
        "evidence": "evidence",
    })

    # 诊断模式的后续边
    workflow.add_edge("evidence", "rca")
    workflow.add_edge("rca", "conclusion")
    workflow.add_edge("conclusion", END)

    # 编译工作流
    return workflow.compile()


def build_simple_workflow(holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None) -> StateGraph:
    """
    构建简化工作流（仅包含节点1和节点4）

    用于快速测试或简单场景。
    注意：build_diagnosis_workflow 现在内置条件路由，QUERY 模式会自动跳过 evidence+rca。
    此函数保留用于显式构建最小工作流。
    """
    workflow = StateGraph(WorkflowState)

    layer_node = LayerClassifierNode(holmes_service, metrics, runbook_catalog)
    conclusion_node = ConclusionFormatterNode(holmes_service, metrics, runbook_catalog)

    workflow.add_node("layer", layer_node.execute)
    workflow.add_node("conclusion", conclusion_node.execute)

    workflow.set_entry_point("layer")
    workflow.add_edge("layer", "conclusion")
    workflow.add_edge("conclusion", END)

    return workflow.compile()
