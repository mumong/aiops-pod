"""
默认模式（非工作流）后置指标提取器

从 internal_events 中提取诊断质量指标，使默认模式也能输出
与工作流模式一致的质量指标表。

提取方式：事件统计 + LLM 输出正则提取（混合提取）。
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.workflow.metrics import (
    MTTR_THRESHOLD_SECONDS,
    ROOT_CAUSE_CONFIDENCE_THRESHOLD,
    EVIDENCE_COMPLETENESS_THRESHOLD,
)

logger = logging.getLogger(__name__)

# 层级映射
LAYER_NAMES = {
    "L0": "基础设施层",
    "L1": "集群与节点层",
    "L2": "工作负载层",
    "L3": "服务与网络层",
    "L4": "应用层",
    "QUERY": "直接查询",
}


@dataclass
class DiagnosisMetrics:
    """诊断质量指标"""
    run_id: str = ""
    mttr_seconds: float = 0.0
    layer: Optional[str] = None
    layer_name: str = ""
    confidence_score: float = 0.0
    confidence_label: str = ""
    evidence_collected: int = 0
    evidence_total: int = 0
    runbooks_referenced: List[str] = field(default_factory=list)
    tool_calls_count: int = 0
    is_diagnosis: bool = False  # 是否为诊断场景（非 QUERY）

    @property
    def mttr_formatted(self) -> str:
        s = self.mttr_seconds
        if s < 60:
            return f"{s:.1f}s"
        elif s < 3600:
            return f"{s / 60:.1f}m"
        return f"{s / 3600:.1f}h"

    @property
    def confidence_pct(self) -> str:
        return f"{self.confidence_score:.0%}"

    @property
    def evidence_ratio(self) -> str:
        if self.evidence_total == 0:
            return f"{self.evidence_collected} 项"
        return f"{self.evidence_collected}/{self.evidence_total}"

    @property
    def runbook_display(self) -> str:
        return ", ".join(self.runbooks_referenced) if self.runbooks_referenced else "无"

    def format_metrics_block(self) -> str:
        """格式化为与工作流模式一致的质量指标表"""
        lines = []

        # 使用配置化阈值
        mttr_threshold_str = f"< {MTTR_THRESHOLD_SECONDS // 60}m"
        rca_threshold_str = f">= {int(ROOT_CAUSE_CONFIDENCE_THRESHOLD * 100)}%"
        ev_threshold_str = f"> {int(EVIDENCE_COMPLETENESS_THRESHOLD * 100)}%"

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 📈 质量指标")
        lines.append("")
        lines.append("| 指标 | 要求 | 实际 | 状态 |")
        lines.append("|------|------|------|------|")

        # MTTR
        mttr_pass = self.mttr_seconds < MTTR_THRESHOLD_SECONDS
        mttr_status = "✅ 达标" if mttr_pass else "❌ 未达标"
        lines.append(f"| **MTTR** | {mttr_threshold_str} | {self.mttr_formatted} | {mttr_status} |")

        if self.is_diagnosis:
            # 根因置信度
            conf_pass = self.confidence_score >= ROOT_CAUSE_CONFIDENCE_THRESHOLD
            conf_status = "✅ 达标" if conf_pass else "⚠️ 待验证"
            lines.append(f"| **根因置信度** | {rca_threshold_str} | {self.confidence_pct} | {conf_status} |")

            # 证据完整率
            if self.evidence_total > 0:
                ratio = self.evidence_collected / self.evidence_total
                ev_pass = ratio > EVIDENCE_COMPLETENESS_THRESHOLD
                ev_status = "✅ 达标" if ev_pass else "⚠️ 不足"
                lines.append(f"| **证据完整率** | {ev_threshold_str} | {ratio:.0%} ({self.evidence_ratio}) | {ev_status} |")
            else:
                lines.append(f"| **证据数量** | - | {self.evidence_collected} 项 | ℹ️ |")

        lines.append("")

        # 诊断追踪
        lines.append("📋 诊断追踪")
        lines.append("")
        if self.is_diagnosis and self.layer:
            lines.append(f"- **诊断层级**: {self.layer} - {self.layer_name}")
        if self.is_diagnosis:
            lines.append(f"- **参考 Runbook**: {self.runbook_display}")
        lines.append(f"- **工具调用**: {self.tool_calls_count} 次")
        lines.append("")

        return "\n".join(lines)


class MetricsExtractor:
    """从 internal_events 后置提取诊断指标"""

    # Runbook 文件名模式
    _RUNBOOK_PATTERN = re.compile(r'[\w-]+\.md')
    # 层级模式
    _LAYER_PATTERN = re.compile(r'\b(L[0-4])\b')
    # 置信度模式（多种格式）
    _CONFIDENCE_PATTERNS = [
        re.compile(r'置信度[：:]\s*(?:约?\s*)?(\d{1,3})%'),
        re.compile(r'置信度[：:]\s*(?:高|中|低)\s*\(?(\d{1,3})%\)?'),
        re.compile(r'confidence[：:]\s*(\d{1,3})%', re.IGNORECASE),
        re.compile(r'"confidence"\s*:\s*(0\.\d+|1\.0)'),
    ]

    def extract(self, events: List[Dict], question: str) -> DiagnosisMetrics:
        """
        从 internal_events 列表提取指标

        Args:
            events: iter_internal_events 产出的事件列表
            question: 用户原始问题

        Returns:
            DiagnosisMetrics 实例
        """
        metrics = DiagnosisMetrics()

        # MTTR: 从 run_end 或 final 事件取 elapsed_seconds
        for ev in reversed(events):
            if ev.get("type") in ("run_end", "final"):
                elapsed = ev.get("elapsed_seconds")
                if elapsed is not None:
                    metrics.mttr_seconds = float(elapsed)
                    break

        # run_id
        for ev in events:
            rid = ev.get("run_id")
            if rid:
                metrics.run_id = rid
                break

        # 工具调用统计与证据统计
        tool_success = 0
        tool_total = 0
        for ev in events:
            if ev.get("type") == "tool_result":
                tool_total += 1
                status = ev.get("status", "")
                if status == "success" and not ev.get("error"):
                    tool_success += 1
        metrics.tool_calls_count = tool_total
        metrics.evidence_collected = tool_success
        metrics.evidence_total = tool_total

        # 从 final answer 和 ai_message 内容提取层级、置信度、runbook
        final_text = ""
        all_ai_text = ""
        for ev in events:
            if ev.get("type") == "final":
                final_text = ev.get("answer", "") or ""
            elif ev.get("type") == "ai_message":
                all_ai_text += (ev.get("content", "") or "") + "\n"

        combined_text = final_text + "\n" + all_ai_text

        # 层级提取
        layer_match = self._LAYER_PATTERN.search(final_text)
        if not layer_match:
            layer_match = self._LAYER_PATTERN.search(all_ai_text)
        if layer_match:
            metrics.layer = layer_match.group(1)
            metrics.layer_name = LAYER_NAMES.get(metrics.layer, "")
            metrics.is_diagnosis = metrics.layer != "QUERY"
        else:
            # 通过问题关键词判断是否为诊断场景
            diag_keywords = ["故障", "异常", "报错", "重启", "crash", "oom", "error", "问题", "排查", "诊断", "为什么"]
            metrics.is_diagnosis = any(kw in question.lower() for kw in diag_keywords)

        # 置信度提取
        for pattern in self._CONFIDENCE_PATTERNS:
            match = pattern.search(combined_text)
            if match:
                val = float(match.group(1))
                if val > 1.0:
                    val = val / 100.0
                if 0 < val <= 1.0:
                    metrics.confidence_score = val
                    break

        # Runbook 提取
        runbook_set = set()
        for match in self._RUNBOOK_PATTERN.finditer(combined_text):
            name = match.group(0)
            if name not in ("README.md",):  # 排除非 runbook 文件
                runbook_set.add(name)
        metrics.runbooks_referenced = sorted(runbook_set)

        # 置信度标签
        if metrics.confidence_score >= 0.85:
            metrics.confidence_label = "高"
        elif metrics.confidence_score >= 0.7:
            metrics.confidence_label = "中"
        elif metrics.confidence_score > 0:
            metrics.confidence_label = "低"

        return metrics
