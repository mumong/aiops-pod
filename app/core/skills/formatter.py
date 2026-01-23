"""
输出格式化器

设计原则：
- 职责单一：只负责将 DeterministicDecision 格式化为各种输出格式
- 可扩展：支持 Markdown、JSON、Plain Text 等格式
- 国际化友好：文本与逻辑分离
"""

from __future__ import annotations

from typing import Optional

from .models import Confidence, DeterministicDecision


class DecisionFormatter:
    """决策格式化器"""
    
    @staticmethod
    def to_markdown(decision: DeterministicDecision) -> str:
        """
        格式化为 Markdown（附加到 LLM 报告末尾）
        """
        d = decision
        lines = []
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🧩 机器判定（Deterministic Analysis）")
        lines.append("")
        
        # 基本信息
        layer_val = d.layer.value if hasattr(d.layer, 'value') else str(d.layer)
        conf_val = d.confidence.value if hasattr(d.confidence, 'value') else str(d.confidence)
        
        lines.append(f"| 属性 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| **层级** | {layer_val} |")
        lines.append(f"| **场景** | {d.scenario} |")
        lines.append(f"| **分类** | {d.category} |")
        lines.append(f"| **置信度** | {conf_val} ({d.confidence_score:.1%}) |")
        lines.append("")
        
        # 命中规则
        if d.matched_rules:
            lines.append("### 命中规则")
            for r in d.matched_rules[:5]:
                lines.append(f"- `{r}`")
            lines.append("")
        
        # 证据状态
        if d.collected_evidence or d.missing_evidence:
            lines.append("### 证据状态")
            lines.append("")
            
            if d.collected_evidence:
                lines.append("**✅ 已采集：**")
                for e in d.collected_evidence[:5]:
                    lines.append(f"- {e}")
                lines.append("")
            
            if d.missing_evidence:
                lines.append("**❌ 缺失：**")
                for e in d.missing_evidence[:5]:
                    if e in (d.critical_missing or []):
                        lines.append(f"- 🚨 **[Critical]** {e}")
                    else:
                        lines.append(f"- {e}")
                lines.append("")
        
        # 下一步建议
        if d.next_steps:
            lines.append("### 建议操作")
            for step in d.next_steps[:8]:
                lines.append(f"{step}")
            lines.append("")
        
        # 置信度说明
        if d.confidence == Confidence.LOW:
            lines.append("> ⚠️ **注意**：当前置信度较低，建议补充上述缺失证据后重新诊断。")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_brief(decision: DeterministicDecision) -> str:
        """
        格式化为简短摘要（一行）
        """
        d = decision
        layer_val = d.layer.value if hasattr(d.layer, 'value') else str(d.layer)
        conf_val = d.confidence.value if hasattr(d.confidence, 'value') else str(d.confidence)
        
        missing_count = len(d.missing_evidence)
        missing_str = f", 缺 {missing_count} 项证据" if missing_count > 0 else ""
        
        return f"[{layer_val}] {d.scenario} | 置信度: {conf_val} ({d.confidence_score:.0%}){missing_str}"
    
    @staticmethod
    def to_json_summary(decision: DeterministicDecision) -> dict:
        """
        格式化为 JSON 摘要（用于 SSE 事件）
        """
        d = decision
        return {
            "layer": d.layer.value if hasattr(d.layer, 'value') else str(d.layer),
            "scenario": d.scenario,
            "category": d.category,
            "confidence": d.confidence.value if hasattr(d.confidence, 'value') else str(d.confidence),
            "confidence_score": d.confidence_score,
            "evidence_collected": len(d.collected_evidence),
            "evidence_missing": len(d.missing_evidence),
            "has_critical_missing": d.has_critical_missing,
        }


def format_decision_markdown(decision: DeterministicDecision) -> str:
    """便捷函数：格式化为 Markdown"""
    return DecisionFormatter.to_markdown(decision)


def format_decision_brief(decision: DeterministicDecision) -> str:
    """便捷函数：格式化为简短摘要"""
    return DecisionFormatter.to_brief(decision)
