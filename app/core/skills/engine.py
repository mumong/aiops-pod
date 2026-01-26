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
        # 注意：更具体的关键词应该放在前面，避免误匹配
        scenarios = [
            ("L2-VolumeLimitExceeded", ["evicted", "volumelimit", "emptydir", "sizelimit", "exceeds limit"]),
            ("L2-OOMKilled", ["oomkilled", "out of memory"]),  # 去掉单独的 "oom" 和 "137" 避免误匹配
            ("L0-DiskFull", ["enospc", "no space left on device", "磁盘满"]),  # 去掉 "磁盘"、"disk" 避免与 VolumeLimit 混淆
            ("L1-KubeletCert", ["x509", "certificate", "tls", "notready"]),
            ("L3-DNSLatency", ["dns_lookup_seconds", "dns latency"]),
            ("L4-Dependency503", ["upstream 503", "service unavailable", "5xx"]),
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
            # 规则未匹配，返回 None（不输出机器判定）
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

        # 构建证据详情（包含具体值和原始片段）
        evidence_details = self._build_evidence_details(evidence_items, facts, tool_text)

        # 构建因果链
        causal_chain = self._build_causal_chain(rule, evidence_items, facts)

        # 构建上下文（用于模板填充）
        context = self._build_context(evidence_items, facts)

        # 生成修复建议和验证步骤
        remediation_steps = self._fill_remediation_steps(rule, context)
        verification_steps = self._generate_verification_steps(rule, context)

        # 生成下一步建议
        next_steps = self._generate_next_steps(rule, evidence_items, missing)

        return DeterministicDecision(
            layer=rule.layer,
            scenario=rule.scenario,
            category=rule.category,
            confidence=confidence,
            confidence_score=round(score, 3),
            issue_found=True,
            issue_summary=self._build_issue_summary(rule, context, match_result),
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
    
    def _build_evidence_details(
        self,
        evidence_items: List[EvidenceItem],
        facts: List[Fact],
        tool_text: str
    ) -> List[Dict]:
        """
        构建详细的证据记录，包含具体值和原始文本片段
        """
        details = []
        for item in evidence_items:
            # 优先使用 item.value（已提取的值），其次从 facts 获取
            value = item.value

            # 如果 item 没有值，从 facts 查找
            if value is None:
                fact = next((f for f in facts if f.key == item.id), None)
                if fact:
                    value = fact.value

            # 提取原始文本片段
            raw_snippet = None
            if item.collected and value is not None:
                value_str = str(value)
                for line in tool_text.split('\n'):
                    line_stripped = line.strip()
                    if value_str in line_stripped and len(line_stripped) > 5:
                        raw_snippet = line_stripped[:200]
                        break

            details.append({
                "id": item.id,
                "description": item.description,
                "level": item.level.value,
                "collected": item.collected,
                "value": value,
                "raw_snippet": raw_snippet,
                "weight": item.weight
            })
        return details

    def _build_causal_chain(
        self,
        rule: Rule,
        evidence_items: List[EvidenceItem],
        facts: List[Fact]
    ) -> Dict[str, str]:
        """
        构建因果链分析
        """
        chain = {}

        # 获取证据中的关键值
        values = {}
        for fact in facts:
            values[fact.key] = str(fact.value) if fact.value is not None else ""

        # 根据规则填充根因模板
        root_cause = rule.root_cause_template
        for key, val in values.items():
            root_cause = root_cause.replace(f"{{{key}}}", val)

        # 构建场景特定的因果链
        if rule.category == "OOMKilled":
            memory_limit = values.get("memory_limit", "未知")
            chain = {
                "root_cause": f"容器内存使用超过 limit ({memory_limit})，被 cgroup OOM Killer 终止",
                "trigger": "应用内存使用 > memory limit",
                "mechanism": "cgroup OOM Killer 触发 (SIGKILL)",
                "manifestation": "容器退出 (exitCode=137)，Pod 重启",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }
        elif rule.category == "DiskFull":
            disk_usage = values.get("disk_usage", "未知")
            chain = {
                "root_cause": f"磁盘使用率达到 {disk_usage}%，导致写入失败 (ENOSPC)",
                "trigger": "磁盘空间耗尽",
                "mechanism": "文件系统返回 ENOSPC 错误",
                "manifestation": "应用写入失败、日志服务停止",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }
        elif rule.category == "VolumeLimitExceeded":
            size_limit = values.get("volume_limit_exceeded", "未知")
            chain = {
                "root_cause": f"Pod {values.get('pod', '未知')} 的 {values.get('volume_type', 'EmptyDir')} Volume 超过 SizeLimit ({size_limit}Mi)",
                "trigger": "临时存储空间写满",
                "mechanism": "kubelet 检测到 Volume 超限，Evict Pod",
                "manifestation": "Pod 被驱逐 (Evicted)，State 变为 Failed",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }
        elif rule.category == "KubeletCertInvalid":
            chain = {
                "root_cause": "Kubelet 证书异常，导致节点无法与 API Server 通信",
                "trigger": "证书过期/损坏/丢失",
                "mechanism": "TLS 握手失败",
                "manifestation": "Node 状态变为 NotReady，Pod 无法调度到该节点",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }
        elif rule.category == "DNSLatency":
            dns_time = values.get("dns_lookup_time", "未知")
            chain = {
                "root_cause": f"DNS 查询延迟达到 {dns_time}s，超过阈值 (0.45s)",
                "trigger": "CoreDNS 服务延迟或网络延迟注入",
                "mechanism": "DNS 解析超时",
                "manifestation": "服务调用超时、应用响应变慢",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }
        elif rule.category == "Dependency503":
            chain = {
                "root_cause": "依赖服务返回 503 (Service Unavailable)",
                "trigger": "依赖服务异常或过载",
                "mechanism": "上游服务拒绝请求",
                "manifestation": "应用 5xx 错误激增",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }
        else:
            chain = {
                "root_cause": root_cause or "待进一步分析",
                "trigger": "待分析",
                "mechanism": "待分析",
                "manifestation": "待分析",
                "evidence": ", ".join([e.description for e in evidence_items if e.collected])
            }

        return chain

    def _build_context(
        self,
        evidence_items: List[EvidenceItem],
        facts: List[Fact]
    ) -> Dict[str, Any]:
        """
        构建上下文字典，用于模板填充
        """
        context = {}
        for fact in facts:
            context[fact.key] = fact.value
        return context

    def _build_issue_summary(
        self,
        rule: Rule,
        context: Dict[str, Any],
        match_result: RuleMatch
    ) -> str:
        """
        构建问题摘要
        """
        summary = f"[{rule.layer.value}] {rule.scenario} - {rule.category}"
        if context:
            # 提取关键上下文值添加到摘要中
            key_values = []
            for key in ["exit_code_137", "memory_limit", "disk_usage", "dns_lookup_time", "node_status"]:
                if key in context and context[key] is not None:
                    key_values.append(f"{key}={context[key]}")
            if key_values:
                summary += f" ({', '.join(key_values)})"
        return summary

    def _fill_remediation_steps(
        self,
        rule: Rule,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        用上下文值填充修复建议模板
        """
        steps = []
        for step_template in rule.remediation_steps:
            step = step_template
            for key, val in context.items():
                step = step.replace(f"<{key}>", str(val))
            steps.append(step)
        return steps

    def _generate_verification_steps(
        self,
        rule: Rule,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        生成验证步骤
        """
        steps = []

        if rule.category == "OOMKilled":
            steps.append("等待 Pod 重新启动并观察状态")
            steps.append("检查 Pod 是否保持 Running 状态: kubectl get pod <pod_name>")
            steps.append("观察内存使用趋势: kubectl top pod <pod_name>")
        elif rule.category == "DiskFull":
            steps.append("验证磁盘空间释放: df -h")
            steps.append("确认应用日志正常写入")
            steps.append("监控磁盘使用趋势")
        elif rule.category == "VolumeLimitExceeded":
            steps.append("删除 Pod 以释放资源: kubectl delete pod <pod>")
            steps.append("调整 Volume SizeLimit 或使用 persistent volume")
            steps.append("检查新 Pod 是否正常运行: kubectl get pods")
        elif rule.category == "KubeletCertInvalid":
            steps.append("验证节点状态: kubectl get nodes")
            steps.append("确认 Node 状态变为 Ready")
            steps.append("检查 Pod 调度是否恢复正常")
        elif rule.category == "DNSLatency":
            steps.append("执行 DNS 查询测试: kubectl exec <pod> -- nslookup kubernetes.default")
            steps.append("确认延迟恢复正常 (< 0.45s)")
            steps.append("观察应用服务是否恢复正常")
        elif rule.category == "Dependency503":
            steps.append("测试依赖服务: kubectl run curl-test --rm -it -- curl http://<svc>")
            steps.append("确认返回 200")
            steps.append("观察应用 5xx 错误是否下降")

        return steps

    def _find_rule_for_scenario(self, scenario: str) -> Optional[Rule]:
        """根据场景 ID 找到对应的规则"""
        scenario_to_rule = {
            "L0-DiskFull": "R-L0-DISK-1",
            "L1-KubeletCert": "R-L1-CERT-1",
            "L2-OOMKilled": "R-L2-OOM-1",
            "L2-VolumeLimitExceeded": "R-L2-VOL-1",
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
