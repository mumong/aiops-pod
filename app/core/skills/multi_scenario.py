"""
多场景并行评估器

设计原则：
- 并行评估：同时运行所有 L0-L4 场景规则，不按顺序扫描
- 证据聚合：将多个场景的证据统一管理，避免重复采集
- 优先级排序：基于置信度、影响范围、证据完整度排序
- 相关性分析：识别共享根本原因的多个场景
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dataclasses import dataclass

from .models import (
    DeterministicDecision,
    EvidenceItem,
    Confidence,
    EvidenceLevel,
    Fact,
)


@dataclass
class ScenarioSummary:
    """场景摘要"""
    scenario_id: str
    layer: str
    category: str
    confidence: Confidence
    confidence_score: float
    evidence_completeness: str
    impact_severity: str  # "critical", "high", "medium", "low"
    has_critical_missing: bool
    decision: Optional[DeterministicDecision]


@dataclass
class CorrelatedScenarios:
    """相关性分析结果"""
    root_cause: str
    scenarios: List[str]  # 场景ID列表
    shared_evidence: List[EvidenceItem]  # 共享的证据项
    correlation_type: str  # "shared_cause", "cascading", "independent"


class MultiScenarioEvaluator:
    """
    多场景并行评估器

    功能：
    1. 并行评估所有场景规则
    2. 聚合多个场景的诊断结果
    3. 按严重程度排序
    4. 识别共享根本原因的场景
    """

    def __init__(self, rules_engine):
        """
        初始化

        Args:
            rules_engine: RulesEngine 实例
        """
        self.rules_engine = rules_engine

    def evaluate_all_scenarios(
        self,
        evidence_items: List[EvidenceItem],
        facts: List[dict],
        tool_text: str,
        context: Optional[dict] = None
    ) -> List[DeterministicDecision]:
        """
        并行评估所有场景

        对每个场景 ID 都尝试评估，不按顺序扫描

        Args:
            evidence_items: 证据项列表
            facts: 事实列表
            tool_text: 工具输出文本
            context: 额外上下文

        Returns:
            所有匹配规则的 DeterministicDecision 列表
        """
        matched_decisions = []

        # 定义所有可能检测的场景 ID（L0-L4）
        scenario_ids = [
            "L0-DiskFull",
            "L1-KubeletCert",
            "L2-OOMKilled",
            "L2-VolumeLimitExceeded",
            "L3-DNSLatency",
            "L4-Dependency503",
        ]

        # 直接使用规则 ID 进行评估，不依赖 detect_scenario()
        # 这样可以避免场景检测的误匹配问题
        scenario_to_rule_id = {
            "L0-DiskFull": "R-L0-DISK-1",
            "L1-KubeletCert": "R-L1-CERT-1",
            "L2-OOMKilled": "R-L2-OOM-1",
            "L2-VolumeLimitExceeded": "R-L2-VOL-1",
            "L3-DNSLatency": "R-L3-DNS-1",
            "L4-Dependency503": "R-L4-DEP-1",
        }

        # 遍历所有场景（不是找到第一个就停止）
        for scenario_id in scenario_ids:
            rule_id = scenario_to_rule_id.get(scenario_id)
            if rule_id:
                rule = self.rules_engine._rules.get(rule_id)
                if rule:
                    # 直接调用规则匹配，不经过 detect_scenario
                    match_result = self.rules_engine.match_rule(rule, evidence_items, facts)
                    if match_result.matched:
                        # 计算置信度
                        confidence, score = self.rules_engine.calculate_confidence(rule, evidence_items)
                        # 构建决策对象（直接调用内部方法）
                        collected = [e.id for e in evidence_items if e.collected]
                        missing = [e.description for e in evidence_items if not e.collected]
                        critical_missing = [
                            e.description for e in evidence_items
                            if not e.collected and e.level == EvidenceLevel.CRITICAL
                        ]
                        evidence_details = self.rules_engine._build_evidence_details(evidence_items, facts, tool_text)
                        causal_chain = self.rules_engine._build_causal_chain(rule, evidence_items, facts)
                        ctx = self.rules_engine._build_context(evidence_items, facts)
                        remediation_steps = self.rules_engine._fill_remediation_steps(rule, ctx)
                        verification_steps = self.rules_engine._generate_verification_steps(rule, ctx)
                        next_steps = self.rules_engine._generate_next_steps(rule, evidence_items, missing)

                        decision = DeterministicDecision(
                            layer=rule.layer,
                            scenario=rule.scenario,
                            category=rule.category,
                            confidence=confidence,
                            confidence_score=round(score, 3),
                            issue_found=True,
                            issue_summary=self.rules_engine._build_issue_summary(rule, ctx, match_result),
                            context=context,
                            matched_rules=[f"{rule.id}: {match_result.conditions_met}"],
                            excluded_rules=[],
                            collected_evidence=collected,
                            missing_evidence=missing,
                            critical_missing=critical_missing,
                            evidence_details=evidence_details,
                            causal_chain=causal_chain,
                            remediation_steps=remediation_steps,
                            verification_steps=verification_steps,
                            next_steps=next_steps,
                            facts=[f.to_dict() for f in facts]
                        )
                        matched_decisions.append(decision)

        return matched_decisions

    def _get_question_for_scenario(self, scenario_id: str) -> str:
        """
        为每个场景 ID 生成对应的问题，用于触发规则检测

        Args:
            scenario_id: 场景 ID（如 "L2-OOMKilled"）

        Returns:
            用于触发该场景的问题字符串
        """
        questions = {
            "L0-DiskFull": "磁盘满排查",
            "L1-KubeletCert": "节点证书问题排查",
            "L2-OOMKilled": "Pod OOMKilled 排查",
            "L2-VolumeLimitExceeded": "Pod VolumeLimitExceeded 排查",
            "L3-DNSLatency": "DNS 延迟排查",
            "L4-Dependency503": "依赖 503 排查",
        }
        return questions.get(scenario_id, "")

    def aggregate_results(
        self,
        decisions: List[DeterministicDecision]
    ) -> List[ScenarioSummary]:
        """
        聚合结果并计算优先级

        Args:
            decisions: 多个 DeterministicDecision

        Returns:
            排序后的场景摘要列表
        """
        summaries = []

        for decision in decisions:
            # 计算影响严重程度
            impact = self._calculate_impact_severity(decision)

            summary = ScenarioSummary(
                scenario_id=f"{decision.layer.value}-{decision.category}",
                layer=decision.layer.value if hasattr(decision.layer, 'value') else str(decision.layer),
                category=decision.category,
                confidence=decision.confidence,
                confidence_score=decision.confidence_score,
                evidence_completeness=decision._calculate_evidence_completeness(),
                impact_severity=impact,
                has_critical_missing=decision.has_critical_missing,
                decision=decision
            )
            summaries.append(summary)

        # 按优先级排序
        sorted_summaries = self._prioritize_by_severity(summaries)
        return sorted_summaries

    def _calculate_impact_severity(
        self,
        decision: DeterministicDecision
    ) -> str:
        """
        计算影响严重程度

        排序规则：
        1. L0 层问题 = critical（影响整个集群）
        2. L1 层问题 = high（影响节点）
        3. 缺失关键证据 = critical
        4. 置信度低 = 降低优先级
        5. 证据完整度 < 50% = low

        Args:
            decision: DeterministicDecision

        Returns:
            "critical", "high", "medium", "low"
        """
        layer_val = decision.layer.value if hasattr(decision.layer, 'value') else str(decision.layer)

        # 检查缺失关键证据
        if decision.has_critical_missing:
            return "critical"

        # 层级判断
        if layer_val == "L0":
            return "critical"
        elif layer_val == "L1":
            return "high"
        elif layer_val in ["L2", "L3"]:
            return "medium"
        else:  # L4
            return "low"

    def _prioritize_by_severity(
        self,
        summaries: List[ScenarioSummary]
    ) -> List[ScenarioSummary]:
        """
        按严重程度排序

        排序优先级：
        1. impact_severity (critical > high > medium > low)
        2. confidence_score (高 > 低)
        3. evidence_completeness (完整 > 不完整)

        Args:
            summaries: 场景摘要列表

        Returns:
            排序后的摘要列表
        """
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        return sorted(
            summaries,
            key=lambda x: (
                severity_order[x.impact_severity],
                -x.confidence_score,
                -float(x.evidence_completeness.replace('%', ''))
            )
        )

    def find_correlations(
        self,
        decisions: List[DeterministicDecision]
    ) -> List[CorrelatedScenarios]:
        """
        识别共享根本原因的场景

        关联类型：
        1. shared_cause: 多个场景共享同一个根本原因（如：磁盘满导致多个 Pod 被驱逐）
        2. cascading: 级联故障（如：DNS 故障导致应用依赖 503）
        3. independent: 独立问题

        Args:
            decisions: 多个 DeterministicDecision

        Returns:
            相关性分析结果列表
        """
        correlations = []

        if len(decisions) < 2:
            return correlations

        # 检查共享证据（相同 source_tool 和 similar value）
        shared_groups = self._group_by_shared_evidence(decisions)

        for group in shared_groups:
            if len(group) > 1:
                # 检查是否有因果链
                causal_chain = group[0].causal_chain
                if causal_chain:
                    root_cause = causal_chain.get("root_cause", "未知")
                    correlation_type = self._determine_correlation_type(group)

                    correlation = CorrelatedScenarios(
                        root_cause=root_cause,
                        scenarios=[f"{d.layer.value}-{d.category}" for d in group],
                        shared_evidence=list(set(
                            [e for d in group for e in d.collected_evidence]
                        )),
                        correlation_type=correlation_type
                    )
                    correlations.append(correlation)

        return correlations

    def _group_by_shared_evidence(
        self,
        decisions: List[DeterministicDecision]
    ) -> List[List[DeterministicDecision]]:
        """
        按共享证据分组

        Args:
            decisions: 多个 DeterministicDecision

        Returns:
            分组后的决策列表
        """
        groups = []
        used = set()

        for i, d1 in enumerate(decisions):
            if i in used:
                continue

            group = [d1]
            used.add(i)

            for j, d2 in enumerate(decisions):
                if j <= i or j in used:
                    continue

                # 检查是否共享证据
                if self._has_shared_evidence(d1, d2):
                    group.append(d2)
                    used.add(j)

            if len(group) > 0:
                groups.append(group)

        return groups

    def _has_shared_evidence(
        self,
        d1: DeterministicDecision,
        d2: DeterministicDecision
    ) -> bool:
        """
        检查两个决策是否共享证据

        Args:
            d1: 决策 1
            d2: 决策 2

        Returns:
            True 如果共享证据
        """
        # 提取证据详情中的描述集合
        # evidence_details 是 List[EvidenceDetail]，包含 description, value 等字段
        evidences1 = {e.get("description", "") for e in d1.evidence_details}
        evidences2 = {e.get("description", "") for e in d2.evidence_details}

        # 计算交集
        intersection = evidences1 & evidences2

        # 如果有超过 30% 的证据重叠，认为相关
        if len(intersection) > 0:
            total = len(evidences1 | evidences2)
            if total > 0 and len(intersection) / total > 0.3:
                return True

        return False

    def _determine_correlation_type(
        self,
        group: List[DeterministicDecision]
    ) -> str:
        """
        确定关联类型

        Args:
            group: 共享证据的决策组

        Returns:
            "shared_cause", "cascading", "independent"
        """
        if len(group) == 1:
            return "independent"

        # 检查是否是级联故障（如 L3 DNS 导致 L4 依赖 503）
        layers = [d.layer.value if hasattr(d.layer, 'value') else str(d.layer) for d in group]

        # 如果层级是递增的（L3 -> L4），可能是级联
        if len(layers) == 2:
            layer_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
            if layer_order[layers[0]] < layer_order[layers[1]]:
                return "cascading"

        # 默认认为是共享根本原因
        return "shared_cause"

    def build_multi_scenario_report(
        self,
        summaries: List[ScenarioSummary],
        correlations: List[CorrelatedScenarios]
    ) -> dict:
        """
        构建多场景诊断报告

        Args:
            summaries: 排序后的场景摘要
            correlations: 相关性分析结果

        Returns:
            结构化报告字典
        """
        return {
            "total_scenarios": len(summaries),
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
            ],
            "priority_summary": {
                "critical": len([s for s in summaries if s.impact_severity == "critical"]),
                "high": len([s for s in summaries if s.impact_severity == "high"]),
                "medium": len([s for s in summaries if s.impact_severity == "medium"]),
                "low": len([s for s in summaries if s.impact_severity == "low"]),
            }
        }


def evaluate_all_scenarios(
    rules_engine,
    evidence_items: List[EvidenceItem],
    facts: List[dict],
    tool_text: str,
    context: Optional[dict] = None
) -> dict:
    """
    便捷函数：评估所有场景并生成报告

    Args:
        rules_engine: RulesEngine 实例
        evidence_items: 证据项列表
        facts: 事实列表
        tool_text: 工具输出文本
        context: 额外上下文

    Returns:
        多场景诊断报告字典
    """
    evaluator = MultiScenarioEvaluator(rules_engine)

    # 并行评估
    decisions = evaluator.evaluate_all_scenarios(
        evidence_items=evidence_items,
        facts=facts,
        tool_text=tool_text,
        context=context
    )

    # 聚合结果
    summaries = evaluator.aggregate_results(decisions)

    # 识别相关性
    correlations = evaluator.find_correlations(decisions)

    # 构建报告
    report = evaluator.build_multi_scenario_report(summaries, correlations)

    return report
