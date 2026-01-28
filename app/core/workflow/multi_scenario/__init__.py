"""
多场景诊断模块

提供多场景检测和报告生成的功能

模块结构：
- output.py: 输出数据模型和结果管理
- formatters.py: 报告格式化器
"""

from app.core.workflow.multi_scenario.output import (
    ScenarioDecision,
    MultiScenarioOutput,
    ScenarioSeverity,
)

from app.core.workflow.multi_scenario.formatters import MultiScenarioFormatter


__all__ = [
    "ScenarioDecision",
    "MultiScenarioOutput",
    "ScenarioSeverity",
    "MultiScenarioFormatter",
]
