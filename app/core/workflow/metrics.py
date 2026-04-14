"""
工作流性能指标和统计

指标要求：
- MTTR（Mean Time To Resolution）: < 10m
- 一次命中率/根因准确率: >= 80%
- 证据完整率: > 90%
- Runbook 覆盖率: > 90%

设计原则：
- 低侵入性：不影响主流程
- 可扩展：方便添加新指标
- 可观测：提供详细的性能分析
"""

import time
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# 指标阈值配置（可从环境变量 / config.yaml 覆盖）
# ============================================================================

# 运行时由 load_metrics_config() 设置，初始值为默认值
MTTR_THRESHOLD_SECONDS = float(os.getenv("METRICS_MTTR_THRESHOLD", "600"))  # 600s = 10m
ROOT_CAUSE_CONFIDENCE_THRESHOLD = float(os.getenv("METRICS_RCA_CONFIDENCE_THRESHOLD", "0.8"))
EVIDENCE_COMPLETENESS_THRESHOLD = float(os.getenv("METRICS_EVIDENCE_THRESHOLD", "0.9"))
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() not in ("false", "0", "no")


def load_metrics_config(config: Optional[Dict] = None):
    """从 config.yaml 的 metrics 块加载阈值（环境变量优先）"""
    global MTTR_THRESHOLD_SECONDS, ROOT_CAUSE_CONFIDENCE_THRESHOLD, EVIDENCE_COMPLETENESS_THRESHOLD, METRICS_ENABLED
    if not config:
        return
    # enabled 开关
    if not os.getenv("METRICS_ENABLED") and "enabled" in config:
        METRICS_ENABLED = bool(config["enabled"])
    thresholds = config.get("thresholds", {})
    if not os.getenv("METRICS_MTTR_THRESHOLD") and "mttr_seconds" in thresholds:
        MTTR_THRESHOLD_SECONDS = float(thresholds["mttr_seconds"])
    if not os.getenv("METRICS_RCA_CONFIDENCE_THRESHOLD") and "rca_confidence" in thresholds:
        ROOT_CAUSE_CONFIDENCE_THRESHOLD = float(thresholds["rca_confidence"])
    if not os.getenv("METRICS_EVIDENCE_THRESHOLD") and "evidence_completeness" in thresholds:
        EVIDENCE_COMPLETENESS_THRESHOLD = float(thresholds["evidence_completeness"])
    logger.info(
        f"📊 指标阈值: MTTR<{MTTR_THRESHOLD_SECONDS}s, "
        f"RCA>={ROOT_CAUSE_CONFIDENCE_THRESHOLD:.0%}, "
        f"Evidence>{EVIDENCE_COMPLETENESS_THRESHOLD:.0%}, "
        f"Enabled={METRICS_ENABLED}"
    )


@dataclass
class NodeMetrics:
    """单个节点的执行指标"""
    node_id: str
    node_name: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    _finished: bool = False  # 内部标记：是否已完成
    llm_calls: int = 0
    llm_duration_ms: float = 0.0
    tool_calls: int = 0
    tool_duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None

    def finish(self, end_ts: float = 0.0):
        """标记节点完成，计算耗时（只执行一次）

        Args:
            end_ts: 精确结束时间戳（0 则用 time.time()）
        """
        if self._finished:
            return  # 已完成，跳过

        self.end_time = end_ts if end_ts > 0 else time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self._finished = True


@dataclass
class WorkflowMetrics:
    """工作流整体指标"""
    run_id: str
    question: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    
    # 各阶段耗时
    init_duration_ms: float = 0.0
    nodes: Dict[str, NodeMetrics] = field(default_factory=dict)
    
    # LLM 调用统计
    total_llm_calls: int = 0
    total_llm_duration_ms: float = 0.0
    
    # 工具调用统计
    total_tool_calls: int = 0
    total_tool_duration_ms: float = 0.0
    tool_call_details: List[Dict] = field(default_factory=list)
    
    # 核心指标
    evidence_collected: int = 0
    evidence_planned: int = 0
    runbook_matched: bool = False
    runbook_id: Optional[str] = None
    primary_runbook: Optional[str] = None  # 核心参考 Runbook（与诊断结论强相关）
    root_cause_confidence: float = 0.0

    # 评分明细（可解释性）
    confidence_breakdown: List[Dict] = field(default_factory=list)
    confidence_penalties: List[Dict] = field(default_factory=list)
    confidence_weighted_total: float = 0.0
    confidence_fallback_applied: bool = False
    evidence_breakdown: Dict = field(default_factory=dict)
    evidence_details: List[Dict] = field(default_factory=list)  # 每项证据的名称+状态

    # Runbook 覆盖率明细
    runbook_coverage_score: float = 0.0       # 最终覆盖率 [0, 1]
    runbook_coverage_breakdown: List[Dict] = field(default_factory=list)

    # 多场景指标
    detected_scenarios_count: int = 0  # 检测到的场景总数

    # 最终状态
    success: bool = True
    errors: List[str] = field(default_factory=list)
    
    def start_node(self, node_id: str, node_name: str) -> NodeMetrics:
        """开始记录节点执行"""
        node = NodeMetrics(
            node_id=node_id,
            node_name=node_name,
            start_time=time.time()
        )
        self.nodes[node_id] = node
        return node
    
    def finish_node(self, node_id: str, success: bool = True, error: str = None, end_ts: float = 0.0):
        """完成节点执行记录（只处理未完成的节点）

        Args:
            end_ts: 精确结束时间戳（0 则由 NodeMetrics.finish() 自动取 time.time()）
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # 只处理未完成的节点，避免重复
            if not node._finished:
                node.finish(end_ts=end_ts)
                node.success = success
                node.error = error
                if not success and error:
                    self.errors.append(f"[{node_id}] {error}")
    
    def record_llm_call(self, node_id: str, duration_ms: float):
        """记录 LLM 调用"""
        self.total_llm_calls += 1
        self.total_llm_duration_ms += duration_ms
        if node_id in self.nodes:
            self.nodes[node_id].llm_calls += 1
            self.nodes[node_id].llm_duration_ms += duration_ms
    
    def record_tool_call(self, tool_name: str, duration_ms: float, success: bool = True):
        """记录工具调用"""
        self.total_tool_calls += 1
        self.total_tool_duration_ms += duration_ms
        self.tool_call_details.append({
            "tool": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": time.time()
        })
    
    def finish(self):
        """完成整个工作流，计算最终指标"""
        self.end_time = time.time()
    
    @property
    def total_duration_ms(self) -> float:
        """总耗时（毫秒）"""
        if self.end_time > 0:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000
    
    @property
    def total_duration_seconds(self) -> float:
        """总耗时（秒）"""
        return self.total_duration_ms / 1000
    
    @property
    def mttr_seconds(self) -> float:
        """MTTR（从开始到输出方案的时间，秒）"""
        return self.total_duration_seconds
    
    @property
    def mttr_formatted(self) -> str:
        """格式化的 MTTR"""
        seconds = self.mttr_seconds
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @property
    def mttr_pass(self) -> bool:
        """MTTR 是否达标（使用配置阈值）"""
        return self.mttr_seconds < MTTR_THRESHOLD_SECONDS

    @property
    def evidence_completeness(self) -> float:
        """证据完整率"""
        if self.evidence_planned == 0:
            return 0.0
        return self.evidence_collected / self.evidence_planned

    @property
    def evidence_completeness_pass(self) -> bool:
        """证据完整率是否达标（使用配置阈值）"""
        return self.evidence_completeness > EVIDENCE_COMPLETENESS_THRESHOLD

    @property
    def root_cause_accuracy_pass(self) -> bool:
        """根因准确率是否达标（使用配置阈值）"""
        return self.root_cause_confidence >= ROOT_CAUSE_CONFIDENCE_THRESHOLD
    
    @property
    def runbook_coverage_pass(self) -> bool:
        """Runbook 覆盖率是否达标（>= 80%）"""
        return self.runbook_coverage_score >= 0.80
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        # 格式化阈值显示
        mttr_threshold_str = f"< {MTTR_THRESHOLD_SECONDS // 60}m"
        rca_threshold_str = f">= {int(ROOT_CAUSE_CONFIDENCE_THRESHOLD * 100)}%"
        ev_threshold_str = f"> {int(EVIDENCE_COMPLETENESS_THRESHOLD * 100)}%"

        return {
            "run_id": self.run_id,
            "mttr": {
                "value": self.mttr_formatted,
                "seconds": self.mttr_seconds,
                "pass": self.mttr_pass,
                "threshold": mttr_threshold_str
            },
            "evidence_completeness": {
                "value": f"{self.evidence_completeness:.0%}",
                "collected": self.evidence_collected,
                "planned": self.evidence_planned,
                "pass": self.evidence_completeness_pass,
                "threshold": ev_threshold_str
            },
            "root_cause_confidence": {
                "value": f"{self.root_cause_confidence:.0%}",
                "pass": self.root_cause_accuracy_pass,
                "threshold": rca_threshold_str
            },
            "runbook_coverage": {
                "matched": self.runbook_matched,
                "runbook_id": self.runbook_id,
                "pass": self.runbook_coverage_pass,
                "score": self.runbook_coverage_score,
                "breakdown": self.runbook_coverage_breakdown,
            },
            "confidence_breakdown": self.confidence_breakdown,
            "confidence_penalties": self.confidence_penalties,
            "evidence_breakdown": self.evidence_breakdown,
            "performance": {
                "total_duration_ms": self.total_duration_ms,
                "llm_calls": self.total_llm_calls,
                "llm_duration_ms": self.total_llm_duration_ms,
                "tool_calls": self.total_tool_calls,
                "tool_duration_ms": self.total_tool_duration_ms,
            },
            "nodes": {
                node_id: {
                    "name": node.node_name,
                    "duration_ms": node.duration_ms,
                    "success": node.success
                }
                for node_id, node in self.nodes.items()
            },
            "success": self.success,
            "errors": self.errors
        }
    
    def format_stats_block(self) -> str:
        """格式化性能统计块（用于输出）"""
        lines = []
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 📊 性能统计")
        lines.append("")

        # 总耗时
        total_s = self.total_duration_seconds
        if total_s < 60:
            total_str = f"{total_s:.1f}s"
        elif total_s < 3600:
            total_str = f"{total_s / 60:.1f}m"
        else:
            total_str = f"{total_s / 3600:.1f}h"

        lines.append(f"├─ 总耗时: {total_str}")

        # 各节点耗时（百分比以总耗时为分母，加起来≈100%）
        total_ms = self.total_duration_seconds * 1000
        for node_id, node in self.nodes.items():
            node_s = node.duration_ms / 1000
            node_pct = (node.duration_ms / total_ms * 100) if total_ms > 0 else 0
            status = "✅" if node.success else "❌"
            lines.append(f"├─ {node.node_name}: {node_s:.1f}s ({node_pct:.0f}%) {status}")

        # LLM 和工具调用次数（简洁，不显示百分比）
        lines.append(f"├─ LLM 调用: {self.total_llm_calls} 次")
        lines.append(f"└─ 工具调用: {self.total_tool_calls} 次")
        lines.append("```")
        lines.append("")

        return "\n".join(lines)
    
    def format_metrics_block(self, enabled: bool = True) -> str:
        """格式化指标达标情况（用于输出）

        Args:
            enabled: 是否显示完整质量指标。False 时只输出诊断追踪部分。
        """
        lines = []

        if enabled:
            lines.append("## 📈 质量指标")
            lines.append("")
            lines.append("| 指标 | 要求 | 实际 | 状态 |")
            lines.append("|------|------|------|------|")

            # 格式化阈值显示
            mttr_threshold_str = f"< {MTTR_THRESHOLD_SECONDS // 60}m"
            rca_threshold_str = f">= {int(ROOT_CAUSE_CONFIDENCE_THRESHOLD * 100)}%"
            ev_threshold_str = f"> {int(EVIDENCE_COMPLETENESS_THRESHOLD * 100)}%"

            # MTTR
            mttr_status = "✅ 达标" if self.mttr_pass else "❌ 未达标"
            lines.append(f"| **MTTR** | {mttr_threshold_str} | {self.mttr_formatted} | {mttr_status} |")

            # 根因准确率
            rca_status = "✅ 达标" if self.root_cause_accuracy_pass else "⚠️ 待验证"
            lines.append(f"| **根因置信度** | {rca_threshold_str} | {self.root_cause_confidence:.0%} | {rca_status} |")

            # 证据完整率
            ev_status = "✅ 达标" if self.evidence_completeness_pass else "⚠️ 不足"
            lines.append(f"| **证据完整率** | {ev_threshold_str} | {self.evidence_completeness:.0%} ({self.evidence_collected}/{self.evidence_planned}) | {ev_status} |")

            # Runbook 覆盖率
            rb_status = "✅ 达标" if self.runbook_coverage_pass else "⚠️ 不足"
            lines.append(f"| **Runbook 覆盖率** | >= 80% | {self.runbook_coverage_score:.0%} | {rb_status} |")

            lines.append("")

            # 评分明细（可解释性）
            if self.confidence_breakdown:
                lines.append("📊 置信度评分明细")
                lines.append("")
                for i, dim in enumerate(self.confidence_breakdown):
                    prefix = "├─" if i < len(self.confidence_breakdown) - 1 or self.confidence_penalties else "└─"
                    lines.append(
                        f"  {prefix} {dim.get('description', dim.get('name', ''))}: "
                        f"{dim.get('score', 0):.0%} (权重 {dim.get('weight', 0):.0%}) "
                        f"→ 贡献 {dim.get('weighted_score', 0):.1%}"
                    )
                for i, p in enumerate(self.confidence_penalties):
                    prefix = "└─" if i == len(self.confidence_penalties) - 1 else "├─"
                    lines.append(f"  {prefix} 惩罚 {p.get('name', '')}: -{p.get('value', 0):.0%} ({p.get('reason', '')})")
                lines.append("")

            # 证据明细
            if self.evidence_breakdown and self.evidence_breakdown.get("breakdown"):
                lines.append("📊 证据完整率明细")
                lines.append("")
                breakdown = self.evidence_breakdown["breakdown"]
                items = list(breakdown.items())
                for i, (level, stats) in enumerate(items):
                    prefix = "└─" if i == len(items) - 1 else "├─"
                    lines.append(
                        f"  {prefix} {level}: {stats['collected']}/{stats['total']} "
                        f"(权重 {stats['weight']}) → {stats['rate']:.0%}"
                    )
                lines.append("")

            # 证据采集清单（每项证据的名称和状态）
            if self.evidence_details:
                lines.append("📋 证据采集清单")
                lines.append("")
                lines.append("| # | 证据项 | 级别 | 状态 |")
                lines.append("|---|--------|------|------|")
                for i, ev in enumerate(self.evidence_details):
                    status_icon = "✅" if ev.get("collected") else "❌"
                    lines.append(
                        f"| {i+1} | {ev.get('description', '未知')} | "
                        f"{ev.get('level', 'IMPORTANT')} | {status_icon} |"
                    )
                lines.append("")

            # Runbook 覆盖率明细
            if self.runbook_coverage_breakdown:
                lines.append("📊 Runbook 覆盖率明细")
                lines.append("")
                for i, dim in enumerate(self.runbook_coverage_breakdown):
                    prefix = "└─" if i == len(self.runbook_coverage_breakdown) - 1 else "├─"
                    lines.append(
                        f"  {prefix} {dim.get('description', '')}: "
                        f"{dim.get('score', 0):.0%} (权重 {dim.get('weight', 0):.0%}) "
                        f"→ 贡献 {dim.get('weighted_score', 0):.1%}"
                    )
                lines.append("")

        # 诊断追踪（始终输出）
        lines.append("📋 诊断追踪")
        lines.append("")
        if self.primary_runbook:
            lines.append(f"- **核心 Runbook**: {self.primary_runbook}")
        runbook_display = self.runbook_id if self.runbook_matched and self.runbook_id else "无"
        lines.append(f"- **参考 Runbook**: {runbook_display}")
        lines.append(f"- **工具调用**: {self.total_tool_calls} 次")
        lines.append(f"- **LLM 调用**: {self.total_llm_calls} 次")
        lines.append("")

        return "\n".join(lines)


# ── 以下全局函数已废弃，保留向后兼容 ──
# 新代码请直接使用 WorkflowMetrics(run_id=..., question=...) 实例
import warnings

_current_metrics: Optional[WorkflowMetrics] = None


def start_workflow_metrics(run_id: str, question: str = "") -> WorkflowMetrics:
    """[deprecated] 开始工作流指标记录 — 请改用 WorkflowMetrics() 实例"""
    warnings.warn(
        "start_workflow_metrics() is deprecated, use WorkflowMetrics() directly",
        DeprecationWarning, stacklevel=2,
    )
    global _current_metrics
    _current_metrics = WorkflowMetrics(run_id=run_id, question=question)
    return _current_metrics


def get_current_metrics() -> Optional[WorkflowMetrics]:
    """[deprecated] 获取当前工作流指标"""
    warnings.warn(
        "get_current_metrics() is deprecated",
        DeprecationWarning, stacklevel=2,
    )
    return _current_metrics


def finish_workflow_metrics() -> Optional[WorkflowMetrics]:
    """[deprecated] 完成工作流指标记录 — 请改用 metrics.finish()"""
    warnings.warn(
        "finish_workflow_metrics() is deprecated, use metrics.finish() directly",
        DeprecationWarning, stacklevel=2,
    )
    global _current_metrics
    if _current_metrics:
        _current_metrics.finish()
        return _current_metrics
    return None
