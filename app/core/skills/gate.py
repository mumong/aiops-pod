"""
证据门禁 (Evidence Gate)

设计原则：
- 职责单一：只负责对 Decision 做后处理（降级/警告）
- 软拦截：不阻断输出，只修改置信度和添加警告
- 可配置：门禁策略可调整
"""

from __future__ import annotations

from typing import List, Optional

from .models import Confidence, DeterministicDecision


class EvidenceGate:
    """
    证据门禁
    
    职责：
    1. 当关键证据缺失时，强制降级置信度
    2. 生成补采建议
    3. 添加警告信息
    """
    
    def __init__(
        self,
        force_downgrade_on_critical: bool = True,
        min_confidence_without_critical: Confidence = Confidence.LOW
    ):
        """
        Args:
            force_downgrade_on_critical: 缺失 Critical 证据时是否强制降级
            min_confidence_without_critical: 缺失 Critical 时的最低置信度
        """
        self.force_downgrade_on_critical = force_downgrade_on_critical
        self.min_confidence_without_critical = min_confidence_without_critical
    
    def apply(self, decision: DeterministicDecision) -> DeterministicDecision:
        """
        应用证据门禁
        
        Args:
            decision: 原始决策对象
        
        Returns:
            处理后的决策对象（可能修改了置信度和建议）
        """
        if not decision.has_critical_missing:
            return decision
        
        if not self.force_downgrade_on_critical:
            return decision
        
        # 强制降级置信度
        original_confidence = decision.confidence
        decision.confidence = self.min_confidence_without_critical
        decision.confidence_score = 0.3  # 固定低分
        
        # 添加警告到 next_steps 开头
        warning = (
            f"🚨 关键证据缺失，置信度已从 [{original_confidence.value}] "
            f"降级为 [{decision.confidence.value}]"
        )
        decision.next_steps.insert(0, warning)
        
        # 生成补采命令建议
        supplement_cmds = self._generate_supplement_commands(decision)
        if supplement_cmds:
            decision.next_steps.insert(1, "📥 请执行以下命令补采关键证据：")
            for cmd in supplement_cmds:
                decision.next_steps.insert(2, f"  $ {cmd}")
        
        return decision
    
    def _generate_supplement_commands(
        self,
        decision: DeterministicDecision
    ) -> List[str]:
        """根据缺失的证据生成补采命令"""
        commands = []
        
        # 根据场景和缺失项生成命令
        category = decision.category
        missing = decision.critical_missing
        
        if category == "DiskFull":
            if any("磁盘使用率" in m for m in missing):
                commands.append("df -h && df -i")
            if any("ENOSPC" in m for m in missing):
                commands.append("dmesg | grep -i 'no space'")
        
        elif category == "KubeletCertInvalid":
            if any("节点状态" in m for m in missing):
                commands.append("kubectl get nodes -o wide")
            if any("证书" in m for m in missing):
                commands.append("journalctl -u kubelet --since '30m ago' | grep -i 'x509\\|cert'")
        
        elif category == "OOMKilled":
            if any("OOMKilled" in m or "Exit Code" in m for m in missing):
                commands.append("kubectl get pod <POD_NAME> -o json | jq '.status.containerStatuses'")
                commands.append("kubectl logs <POD_NAME> --previous --tail=200")
        
        elif category == "DNSLatency":
            if any("DNS" in m for m in missing):
                commands.append("kubectl exec <POD_NAME> -- sh -c 'for i in 1 2 3 4 5; do time nslookup kubernetes.default; done'")
        
        elif category == "Dependency503":
            if any("503" in m or "5xx" in m for m in missing):
                commands.append("kubectl logs <APP_POD> --tail=100 | grep -i '503\\|5xx\\|upstream'")
                commands.append("kubectl run curl-test --rm -it --image=curlimages/curl -- curl -v http://<DEPENDENCY_SVC>")
        
        return commands


# 默认门禁实例
_default_gate: Optional[EvidenceGate] = None


def get_default_gate() -> EvidenceGate:
    """获取默认门禁实例"""
    global _default_gate
    if _default_gate is None:
        _default_gate = EvidenceGate()
    return _default_gate


def apply_gate(decision: DeterministicDecision) -> DeterministicDecision:
    """便捷函数：应用默认门禁"""
    return get_default_gate().apply(decision)
