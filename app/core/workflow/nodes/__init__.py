"""
工作流节点模块

auto 图节点（见 graph.build_diagnosis_workflow）：
- RequestRouterNode: 请求路由（focused / full_diagnosis / remediation / clarify / stop）
- QueryCollectNode / QueryConclusionNode: 自主查询与结论
- DiagnosisStageNode / DiagnosisEvidenceNode / DiagnosisRootCauseNode: 定位、采证、根因
- AutonomousParallelNode: 多组独立 lane 并发
- RemediationNode: 修复规划
"""

from .base import WorkflowNode

__all__ = ["WorkflowNode"]
