"""
Deterministic Skills Layer for AIOps

模块结构：
- models.py    : 数据模型（DeterministicDecision, Evidence, Fact 等）
- evidence.py  : 证据规格定义与提取器
- rules.py     : 声明式规则定义
- engine.py    : 规则引擎（匹配、置信度计算）
"""

# 数据模型
from .models import (
    Confidence,
    DeterministicDecision,
    EvidenceItem,
    EvidenceLevel,
    Fact,
    Layer,
)

# 规则引擎
from .engine import RulesEngine, get_engine

# 证据与规则
from .evidence import EvidenceExtractor, EvidenceSpec, EVIDENCE_SPECS
from .rules import Rule, RULES, get_rule, list_all_rules


__all__ = [
    # 数据模型
    "Confidence",
    "DeterministicDecision",
    "EvidenceItem",
    "EvidenceLevel",
    "Fact",
    "Layer",

    # 引擎
    "RulesEngine",
    "get_engine",

    # 规则与证据
    "Rule",
    "RULES",
    "EvidenceSpec",
    "EVIDENCE_SPECS",
]
