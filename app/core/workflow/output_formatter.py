"""
工作流输出格式化器

职责：
- 将工作流执行结果转换为人类可读的格式
- 统一管理输出格式，避免重复代码
- 支持控制是否显示中间节点分析

设计原则：
- 单一职责：只负责格式化，不负责业务逻辑
- 可配置：通过参数控制输出内容
"""

import json
import logging
from typing import Generator, Dict, Any, Optional
from dataclasses import dataclass

from app.core.holmes.streaming import format_duration
from app.core.text_helpers import truncate_question, emit_text

logger = logging.getLogger(__name__)


@dataclass
class NodeOutputs:
    """收集各节点的完整输出"""
    layer: str = ""
    evidence: str = ""
    rca: str = ""
    conclusion: str = ""


@dataclass
class WorkflowContext:
    """工作流上下文"""
    question: str = ""
    run_id: str = ""
    node_outputs: Optional[NodeOutputs] = None
    total_elapsed: float = 0
    metrics_data: Optional[Dict] = None
    final_answer: str = ""


class WorkflowOutputFormatter:
    """
    工作流输出格式化器

    职责：
    - 格式化工作流执行过程（实时输出）
    - 格式化最终诊断报告
    - 统一管理输出格式，避免重复代码
    - 支持控制是否显示中间节点分析
    """

    def __init__(self, show_intermediate: bool = False):
        """
        初始化格式化器

        Args:
            show_intermediate: 是否显示中间节点的完整分析（默认 True）
                              False = 只显示最终 LLM 响应
        """
        self.show_intermediate = show_intermediate
        self._section_count = 0

    def _format_header(self) -> Generator[str, None, None]:
        """格式化报告头部"""
        yield emit_text("=" * 70)
        yield emit_text("🔄 K8s AIOps Copilot - 工作流诊断模式")
        yield emit_text("=" * 70)
        yield emit_text("")

        if self.show_intermediate:
            yield emit_text(f"📝 问题: {truncate_question(self.ctx.question)}")

    def _format_final_report(self) -> Generator[str, None, None]:
        """格式化最终诊断报告"""
        # 只显示最终 LLM 响应，不显示中间节点分析
        yield emit_text("=" * 70)
        yield emit_text("🎯 诊断报告")
        yield emit_text("=" * 70)
        yield emit_text("")

        # 输出最终 LLM 响应
        conclusion = self.ctx.final_answer or ""
        if conclusion:
            yield emit_text(conclusion)

    def _format_metrics(self) -> Generator[str, None, None]:
        """格式化质量指标"""
        if not self.ctx.metrics_data:
            return

        yield emit_text("-" * 70)
        yield emit_text("📈 质量指标")
        yield emit_text("-" * 70)
        yield emit_text("")

        mttr = self.ctx.metrics_data.get("mttr", {})
        evidence = self.ctx.metrics_data.get("evidence_completeness", {})
        rca = self.ctx.metrics_data.get("root_cause_confidence", {})
        runbook = self.ctx.metrics_data.get("runbook_coverage", {})

        mttr_pass = "✅" if mttr.get("pass") else "❌"
        evidence_pass = "✅" if evidence.get("pass") else "⚠️"
        rca_pass = "✅" if rca.get("pass") else "⚠️"
        runbook_pass = "✅" if runbook.get("pass") else "⚠️"

        # 使用配置化阈值显示
        from app.core.workflow.metrics import (
            MTTR_THRESHOLD_SECONDS,
            ROOT_CAUSE_CONFIDENCE_THRESHOLD,
            EVIDENCE_COMPLETENESS_THRESHOLD,
        )
        mttr_threshold_str = f"< {MTTR_THRESHOLD_SECONDS // 60}m"
        rca_threshold_str = f">= {int(ROOT_CAUSE_CONFIDENCE_THRESHOLD * 100)}%"
        ev_threshold_str = f"> {int(EVIDENCE_COMPLETENESS_THRESHOLD * 100)}%"

        yield emit_text(f"  MTTR:        {mttr.get('value', '?')} {mttr_pass} (要求 {mttr_threshold_str})")
        yield emit_text(f"  根因置信度: {rca.get('value', '?')} {rca_pass} (要求 {rca_threshold_str})")
        yield emit_text(f"  证据完整率: {evidence.get('value', '?')} {evidence_pass} (要求 {ev_threshold_str})")

        if runbook.get('matched'):
            runbook_id = runbook.get('id', '')
            yield emit_text(f"  Runbook:    已匹配 {runbook_pass}")
            if runbook_id:
                runbook_names = [name.replace('.md', '') for name in runbook_id.split(', ')]
                yield emit_text(f"    使用的Runbook: {', '.join(runbook_names)}")
        else:
            yield emit_text(f"  Runbook:    未匹配 {runbook_pass}")

        yield emit_text("")

    def _format_footer(self) -> Generator[str, None, None]:
        """格式化报告尾部"""
        yield emit_text("=" * 70)
        yield emit_text("✅ 诊断完成!")
        yield emit_text("=" * 70)
        yield emit_text("")

    def format_workflow_text(self, events: list, question: str, show_intermediate: bool = True) -> Generator[str, None, None]:
        """
        将工作流执行事件格式化为文本输出

        Args:
            events: 工作流事件列表
            question: 用户问题
            show_intermediate: 是否显示中间节点分析（默认 True）

        Yields:
            格式化后的文本行
        """
        # 初始化上下文
        self.ctx = WorkflowContext(question=question)

        # 格式化头部
        yield from self._format_header()

        # 处理事件流
        for event in events:
            event_type = event.get("type", "unknown")

            if event_type == "run_start":
                self.ctx.run_id = event.get("run_id", "?")

            elif event_type == "node_start":
                node_name = event.get("node_name", event.get("node", "?"))
                yield emit_text(f"📍 [{node_name}] 执行中...")

            elif event_type == "node_complete":
                yield from self._handle_node_complete(event)

            elif event_type == "final":
                self.ctx.final_answer = event.get("answer", "")
                self.ctx.metrics_data = event.get("metrics", {})
                self.ctx.total_elapsed = event.get("elapsed_seconds", 0)

            elif event_type == "error":
                error = event.get("error", "未知错误")
                yield emit_text(f"❌ 错误: {error}")

        # 格式化最终报告
        yield from self._format_final_report()

        # 格式化指标
        yield from self._format_metrics()

        # 格式化尾部
        yield from self._format_footer()

    def _handle_node_complete(self, event: Dict[str, Any]):
        """处理节点完成事件"""
        node_id = event.get("node", "")
        node_name = event.get("node_name", event.get("node", "?"))
        duration = event.get("duration_seconds", 0)
        snapshot = event.get("state_snapshot", {})

        yield emit_text(f"   ✅ [{node_name}] 完成 ({format_duration(duration)})")
        yield emit_text("")

        # 只在需要显示中间节点时保存
        if self.show_intermediate:
            if node_id == "layer":
                self.ctx.node_outputs.layer = snapshot.get("layer_analysis", "")
            elif node_id == "evidence":
                self.ctx.node_outputs.evidence = snapshot.get("evidence_analysis", "")
            elif node_id == "rca":
                self.ctx.node_outputs.rca = snapshot.get("rca_analysis", "")


def format_workflow_text(events: list, question: str, show_intermediate: bool = True) -> Generator[str, None, None]:
    """
    便捷函数：创建格式化器并格式化工作流文本

    Args:
        events: 工作流事件列表
        question: 用户问题
        show_intermediate: 是否显示中间节点分析（默认 True）

    Yields:
        格式化后的文本行
    """
    formatter = WorkflowOutputFormatter(show_intermediate=show_intermediate)
    yield from formatter.format_workflow_text(events, question, show_intermediate)
