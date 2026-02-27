"""
工作流图构建

设计原则：
- 节点顺序：由节点注册表统一管理（默认：layer → evidence → rca → conclusion）
- 线性流程（未来可扩展条件分支）
- 每个节点独立，易于替换/扩展
"""

from typing import Any, Iterable, List

from langgraph.graph import END, StateGraph

from app.core.workflow.state import WorkflowState
from app.core.workflow.node_registry import NodeSpec, iter_specs


def build_diagnosis_workflow(
    holmes_service: Any = None,
    metrics: Any = None,
    runbook_catalog: Any = None
) -> StateGraph:
    """
    构建诊断工作流图

    每个节点都会调用 LLM 进行独立分析，并使用 runbooks：
    - 节点1: 使用 LAYER_CLASSIFIER_PROMPT 判断问题层级
    - 节点2: 使用 EVIDENCE_COLLECTOR_PROMPT 规划证据采集
    - 节点3: 使用 ROOT_CAUSE_ANALYZER_PROMPT 进行根因推理
    - 节点4: 使用 CONCLUSION_FORMATTER_PROMPT 生成最终报告

    Args:
        holmes_service: HolmesService 实例（用于 LLM 调用）
        metrics: WorkflowMetrics 实例（用于记录统计）
        runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）

    Returns:
        编译后的工作流图
    """
    workflow = StateGraph(WorkflowState)
    _register_nodes_and_edges(
        workflow=workflow,
        specs=iter_specs(),
        holmes_service=holmes_service,
        metrics=metrics,
        runbook_catalog=runbook_catalog,
    )

    return workflow.compile()


def build_simple_workflow(holmes_service: Any = None, runbook_catalog: Any = None) -> StateGraph:
    """
    构建简化工作流（仅包含节点1和节点4）

    用于快速测试或简单场景
    """
    workflow = StateGraph(WorkflowState)

    # 从注册表中仅选择 layer 和 conclusion 两个节点，保持原有行为
    specs = [
        spec
        for spec in iter_specs()
        if spec.id in ("layer", "conclusion")
    ]
    _register_nodes_and_edges(
        workflow=workflow,
        specs=specs,
        holmes_service=holmes_service,
        metrics=None,
        runbook_catalog=runbook_catalog,
    )

    return workflow.compile()


def _register_nodes_and_edges(
    workflow: StateGraph,
    specs: Iterable[NodeSpec],
    holmes_service: Any,
    metrics: Any,
    runbook_catalog: Any,
) -> None:
    """
    根据节点规格列表注册节点并构建线性边关系
    """
    specs_list: List[NodeSpec] = list(specs)
    if not specs_list:
        return

    # 添加节点
    for spec in specs_list:
        node_instance = spec.cls(holmes_service, metrics, runbook_catalog)
        workflow.add_node(spec.id, node_instance.execute)

    # 设置入口与边（线性）
    first = specs_list[0]
    workflow.set_entry_point(first.id)

    for prev, curr in zip(specs_list, specs_list[1:]):
        workflow.add_edge(prev.id, curr.id)

    # 末节点指向 END
    last = specs_list[-1]
    workflow.add_edge(last.id, END)
