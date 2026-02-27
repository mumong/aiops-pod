"""
工作流节点注册表

职责：
- 作为「单一事实来源」统一管理诊断工作流中的节点列表与元数据
- 为图构建、结论节点、执行器、输出格式化器提供统一的节点视图

设计原则：
- 高内聚：所有与节点 ID / 显示名 / 分析字段 相关的信息集中在此处
- 低耦合：调用方通过辅助函数访问信息，而不是手写映射 / 分支
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Type

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode


@dataclass(frozen=True)
class NodeSpec:
    """
    工作流节点元数据

    Attributes:
        id: 节点唯一 ID（与状态字段、prompt key 等保持一致）
        name: 节点中文显示名
        cls: 节点实现类（继承自 WorkflowNode）
        analysis_key: 该节点在 WorkflowState 中用于保存「完整分析文本」的字段名
    """

    id: str
    name: str
    cls: Type[WorkflowNode]
    analysis_key: Optional[str] = None


# 诊断工作流的默认节点顺序：
# layer → evidence → rca → conclusion
WORKFLOW_NODE_SPECS: List[NodeSpec] = [
    NodeSpec(
        id="layer",
        name="问题定位",
        cls=LayerClassifierNode,
        analysis_key="layer_analysis",
    ),
    NodeSpec(
        id="evidence",
        name="证据链采集",
        cls=EvidenceCollectorNode,
        analysis_key="evidence_analysis",
    ),
    NodeSpec(
        id="rca",
        name="根因分析",
        cls=RootCauseAnalyzerNode,
        analysis_key="rca_analysis",
    ),
    NodeSpec(
        id="conclusion",
        name="汇总总结",
        cls=ConclusionFormatterNode,
        analysis_key=None,  # 结论节点输出的是 conclusion/conclusion_formatted
    ),
]


def get_specs_before(node_id: str) -> List[NodeSpec]:
    """
    获取位于指定节点之前的所有节点规格（按默认顺序）
    """
    result: List[NodeSpec] = []
    for spec in WORKFLOW_NODE_SPECS:
        if spec.id == node_id:
            break
        result.append(spec)
    return result


def get_display_name(node_id: str) -> str:
    """
    根据节点 ID 获取显示名；若未注册则回退为原 ID
    """
    for spec in WORKFLOW_NODE_SPECS:
        if spec.id == node_id:
            return spec.name
    return node_id


def get_spec(node_id: str) -> Optional[NodeSpec]:
    """
    获取单个节点的规格
    """
    for spec in WORKFLOW_NODE_SPECS:
        if spec.id == node_id:
            return spec
    return None


def iter_specs(predicate: Optional[Callable[[NodeSpec], bool]] = None) -> List[NodeSpec]:
    """
    按顺序返回满足条件的节点规格列表；不传 predicate 则返回全部
    """
    if predicate is None:
        return list(WORKFLOW_NODE_SPECS)
    return [spec for spec in WORKFLOW_NODE_SPECS if predicate(spec)]


def get_all_analysis_keys() -> List[str]:
    """
    返回所有已声明的 analysis_key（用于初始化或调试）
    """
    return [s.analysis_key for s in WORKFLOW_NODE_SPECS if s.analysis_key]

