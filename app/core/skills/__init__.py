"""
Deterministic Skills Layer for AIOps

设计原则：
- 高内聚：每个模块职责单一
- 低耦合：模块间通过数据模型交互
- 可扩展：新增场景只需添加配置

模块结构：
- models.py    : 数据模型（DeterministicDecision, Evidence, Fact 等）
- evidence.py  : 证据规格定义与提取器
- rules.py     : 声明式规则定义
- engine.py    : 规则引擎（匹配、置信度计算）
- gate.py      : 证据门禁（软拦截降级）
- formatter.py : 输出格式化

使用示例：
    from app.core.skills import evaluate_and_format
    
    markdown = evaluate_and_format(question, tool_text)
    if markdown:
        final_answer += markdown
"""

from typing import Dict, List, Optional

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

# 证据门禁
from .gate import EvidenceGate, apply_gate, get_default_gate

# 格式化
from .formatter import (
    DecisionFormatter,
    format_decision_brief,
    format_decision_markdown,
)

# 证据与规则（供高级用户扩展）
from .evidence import EvidenceExtractor, EvidenceSpec, EVIDENCE_SPECS
from .rules import Rule, RULES, get_rule, list_all_rules


def evaluate_deterministic_decision(
    question: str,
    events: List[Dict]
) -> Optional[DeterministicDecision]:
    """
    主入口：评估确定性决策（兼容旧接口）
    
    Args:
        question: 用户问题
        events: 内部事件列表（包含 tool_result 等）
    
    Returns:
        DeterministicDecision 或 None
    """
    # 从事件中提取工具输出文本
    tool_texts = []
    evidence_refs = []
    
    for ev in events:
        if ev.get("type") == "tool_result":
            text = ev.get("result_preview", "") or ""
            desc = ev.get("description", "") or ""
            tool_texts.append(f"{text}\n{desc}")
            evidence_refs.append(f"tool_result#{ev.get('seq', '?')}")
    
    tool_text = "\n".join(tool_texts)
    
    if not tool_text.strip():
        return None
    
    # 使用规则引擎评估
    engine = get_engine()
    decision = engine.evaluate(question, tool_text)
    
    if decision:
        # 应用证据门禁
        decision = apply_gate(decision)
        # 添加证据引用
        decision.evidence_refs = evidence_refs[:10]
    
    return decision


def evaluate_and_format(
    question: str,
    events: List[Dict],
    output_format: str = "markdown"
) -> Optional[str]:
    """
    便捷函数：评估并格式化输出
    
    Args:
        question: 用户问题
        events: 内部事件列表
        output_format: 输出格式 ("markdown" 或 "brief")
    
    Returns:
        格式化后的字符串或 None
    """
    decision = evaluate_deterministic_decision(question, events)
    
    if decision is None:
        return None
    
    if output_format == "brief":
        return format_decision_brief(decision)
    
    return format_decision_markdown(decision)


__all__ = [
    # 主入口
    "evaluate_deterministic_decision",
    "evaluate_and_format",
    
    # 数据模型
    "Confidence",
    "DeterministicDecision",
    "EvidenceItem",
    "EvidenceLevel",
    "Fact",
    "Layer",
    
    # 引擎与门禁
    "RulesEngine",
    "get_engine",
    "EvidenceGate",
    "apply_gate",
    
    # 格式化
    "format_decision_markdown",
    "format_decision_brief",
    "DecisionFormatter",
    
    # 规则与证据（高级）
    "Rule",
    "RULES",
    "EvidenceSpec",
    "EVIDENCE_SPECS",
]
