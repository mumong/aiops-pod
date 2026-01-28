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

    def _emit(self, text: str) -> str:
        """发出带换行的文本"""
        return text + "\n"

    def _draw_box(self, title: str) -> Generator[str, None, None]:
        """绘制 ASCII 边框"""
        width = 50
        line = "─" * width
        yield self._emit("┌" + line + "┐")
        padding = (width - len(title) - 4) // 2
        title_with_padding = " " * padding + title + " " * padding
        yield self._emit("│" + title_with_padding + "│")
        yield self._emit("└" + line + "┘")

    def _format_header(self) -> Generator[str, None, None]:
        """格式化报告头部"""
        yield self._emit("=" * 70)
        yield self._emit("🔄 K8s AIOps Copilot - 工作流诊断模式")
        yield self._emit("=" * 70)
        yield self._emit("")

        if self.show_intermediate:
            yield self._emit(f"📝 问题: {self.ctx.question[:100] if len(self.ctx.question) > 100 else self.ctx.question}")

    def _format_final_report(self) -> Generator[str, None, None]:
        """格式化最终诊断报告"""
        # 只显示最终 LLM 响应，不显示中间节点分析
        yield self._emit("=" * 70)
        yield self._emit("🎯 诊断报告")
        yield self._emit("=" * 70)
        yield self._emit("")

        # 输出最终 LLM 响应
        conclusion = self.ctx.final_answer or ""
        if conclusion:
            yield self._emit(conclusion)

    def _format_metrics(self) -> Generator[str, None, None]:
        """格式化质量指标"""
        if not self.ctx.metrics_data:
            return

        yield self._emit("-" * 70)
        yield self._emit("📈 质量指标")
        yield self._emit("-" * 70)
        yield self._emit("")

        mttr = self.ctx.metrics_data.get("mttr", {})
        evidence = self.ctx.metrics_data.get("evidence_completeness", {})
        rca = self.ctx.metrics_data.get("root_cause_confidence", {})
        runbook = self.ctx.metrics_data.get("runbook_coverage", {})

        mttr_pass = "✅" if mttr.get("pass") else "❌"
        evidence_pass = "✅" if evidence.get("pass") else "⚠️"
        rca_pass = "✅" if rca.get("pass") else "⚠️"
        runbook_pass = "✅" if runbook.get("pass") else "⚠️"

        yield self._emit(f"  MTTR:        {mttr.get('value', '?')} {mttr_pass} (要求 < 10m)")
        yield self._emit(f"  根因置信度: {rca.get('value', '?')} {rca_pass} (要求 >= 80%)")
        yield self._emit(f"  证据完整率: {evidence.get('value', '?')} {evidence_pass} (要求 > 80%)")

        if runbook.get('matched'):
            runbook_id = runbook.get('id', '')
            yield self._emit(f"  Runbook:    已匹配 {runbook_pass}")
            if runbook_id:
                runbook_names = [name.replace('.md', '') for name in runbook_id.split(', ')]
                yield self._emit(f"    使用的Runbook: {', '.join(runbook_names)}")
        else:
            yield self._emit(f"  Runbook:    未匹配 {runbook_pass}")

        yield self._emit("")

    def _format_footer(self) -> Generator[str, None, None]:
        """格式化报告尾部"""
        yield self._emit("=" * 70)
        yield self._emit("✅ 诊断完成!")
        yield self._emit("=" * 70)
        yield self._emit("")

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
                yield self._emit(f"📍 [{node_name}] 执行中...")

            elif event_type == "node_complete":
                self._handle_node_complete(event)

            elif event_type == "final":
                self.ctx.final_answer = event.get("answer", "")
                self.ctx.metrics_data = event.get("metrics", {})
                self.ctx.total_elapsed = event.get("elapsed_seconds", 0)

            elif event_type == "error":
                error = event.get("error", "未知错误")
                yield self._emit(f"❌ 错误: {error}")

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

        yield self._emit(f"   ✅ [{node_name}] 完成 ({format_duration(duration)})")
        yield self._emit("")

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
