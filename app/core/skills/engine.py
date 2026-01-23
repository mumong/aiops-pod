"""
规则引擎 - 核心评估逻辑

设计原则：
- 单一职责：只负责规则匹配和置信度计算
- 无副作用：纯函数，输入确定则输出确定
- 可测试：所有方法可独立单元测试
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .models import (
    Confidence,
    DeterministicDecision,
    EvidenceItem,
    EvidenceLevel,
    Fact,
    Layer,
    RuleMatch,
)
from .rules import ConditionOp, Rule, RULES
from .evidence import EvidenceExtractor, EVIDENCE_SPECS


class RulesEngine:
    """
    规则引擎
    
    职责：
    1. 从原始文本中检测场景
    2. 匹配规则条件
    3. 计算置信度
    4. 生成 DeterministicDecision
    """
    
    def __init__(self):
        self._rules = RULES
    
    def detect_scenario(self, question: str, tool_text: str) -> Optional[str]:
        """
        根据问题和工具输出检测最可能的场景
        
        Returns:
            场景 ID (如 "L2-OOMKilled") 或 None
        """
        q_lower = question.lower()
        text_lower = tool_text.lower()
        combined = f"{q_lower} {text_lower}"
        
        # 场景检测优先级（从高到低）
        scenarios = [
            ("L2-OOMKilled", ["oom", "oomkilled", "137", "内存", "out of memory"]),
            ("L0-DiskFull", ["磁盘", "disk", "enospc", "no space", "磁盘满"]),
            ("L1-KubeletCert", ["notready", "node", "kubelet", "证书", "x509", "certificate"]),
            ("L3-DNSLatency", ["dns", "coredns", "解析", "延迟", "dns_lookup"]),
            ("L4-Dependency503", ["503", "5xx", "依赖", "upstream", "service unavailable"]),
        ]
        
        for scenario_id, keywords in scenarios:
            if any(kw in combined for kw in keywords):
                return scenario_id
        
        return None
    
    def evaluate_evidence(
        self,
        scenario: str,
        tool_text: str
    ) -> Tuple[List[EvidenceItem], List[Fact]]:
        """
        评估指定场景的证据收集情况
        
        Returns:
            (证据项列表, 事实列表)
        """
        return EvidenceExtractor.extract_all(tool_text, scenario)
    
    def evaluate_condition(
        self,
        condition: "Condition",  # 避免循环导入
        evidence_items: List[EvidenceItem],
        facts: List[Fact]
    ) -> bool:
        """评估单个条件是否满足"""
        from .rules import Condition, ConditionOp
        
        # 找到对应的证据项
        item = next((e for e in evidence_items if e.id == condition.evidence_id), None)
        
        if condition.op == ConditionOp.EXISTS:
            return item is not None and item.collected
        
        if item is None or not item.collected:
            return False
        
        value = item.value
        if value is None:
            # 尝试从 facts 获取
            fact = next((f for f in facts if f.key == condition.evidence_id), None)
            if fact:
                value = fact.value
        
        if value is None:
            return False
        
        # 执行比较
        if condition.op == ConditionOp.EQUALS:
            return value == condition.value
        elif condition.op == ConditionOp.NOT_EQUALS:
            return value != condition.value
        elif condition.op == ConditionOp.GREATER_THAN:
            return value > condition.value
        elif condition.op == ConditionOp.LESS_THAN:
            return value < condition.value
        elif condition.op == ConditionOp.GREATER_EQ:
            return value >= condition.value
        elif condition.op == ConditionOp.LESS_EQ:
            return value <= condition.value
        elif condition.op == ConditionOp.CONTAINS:
            return str(condition.value).lower() in str(value).lower()
        elif condition.op == ConditionOp.REGEX:
            return bool(re.search(str(condition.value), str(value), re.IGNORECASE))
        
        return False
    
    def match_rule(
        self,
        rule: Rule,
        evidence_items: List[EvidenceItem],
        facts: List[Fact]
    ) -> RuleMatch:
        """
        匹配规则
        
        Returns:
            RuleMatch 对象，包含匹配结果和详情
        """
        conditions_met = []
        conditions_failed = []
        
        for cond in rule.conditions:
            if self.evaluate_condition(cond, evidence_items, facts):
                conditions_met.append(cond.description)
            else:
                conditions_failed.append(cond.description)
        
        # 根据逻辑判断是否匹配
        if rule.condition_logic == "AND":
            matched = len(conditions_failed) == 0
        else:  # OR
            matched = len(conditions_met) > 0
        
        return RuleMatch(
            rule_id=rule.id,
            rule_name=rule.name,
            matched=matched,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed
        )
    
    def calculate_confidence(
        self,
        rule: Rule,
        evidence_items: List[EvidenceItem]
    ) -> Tuple[Confidence, float]:
        """
        计算置信度
        
        算法：
        1. 从规则的基础置信度开始
        2. 对于每个缺失的证据，扣除其权重
        3. Critical 证据缺失会额外惩罚
        
        Returns:
            (置信度等级, 量化分数)
        """
        score = rule.base_confidence
        
        for item in evidence_items:
            if not item.collected:
                # 扣除权重
                score -= item.weight
                
                # Critical 证据缺失额外惩罚
                if item.level == EvidenceLevel.CRITICAL:
                    score -= 0.1
        
        # 确保分数在 [0, 1] 范围内
        score = max(0.0, min(1.0, score))
        
        return Confidence.from_score(score), score
    
    def evaluate(
        self,
        question: str,
        tool_text: str
    ) -> Optional[DeterministicDecision]:
        """
        主评估入口
        
        Args:
            question: 用户问题
            tool_text: 所有工具输出的合并文本
        
        Returns:
            DeterministicDecision 或 None（无法判定时）
        """
        # 1. 检测场景
        scenario = self.detect_scenario(question, tool_text)
        if not scenario:
            return None
        
        # 2. 评估证据
        evidence_items, facts = self.evaluate_evidence(scenario, tool_text)
        
        # 3. 找到对应的规则
        rule = self._find_rule_for_scenario(scenario)
        if not rule:
            return None
        
        # 4. 匹配规则
        match_result = self.match_rule(rule, evidence_items, facts)
        if not match_result.matched:
            return None
        
        # 5. 计算置信度
        confidence, score = self.calculate_confidence(rule, evidence_items)
        
        # 6. 构建决策对象
        collected = [e.id for e in evidence_items if e.collected]
        missing = [e.description for e in evidence_items if not e.collected]
        critical_missing = [
            e.description for e in evidence_items 
            if not e.collected and e.level == EvidenceLevel.CRITICAL
        ]
        
        # 生成建议
        next_steps = self._generate_next_steps(rule, evidence_items, missing)
        
        return DeterministicDecision(
            layer=rule.layer,
            scenario=rule.scenario,
            category=rule.category,
            confidence=confidence,
            confidence_score=round(score, 3),
            matched_rules=[f"{rule.id}: {match_result.conditions_met}"],
            collected_evidence=collected,
            missing_evidence=missing,
            critical_missing=critical_missing,
            next_steps=next_steps,
            facts=[f.to_dict() for f in facts]
        )
    
    def _find_rule_for_scenario(self, scenario: str) -> Optional[Rule]:
        """根据场景 ID 找到对应的规则"""
        scenario_to_rule = {
            "L0-DiskFull": "R-L0-DISK-1",
            "L1-KubeletCert": "R-L1-CERT-1",
            "L2-OOMKilled": "R-L2-OOM-1",
            "L3-DNSLatency": "R-L3-DNS-1",
            "L4-Dependency503": "R-L4-DEP-1",
        }
        rule_id = scenario_to_rule.get(scenario)
        return self._rules.get(rule_id) if rule_id else None
    
    def _generate_next_steps(
        self,
        rule: Rule,
        evidence_items: List[EvidenceItem],
        missing: List[str]
    ) -> List[str]:
        """生成下一步建议"""
        steps = []
        
        if missing:
            steps.append("⚠️ 建议先补充以下证据以提高置信度：")
            for m in missing[:3]:  # 最多显示 3 条
                steps.append(f"  - {m}")
        
        # 添加规则定义的修复建议
        if rule.remediation_steps:
            if not missing:
                steps.append("📋 修复建议：")
            else:
                steps.append("📋 若确认诊断正确，修复建议：")
            for step in rule.remediation_steps[:4]:  # 最多显示 4 条
                steps.append(f"  - {step}")
        
        return steps


# 全局引擎实例
_engine: Optional[RulesEngine] = None


def get_engine() -> RulesEngine:
    """获取全局引擎实例（单例）"""
    global _engine
    if _engine is None:
        _engine = RulesEngine()
    return _engine
