"""
工作流图构建

设计原则：
- 节点顺序：layer → evidence → rca → conclusion
- 线性流程（未来可扩展条件分支）
- 每个节点独立，易于替换/扩展
"""

from typing import Any
from langgraph.graph import StateGraph, END
from app.core.workflow.state import WorkflowState
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode


def build_diagnosis_workflow(
    holmes_service: Any = None,
    full_mode: bool = True
) -> StateGraph:
    """
    构建诊断工作流图
    
    每个节点都会调用 LLM 进行独立分析：
    - 节点1: 使用 LAYER_CLASSIFIER_PROMPT 判断问题层级
    - 节点2: 使用 EVIDENCE_COLLECTOR_PROMPT 规划证据采集
    - 节点3: 使用 ROOT_CAUSE_ANALYZER_PROMPT 进行根因推理
    - 节点4: 使用 CONCLUSION_FORMATTER_PROMPT 生成最终报告
    
    Args:
        holmes_service: HolmesService 实例（用于 LLM 调用）
        full_mode: 是否使用完整4节点流程（默认 True）
    
    Returns:
        编译后的工作流图
    """
    workflow = StateGraph(WorkflowState)
    
    # 创建节点实例（每个节点都接收 holmes_service 用于 LLM 调用）
    layer_node = LayerClassifierNode(holmes_service)
    evidence_node = EvidenceCollectorNode(holmes_service)
    rca_node = RootCauseAnalyzerNode(holmes_service)
    conclusion_node = ConclusionFormatterNode(holmes_service)
    
    # 添加节点
    workflow.add_node("layer", layer_node.execute)
    workflow.add_node("evidence", evidence_node.execute)
    workflow.add_node("rca", rca_node.execute)
    workflow.add_node("conclusion", conclusion_node.execute)
    
    # 定义边（完整4节点流程）
    workflow.set_entry_point("layer")
    workflow.add_edge("layer", "evidence")
    workflow.add_edge("evidence", "rca")
    workflow.add_edge("rca", "conclusion")
    workflow.add_edge("conclusion", END)
    
    # 编译工作流
    return workflow.compile()


def build_simple_workflow(holmes_service: Any = None) -> StateGraph:
    """
    构建简化工作流（仅包含节点1和节点4）
    
    用于快速测试或简单场景
    """
    workflow = StateGraph(WorkflowState)
    
    layer_node = LayerClassifierNode()
    conclusion_node = ConclusionFormatterNode()
    
    workflow.add_node("layer", layer_node.execute)
    workflow.add_node("conclusion", conclusion_node.execute)
    
    workflow.set_entry_point("layer")
    workflow.add_edge("layer", "conclusion")
    workflow.add_edge("conclusion", END)
    
    return workflow.compile()
