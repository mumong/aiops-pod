"""
多场景输出管理

职责：
- 管理多个场景检测的结果
- 提供统一的输出格式
- 支持优先级排序和去重

设计原则：
- 高内聚：每个功能模块职责单一
- 低耦合：通过数据模型交互
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum

from app.core.skills.models import Layer, Confidence


class ScenarioSeverity(str, Enum):
    """场景严重程度"""
    CRITICAL = "critical"   # 立即处理，影响整个集群
    HIGH = "high"          # 影响节点级，需要优先处理
    MEDIUM = "medium"        # 影响工作负载，建议尽快处理
    LOW = "low"            # 应用层问题，影响范围有限


@dataclass
class ScenarioDecision:
    """
    场景判定结果

    每个场景包含完整的分析结果
    """
    scenario_id: str                    # 场景ID，如 "L0-DiskFull"
    scenario_name: str                  # 场景名称
    layer: Layer                        # 所属层级
    severity: ScenarioSeverity            # 严重程度
    confidence: Confidence              # 置信度
    confidence_score: float            # 量化分数 [0, 1]

    # 证据信息
    evidence_count: int = 0           # 已采集证据数
    evidence_total: int = 0           # 总证据数
    collected_evidence: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)

    # 问题描述
    issue_summary: str = ""
    detailed_description: str = ""

    # 因果链
    root_cause: str = ""
    causal_chain: Dict[str, str] = field(default_factory=dict)

    # 修复建议
    remediation_steps: List[str] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)

    # 数据来源
    source_tools: List[str] = field(default_factory=list)  # 使用的工具
    referenced_evidence: List[str] = field(default_factory=list)  # 引用的证据

    # 相关信息
    affected_entities: Dict[str, Any] = field(default_factory=dict)  # 受影响的实体 (Pod, Node等)
    related_scenarios: List[str] = field(default_factory=list)  # 相关的其他场景

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "layer": self.layer.value if isinstance(self.layer, Layer) else str(self.layer),
            "severity": self.severity.value,
            "confidence": self.confidence.value if isinstance(self.confidence, Confidence) else str(self.confidence),
            "confidence_score": self.confidence_score,
            "evidence_count": self.evidence_count,
            "evidence_total": self.evidence_total,
            "collected_evidence": self.collected_evidence,
            "missing_evidence": self.missing_evidence,
            "issue_summary": self.issue_summary,
            "detailed_description": self.detailed_description,
            "root_cause": self.root_cause,
            "causal_chain": self.causal_chain,
            "remediation_steps": self.remediation_steps,
            "verification_steps": self.verification_steps,
            "source_tools": self.source_tools,
            "affected_entities": self.affected_entities,
            "related_scenarios": self.related_scenarios,
        }


class MultiScenarioOutput:
    """
    多场景输出管理器

    负责管理多个场景的检测结果和最终输出
    """

    def __init__(self):
        self.scenarios: List[ScenarioDecision] = []
        self.processed_scenarios: Set[str] = set()  # 避免重复

    def add_scenario(self, decision: ScenarioDecision):
        """添加场景判定结果"""
        # 避免重复
        if decision.scenario_id not in self.processed_scenarios:
            self.scenarios.append(decision)
            self.processed_scenarios.add(decision.scenario_id)

    def sort_by_priority(self) -> List[ScenarioDecision]:
        """
        按优先级排序场景

        排序规则：
        1. 严重程度：Critical > High > Medium > Low
        2. 层级：L0 > L1 > L2 > L3 > L4 (低层问题优先)
        3. 置信度：高 > 中 > 低
        """
        # 严重程度权重
        severity_order = {
            ScenarioSeverity.CRITICAL: 0,
            ScenarioSeverity.HIGH: 1,
            ScenarioSeverity.MEDIUM: 2,
            ScenarioSeverity.LOW: 3,
        }

        # 层级权重
        layer_order = {
            Layer.L0: 0,
            Layer.L1: 1,
            Layer.L2: 2,
            Layer.L3: 3,
            Layer.L4: 4,
        }

        def get_sort_key(decision: ScenarioDecision):
            severity_score = severity_order.get(decision.severity, 99)
            layer_score = layer_order.get(decision.layer, 99)
            confidence_score = {
                Confidence.HIGH: 0,
                Confidence.MEDIUM: 1,
                Confidence.LOW: 2,
            }.get(decision.confidence, 99)

            return (
                severity_score,
                layer_score,
                confidence_score,
                -decision.confidence_score,  # 置信度分数越高越优先
            )

        return sorted(self.scenarios, key=get_sort_key)

    def group_by_severity(self) -> Dict[str, List[ScenarioDecision]]:
        """按严重程度分组"""
        groups = {
            ScenarioSeverity.CRITICAL: [],
            ScenarioSeverity.HIGH: [],
            ScenarioSeverity.MEDIUM: [],
            ScenarioSeverity.LOW: [],
        }

        for scenario in self.scenarios:
            groups[scenario.severity].append(scenario)

        return groups

    def group_by_layer(self) -> Dict[str, List[ScenarioDecision]]:
        """按层级分组"""
        groups = {
            Layer.L0: [],
            Layer.L1: [],
            Layer.L2: [],
            Layer.L3: [],
            Layer.L4: [],
        }

        for scenario in self.scenarios:
            if scenario.layer in groups:
                groups[scenario.layer].append(scenario)

        return groups

    def find_related_scenarios(self, decision: ScenarioDecision) -> List[str]:
        """查找相关的其他场景"""
        related = []

        # 基于层级查找相关场景
        for other in self.scenarios:
            if other.scenario_id == decision.scenario_id:
                continue

            # 同一层级的场景可能相关
            if other.layer == decision.layer and other.scenario_id not in related:
                related.append(other.scenario_id)

        # 基于影响实体查找相关场景
        if decision.affected_entities:
            for other in self.scenarios:
                if other.scenario_id == decision.scenario_id or other.scenario_id in related:
                    continue

                # 检查是否有共同的受影响实体
                for key, value in decision.affected_entities.items():
                    if key in other.affected_entities and other.affected_entities[key] == value:
                        if other.scenario_id not in related:
                            related.append(other.scenario_id)
                            break

        return related

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        sorted_scenarios = self.sort_by_priority()
        severity_groups = self.group_by_severity()

        return {
            "total_scenarios": len(self.scenarios),
            "scenarios_by_severity": {
                sev.value: len(scenarios)
                for sev, scenarios in severity_groups.items()
            },
            "critical_count": len(severity_groups[ScenarioSeverity.CRITICAL]),
            "high_count": len(severity_groups[ScenarioSeverity.HIGH]),
            "medium_count": len(severity_groups[ScenarioSeverity.MEDIUM]),
            "low_count": len(severity_groups[ScenarioSeverity.LOW]),
            "top_scenarios": sorted_scenarios[:5],  # 前5个最严重的问题
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为完整字典"""
        return {
            "scenarios": [s.to_dict() for s in self.scenarios],
            "sorted_scenarios": [s.to_dict() for s in self.sort_by_priority()],
            "groups_by_severity": {
                sev.value: [s.to_dict() for s in scenarios]
                for sev, scenarios in self.group_by_severity().items()
            },
            "groups_by_layer": {
                layer.value: [s.to_dict() for s in scenarios]
                for layer, scenarios in self.group_by_layer().items()
            },
            "summary": self.get_summary(),
        }
