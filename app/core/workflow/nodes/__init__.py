"""
工作流节点模块

每个节点都是独立的模块，高内聚低耦合

节点列表：
- LayerClassifierNode: 节点1 - 问题定位（初步定层）
- EvidenceCollectorNode: 节点2 - 证据链采集
- RootCauseAnalyzerNode: 节点3 - 根因分析
- ConclusionFormatterNode: 节点4 - 汇总总结
"""

from .base import WorkflowNode
from .layer_classifier import LayerClassifierNode
from .evidence_collector import EvidenceCollectorNode
from .root_cause_analyzer import RootCauseAnalyzerNode
from .conclusion_formatter import ConclusionFormatterNode

__all__ = [
    "WorkflowNode",
    "LayerClassifierNode",
    "EvidenceCollectorNode",
    "RootCauseAnalyzerNode",
    "ConclusionFormatterNode",
]
