"""
工作流执行器

职责：
- 封装 LangGraph 工作流的执行
- 与现有 SSE 事件流对接
- 支持流式输出（逐步发出节点完成事件）
- 记录性能指标和质量指标
"""

import uuid
import os
import time
import logging
import queue
import re
import threading
from datetime import datetime
from typing import Generator, Dict, Any, Optional

from app.core.workflow.state import WorkflowState
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.metrics import WorkflowMetrics
from app.core.holmes.log_listener import create_log_listener, HolmesLogListener
from app.core.workflow.reporter import (
    save_report as _save_report_fn,
    extract_layer_from_report as _extract_layer_fn,
    update_metrics_from_state as _update_metrics_fn,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    工作流执行器（与 HolmesService 集成）
    
    设计原则：
    - 封装 LangGraph 工作流的执行细节
    - 输出格式与现有 event_mapper 兼容
    - 记录性能和质量指标
    """
    
    def __init__(self, holmes_service: Any = None, metrics: Any = None):
        """
        初始化执行器

        Args:
            holmes_service: HolmesService 实例
            metrics: WorkflowMetrics 实例（用于记录统计）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.ai_call = None       # Set externally to enable aicall path
        self.mcp_tools = []       # Set externally (list of tool defs for aicall)
        # 获取 runbook_catalog（从 HolmesService）
        self.runbook_catalog = (
            holmes_service.merged_catalog
            if holmes_service and holmes_service.merged_catalog
            else None
        )
        # workflow 不再缓存，每次 execute_stream 重建（并发安全）

    # 报告保存目录（固定路径，不随工作目录变化）
    REPORTS_DIR = os.environ.get("REPORTS_DIR", "/tmp/aiops/reports")

    def _save_report(self, layer, question: str, full_answer: str):
        """保存诊断报告到固定目录"""
        _save_report_fn(self.REPORTS_DIR, layer, question, full_answer)

    @staticmethod
    def _extract_layer_from_report(text: str) -> str:
        """从报告文本中提取实际层级（优先用 conclusion 的判断）"""
        return _extract_layer_fn(text)

    def execute_stream(
        self,
        question: str,
        run_id: Optional[str] = None
    ) -> Generator[Dict, None, None]:
        """
        流式执行工作流（SSE 兼容）
        
        Args:
            question: 用户问题
            run_id: 运行 ID（可选，不提供则自动生成）
        
        Yields:
            工作流事件（与现有 event_mapper 格式兼容）
        """
        if run_id is None:
            run_id = uuid.uuid4().hex[:16]
        
        # 开始指标记录（每次请求独立创建，并发安全）
        if self.metrics is None:
            metrics = WorkflowMetrics(run_id=run_id, question=question)
        else:
            # 使用传入的 metrics（重置状态）
            metrics = self.metrics
            # 重置 metrics 状态
            metrics.run_id = run_id
            metrics.question = question
            metrics.start_time = time.time()

        # 每次请求重建 workflow（并发安全，避免共享节点实例）
        wf_config = getattr(self.holmes_service, "workflow_config", {}) or {}
        node_config = wf_config.get("nodes", {})
        workflow, node_instances = build_diagnosis_workflow(
            self.holmes_service, metrics, self.runbook_catalog,
            node_config=node_config,
        )

        # Propagate aicall to nodes if available
        if self.ai_call:
            for node in node_instances:
                node.ai_call = self.ai_call
                node.tools = self.mcp_tools or []

        total_start = time.time()

        # 创建并附加日志监听器（用于捕获 HolmesGPT 内部的工具调用）
        log_listener: Optional[HolmesLogListener] = create_log_listener()

        # 初始化状态
        initial_state: WorkflowState = {
            "question": question,
            "run_id": run_id,
            "layer": None,
            "layers": [],
            "layer_confidence": None,
            "layer_reasoning": None,
            "layer_analysis": None,
            "layer_full_analysis": None,
            "key_entities": [],
            "possible_scenarios": [],
            "evidence_items": [],
            "tool_results": [],
            "evidence_completeness": None,
            "evidence_analysis": None,
            "deterministic_decision": None,
            "root_cause": None,
            "causal_chain": None,
            "rca_analysis": None,
            "primary_runbook_id": None,
            "conclusion": None,
            "conclusion_formatted": None,
            "current_node": None,
            "errors": [],
            "warnings": [],
            "thinking_events": [],
        }

        # 发出开始事件
        logger.info(f"🚀 工作流开始: run_id={run_id}")
        yield {
            "type": "run_start",
            "id": f"{run_id}-run_start",
            "run_id": run_id,
            "seq": 0,
            "ts_ms": int(time.time() * 1000),
            "question": question,
            "timestamp": datetime.now().isoformat(),
        }

        # 执行工作流（threading + queue 实时模式）
        completed_nodes = set()
        current_nodes = set()
        node_start_times = {}
        seq = 0
        final_state = initial_state.copy()

        # 创建共享事件队列
        event_queue: queue.Queue = queue.Queue(maxsize=500)

        def _run_workflow_in_thread():
            """在后台线程中运行 LangGraph workflow.stream()"""
            try:
                for lg_event in workflow.stream(initial_state):
                    event_queue.put(("langgraph_event", lg_event))
                event_queue.put(("langgraph_done", None))
            except Exception as exc:
                event_queue.put(("langgraph_error", exc))

        try:
            # 设置节点级事件队列（per-request，并发安全）
            for node in node_instances:
                node.set_event_queue(event_queue)

            # 启动后台线程
            worker = threading.Thread(target=_run_workflow_in_thread, daemon=True)
            worker.start()

            workflow_done = False
            while not workflow_done:
                try:
                    item = event_queue.get(timeout=0.3)
                except queue.Empty:
                    # 检查线程是否还活着
                    if not worker.is_alive():
                        workflow_done = True
                    continue

                tag, data = item

                if tag == "thinking":
                    # 实时 thinking 事件 — 立刻 yield
                    node_id = data.get("node", "")

                    # 如果该节点还没有 node_start，先补发 node_start
                    if node_id and node_id not in node_start_times:
                        node_start_times[node_id] = time.time()
                        metrics.start_node(node_id, self._get_node_display_name(node_id))
                        logger.info(f"📍 [{node_id}] {self._get_node_display_name(node_id)} 开始...")
                        yield {
                            "type": "node_start",
                            "id": f"{run_id}-node_start-{node_id}",
                            "run_id": run_id,
                            "seq": seq,
                            "ts_ms": int(time.time() * 1000),
                            "node": node_id,
                            "node_name": self._get_node_display_name(node_id),
                        }
                        seq += 1

                    yield {
                        "type": "thinking",
                        "id": f"{run_id}-thinking-{node_id}-{seq}",
                        "run_id": run_id,
                        "node": node_id,
                        "node_name": self._get_node_display_name(node_id),
                        "thinking_type": data.get("type", ""),
                        "tool_name": data.get("tool_name"),
                        "content": data.get("content"),
                        "status": data.get("status"),
                        "result_preview": data.get("result_preview"),
                        "duration_seconds": data.get("duration_seconds"),
                        "iteration": data.get("iteration"),
                        "ts_ms": data.get("ts_ms", int(time.time() * 1000)),
                    }
                    seq += 1

                elif tag == "langgraph_event":
                    lg_event = data
                    new_nodes_in_this_event = set()

                    for node_name, updated_state in lg_event.items():
                        new_nodes_in_this_event.add(node_name)

                        # 节点开始（只记录一次）
                        if node_name not in node_start_times:
                            node_start_times[node_name] = time.time()
                            metrics.start_node(node_name, self._get_node_display_name(node_name))
                            logger.info(f"📍 [{node_name}] {self._get_node_display_name(node_name)} 开始...")

                            yield {
                                "type": "node_start",
                                "id": f"{run_id}-node_start-{node_name}",
                                "run_id": run_id,
                                "seq": seq,
                                "ts_ms": int(time.time() * 1000),
                                "node": node_name,
                                "node_name": self._get_node_display_name(node_name),
                            }
                            seq += 1

                    # 更新最终状态
                    final_state.update(updated_state)

                    # 检查是否有节点完成
                    for node_name in current_nodes:
                        if node_name not in new_nodes_in_this_event:
                            node_duration = time.time() - node_start_times.get(node_name, time.time())
                            metrics.finish_node(node_name, success=True)
                            completed_nodes.add(node_name)

                            snapshot = self._extract_state_snapshot(final_state, node_name)
                            node_summary = self._format_node_summary(node_name, final_state, snapshot)
                            handoff = self._format_handoff_summary(node_name, final_state)

                            logger.info(f"✅ [{node_name}] 完成 ({node_duration:.1f}s)")
                            if node_summary:
                                logger.info(f"   {node_summary}")
                            if handoff:
                                logger.info(f"   📤 传递给下游: {handoff}")

                            yield {
                                "type": "node_complete",
                                "id": f"{run_id}-node_complete-{node_name}",
                                "run_id": run_id,
                                "seq": seq,
                                "ts_ms": int(time.time() * 1000),
                                "node": node_name,
                                "node_name": self._get_node_display_name(node_name),
                                "duration_seconds": round(node_duration, 3),
                                "state_snapshot": snapshot,
                                "handoff_summary": handoff,
                            }
                            seq += 1

                    current_nodes = new_nodes_in_this_event

                elif tag == "langgraph_done":
                    workflow_done = True

                elif tag == "langgraph_error":
                    raise data  # re-raise exception from worker thread

            # 等待线程结束
            worker.join(timeout=5)

            # Finalize 剩余节点（最后一个节点）
            for node_name in current_nodes:
                if node_name not in completed_nodes:
                    node_duration = time.time() - node_start_times.get(node_name, time.time())
                    metrics.finish_node(node_name, success=True)
                    completed_nodes.add(node_name)

                    snapshot = self._extract_state_snapshot(final_state, node_name)
                    node_summary = self._format_node_summary(node_name, final_state, snapshot)

                    logger.info(f"✅ [{node_name}] 完成 ({node_duration:.1f}s)")
                    if node_summary:
                        logger.info(f"   {node_summary}")

                    yield {
                        "type": "node_complete",
                        "id": f"{run_id}-node_complete-{node_name}",
                        "run_id": run_id,
                        "seq": seq,
                        "ts_ms": int(time.time() * 1000),
                        "node": node_name,
                        "node_name": self._get_node_display_name(node_name),
                        "duration_seconds": round(node_duration, 3),
                        "state_snapshot": snapshot,
                    }
                    seq += 1
            
            # 更新指标
            self._update_metrics_from_state(metrics, final_state)

            # 从日志监听器提取 runbook 信息（补充，不覆盖已有结果）
            runbook_summary = log_listener.get_runbook_summary()
            if runbook_summary["matched"]:
                metrics.runbook_matched = True
                metrics.runbook_id = ", ".join(runbook_summary["runbook_ids"])
                logger.info(f"   Runbook 使用(日志): {metrics.runbook_id}")

            # 补充：从 log_listener 的工具调用记录补充 metrics 统计
            tool_calls_from_log = log_listener.get_tool_calls()
            if tool_calls_from_log and metrics.total_tool_calls == 0:
                for tc in tool_calls_from_log:
                    metrics.total_tool_calls += 1

            # 分离日志监听器
            log_listener.detach()

            # 完成指标记录
            metrics.finish()
            
            # 构建最终答案（包含性能统计）
            conclusion = final_state.get("conclusion_formatted") or final_state.get("conclusion") or ""
            
            # 添加性能统计和指标到报告末尾
            stats_block = metrics.format_stats_block()
            from app.core.workflow.metrics import METRICS_ENABLED
            metrics_block = metrics.format_metrics_block(enabled=METRICS_ENABLED)

            full_answer = f"{conclusion}\n{stats_block}\n{metrics_block}"

            # 保存诊断报告到 reports/ 目录
            layer = final_state.get("layer")
            self._save_report(layer, question, full_answer)
            
            # 日志输出完成信息
            logger.info(f"🎉 工作流完成: 耗时 {metrics.mttr_formatted}")
            logger.info("=" * 60)
            logger.info("⏱️ [耗时分析] 各节点耗时明细:")
            for nid, node in metrics.nodes.items():
                pct = (node.duration_ms / metrics.total_duration_ms * 100) if metrics.total_duration_ms > 0 else 0
                logger.info(f"   {node.node_name}: {node.duration_ms/1000:.1f}s ({pct:.0f}%)")
            logger.info(f"   LLM 总耗时: {metrics.total_llm_duration_ms/1000:.1f}s ({metrics.total_llm_calls} 次)")
            logger.info(f"   工具总耗时: {metrics.total_tool_duration_ms/1000:.1f}s ({metrics.total_tool_calls} 次)")
            logger.info(f"   总计: {metrics.total_duration_seconds:.1f}s")
            logger.info("=" * 60)
            
            # 发出最终答案事件
            seq += 1
            yield {
                "type": "final",
                "id": f"{run_id}-final",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "status": "success",
                "answer": full_answer,
                "answer_source": "workflow",
                "elapsed_seconds": round(time.time() - total_start, 3),
                "metrics": metrics.get_summary(),
            }
            
            # 发出结束事件
            seq += 1
            yield {
                "type": "run_end",
                "id": f"{run_id}-run_end",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "elapsed_seconds": round(time.time() - total_start, 3),
            }
        
        except Exception as e:
            # 分离日志监听器
            if log_listener:
                log_listener.detach()

            logger.error(f"❌ 工作流执行失败: {e}", exc_info=True)
            metrics.success = False
            metrics.errors.append(str(e))
            metrics.finish()

            # 错误事件
            seq += 1
            yield {
                "type": "error",
                "id": f"{run_id}-error",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "error": str(e),
            }
        finally:
            # 清除事件队列（实例级，无需类级别清理）+ 等待后台线程结束
            for node in node_instances:
                node.set_event_queue(None)
            if worker.is_alive():
                worker.join(timeout=5)
    
    def _get_node_display_name(self, node_id: str) -> str:
        """获取节点显示名称"""
        name_map = {
            "layer": "问题定位",
            "evidence": "证据链采集",
            "rca": "根因分析",
            "conclusion": "汇总总结",
        }
        return name_map.get(node_id, node_id)
    
    def _extract_state_snapshot(
        self,
        state: WorkflowState,
        node_name: str
    ) -> Dict[str, Any]:
        """提取状态快照（用于调试和日志）

        设计：
        - 包含完整的分析 JSON (layer_analysis, evidence_analysis, rca_analysis)
        - 用于 service.py 中收集并显示所有节点的完整输出
        """
        snapshot = {}

        if node_name == "layer":
            layers = state.get("layers", [])
            snapshot = {
                "layer": str(state.get("layer", "")),
                "layers": [l.value if hasattr(l, 'value') else str(l) for l in layers],
                "layer_confidence": state.get("layer_confidence"),
                "layer_reasoning": state.get("layer_reasoning") or "",
                "layer_analysis": state.get("layer_analysis", ""),
                "key_entities": state.get("key_entities", []),
                "possible_scenarios": state.get("possible_scenarios", []),
            }
        elif node_name == "evidence":
            evidence_items = state.get("evidence_items", [])
            collected = sum(1 for e in evidence_items if getattr(e, 'collected', False))
            snapshot = {
                "evidence_count": len(evidence_items),
                "collected_count": collected,
                "completeness": state.get("evidence_completeness"),
                "evidence_analysis": state.get("evidence_analysis", ""),
                "evidence_items": evidence_items,
            }
        elif node_name == "rca":
            decision = state.get("deterministic_decision")
            snapshot = {
                "root_cause": state.get("root_cause") or "",
                "has_causal_chain": bool(state.get("causal_chain")),
                "causal_chain": state.get("causal_chain", {}),
                "confidence": decision.confidence_score if decision else None,
                "category": decision.category if decision else None,
                "rca_analysis": state.get("rca_analysis", ""),
            }
        elif node_name == "conclusion":
            snapshot = {
                "conclusion_length": len(state.get("conclusion", "") or ""),
                "has_errors": len(state.get("errors", [])) > 0,
                "has_warnings": len(state.get("warnings", [])) > 0,
                "conclusion": state.get("conclusion", ""),
                "conclusion_formatted": state.get("conclusion_formatted", ""),
            }

        return snapshot
    
    def _format_node_summary(
        self,
        node_name: str,
        state: WorkflowState,
        snapshot: Dict
    ) -> str:
        """格式化节点摘要（用于日志输出）"""
        if node_name == "layer":
            layer = snapshot.get("layer", "?")
            conf = snapshot.get("layer_confidence", 0) or 0
            return f"层级: {layer}, 置信度: {conf:.0%}"
        
        elif node_name == "evidence":
            count = snapshot.get("evidence_count", 0)
            collected = snapshot.get("collected_count", 0)
            completeness = snapshot.get("completeness", 0) or 0
            return f"证据: {collected}/{count}, 完整度: {completeness:.0%}"
        
        elif node_name == "rca":
            root_cause = snapshot.get("root_cause", "")
            conf = snapshot.get("confidence")
            conf_str = f"{conf:.0%}" if conf else "?"
            return f"根因: {root_cause[:50]}..., 置信度: {conf_str}"
        
        elif node_name == "conclusion":
            length = snapshot.get("conclusion_length", 0)
            return f"报告长度: {length} 字符"
        
        return ""

    def _format_handoff_summary(self, node_name: str, state: WorkflowState) -> str:
        """格式化节点间传递的完整数据（不截断，供审查）"""
        import json as _json

        if node_name == "layer":
            layer = state.get("layer", "?")
            layers = state.get("layers", [])
            scenarios = state.get("possible_scenarios", [])
            entities = state.get("key_entities", [])
            analysis = state.get("layer_analysis", "")
            reasoning = state.get("layer_reasoning", "")
            layers_str = "+".join(l.value if hasattr(l, 'value') else str(l) for l in layers) if layers else str(layer)
            return (
                f"layer={layer}, layers={layers_str}\n"
                f"   scenarios={scenarios}\n"
                f"   entities={_json.dumps(entities, ensure_ascii=False)}\n"
                f"   reasoning={reasoning}\n"
                f"   layer_analysis={analysis}"
            )
        elif node_name == "evidence":
            items = state.get("evidence_items", [])
            collected = sum(1 for e in items if getattr(e, 'collected', False))
            analysis = state.get("evidence_analysis", "")
            return (
                f"evidence_items={collected}/{len(items)}\n"
                f"   evidence_analysis={analysis}"
            )
        elif node_name == "rca":
            root_cause = state.get("root_cause", "") or ""
            decision = state.get("deterministic_decision")
            conf = f"{decision.confidence_score:.0%}" if decision else "?"
            causal_chain = state.get("causal_chain", {})
            rca_analysis = state.get("rca_analysis", "")
            return (
                f"root_cause={root_cause}\n"
                f"   confidence={conf}\n"
                f"   causal_chain={_json.dumps(causal_chain, ensure_ascii=False)}\n"
                f"   rca_analysis={rca_analysis}"
            )
        return ""

    def _update_metrics_from_state(
        self,
        metrics: WorkflowMetrics,
        state: WorkflowState
    ):
        """从最终状态更新指标"""
        _update_metrics_fn(
            metrics, state,
            runbook_catalog=self.runbook_catalog,
            holmes_service=self.holmes_service,
        )
