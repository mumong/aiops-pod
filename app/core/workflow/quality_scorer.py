"""
质量评分引擎

职责：
- 多维度加权评分计算根因置信度
- 加权证据完整率计算
- 评分明细输出（可解释性）
- 所有权重和阈值可配置

设计原则：
- 独立模块，不依赖具体节点实现
- 评分公式：final = max(0, Σ(w_i * d_i) - Σ(penalties))
- 每个维度和惩罚项都有明确的数据来源和计算规则
"""

import logging
import re
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# 默认配置（可被 config.yaml / 环境变量覆盖）
# ============================================================================

DEFAULT_CONFIDENCE_DIMENSIONS = {
    "evidence_strength": {"weight": 0.35, "description": "加权证据完整率"},
    "causal_chain": {"weight": 0.25, "description": "因果链完整性"},
    "tool_coverage": {"weight": 0.15, "description": "关键探针覆盖率"},
    "runbook_match": {"weight": 0.15, "description": "Runbook 匹配质量"},
    "llm_self_score": {"weight": 0.10, "description": "LLM 自评分数"},
}

DEFAULT_PENALTIES = {
    # 惩罚项已禁用，保留配置结构以备后续启用
    "enabled": False,
}

# 保底分配置
DEFAULT_BASELINE = {
    "with_evidence": 0.80,      # 有结论 + 有证据/工具 → 保底
    "with_root_cause": 0.75,    # 有结论 + 有根因但无工具证据 → 保底
    "minimum": 0.0,             # 绝对最低分
}

DEFAULT_EVIDENCE_LEVEL_WEIGHTS = {
    "CRITICAL": 1.0,
    "IMPORTANT": 0.6,
    "SUPPLEMENTARY": 0.3,
}

@dataclass
class ConfidenceDimension:
    """单个评分维度"""
    name: str
    weight: float
    score: float          # [0, 1]
    description: str
    detail: str = ""      # 人类可读的评分依据

    @property
    def weighted_score(self) -> float:
        return self.weight * self.score

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "weight": self.weight,
            "score": self.score,
            "weighted_score": round(self.weighted_score, 4),
            "description": self.description,
            "detail": self.detail,
        }


@dataclass
class Penalty:
    """惩罚项"""
    name: str
    value: float          # 扣分值 [0, 1]
    reason: str

    def to_dict(self) -> Dict:
        return {"name": self.name, "value": self.value, "reason": self.reason}


@dataclass
class ConfidenceResult:
    """置信度评分结果"""
    final_score: float
    dimensions: List[ConfidenceDimension]
    penalties: List[Penalty]
    weighted_total: float  # 惩罚前的加权总分
    fallback_applied: bool = False

    def to_dict(self) -> Dict:
        return {
            "final_score": round(self.final_score, 4),
            "weighted_total": round(self.weighted_total, 4),
            "fallback_applied": self.fallback_applied,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "penalties": [p.to_dict() for p in self.penalties],
        }

class QualityScorer:
    """
    质量评分引擎

    配置优先级：环境变量 > config.yaml > 代码默认值
    """

    def __init__(self, config: Optional[Dict] = None):
        metrics_config = config or {}
        self._dimensions_config = metrics_config.get(
            "confidence_dimensions", DEFAULT_CONFIDENCE_DIMENSIONS
        )
        self._penalties_config = metrics_config.get(
            "penalties", DEFAULT_PENALTIES
        )
        self._evidence_weights = metrics_config.get(
            "evidence_level_weights", DEFAULT_EVIDENCE_LEVEL_WEIGHTS
        )
        self._baseline = metrics_config.get(
            "baseline", DEFAULT_BASELINE
        )

    # ================================================================
    # 根因置信度评分
    # ================================================================
    def score_confidence(
        self,
        state: Dict[str, Any],
        metrics: Any,
    ) -> ConfidenceResult:
        """
        多维度加权评分计算根因置信度

        Returns:
            ConfidenceResult 包含最终分数、各维度明细、惩罚项
        """
        dimensions = []
        penalties = []
        fallback_applied = False

        # --- 维度1: evidence_strength ---
        evidence_items = state.get("evidence_items", [])
        ev_score, _ = self.score_evidence_completeness(evidence_items)
        dim_cfg = self._dimensions_config.get("evidence_strength", {})
        dimensions.append(ConfidenceDimension(
            name="evidence_strength",
            weight=dim_cfg.get("weight", 0.35),
            score=ev_score,
            description=dim_cfg.get("description", "加权证据完整率"),
            detail=f"加权完整率 {ev_score:.0%}",
        ))

        # --- 维度2: causal_chain ---
        # 从结构化字段 + 文本内容中检测因果链
        causal_chain = state.get("causal_chain") or {}
        decision = state.get("deterministic_decision")
        conclusion = state.get("conclusion_formatted") or state.get("conclusion") or ""
        rca_raw = state.get("rca_analysis", "")
        chain_score = self._score_causal_chain(causal_chain, decision, evidence_items, conclusion, rca_raw)
        dim_cfg = self._dimensions_config.get("causal_chain", {})
        dimensions.append(ConfidenceDimension(
            name="causal_chain",
            weight=dim_cfg.get("weight", 0.25),
            score=chain_score,
            description=dim_cfg.get("description", "因果链完整性"),
            detail=f"{'完整' if chain_score >= 0.8 else '部分' if chain_score > 0 else '无'}因果链",
        ))

        # --- 维度3: tool_coverage ---
        tool_results = state.get("tool_results", [])
        tool_score = self._score_tool_coverage(tool_results, metrics)
        dim_cfg = self._dimensions_config.get("tool_coverage", {})
        dimensions.append(ConfidenceDimension(
            name="tool_coverage",
            weight=dim_cfg.get("weight", 0.15),
            score=tool_score,
            description=dim_cfg.get("description", "关键探针覆盖率"),
            detail=f"工具成功率 {tool_score:.0%}",
        ))

        # --- 维度4: runbook_match (梯度评分) ---
        runbook_matched = getattr(metrics, 'runbook_matched', False) if metrics else False
        runbook_id = getattr(metrics, 'runbook_id', '') or '' if metrics else ''
        primary_runbook = getattr(metrics, 'primary_runbook', None) if metrics else None
        if primary_runbook:
            runbook_score = 1.0  # 有核心 runbook 命中
            runbook_detail = f"核心: {primary_runbook}"
        elif runbook_matched:
            runbook_score = 0.8  # 有 runbook 但未识别核心
            runbook_detail = "已匹配（未识别核心）"
        else:
            runbook_score = 0.3  # 未匹配，但不是 0（AI 可能用了通用知识）
            runbook_detail = "未匹配"
        dim_cfg = self._dimensions_config.get("runbook_match", {})
        dimensions.append(ConfidenceDimension(
            name="runbook_match",
            weight=dim_cfg.get("weight", 0.15),
            score=runbook_score,
            description=dim_cfg.get("description", "Runbook 匹配质量"),
            detail=runbook_detail,
        ))

        # --- 维度5: llm_self_score ---
        llm_score, llm_source = self._extract_llm_self_score(state)
        if llm_source == "fallback":
            fallback_applied = True
        dim_cfg = self._dimensions_config.get("llm_self_score", {})
        dimensions.append(ConfidenceDimension(
            name="llm_self_score",
            weight=dim_cfg.get("weight", 0.10),
            score=llm_score,
            description=dim_cfg.get("description", "LLM 自评分数"),
            detail=f"来源: {llm_source}, 分数: {llm_score:.0%}",
        ))

        # --- 计算加权总分 ---
        total_weight = sum(d.weight for d in dimensions)
        if total_weight > 0:
            weighted_total = sum(d.weighted_score for d in dimensions) / total_weight
        else:
            weighted_total = 0.5
            fallback_applied = True

        # --- 最终分数（可配置保底）---
        baseline_with_evidence = self._baseline.get("with_evidence", 0.80)
        baseline_with_root_cause = self._baseline.get("with_root_cause", 0.75)

        has_conclusion = bool(state.get("conclusion") or state.get("conclusion_formatted"))
        has_root_cause = bool(state.get("root_cause"))
        has_evidence = len(evidence_items) > 0
        has_tool_calls = len(state.get("tool_results", [])) > 0 or (
            getattr(metrics, 'total_tool_calls', 0) > 0 if metrics else False
        )

        final_score = weighted_total
        if has_conclusion and (has_evidence or has_tool_calls):
            final_score = max(baseline_with_evidence, weighted_total)
        elif has_conclusion and has_root_cause:
            final_score = max(baseline_with_root_cause, weighted_total)

        final_score = min(1.0, final_score)

        return ConfidenceResult(
            final_score=final_score,
            dimensions=dimensions,
            penalties=[],  # 不再使用惩罚项
            weighted_total=weighted_total,
            fallback_applied=fallback_applied,
        )

    # ================================================================
    # 证据完整率（加权）
    # ================================================================
    def score_evidence_completeness(
        self, evidence_items: List[Any]
    ) -> Tuple[float, Dict]:
        """
        按 EvidenceLevel 加权计算证据完整率

        Returns:
            (加权完整率, 各级别明细)
        """
        if not evidence_items:
            return 0.0, {"total": 0, "breakdown": {}}

        level_stats: Dict[str, Dict] = {}
        total_weight = 0.0
        collected_weight = 0.0

        for item in evidence_items:
            level_name = "IMPORTANT"  # 默认
            if hasattr(item, 'level'):
                level_val = item.level
                if hasattr(level_val, 'value'):
                    level_name = level_val.value
                elif isinstance(level_val, str):
                    level_name = level_val.upper()

            level_w = self._evidence_weights.get(level_name, 0.6)

            if level_name not in level_stats:
                level_stats[level_name] = {"total": 0, "collected": 0, "weight": level_w}
            level_stats[level_name]["total"] += 1

            collected = getattr(item, 'collected', False) if hasattr(item, 'collected') else False
            if collected:
                level_stats[level_name]["collected"] += 1
                collected_weight += level_w
            total_weight += level_w

        completeness = collected_weight / total_weight if total_weight > 0 else 0.0

        breakdown = {}
        for level_name, stats in level_stats.items():
            rate = stats["collected"] / stats["total"] if stats["total"] > 0 else 0.0
            breakdown[level_name] = {
                "total": stats["total"],
                "collected": stats["collected"],
                "weight": stats["weight"],
                "rate": round(rate, 4),
            }

        return completeness, {
            "total": len(evidence_items),
            "weighted_completeness": round(completeness, 4),
            "breakdown": breakdown,
        }

    # ================================================================
    # 私有方法：各维度评分逻辑
    # ================================================================
    def _score_causal_chain(
        self, causal_chain: Dict, decision: Any, evidence_items: List,
        conclusion: str = "", rca_raw: str = ""
    ) -> float:
        """因果链完整性评分 — 从结构化字段 + 文本内容检测"""
        score = 0.0

        # 1. 结构化字段有因果链
        if causal_chain and len(causal_chain) > 0:
            score = 0.5 if len(causal_chain) == 1 else min(1.0, 0.3 + len(causal_chain) * 0.2)

        # 2. 从文本中检测因果链（LLM 常在 conclusion 中输出因果链）
        if score < 0.5:
            all_text = f"{conclusion}\n{rca_raw}"
            chain_indicators = [
                "因果链", "根本原因", "传导机制", "直接原因",
                "causal", "root cause", "→",
                "┌─", "└─",  # ASCII 因果链图
            ]
            matches = sum(1 for ind in chain_indicators if ind in all_text)
            if matches >= 3:
                score = 1.0  # 文本中有完整因果链描述
            elif matches >= 1:
                score = 0.7  # 有部分因果分析

        # 3. 有证据支撑加分
        if evidence_items and score > 0:
            collected = [e for e in evidence_items if getattr(e, 'collected', False)]
            if collected:
                score = min(1.0, score + 0.1)

        return score

    def _score_tool_coverage(self, tool_results: List[Dict], metrics: Any) -> float:
        """关键探针覆盖率（梯度评分）"""
        total = len(tool_results) if tool_results else 0
        if total == 0:
            # 从 metrics 补充
            total = getattr(metrics, 'total_tool_calls', 0) if metrics else 0
            if total > 0:
                return 0.85  # 有工具调用但无详细结果，给个合理分
            return 0.3  # 完全没有工具调用，但不是 0

        success = sum(1 for r in tool_results if r.get("success", True))
        ratio = success / total
        # 梯度：成功率映射到 0.5-1.0 区间（即使有失败也不会太低）
        return 0.5 + ratio * 0.5

    def _extract_llm_self_score(self, state: Dict) -> Tuple[float, str]:
        """
        从 state 中提取 LLM 自评分数

        Returns:
            (score, source_description)
        """
        # 1. 优先从 deterministic_decision.confidence_score
        decision = state.get("deterministic_decision")
        if decision and hasattr(decision, 'confidence_score') and decision.confidence_score > 0:
            return decision.confidence_score, "deterministic_decision"

        # 2. 从 rca_analysis JSON
        rca_raw = state.get("rca_analysis", "")
        if rca_raw:
            try:
                rca_data = json.loads(rca_raw) if isinstance(rca_raw, str) else rca_raw
                if isinstance(rca_data, dict):
                    conf_val = rca_data.get("confidence")
                    if conf_val is not None:
                        conf_float = float(conf_val)
                        if 0 < conf_float <= 1.0:
                            return conf_float, "rca_analysis_json"
                        elif 1 < conf_float <= 100:
                            return conf_float / 100.0, "rca_analysis_json"
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # 3. 从文本正则提取
        conclusion = state.get("conclusion_formatted") or state.get("conclusion") or ""
        evidence_raw = state.get("evidence_analysis", "")
        all_text = f"{conclusion}\n{rca_raw}\n{evidence_raw}"

        patterns = [
            r'置信度[：:]\s*(?:约?\s*)?(\d{1,3})\s*%',
            r'置信度[：:|\s]*(?:高|中|低)\s*\(?(\d{1,3})\s*%\)?',
            r'\*\*置信度\*\*\s*\|\s*(?:高|中|低)\s*\(?(\d{1,3})\s*%\)?',
            r'"confidence"\s*:\s*(0\.\d+|1\.0)',
        ]
        for pattern in patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if val > 1.0:
                    val = val / 100.0
                if 0 < val <= 1.0:
                    return val, "text_regex"

        # 4. 回退到 layer_confidence
        layer_conf = state.get("layer_confidence")
        if layer_conf is not None and layer_conf > 0:
            return layer_conf, "layer_confidence"

        # 5. 最终兜底
        return 0.5, "fallback"

    # ================================================================
    # 格式化输出
    # ================================================================
    @staticmethod
    def format_confidence_breakdown(result: ConfidenceResult) -> str:
        """格式化置信度评分明细"""
        lines = [f"根因置信度: {result.final_score:.0%}"]
        for i, d in enumerate(result.dimensions):
            prefix = "├─" if i < len(result.dimensions) - 1 or result.penalties else "└─"
            lines.append(
                f"  {prefix} {d.description}: {d.score:.0%} "
                f"(权重 {d.weight:.0%}) → 贡献 {d.weighted_score:.1%}"
            )
        for i, p in enumerate(result.penalties):
            prefix = "└─" if i == len(result.penalties) - 1 else "├─"
            lines.append(f"  {prefix} 惩罚 {p.name}: -{p.value:.0%} ({p.reason})")
        return "\n".join(lines)

    @staticmethod
    def format_evidence_breakdown(completeness: float, detail: Dict) -> str:
        """格式化证据完整率明细"""
        breakdown = detail.get("breakdown", {})
        lines = [f"证据完整率: {completeness:.0%} (加权)"]
        items = list(breakdown.items())
        for i, (level, stats) in enumerate(items):
            prefix = "└─" if i == len(items) - 1 else "├─"
            lines.append(
                f"  {prefix} {level}: {stats['collected']}/{stats['total']} "
                f"(权重 {stats['weight']}) → {stats['rate']:.0%}"
            )
        return "\n".join(lines)
