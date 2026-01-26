"""
声明式规则定义

设计原则：
- 规则与逻辑分离：规则是数据，引擎是逻辑
- 可配置：未来可从 YAML/JSON 加载规则
- 可解释：每条规则有清晰的 ID、名称、说明
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .models import Layer


class ConditionOp(str, Enum):
    """条件操作符"""
    CONTAINS = "contains"      # 包含（字符串）
    EQUALS = "eq"              # 相等
    NOT_EQUALS = "neq"         # 不相等
    GREATER_THAN = "gt"        # 大于
    LESS_THAN = "lt"           # 小于
    GREATER_EQ = "gte"         # 大于等于
    LESS_EQ = "lte"            # 小于等于
    REGEX = "regex"            # 正则匹配
    EXISTS = "exists"          # 存在


@dataclass
class Condition:
    """规则条件"""
    evidence_id: str           # 证据 ID
    op: ConditionOp            # 操作符
    value: Optional[any] = None  # 比较值（某些操作符不需要）
    description: str = ""      # 条件说明


@dataclass
class Rule:
    """
    诊断规则
    
    设计说明：
    - 每条规则对应一个原子场景
    - 支持多条件组合（AND/OR）
    - 包含置信度基准和修复建议
    """
    id: str
    name: str
    layer: Layer
    scenario: str
    category: str
    
    # 条件
    conditions: List[Condition] = field(default_factory=list)
    condition_logic: str = "OR"  # AND / OR
    
    # 置信度
    base_confidence: float = 0.8  # 基础置信度
    
    # 修复建议
    remediation_steps: List[str] = field(default_factory=list)
    
    # 描述
    description: str = ""
    root_cause_template: str = ""  # 根因描述模板


# ============================================================================
# 规则库定义
# ============================================================================

RULES: Dict[str, Rule] = {
    "R-L0-DISK-1": Rule(
        id="R-L0-DISK-1",
        name="磁盘空间耗尽",
        layer=Layer.L0,
        scenario="日志文件占满磁盘",
        category="DiskFull",
        conditions=[
            Condition("disk_usage", ConditionOp.GREATER_EQ, 95, "磁盘使用率 >= 95%"),
            Condition("enospc_error", ConditionOp.EXISTS, None, "存在 ENOSPC 错误"),
        ],
        condition_logic="OR",
        base_confidence=0.9,
        remediation_steps=[
            "定位占用最大的目录: du -sh /* | sort -hr | head -10",
            "清理日志文件（优先 truncate）: truncate -s 0 /path/to/large.log",
            "检查已删除但未释放的文件: lsof +L1 | grep deleted",
            "若发现 deleted still open，重启占用进程释放空间",
        ],
        description="磁盘空间耗尽导致 ENOSPC 错误",
        root_cause_template="磁盘 {mount_point} 使用率达到 {usage}%，导致写入失败 (ENOSPC)"
    ),
    
    "R-L1-CERT-1": Rule(
        id="R-L1-CERT-1",
        name="Kubelet 证书异常",
        layer=Layer.L1,
        scenario="Kubelet 证书失效导致 Node NotReady",
        category="KubeletCertInvalid",
        conditions=[
            Condition("node_status", ConditionOp.EXISTS, None, "节点状态异常"),
            Condition("cert_error", ConditionOp.EXISTS, None, "存在证书错误"),
        ],
        condition_logic="AND",
        base_confidence=0.85,
        remediation_steps=[
            "检查证书有效期: openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -dates",
            "若证书丢失/损坏，还原证书文件",
            "重启 kubelet: systemctl restart kubelet",
            "验证节点恢复: kubectl get nodes",
        ],
        description="Kubelet 证书异常（过期/丢失/损坏）导致节点 NotReady",
        root_cause_template="Kubelet 证书异常 ({cert_error})，导致节点 {node} 无法与 API Server 通信"
    ),
    
    "R-L2-OOM-1": Rule(
        id="R-L2-OOM-1",
        name="容器 OOMKilled",
        layer=Layer.L2,
        scenario="OOMKilled (内存超限)",
        category="OOMKilled",
        conditions=[
            Condition("oom_reason", ConditionOp.EXISTS, None, "存在 OOMKilled 标记"),
            Condition("exit_code_137", ConditionOp.EQUALS, 137, "Exit Code = 137"),
        ],
        condition_logic="OR",
        base_confidence=0.9,
        remediation_steps=[
            "检查当前 memory limit: kubectl get pod <name> -o yaml | grep -A5 resources",
            "临时调高 memory limit（需审批）: kubectl patch deploy <name> -p '{...}'",
            "分析崩溃前日志确定内存消耗来源: kubectl logs <pod> --previous --tail=200",
            "若为泄漏，修复代码后重新发布",
        ],
        description="容器内存使用超过 limit 被 OOM Killer 终止",
        root_cause_template="容器 {container} 内存使用超过 limit ({memory_limit})，被 cgroup OOM Killer 终止 (exitCode=137)"
    ),

    "R-L2-VOL-1": Rule(
        id="R-L2-VOL-1",
        name="Pod 存储卷超限",
        layer=Layer.L2,
        scenario="EmptyDir/HostPath Volume 超限",
        category="VolumeLimitExceeded",
        conditions=[
            Condition("evicted_reason", ConditionOp.EXISTS, None, "Pod 被 Evicted"),
            Condition("volume_limit_exceeded", ConditionOp.EXISTS, None, "Volume 超限错误"),
        ],
        condition_logic="OR",
        base_confidence=0.9,
        remediation_steps=[
            "检查 Volume 配置: kubectl describe pod <pod> | grep -A5 Volumes",
            "清理 EmptyDir 中的临时文件（如果可以）: kubectl exec <pod> -- rm /path/to/temp/*",
            "增大 SizeLimit: 在 Deployment spec 中修改 volume sizeLimit 值",
            "使用 persistent volume 替代临时存储（长期数据）",
            "监控 Pod 状态: kubectl get pods -w",
        ],
        description="EmptyDir/HostPath Volume 超过 SizeLimit 导致 Pod 被 Evicted",
        root_cause_template="Pod {pod} 的 {volume_type} Volume 超过 SizeLimit ({size_limit})，kubelet 驱逐 Pod"
    ),
    
    "R-L3-DNS-1": Rule(
        id="R-L3-DNS-1",
        name="DNS 延迟过高",
        layer=Layer.L3,
        scenario="CoreDNS 网络延迟注入 (500ms)",
        category="DNSLatency",
        conditions=[
            Condition("dns_lookup_time", ConditionOp.GREATER_EQ, 0.45, "DNS 查询延迟 >= 450ms"),
        ],
        condition_logic="AND",
        base_confidence=0.85,
        remediation_steps=[
            "检查 CoreDNS Pod 状态: kubectl get pods -n kube-system -l k8s-app=kube-dns",
            "查看 CoreDNS 日志: kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100",
            "检查是否有 TC 延迟注入: tc qdisc show",
            "移除 TC 延迟规则: tc qdisc del dev eth0 root (若存在)",
        ],
        description="DNS 查询延迟过高导致服务调用超时",
        root_cause_template="DNS 查询延迟 p95 达到 {dns_latency}s，超过阈值 (0.45s)"
    ),
    
    "R-L4-DEP-1": Rule(
        id="R-L4-DEP-1",
        name="依赖服务 503",
        layer=Layer.L4,
        scenario="依赖服务固定返回 503",
        category="Dependency503",
        conditions=[
            Condition("upstream_503", ConditionOp.EXISTS, None, "上游返回 503"),
            Condition("app_5xx_logs", ConditionOp.EXISTS, None, "应用 5xx 日志"),
        ],
        condition_logic="AND",
        base_confidence=0.85,
        remediation_steps=[
            "确认依赖服务状态: kubectl get pods -l app=<dependency>",
            "从集群内测试依赖: kubectl run curl --rm -it --image=curlimages/curl -- curl -v http://<svc>",
            "检查依赖服务日志: kubectl logs -l app=<dependency> --tail=100",
            "滚动更新/重启依赖服务: kubectl rollout restart deploy/<dependency>",
        ],
        description="依赖服务返回 503 导致应用 5xx 激增",
        root_cause_template="依赖服务 {dependency} 返回 503 (Service Unavailable)，导致应用 {app} 5xx 错误激增"
    ),
}


def get_rule(rule_id: str) -> Optional[Rule]:
    """获取规则"""
    return RULES.get(rule_id)


def get_rules_by_layer(layer: Layer) -> List[Rule]:
    """获取指定层级的所有规则"""
    return [r for r in RULES.values() if r.layer == layer]


def get_rules_by_scenario(scenario: str) -> List[Rule]:
    """获取指定场景的所有规则"""
    return [r for r in RULES.values() if scenario.lower() in r.scenario.lower()]


def list_all_rules() -> List[Rule]:
    """列出所有规则"""
    return list(RULES.values())
