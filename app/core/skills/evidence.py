"""
证据规格定义与提取器

设计原则：
- 声明式定义：每个场景的证据需求通过配置描述
- 可扩展：新增场景只需添加新的 EvidenceSpec
- 分离采集与解析：EvidenceSpec 定义需要什么，Extractor 负责提取
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .models import EvidenceItem, EvidenceLevel, Fact


@dataclass
class EvidenceSpec:
    """
    证据规格定义
    
    用于描述某个场景需要哪些证据、如何判断证据是否存在
    """
    id: str
    description: str
    level: EvidenceLevel
    weight: float = 0.2
    
    # 匹配规则（任一满足即视为已采集）
    keywords: List[str] = field(default_factory=list)  # 关键词匹配
    patterns: List[str] = field(default_factory=list)  # 正则匹配
    
    # 提取规则（可选，用于从原始文本提取结构化值）
    extract_pattern: Optional[str] = None
    extract_type: str = "str"  # str, int, float, bool


# ============================================================================
# 场景证据规格定义（声明式配置）
# ============================================================================

EVIDENCE_SPECS: Dict[str, List[EvidenceSpec]] = {
    "L0-DiskFull": [
        EvidenceSpec(
            id="disk_usage",
            description="磁盘使用率（df -h 输出）",
            level=EvidenceLevel.CRITICAL,
            weight=0.3,
            keywords=["df", "filesystem", "use%", "mounted on"],
            patterns=[r"\d{1,3}%"],
            extract_pattern=r"(\d{1,3})%",
            extract_type="int"
        ),
        EvidenceSpec(
            id="enospc_error",
            description="ENOSPC 错误信息",
            level=EvidenceLevel.CRITICAL,
            weight=0.3,
            keywords=["no space left on device", "enospc", "disk full"],
        ),
        EvidenceSpec(
            id="top_directories",
            description="Top 占用目录（du 输出）",
            level=EvidenceLevel.IMPORTANT,
            weight=0.2,
            keywords=["du -sh", "du -h", "/var/log", "/var/lib"],
        ),
        EvidenceSpec(
            id="deleted_files",
            description="已删除但未释放的文件（lsof +L1）",
            level=EvidenceLevel.OPTIONAL,
            weight=0.1,
            keywords=["lsof", "deleted", "(deleted)"],
        ),
    ],
    
    "L1-KubeletCert": [
        EvidenceSpec(
            id="node_status",
            description="节点状态（NotReady）",
            level=EvidenceLevel.CRITICAL,
            weight=0.3,
            keywords=["notready", "not ready", "ready=false"],
            patterns=[r"ready\s+(false|unknown)", r"status.*notready"],
        ),
        EvidenceSpec(
            id="cert_error",
            description="证书错误日志（x509/certificate）",
            level=EvidenceLevel.CRITICAL,
            weight=0.4,
            keywords=["x509", "certificate", "tls", "cert"],
            patterns=[r"x509:.*certificate", r"certificate.*expired", r"tls.*error"],
        ),
        EvidenceSpec(
            id="kubelet_logs",
            description="kubelet 日志",
            level=EvidenceLevel.IMPORTANT,
            weight=0.2,
            keywords=["kubelet", "journalctl"],
        ),
    ],
    
    "L2-OOMKilled": [
        EvidenceSpec(
            id="oom_reason",
            description="OOMKilled 终止原因",
            level=EvidenceLevel.CRITICAL,
            weight=0.3,
            keywords=["oomkilled", "oom killed", "out of memory"],
            patterns=[r"reason[:\s]+oomkilled", r"oom\s*kill"],
        ),
        EvidenceSpec(
            id="exit_code_137",
            description="Exit Code 137",
            level=EvidenceLevel.CRITICAL,
            weight=0.3,
            keywords=["exit code: 137", "exitcode: 137", "exit code 137"],
            patterns=[r"exit\s*code[:\s]+137", r"exitcode[:\s]+137"],
            extract_pattern=r"exit\s*code[:\s]+(\d+)",
            extract_type="int"
        ),
        EvidenceSpec(
            id="previous_logs",
            description="崩溃前日志（--previous）",
            level=EvidenceLevel.IMPORTANT,
            weight=0.2,
            keywords=["--previous", "previous", "cannot allocate memory"],
        ),
        EvidenceSpec(
            id="memory_limit",
            description="容器 memory limit 配置",
            level=EvidenceLevel.IMPORTANT,
            weight=0.2,
            keywords=["limits", "memory:", "resources"],
            patterns=[r"memory[:\s]+\d+[mgMG]i?"],
        ),
    ],
    
    "L3-DNSLatency": [
        EvidenceSpec(
            id="dns_lookup_time",
            description="DNS 查询耗时",
            level=EvidenceLevel.CRITICAL,
            weight=0.4,
            keywords=["dns_lookup_seconds", "nslookup", "dns lookup"],
            patterns=[r"dns_lookup_seconds[=:\s]+[\d.]+"],
            extract_pattern=r"dns_lookup_seconds[=:\s]+([\d.]+)",
            extract_type="float"
        ),
        EvidenceSpec(
            id="coredns_status",
            description="CoreDNS 状态",
            level=EvidenceLevel.IMPORTANT,
            weight=0.3,
            keywords=["coredns", "kube-dns"],
        ),
        EvidenceSpec(
            id="tc_rules",
            description="TC 延迟规则（如有注入）",
            level=EvidenceLevel.OPTIONAL,
            weight=0.2,
            keywords=["tc qdisc", "netem", "delay"],
        ),
    ],
    
    "L4-Dependency503": [
        EvidenceSpec(
            id="upstream_503",
            description="上游返回 503 证据",
            level=EvidenceLevel.CRITICAL,
            weight=0.4,
            keywords=["503", "service unavailable"],
            patterns=[r"(upstream|dependency).*503", r"received.*503", r"http.*503"],
        ),
        EvidenceSpec(
            id="app_5xx_logs",
            description="应用 5xx 日志",
            level=EvidenceLevel.CRITICAL,
            weight=0.3,
            keywords=["5xx", "500", "502", "503", "504"],
            patterns=[r"status[:\s]+5\d{2}"],
        ),
        EvidenceSpec(
            id="dependency_check",
            description="依赖服务检查（curl/http）",
            level=EvidenceLevel.IMPORTANT,
            weight=0.2,
            keywords=["curl", "http_code", "status_code"],
        ),
    ],
}


class EvidenceExtractor:
    """
    证据提取器
    
    负责从工具输出中提取结构化事实
    """
    
    @staticmethod
    def check_evidence(
        text: str,
        spec: EvidenceSpec
    ) -> Tuple[bool, Optional[Any]]:
        """
        检查文本中是否包含指定证据
        
        Returns:
            (是否存在, 提取的值)
        """
        text_lower = text.lower()
        
        # 关键词匹配
        keyword_found = any(kw.lower() in text_lower for kw in spec.keywords)
        
        # 正则匹配
        pattern_found = False
        for pattern in spec.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_found = True
                break
        
        exists = keyword_found or pattern_found
        
        # 提取值
        extracted = None
        if exists and spec.extract_pattern:
            match = re.search(spec.extract_pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(1)
                try:
                    if spec.extract_type == "int":
                        extracted = int(raw)
                    elif spec.extract_type == "float":
                        extracted = float(raw)
                    elif spec.extract_type == "bool":
                        extracted = raw.lower() in ("true", "1", "yes")
                    else:
                        extracted = raw
                except (ValueError, TypeError):
                    extracted = raw
        
        return exists, extracted

    @staticmethod
    def extract_all(
        text: str,
        scenario: str
    ) -> Tuple[List[EvidenceItem], List[Fact]]:
        """
        从文本中提取指定场景的所有证据
        
        Returns:
            (证据项列表, 事实列表)
        """
        specs = EVIDENCE_SPECS.get(scenario, [])
        evidence_items: List[EvidenceItem] = []
        facts: List[Fact] = []
        
        for spec in specs:
            exists, value = EvidenceExtractor.check_evidence(text, spec)
            
            item = EvidenceItem(
                id=spec.id,
                description=spec.description,
                level=spec.level,
                weight=spec.weight,
                collected=exists,
                value=value,
                source="tool_result" if exists else None
            )
            evidence_items.append(item)
            
            if exists and value is not None:
                facts.append(Fact(
                    key=spec.id,
                    value=value,
                    source="extracted"
                ))
        
        return evidence_items, facts

    @staticmethod
    def get_scenario_specs(scenario: str) -> List[EvidenceSpec]:
        """获取场景的证据规格"""
        return EVIDENCE_SPECS.get(scenario, [])

    @staticmethod
    def list_scenarios() -> List[str]:
        """列出所有已定义的场景"""
        return list(EVIDENCE_SPECS.keys())
