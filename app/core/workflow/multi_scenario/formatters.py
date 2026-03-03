"""
多场景报告格式化器

职责：
- 生成多场景诊断的结构化报告
- 按严重程度、层级分组展示
- 提供清晰的修复建议和验证步骤

设计原则：
- 高内聚：格式化逻辑独立
- 低耦合：通过数据模型输入输出
"""

from typing import List, Dict, Any
from app.core.workflow.multi_scenario.output import ScenarioDecision, ScenarioSeverity
from app.core.skills.models import Layer
from app.core.text_helpers import truncate_question


class MultiScenarioFormatter:
    """
    多场景报告格式化器

    将多个场景判定结果格式化为易读的报告
    """

    def format_full_report(self, scenarios: List[ScenarioDecision], question: str = "") -> str:
        """
        生成完整的多场景诊断报告

        Args:
            scenarios: 检测到的场景列表
            question: 用户问题

        Returns:
            Markdown 格式的报告
        """
        lines = []

        # 报告头部
        lines.append("=" * 70)
        lines.append("🔍 K8s 多场景诊断报告")
        lines.append("=" * 70)
        lines.append("")

        # 用户问题
        lines.append(f"📝 用户问题: {truncate_question(question)}")
        lines.append("")

        # 统计摘要
        lines.append("-" * 70)
        lines.append("")

        # 按严重程度分组
        severity_groups = self._group_by_severity(scenarios)
        lines.append(self._format_summary_section(severity_groups))
        lines.append("")

        # 详细场景列表（按严重程度排序）
        lines.append("---")
        lines.append("")

        for severity in [ScenarioSeverity.CRITICAL, ScenarioSeverity.HIGH, ScenarioSeverity.MEDIUM, ScenarioSeverity.LOW]:
            group_scenarios = severity_groups.get(severity, [])
            if not group_scenarios:
                continue

            lines.append(self._format_severity_header(severity))
            lines.append("")

            for i, scenario in enumerate(group_scenarios, 1):
                lines.append(self._format_scenario_detail(scenario, i))
                lines.append("")

        # 综合修复建议
        lines.append("---")
        lines.append("")

        lines.append(self._format_remediation_summary(scenarios))
        lines.append("")

        lines.append("=" * 70)
        lines.append("")

        return "\n".join(lines)

    def _group_by_severity(self, scenarios: List[ScenarioDecision]) -> Dict[ScenarioSeverity, List[ScenarioDecision]]:
        """按严重程度分组"""
        groups = {
            ScenarioSeverity.CRITICAL: [],
            ScenarioSeverity.HIGH: [],
            ScenarioSeverity.MEDIUM: [],
            ScenarioSeverity.LOW: [],
        }

        for scenario in scenarios:
            groups[scenario.severity].append(scenario)

        return groups

    def _format_summary_section(self, severity_groups: Dict[ScenarioSeverity, List[ScenarioDecision]]) -> str:
        """格式化统计摘要"""
        lines = []
        lines.append("## 📊 诊断统计")

        total_count = len(severity_groups[ScenarioSeverity.CRITICAL]) + len(severity_groups[ScenarioSeverity.HIGH]) + \
                     len(severity_groups[ScenarioSeverity.MEDIUM]) + len(severity_groups[ScenarioSeverity.LOW])

        lines.append(f"**总检测场景数**: {total_count}")

        lines.append("")
        lines.append("| 严重程度 | 数量 | 占比 |")
        lines.append("|----------|------|------|")
        for severity in [ScenarioSeverity.CRITICAL, ScenarioSeverity.HIGH, ScenarioSeverity.MEDIUM, ScenarioSeverity.LOW]:
            count = len(severity_groups[severity])
            pct = (count / total_count * 100) if total_count > 0 else 0
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}[severity.value]
            lines.append(f"| {icon} {severity.value.capitalize():10s} | {count:2d} | {pct:5.1f}% |")

        lines.append("")
        lines.append("")

        # 按层级统计
        lines.append("**按层级分布**:")
        lines.append("")
        layer_counts = {}
        for scenarios in severity_groups.values():
            for scenario in scenarios:
                layer = scenario.layer.value if isinstance(scenario.layer, Layer) else str(scenario.layer)
                layer_counts[layer] = layer_counts.get(layer, 0) + 1

        for layer, count in sorted(layer_counts.items(), key=lambda x: x):
            lines.append(f"  - {layer}: {count} 个")

        lines.append("")

        return "\n".join(lines)

    def _format_severity_header(self, severity: ScenarioSeverity) -> str:
        """格式化严重程度头部"""
        icon_map = {
            ScenarioSeverity.CRITICAL: "🔴",
            ScenarioSeverity.HIGH: "🟠",
            ScenarioSeverity.MEDIUM: "🟡",
            ScenarioSeverity.LOW: "⚪",
        }

        name_map = {
            ScenarioSeverity.CRITICAL: "Critical（立即处理）",
            ScenarioSeverity.HIGH: "High（优先处理）",
            ScenarioSeverity.MEDIUM: "Medium（建议尽快处理）",
            ScenarioSeverity.LOW: "Low（关注即可）",
        }

        return f"### {icon_map[severity.value]} {name_map[severity.value]}"

    def _format_scenario_detail(self, scenario: ScenarioDecision, index: int) -> str:
        """格式化单个场景的详细信息"""
        lines = []

        lines.append(f"#### 场景 {index}: {scenario.scenario_name}")
        lines.append("")

        # 基本信息
        lines.append(f"**层级**: {scenario.layer.value if isinstance(scenario.layer, Layer) else str(scenario.layer)}")
        lines.append(f"**置信度**: {scenario.confidence.value} ({scenario.confidence_score:.0%})")
        lines.append(f"**证据完整度**: {scenario.evidence_count}/{scenario.evidence_total} ({scenario.evidence_count/max(scenario.evidence_total, 1)*100:.0f}%)")
        lines.append("")

        # 问题描述
        if scenario.issue_summary:
            lines.append(f"**问题描述**: {scenario.issue_summary}")

        lines.append("")

        # 根因分析
        if scenario.root_cause:
            lines.append(f"**根因**: {scenario.root_cause}")

        lines.append("")

        # 证据链
        if scenario.collected_evidence:
            lines.append("**已采集证据**:")
            for i, evidence in enumerate(scenario.collected_evidence, 1):
                lines.append(f"  {i}. {evidence}")
            lines.append("")

        if scenario.missing_evidence:
            lines.append("**缺失证据**:")
            for i, evidence in enumerate(scenario.missing_evidence, 1):
                lines.append(f"  {i}. {evidence}")
            lines.append("")

        lines.append("")

        # 修复建议
        if scenario.remediation_steps:
            lines.append("**修复建议**:")
            for i, step in enumerate(scenario.remediation_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        if scenario.verification_steps:
            lines.append("")
            lines.append("**验证步骤**:")
            for i, step in enumerate(scenario.verification_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        # 受影响实体
        if scenario.affected_entities:
            lines.append("")
            lines.append("**受影响实体**:")
            for key, value in scenario.affected_entities.items():
                lines.append(f"  - {key}: {value}")
            lines.append("")

        # 使用的工具
        if scenario.source_tools:
            lines.append("")
            lines.append("**使用的工具**: {', '.join(scenario.source_tools)}")

        lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _format_remediation_summary(self, scenarios: List[ScenarioDecision]) -> str:
        """格式化综合修复建议"""
        lines = []
        lines.append("## 🛠️ 综合修复建议")

        if not scenarios:
            lines.append("未检测到需要处理的问题")
            return "\n".join(lines)

        # Critical 问题
        critical_scenarios = [s for s in scenarios if s.severity == ScenarioSeverity.CRITICAL]
        if critical_scenarios:
            lines.append("")
            lines.append("### 🔴 Critical 问题（立即处理）")
            lines.append("")
            for scenario in critical_scenarios:
                lines.append(f"**{scenario.scenario_name}**: {scenario.issue_summary[:80]}")
                if scenario.remediation_steps:
                    lines.append(f"  修复: {scenario.remediation_steps[0][:60]}...")
                lines.append("")

        # High 问题
        high_scenarios = [s for s in scenarios if s.severity == ScenarioSeverity.HIGH]
        if high_scenarios:
            lines.append("")
            lines.append("### 🟠 High 问题（优先处理）")
            lines.append("")
            for scenario in high_scenarios:
                lines.append(f"**{scenario.scenario_name}**: {scenario.issue_summary[:80]}")
                if scenario.remediation_steps:
                    lines.append(f"  修复: {scenario.remediation_steps[0][:60]}...")
                lines.append("")

        # Medium 问题
        medium_scenarios = [s for s in scenarios if s.severity == ScenarioSeverity.MEDIUM]
        if medium_scenarios:
            lines.append("")
            lines.append("### 🟡 Medium 问题（建议处理）")
            lines.append("")
            for scenario in medium_scenarios:
                lines.append(f"**{scenario.scenario_name}**: {scenario.issue_summary[:80]}")
                if scenario.remediation_steps:
                    lines.append(f"  修复: {scenario.remediation_steps[0][:60]}...")

        # Low 问题
        low_scenarios = [s for s in scenarios if s.severity == ScenarioSeverity.LOW]
        if low_scenarios:
            lines.append("")
            lines.append("### ⚪ Low 问题（关注即可）")
            lines.append("")
            for scenario in low_scenarios:
                lines.append(f"**{scenario.scenario_name}**: {scenario.issue_summary[:80]}")
                if scenario.remediation_steps:
                    lines.append(f"  修复: {scenario.remediation_steps[0][:60]}...")

        lines.append("")

        return "\n".join(lines)
