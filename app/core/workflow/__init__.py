"""
工作流模块 - LangGraph 分阶段诊断工作流

设计原则：
- 高内聚：每个节点封装完整的业务逻辑
- 低耦合：节点间通过状态传递数据
- 可扩展：新增节点只需继承 WorkflowNode

启用方式：
- 设置环境变量 USE_WORKFLOW=true
- 在 deploy/secrets/core.yaml 中配置

Prompt 管理：
- 所有节点的 Prompt 统一在 app/core/prompts.py 中管理

指标要求：
- MTTR < 10m
- 根因准确率 >= 80%
- 证据完整率 > 90%
- Runbook 覆盖率 > 90%
"""

from typing import Optional

# 状态模型
from .state import WorkflowState

# 节点基类
from .nodes.base import WorkflowNode

# 工作流图和执行器
from .graph import build_diagnosis_workflow, build_simple_workflow
from .executor import WorkflowExecutor
from .node_registry import (
    NodeSpec,
    WORKFLOW_NODE_SPECS,
    get_specs_before,
    get_display_name,
    get_spec,
    iter_specs,
)

# 指标模块
from .metrics import (
    WorkflowMetrics,
    NodeMetrics,
    start_workflow_metrics,
    finish_workflow_metrics,
    get_current_metrics,
)

__all__ = [
    # 状态和节点
    "WorkflowState",
    "WorkflowNode",
    # 图和执行器
    "build_diagnosis_workflow",
    "build_simple_workflow",
    "WorkflowExecutor",
    # 节点注册表
    "NodeSpec",
    "WORKFLOW_NODE_SPECS",
    "get_specs_before",
    "get_display_name",
    "get_spec",
    "iter_specs",
    # 指标
    "WorkflowMetrics",
    "NodeMetrics",
    "start_workflow_metrics",
    "finish_workflow_metrics",
    "get_current_metrics",
]
