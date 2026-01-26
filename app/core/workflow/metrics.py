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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class NodeMetrics:
    """单个节点的执行指标"""
    node_id: str
    node_name: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    llm_calls: int = 0
    llm_duration_ms: float = 0.0
    tool_calls: int = 0
    tool_duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def finish(self):
        """标记节点完成，计算耗时"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000


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
    root_cause_confidence: float = 0.0
    
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
    
    def finish_node(self, node_id: str, success: bool = True, error: str = None):
        """完成节点执行记录"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.finish()
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
        """MTTR 是否达标 (< 10m = 600s)"""
        return self.mttr_seconds < 600
    
    @property
    def evidence_completeness(self) -> float:
        """证据完整率"""
        if self.evidence_planned == 0:
            return 0.0
        return self.evidence_collected / self.evidence_planned
    
    @property
    def evidence_completeness_pass(self) -> bool:
        """证据完整率是否达标 (> 90%)"""
        return self.evidence_completeness > 0.9
    
    @property
    def root_cause_accuracy_pass(self) -> bool:
        """根因准确率是否达标 (>= 80%)"""
        return self.root_cause_confidence >= 0.8
    
    @property
    def runbook_coverage_pass(self) -> bool:
        """Runbook 覆盖率是否达标"""
        return self.runbook_matched
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "run_id": self.run_id,
            "mttr": {
                "value": self.mttr_formatted,
                "seconds": self.mttr_seconds,
                "pass": self.mttr_pass,
                "threshold": "< 10m"
            },
            "evidence_completeness": {
                "value": f"{self.evidence_completeness:.0%}",
                "collected": self.evidence_collected,
                "planned": self.evidence_planned,
                "pass": self.evidence_completeness_pass,
                "threshold": "> 90%"
            },
            "root_cause_confidence": {
                "value": f"{self.root_cause_confidence:.0%}",
                "pass": self.root_cause_accuracy_pass,
                "threshold": ">= 80%"
            },
            "runbook_coverage": {
                "matched": self.runbook_matched,
                "runbook_id": self.runbook_id,
                "pass": self.runbook_coverage_pass,
                "threshold": "> 90%"
            },
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
        else:
            minutes = int(total_s // 60)
            seconds = total_s % 60
            total_str = f"{minutes}m {seconds:.1f}s"
        
        lines.append("```")
        lines.append(f"├─ 总耗时: {total_str}")
        
        # 各节点耗时
        for node_id, node in self.nodes.items():
            node_s = node.duration_ms / 1000
            pct = (node.duration_ms / self.total_duration_ms * 100) if self.total_duration_ms > 0 else 0
            status = "✅" if node.success else "❌"
            lines.append(f"├─ {node.node_name}: {node_s:.1f}s ({pct:.1f}%) {status}")
        
        # LLM 统计
        llm_s = self.total_llm_duration_ms / 1000
        llm_pct = (self.total_llm_duration_ms / self.total_duration_ms * 100) if self.total_duration_ms > 0 else 0
        lines.append(f"├─ LLM 调用: {llm_s:.1f}s ({llm_pct:.1f}%) - {self.total_llm_calls} 次")
        
        # 工具调用统计
        tool_s = self.total_tool_duration_ms / 1000
        tool_pct = (self.total_tool_duration_ms / self.total_duration_ms * 100) if self.total_duration_ms > 0 else 0
        lines.append(f"└─ 工具调用: {tool_s:.1f}s ({tool_pct:.1f}%) - {self.total_tool_calls} 次")
        lines.append("```")
        lines.append("")
        
        return "\n".join(lines)
    
    def format_metrics_block(self) -> str:
        """格式化指标达标情况（用于输出）"""
        lines = []
        lines.append("## 📈 质量指标")
        lines.append("")
        lines.append("| 指标 | 要求 | 实际 | 状态 |")
        lines.append("|------|------|------|------|")
        
        # MTTR
        mttr_status = "✅ 达标" if self.mttr_pass else "❌ 未达标"
        lines.append(f"| **MTTR** | < 10m | {self.mttr_formatted} | {mttr_status} |")
        
        # 根因准确率
        rca_status = "✅ 达标" if self.root_cause_accuracy_pass else "⚠️ 待验证"
        lines.append(f"| **根因置信度** | >= 80% | {self.root_cause_confidence:.0%} | {rca_status} |")
        
        # 证据完整率
        ev_status = "✅ 达标" if self.evidence_completeness_pass else "⚠️ 不足"
        lines.append(f"| **证据完整率** | > 90% | {self.evidence_completeness:.0%} ({self.evidence_collected}/{self.evidence_planned}) | {ev_status} |")
        
        # Runbook 覆盖
        rb_status = "✅ 已匹配" if self.runbook_matched else "⚠️ 未匹配"
        rb_value = self.runbook_id if self.runbook_id else "-"
        lines.append(f"| **Runbook 覆盖** | 匹配 | {rb_value} | {rb_status} |")
        
        lines.append("")
        
        return "\n".join(lines)


# 全局指标存储（用于跨模块访问）
_current_metrics: Optional[WorkflowMetrics] = None


def start_workflow_metrics(run_id: str, question: str = "") -> WorkflowMetrics:
    """开始工作流指标记录"""
    global _current_metrics
    _current_metrics = WorkflowMetrics(run_id=run_id, question=question)
    return _current_metrics


def get_current_metrics() -> Optional[WorkflowMetrics]:
    """获取当前工作流指标"""
    return _current_metrics


def finish_workflow_metrics() -> Optional[WorkflowMetrics]:
    """完成工作流指标记录"""
    global _current_metrics
    if _current_metrics:
        _current_metrics.finish()
        return _current_metrics
    return None
