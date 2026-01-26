"""
输出格式化器

设计原则：
- 职责单一：只负责将 DeterministicDecision 格式化为各种输出格式
- 可扩展：支持 Markdown、JSON、Plain Text 等格式
- 国际化友好：文本与逻辑分离
- 业界标准：参考 Datadog、New Relic、Dynatrace、Splunk 等商业 AIOps 产品的输出格式

业界参考：
1. Datadog Root Cause Analysis (RCA) - 结构化证据链 + 时序分析
2. New Relic AI Root Cause - 因果图 + 影响评估
3. Dynatrace Davis - 评分机制 + 建议优先级
4. Splunk ITSI - KPI 趋势 + 相关事件关联
"""

from __future__ import annotations

from .models import Confidence, DeterministicDecision


class DecisionFormatter:
    """决策格式化器"""

    @staticmethod
    def to_markdown(decision: DeterministicDecision) -> str:
        """
        格式化为 Markdown（附加到 LLM 报告末尾）

        参考业界格式：
        - Datadog RCA 报告结构
        - New Relic AI Root Cause 分析
        - Dynatrace Davis 分析
        - Splunk ITSI 异常检测报告
        """
        d = decision
        lines = []

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🤖 确定性分析（Deterministic Analysis）")
        lines.append("")

        # ============================================================
        # 1. 问题概览（Issue Overview）
        # ============================================================
        lines.append("### 📍 问题概览")
        lines.append("")

        # 使用表格展示基本信息
        layer_val = d.layer.value if hasattr(d.layer, 'value') else str(d.layer)
        conf_val = d.confidence.value if hasattr(d.confidence, 'value') else str(d.confidence)
        conf_color = "🟢" if d.confidence == Confidence.HIGH else ("🟡" if d.confidence == Confidence.MEDIUM else "🔴")

        lines.append(f"**问题摘要**: {d.issue_summary if d.issue_summary else f'{layer_val} - {d.category}'}")
        lines.append("")
        lines.append("| 属性 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| **诊断层级** | {layer_val} |")
        lines.append(f"| **异常场景** | {d.scenario} |")
        lines.append(f"| **问题分类** | {d.category} |")
        lines.append(f"| **置信度** | {conf_color} {conf_val} ({d.confidence_score:.1%}) |")
        lines.append(f"| **证据完整度** | {d._calculate_evidence_completeness()} |")
        lines.append(f"| **问题状态** | {'✅ 已确认' if d.issue_found else '❓ 待确认'} |")
        lines.append("")

        # ============================================================
        # 2. 深度分析（Deep Analysis）- 业界特色
        # ============================================================
        lines.append("### 🔬 深度分析")
        lines.append("")
        lines.append("**分析维度**:")
        lines.append("")
        lines.append("| 维度 | 分析结果 | 证据来源 |")
        lines.append("|------|----------|----------|")

        # 层级定位分析
        lines.append(f"| **层级定位** | 基于 L0-L4 模型定位到 **{layer_val}** 层 | 规则引擎 |")

        # 场景分类分析
        lines.append(f"| **场景识别** | 匹配到 **{d.category}** 异常场景 | {d.matched_rules[0] if d.matched_rules else '无'} |")

        # 证据完整性分析
        completeness = d._calculate_evidence_completeness()
        if completeness == "100%":
            lines.append(f"| **证据状态** | 证据完整 ({completeness})，判定可信 | 规则引擎 |")
        elif completeness.replace('%', '').isdigit():
            comp_val = float(completeness.replace('%', ''))
            if comp_val >= 75:
                lines.append(f"| **证据状态** | 证据较为完整 ({completeness})，判定基本可信 | 规则引擎 |")
            elif comp_val >= 50:
                lines.append(f"| **证据状态** | 证据部分完整 ({completeness})，判定需谨慎 | 规则引擎 |")
            else:
                lines.append(f"| **证据状态** | 证据不足 ({completeness})，判定需补充证据 | 规则引擎 |")
        lines.append("")

        # ============================================================
        # 3. 证据详情（Evidence Details）
        # ============================================================
        lines.append("### 🔍 证据详情")
        lines.append("")
        lines.append(f"已采集 **{len(d.collected_evidence)}/{len(d.collected_evidence) + len(d.missing_evidence)}** 项证据")
        lines.append("")

        # 证据详情表格 - 增强版
        lines.append("| # | 证据项 | 级别 | 状态 | 采集值 | 来源片段 | 来源工具 |")
        lines.append("|---|--------|------|------|--------|----------|----------|")

        seq = 1
        # 已采集证据
        for evidence in d.evidence_details:
            if evidence.get("collected"):
                level_icon = "🔴" if evidence["level"] == "critical" else ("🟠" if evidence["level"] == "important" else "⚪")
                value = f"`{evidence['value']}`" if evidence.get("value") else "-"
                snippet = evidence.get("raw_snippet", "")
                if snippet and len(snippet) > 60:
                    snippet = snippet[:60] + "..."
                # 推断来源工具
                source_tool = DecisionFormatter._infer_source_tool(evidence)
                lines.append(f"| {seq} | {evidence['description']} | {level_icon} {evidence['level']} | ✅ 已采集 | {value} | {snippet} | {source_tool} |")
                seq += 1

        # 缺失证据
        for evidence in d.evidence_details:
            if not evidence.get("collected"):
                level_icon = "🔴" if evidence["level"] == "critical" else ("🟠" if evidence["level"] == "important" else "⚪")
                critical_flag = " 🚨" if evidence["level"] == "critical" else ""
                lines.append(f"| {seq} | {evidence['description']} | {level_icon} {evidence['level']}{critical_flag} | ❌ 未采集 | - | - | - |")
                seq += 1

        lines.append("")

        # ============================================================
        # 4. 因果链分析（Causal Chain Analysis）- 增强版
        # ============================================================
        if d.causal_chain:
            lines.append("### ⛓️ 因果链分析")
            lines.append("")
            lines.append("基于收集的证据，构建问题的完整因果链：")
            lines.append("")

            # 可视化因果链
            root_cause = d.causal_chain.get("root_cause", "")
            trigger = d.causal_chain.get("trigger", "")
            mechanism = d.causal_chain.get("mechanism", "")
            manifestation = d.causal_chain.get("manifestation", "")

            lines.append("```")
            lines.append("┌─────────────────────────────────────────────────────────┐")
            lines.append("│                    根因分析 (RCA)                     │")
            lines.append("├─────────────────────────────────────────────────────────┤")
            lines.append("│                                                         │")
            lines.append(f"│  🌱 根本原因 (Root Cause)                                 │")
            lines.append(f"│     └──→ {root_cause}                                    │")
            lines.append("│                                                         │")
            lines.append(f"│  🔥 触发条件 (Trigger)                                   │")
            lines.append(f"│     └──→ {trigger}                                          │")
            lines.append("│                                                         │")
            lines.append(f"│  ⚙️  作用机制 (Mechanism)                                  │")
            lines.append(f"│     └──→ {mechanism}                                        │")
            lines.append("│                                                         │")
            lines.append(f"│  💥 表现形式 (Manifestation)                               │")
            lines.append(f"│     └──→ {manifestation}                                     │")
            lines.append("│                                                         │")
            lines.append("└─────────────────────────────────────────────────────────┘")
            lines.append("```")
            lines.append("")

            # 添加因果链解释
            lines.append("**因果链说明**:")
            lines.append("")
            lines.append("1. **根本原因** - 问题的核心起因，这是需要解决的核心")
            lines.append("2. **触发条件** - 导致问题发生的前置条件或事件")
            lines.append("3. **作用机制** - 问题如何从触发条件发展到表现形式")
            lines.append("4. **表现形式** - 最终呈现给用户的可观测症状")
            lines.append("")

        # ============================================================
        # 5. 时序分析（Timeline Analysis）- 业界特色
        # ============================================================
        if d.evidence_refs:
            lines.append("### ⏱️ 时序分析")
            lines.append("")
            lines.append("**证据采集时序** (证据按工具调用顺序排列):")
            lines.append("")

            for i, ref in enumerate(d.evidence_refs[:10], 1):
                lines.append(f"{i}. {ref}")
            lines.append("")

        # ============================================================
        # 6. 命中的判定规则
        # ============================================================
        if d.matched_rules:
            lines.append("### 📋 命中规则")
            lines.append("")
            lines.append("以下规则被成功匹配并触发判定：")
            lines.append("")
            for r in d.matched_rules[:5]:
                lines.append(f"- `{r}`")
            lines.append("")

        # ============================================================
        # 7. 修复方案（Remediation Plan）
        # ============================================================
        if d.remediation_steps or d.verification_steps:
            lines.append("### 🛠️ 修复方案")
            lines.append("")

            # 紧急修复措施
            if d.remediation_steps:
                lines.append("**紧急修复措施**:")
                lines.append("")
                for step in d.remediation_steps[:5]:
                    # 将代码块格式化
                    if step.strip().startswith("kubectl") or step.strip().startswith("df") or step.strip().startswith("du") or step.strip().startswith("openssl") or step.strip().startswith("tc"):
                        lines.append(f"```bash")
                        lines.append(f"{step}")
                        lines.append(f"```")
                    else:
                        lines.append(f"- {step}")
                lines.append("")

            # 验证步骤
            if d.verification_steps:
                lines.append("**验证步骤** (修复后执行):")
                lines.append("")
                for step in d.verification_steps[:5]:
                    lines.append(f"- [ ] {step}")
                lines.append("")

        # ============================================================
        # 8. 下一步建议（Next Steps）
        # ============================================================
        if d.next_steps:
            lines.append("### 📌 下一步建议")
            lines.append("")
            for step in d.next_steps[:8]:
                lines.append(f"{step}")
            lines.append("")

        # ============================================================
        # 9. 数据来源（Data Sources）- 增强版
        # ============================================================
        if d.evidence_refs:
            lines.append("### 🔗 数据来源")
            lines.append("")
            lines.append("本分析基于以下工具调用的原始输出:")
            lines.append("")

            # 按工具类型分组展示
            sources = DecisionFormatter._group_evidence_sources(d.evidence_refs)
            for tool, refs in sources.items():
                lines.append(f"**{tool}**:")
                for ref in refs:
                    lines.append(f"  - {ref}")
                lines.append("")
            lines.append("")

        # ============================================================
        # 10. 相关事实（Facts）- 业界特色
        # ============================================================
        if d.facts:
            lines.append("### 📊 提取的事实")
            lines.append("")
            lines.append("| 事实键 | 事实值 | 来源 |")
            lines.append("|--------|--------|------|")
            for fact in d.facts[:8]:
                key = fact.get("key", "")
                value = fact.get("value", "")
                source = fact.get("source", "")
                lines.append(f"| `{key}` | `{value}` | {source} |")
            lines.append("")

        # ============================================================
        # 11. 影响评估（Impact Assessment）- 业界特色
        # ============================================================
        lines.append("### 📈 影响评估")
        lines.append("")
        lines.append("| 评估维度 | 影响程度 | 说明 |")
        lines.append("|----------|----------|------|")

        # 基于层级评估影响
        layer_impact_map = {
            "L0": "高 - 基础设施问题可能影响整个集群",
            "L1": "高 - 节点问题影响该节点上的所有 Pod",
            "L2": "中 - 工作负载问题影响特定应用",
            "L3": "中 - 网络问题影响服务间通信",
            "L4": "低 - 应用层问题通常影响范围有限",
        }

        impact_desc = layer_impact_map.get(layer_val, "待评估")
        lines.append(f"| **影响范围** | {impact_desc.split(' - ')[0]} | {impact_desc.split(' - ')[1] if ' - ' in impact_desc else impact_desc} |")

        # 基于置信度评估可靠性
        if d.confidence == Confidence.HIGH:
            lines.append(f"| **诊断可靠性** | 高 | 证据完整，判定可信 |")
        elif d.confidence == Confidence.MEDIUM:
            lines.append(f"| **诊断可靠性** | 中 | 证据较为完整，判定基本可信 |")
        else:
            lines.append(f"| **诊断可靠性** | 低 | 证据不足，需谨慎对待 |")
        lines.append("")

        # ============================================================
        # 12. 置信度说明（Confidence Note）
        # ============================================================
        if d.confidence == Confidence.LOW or d.has_critical_missing:
            lines.append("---")
            lines.append("")
            lines.append("> ⚠️ **置信度较低说明**：")
            lines.append(">")
            if d.has_critical_missing:
                lines.append(f"> - 缺失关键证据 ({len(d.critical_missing)} 项 Critical)，无法做出高置信度判定")
            if d.confidence_score < 0.5:
                lines.append(f"> - 证据完整度低于 50%，建议补充证据后重新分析")
            lines.append(">")
            lines.append(f"> - 当前置信度: {d.confidence_score:.1%}")
            lines.append("")

        # ============================================================
        # 13. 报告元数据（Report Metadata）
        # ============================================================
        lines.append("---")
        lines.append("")
        lines.append("*报告生成: K8s-SRE Agent Deterministic Engine*")
        lines.append(f"*证据完整度: {d._calculate_evidence_completeness()}*")
        lines.append(f"*置信度评分: {d.confidence_score:.3f}*")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _infer_source_tool(evidence: dict) -> str:
        """
        根据证据描述推断来源工具
        """
        desc = evidence.get("description", "").lower()
        if "exit code" in desc or "terminated" in desc or "pod" in desc:
            return "kubectl"
        elif "memory" in desc or "resource" in desc:
            return "kubectl"
        elif "log" in desc:
            return "kubectl logs"
        elif "disk" in desc or "usage" in desc:
            return "df/du"
        elif "dns" in desc or "lookup" in desc:
            return "Prometheus"
        elif "503" in desc or "5xx" in desc or "upstream" in desc:
            return "Application Logs"
        elif "node" in desc:
            return "kubectl get nodes"
        elif "certificate" in desc or "cert" in desc or "x509" in desc:
            return "Journalctl"
        else:
            return "System"

    @staticmethod
    def _group_evidence_sources(refs: list) -> dict:
        """
        按工具类型分组证据来源
        """
        groups = {}
        for ref in refs:
            if "kubectl" in ref.lower():
                tool = "kubectl"
            elif "prometheus" in ref.lower():
                tool = "Prometheus"
            elif "bash" in ref.lower():
                tool = "Bash"
            elif "promql" in ref.lower():
                tool = "Prometheus Query"
            else:
                tool = "其他工具"

            if tool not in groups:
                groups[tool] = []
            groups[tool].append(ref)

        return groups

    @staticmethod
    def to_brief(decision: DeterministicDecision) -> str:
        """
        格式化为简短摘要（一行）
        用于日志、监控告警等场景
        """
        d = decision
        layer_val = d.layer.value if hasattr(d.layer, 'value') else str(d.layer)
        conf_val = d.confidence.value if hasattr(d.confidence, 'value') else str(d.confidence)
        conf_icon = "🟢" if d.confidence == Confidence.HIGH else ("🟡" if d.confidence == Confidence.MEDIUM else "🔴")

        missing_count = len(d.missing_evidence)
        critical_count = len(d.critical_missing)

        parts = [
            f"[{layer_val}]",
            f"{d.category}",
            f"{conf_icon} {conf_val}({d.confidence_score:.0%})"
        ]

        if missing_count > 0:
            parts.append(f"缺{missing_count}证")
        if critical_count > 0:
            parts.append(f"🚨{critical_count}关键")

        return " | ".join(parts)

    @staticmethod
    def to_json_summary(decision: DeterministicDecision) -> dict:
        """
        格式化为 JSON 摘要（用于 SSE 事件、API 响应等）
        """
        d = decision
        return {
            "issue_found": d.issue_found,
            "issue_summary": d.issue_summary,
            "layer": d.layer.value if hasattr(d.layer, 'value') else str(d.layer),
            "scenario": d.scenario,
            "category": d.category,
            "confidence": d.confidence.value if hasattr(d.confidence, 'value') else str(d.confidence),
            "confidence_score": d.confidence_score,
            "evidence_completeness": d._calculate_evidence_completeness(),
            "evidence_collected": len(d.collected_evidence),
            "evidence_missing": len(d.missing_evidence),
            "has_critical_missing": d.has_critical_missing,
            "causal_chain": d.causal_chain,
            "evidence_count": len(d.collected_evidence),
            "evidence_refs_count": len(d.evidence_refs),
        }

    @staticmethod
    def to_slack_alert(decision: DeterministicDecision) -> str:
        """
        格式化为 Slack 告警消息
        """
        d = decision
        layer_val = d.layer.value if hasattr(d.layer, 'value') else str(d.layer)
        conf_emoji = "white_check_mark" if d.confidence == Confidence.HIGH else ("warning" if d.confidence == Confidence.MEDIUM else "x")

        lines = [
            f":rotating_light: *K8s-SRE Agent 确定性分析*",
            f"",
            f"*问题*: {d.issue_summary or f'{layer_val} - {d.category}'}",
            f"",
            f"| 属性 | 值 |",
            f"|------|-----|",
            f"| 层级 | {layer_val} |",
            f"| 置信度 | :{conf_emoji}: {d.confidence.value} ({d.confidence_score:.1%}) |",
            f"| 证据完整度 | {d._calculate_evidence_completeness()} |",
            f"",
            f"*修复建议*:",
        ]

        for step in d.remediation_steps[:3]:
            lines.append(f"• {step}")

        if d.has_critical_missing:
            lines.append("")
            lines.append(f":warning: *注意*: 缺失 {len(d.critical_missing)} 项关键证据")

        return "\n".join(lines)


def format_decision_markdown(decision: DeterministicDecision) -> str:
    """便捷函数：格式化为 Markdown"""
    return DecisionFormatter.to_markdown(decision)


def format_decision_brief(decision: DeterministicDecision) -> str:
    """便捷函数：格式化为简短摘要"""
    return DecisionFormatter.to_brief(decision)


class MultiScenarioFormatter:
    """多场景格式化器"""

    @staticmethod
    def to_markdown(
        summaries: List["ScenarioSummary"],
        correlations: List["CorrelatedScenarios"],
        priority_summary: dict
    ) -> str:
        """
        格式化多场景诊断报告为 Markdown

        输出结构：
        1. 问题汇总表格（按优先级排序）
        2. 优先级统计
        3. 相关性分析
        4. 每个场景的详细信息（复用 DecisionFormatter.to_markdown）
        """
        lines = []

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🎯 多场景诊断汇总（Multi-Scenario Analysis）")
        lines.append("")

        # ============================================================
        # 1. 优先级统计
        # ============================================================
        lines.append("### 📊 优先级统计")
        lines.append("")
        lines.append("| 严重程度 | 数量 | 说明 |")
        lines.append("|----------|------|------|")
        lines.append(f"| 🔴 **Critical** | {priority_summary.get('critical', 0)} | 需要立即处理，影响整个集群 |")
        lines.append(f"| 🟠 **High** | {priority_summary.get('high', 0)} | 影响节点级，需要优先处理 |")
        lines.append(f"| 🟡 **Medium** | {priority_summary.get('medium', 0)} | 影响工作负载，建议尽快处理 |")
        lines.append(f"| ⚪ **Low** | {priority_summary.get('low', 0)} | 应用层问题，影响范围有限 |")
        lines.append("")

        # ============================================================
        # 2. 问题汇总表格
        # ============================================================
        lines.append("### 📋 问题汇总")
        lines.append("")
        lines.append("| # | 层级 | 问题分类 | 置信度 | 证据完整度 | 严重程度 | 状态 |")
        lines.append("|---|------|----------|--------|------------|----------|------|")

        for i, summary in enumerate(summaries, 1):
            conf_val = summary.confidence.value if hasattr(summary.confidence, 'value') else str(summary.confidence)
            conf_icon = "🟢" if summary.confidence == Confidence.HIGH else ("🟡" if summary.confidence == Confidence.MEDIUM else "🔴")

            severity_map = {
                "critical": "🔴 Critical",
                "high": "🟠 High",
                "medium": "🟡 Medium",
                "low": "⚪ Low"
            }
            severity = severity_map.get(summary.impact_severity, "⚪ Low")

            status = "⚠️ 缺关键证" if summary.has_critical_missing else "✅ 正常"

            lines.append(
                f"| {i} | {summary.layer} | {summary.category} | "
                f"{conf_icon} {conf_val}({summary.confidence_score:.0%}) | "
                f"{summary.evidence_completeness} | {severity} | {status} |"
            )
        lines.append("")

        # ============================================================
        # 3. 相关性分析
        # ============================================================
        if correlations:
            lines.append("### 🔗 相关性分析")
            lines.append("")

            correlation_type_map = {
                "shared_cause": "🔄 共享根本原因",
                "cascading": "🔀 级联故障",
                "independent": "✅ 独立问题"
            }

            for corr in correlations:
                corr_type = correlation_type_map.get(corr.correlation_type, corr.correlation_type)
                scenarios_str = ", ".join([f"**{s}**" for s in corr.scenarios])

                lines.append(f"**{corr_type}**")
                lines.append(f"- **涉及场景**: {scenarios_str}")
                lines.append(f"- **根本原因**: {corr.root_cause}")
                lines.append(f"- **共享证据数**: {corr.shared_evidence_count}")
                lines.append("")

        # ============================================================
        # 4. 每个场景的详细信息
        # ============================================================
        if summaries:
            lines.append("---")
            lines.append("")
            lines.append("## 📌 各场景详细分析")
            lines.append("")

            for i, summary in enumerate(summaries, 1):
                if summary.decision:
                    lines.append(f"### 场景 {i}: {summary.layer} - {summary.category}")
                    lines.append("")

                    # 调用单场景格式化器
                    single_report = DecisionFormatter.to_markdown(summary.decision)
                    lines.append(single_report)

                    # 添加场景分隔线
                    if i < len(summaries):
                        lines.append("")
                        lines.append("---")
                        lines.append("")

        # ============================================================
        # 5. 修复建议汇总
        # ============================================================
        lines.append("---")
        lines.append("")
        lines.append("### 🛠️ 综合修复建议")
        lines.append("")
        lines.append("**优先处理顺序**:")
        lines.append("")

        # 按严重程度排序所有修复步骤
        all_steps = []
        for summary in summaries:
            if summary.decision and summary.decision.remediation_steps:
                for step in summary.decision.remediation_steps:
                    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                    severity_num = severity_order.get(summary.impact_severity, 3)
                    all_steps.append({
                        "severity": summary.impact_severity,
                        "severity_num": severity_num,
                        "scenario": f"{summary.layer}-{summary.category}",
                        "step": step
                    })

        # 排序并输出
        all_steps.sort(key=lambda x: (x["severity_num"], x["scenario"]))
        for item in all_steps[:10]:
            severity_icon = "🔴" if item["severity"] == "critical" else ("🟠" if item["severity"] == "high" else "🟡")
            lines.append(f"{severity_icon} **[{item['scenario']}]** {item['step']}")

        lines.append("")

        # ============================================================
        # 6. 报告元数据
        # ============================================================
        lines.append("---")
        lines.append("")
        lines.append("*报告生成: K8s-SRE Agent Multi-Scenario Engine*")
        lines.append(f"*检测到场景数: {len(summaries)}*")
        lines.append(f"*相关性分析: {len(correlations)} 组*")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_json_summary(
        summaries: List["ScenarioSummary"],
        correlations: List["CorrelatedScenarios"],
        priority_summary: dict
    ) -> dict:
        """
        格式化为 JSON 摘要（用于 SSE 事件、API 响应等）
        """
        return {
            "total_scenarios": len(summaries),
            "priority_summary": priority_summary,
            "scenarios": [
                {
                    "id": s.scenario_id,
                    "layer": s.layer,
                    "category": s.category,
                    "confidence": s.confidence.value if hasattr(s.confidence, 'value') else str(s.confidence),
                    "confidence_score": s.confidence_score,
                    "evidence_completeness": s.evidence_completeness,
                    "impact_severity": s.impact_severity,
                    "has_critical_missing": s.has_critical_missing,
                }
                for s in summaries
            ],
            "correlations": [
                {
                    "root_cause": c.root_cause,
                    "scenarios": c.scenarios,
                    "correlation_type": c.correlation_type,
                    "shared_evidence_count": len(c.shared_evidence)
                }
                for c in correlations
            ]
        }
