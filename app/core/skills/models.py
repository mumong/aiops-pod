"""
数据模型定义 - skills 模块的核心数据结构

设计原则：
- 所有模型使用 dataclass，简洁且类型安全
- 模型之间低耦合，通过组合而非继承
- 支持序列化（to_dict）便于 JSON 输出
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class Layer(str, Enum):
    """诊断模式判定

    当前语义：HEALTHY（无异常）/ QUERY（直接查询）/ ABNORMAL（存在异常 Pod，
    进入完整诊断链路）。异常的具体分类由 pod_status_keyword / pod_abnormal_type
    表达，不再做 L0-L4 层级归因。
    L0-L4 仅作为历史兼容值保留（旧输入仍可解析），运行时等同 ABNORMAL。
    """
    HEALTHY = "HEALTHY"  # 集群健康，无异常
    QUERY = "QUERY"  # 直接查询（非故障诊断）
    ABNORMAL = "ABNORMAL"  # 存在异常 Pod，进入完整诊断链路
    L0 = "L0"  # 兼容保留（deprecated）
    L1 = "L1"  # 兼容保留（deprecated）
    L2 = "L2"  # 兼容保留（deprecated）
    L3 = "L3"  # 兼容保留（deprecated）
    L4 = "L4"  # 兼容保留（deprecated）


class Confidence(str, Enum):
    """置信度等级"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    
    @classmethod
    def from_score(cls, score: float) -> "Confidence":
        """从分数转换为置信度等级"""
        if score >= 0.8:
            return cls.HIGH
        elif score >= 0.5:
            return cls.MEDIUM
        return cls.LOW


class EvidenceLevel(str, Enum):
    """证据重要性级别"""
    CRITICAL = "critical"    # 关键证据，缺失则强制降级
    IMPORTANT = "important"  # 重要证据，影响置信度
    OPTIONAL = "optional"    # 可选证据，辅助判断


@dataclass
class EvidenceItem:
    """单项证据"""
    id: str
    description: str
    level: EvidenceLevel = EvidenceLevel.IMPORTANT
    weight: float = 0.2  # 对置信度的影响权重
    collected: bool = False
    value: Optional[Any] = None
    source: Optional[str] = None  # 来源（如 tool_result#5）
    outcome: str = "unknown"  # positive/negative/inconclusive/failed/unknown

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["level"] = self.level.value
        return d


@dataclass
class Fact:
    """结构化事实"""
    key: str
    value: Any
    source: str  # 来源事件引用
    confidence: float = 1.0  # 事实本身的可信度

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RuleMatch:
    """规则匹配结果"""
    rule_id: str
    rule_name: str
    matched: bool
    conditions_met: List[str] = field(default_factory=list)
    conditions_failed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EvidenceDetail:
    """详细证据记录（包含具体采集内容）"""
    id: str
    description: str
    level: str  # critical/important/optional
    collected: bool
    value: Optional[Any] = None  # 提取的具体值（如 98%、137）
    raw_snippet: Optional[str] = None  # 原始文本片段（证据来源）
    source_tool: Optional[str] = None  # 采集工具（如 kubectl describe）
    source_ref: Optional[str] = None  # 事件引用（如 tool_result#3）
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def format_display(self) -> str:
        """格式化为可读字符串"""
        if not self.collected:
            return f"❌ {self.description}：未采集"
        
        parts = [f"✅ {self.description}"]
        if self.value is not None:
            parts.append(f"值 = `{self.value}`")
        if self.raw_snippet:
            # 截取关键片段
            snippet = self.raw_snippet[:200].replace('\n', ' ').strip()
            if len(self.raw_snippet) > 200:
                snippet += "..."
            parts.append(f"来源: {snippet}")
        return " | ".join(parts)


@dataclass
class DeterministicDecision:
    """
    确定性判定结果
    
    设计说明：
    - 这是 skills 模块的核心输出
    - 包含完整的判定上下文，便于追溯和解释
    - 支持软拦截模式：不阻断 LLM 输出，只附加判定结果
    """
    layer: Layer
    scenario: str
    category: str
    confidence: Confidence
    confidence_score: float = 0.0  # 量化分数 [0, 1]
    
    # 是否真正发现了问题
    issue_found: bool = True
    issue_summary: str = ""  # 一句话总结
    
    # 上下文信息（填充占位符用）
    context: Dict[str, Any] = field(default_factory=dict)
    # 例如: {"pod": "my-app-xxx", "namespace": "default", "memory_limit": "512Mi", "exit_code": 137}
    
    # 规则匹配详情
    matched_rules: List[str] = field(default_factory=list)
    excluded_rules: List[str] = field(default_factory=list)
    
    # 证据状态（简单标签列表，向后兼容）
    collected_evidence: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    critical_missing: List[str] = field(default_factory=list)
    
    # 详细证据（包含具体内容）
    evidence_details: List[EvidenceDetail] = field(default_factory=list)
    
    # 因果链
    causal_chain: Dict[str, str] = field(default_factory=dict)
    # 例如: {"root_cause": "容器内存超限", "propagation": "OOM Killer 触发", "impact": "Pod 重启"}
    
    # 修复建议（已填充具体值）
    remediation_steps: List[str] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)
    
    # 建议（原字段保留兼容）
    next_steps: List[str] = field(default_factory=list)
    
    # 溯源
    evidence_refs: List[str] = field(default_factory=list)
    facts: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["layer"] = self.layer.value if isinstance(self.layer, Layer) else self.layer
        d["confidence"] = self.confidence.value if isinstance(self.confidence, Confidence) else self.confidence
        return d

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence == Confidence.HIGH

    @property
    def has_critical_missing(self) -> bool:
        return len(self.critical_missing) > 0

    def _calculate_evidence_completeness(self) -> str:
        """
        计算证据完整度百分比

        Returns:
            格式化的百分比字符串，如 "75%"
        """
        total = len(self.collected_evidence) + len(self.missing_evidence)
        if total == 0:
            return "0%"
        percentage = (len(self.collected_evidence) / total) * 100
        return f"{percentage:.0f}%"

    def get_context_value(self, key: str, default: str = "<未知>") -> str:
        """安全获取上下文值"""
        return self.context.get(key, default)
