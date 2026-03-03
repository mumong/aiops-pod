"""
多场景工作流

职责：
- 提供多场景诊断的完整流程
- 与现有 service.py 集成
- 支持作为工作流模式使用

设计原则：
- 保持与现有工作流的一致性
- 模块化设计，易于扩展
"""

import logging
import os
from typing import Generator, Dict, Any, Optional
from datetime import datetime

from app.core.workflow.state import WorkflowState
from app.core.workflow.nodes.global_detector import GlobalDetectorNode
from app.core.workflow.multi_scenario.output import MultiScenarioOutput, ScenarioSeverity
from app.core.workflow.multi_scenario.formatters import MultiScenarioFormatter
from app.core.workflow.metrics import WorkflowMetrics, start_workflow_metrics, finish_workflow_metrics
from app.core.text_helpers import truncate_question, emit_text

logger = logging.getLogger(__name__)


class MultiScenarioWorkflowExecutor:
    """
    多场景工作流执行器

    提供完整的多场景诊断流程
    """

    def __init__(self, holmes_service: Any = None):
        """
        初始化执行器

        Args:
            holmes_service: HolmesService 实例（用于工具调用）
        """
        self.holmes_service = holmes_service

        # 创建全局检测器节点
        self.detector_node = GlobalDetectorNode(holmes_service)

        # 创建格式化器
        self.formatter = MultiScenarioFormatter()

    def execute_stream(
        self,
        question: str,
        run_id: Optional[str] = None,
        output_format: str = "text"
    ) -> Generator[str, None, None]:
        """
        执行多场景诊断（流式输出）

        Args:
            question: 用户问题
            run_id: 运行 ID（可选）
            output_format: 输出格式 - "text"=易读纯文本, "sse"=JSON格式SSE事件

        Yields:
            格式化的事件字符串
        """
        if run_id is None:
            import uuid
            run_id = uuid.uuid4().hex[:16]

        # 开始指标记录
        metrics = start_workflow_metrics(run_id, question)

        try:
            # 输出格式：终端友好或 SSE
            if output_format == "text":
                yield from self._workflow_to_text(question, run_id, metrics)
            else:
                yield from self._workflow_to_sse(question, run_id, metrics)

        except Exception as e:
            logger.error(f"❌ 多场景工作流执行失败: {e}", exc_info=True)
            if output_format == "text":
                yield emit_text(f"❌ 多场景工作流执行失败: {e}")
            else:
                yield self._create_sse_message("error", {
                    "error": f"多场景工作流执行失败: {str(e)}"
                })

    def _workflow_to_text(
        self,
        question: str,
        run_id: str,
        metrics: WorkflowMetrics
    ) -> Generator[str, None, None]:
        """
        工作流执行结果转换为美观的文本格式
        """
        yield emit_text("=" * 70)
        yield emit_text("🔍 K8s 多场景诊断模式")
        yield emit_text("=" * 70)
        yield emit_text("")
        yield emit_text(f"📝 问题: {truncate_question(question)}")
        yield emit_text("")
        yield emit_text("-" * 70)
        yield emit_text("")

        # 执行检测
        initial_state = WorkflowState(
            question=question,
            run_id=run_id,
        )

        final_state = initial_state.copy()
        detected_scenarios = []

        for event in self.detector_node.execute(initial_state):
            # 检查是否是最终状态更新
            if "detected_scenarios" in event:
                detected_scenarios = event["detected_scenarios"]
            final_state.update(event)

        # 生成报告
        if detected_scenarios:
            # 创建多场景输出对象
            multi_output = MultiScenarioOutput()
            for scenario_data in detected_scenarios:
                multi_output.add_scenario(ScenarioDecision(**scenario_data))

            # 更新指标
            metrics.detected_scenarios_count = len(detected_scenarios)
            metrics.finish()

            # 生成报告
            report = self.formatter.format_full_report(multi_output.scenarios, question)

            # 输出报告
            yield emit_text("-" * 70)
            yield emit_text(report)
            yield emit_text("")

            # 输出指标
            self._output_metrics_text(metrics)

        else:
            yield emit_text("-" * 70)
            yield emit_text("⚠️  未检测到异常场景")
            yield emit_text("")

            # 输出指标
            self._output_metrics_text(metrics)

        yield emit_text("=" * 70)
        yield emit_text("✅ 多场景诊断完成")
        yield emit_text("=" * 70)

    def _workflow_to_sse(
        self,
        question: str,
        run_id: str,
        metrics: WorkflowMetrics
    ):
        """
        工作流执行结果转换为 SSE 格式
        """
        import json

        # 发出开始事件
        yield self._create_sse_message("run_start", {
            "run_id": run_id,
            "question": question,
            "timestamp": datetime.now().isoformat(),
        })

        # 执行检测
        initial_state = WorkflowState(
            question=question,
            run_id=run_id,
        )

        final_state = initial_state.copy()
        detected_scenarios = []

        for event in self.detector_node.execute(initial_state):
            if "detected_scenarios" in event:
                detected_scenarios = event["detected_scenarios"]
            final_state.update(event)

        # 生成报告
        if detected_scenarios:
            # 创建多场景输出对象
            multi_output = MultiScenarioOutput()
            for scenario_data in detected_scenarios:
                multi_output.add_scenario(ScenarioDecision(**scenario_data))

            # 更新指标
            metrics.detected_scenarios_count = len(detected_scenarios)
            metrics.finish()

            # 生成报告
            report = self.formatter.format_full_report(multi_output.scenarios, question)

            # 发出最终答案事件
            yield self._create_sse_message("final", {
                "answer": report,
                "scenarios": [s.to_dict() for s in multi_output.scenarios],
                "summary": multi_output.get_summary(),
                "metrics": metrics.get_summary(),
                "detection_duration": final_state.get("detection_duration", 0),
            })

        else:
            # 发出无检测结果事件
            yield self._create_sse_message("final", {
                "answer": "未检测到异常场景",
                "scenarios": [],
                "summary": {
                    "total_scenarios": 0,
                },
                "metrics": metrics.get_summary(),
            })

        # 发出结束事件
        yield self._create_sse_message("run_end", {})

    def _output_metrics_text(self, metrics: WorkflowMetrics):
        """输出指标文本"""
        lines = []

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 📊 性能统计")
        lines.append("")

        lines.append(f"**总耗时**: {metrics.mttr_formatted}")
        lines.append(f"**检测耗时**: {final_state.get('detection_duration', 0):.1f}s")

        if hasattr(metrics, 'detected_scenarios_count'):
            detected_count = metrics.detected_scenarios_count
            lines.append(f"**检测场景数**: {detected_count}")

        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 📈 质量指标")
        lines.append("")

        # MTTR
        mttr_status = "✅ 达标" if metrics.mttr_pass else "❌ 未达标"
        lines.append(f"| **MTTR** | {self._get_mttr_threshold()} | {metrics.mttr_formatted} | {mttr_status} |")

        lines.append("")

        yield "\n".join(lines)

    def _get_mttr_threshold(self) -> str:
        """获取 MTTR 阈值显示"""
        from app.core.workflow.metrics import MTTR_THRESHOLD_SECONDS
        return f"< {MTTR_THRESHOLD_SECONDS // 60}m"

    def _create_sse_message(self, event_type: str, payload: Dict[str, Any]) -> str:
        """创建 SSE 消息"""
        import json

        data = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **payload
        }

        return f"event: {json.dumps(data)}"
