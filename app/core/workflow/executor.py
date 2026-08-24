"""
工作流执行器

职责：
- 封装 LangGraph 工作流的执行
- 与现有 SSE 事件流对接
- 支持流式输出（逐步发出节点完成事件）
- 记录性能指标和质量指标
"""

import copy
import json
import uuid
import os
import time
import logging
import queue
import re
import threading
from contextlib import contextmanager, nullcontext
from datetime import datetime
from typing import Generator, Dict, Any, Optional

from app.core.workflow.state import WorkflowState
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.metrics import WorkflowMetrics
from app.core.workflow.stream_contract import project_parallel_tool_event
from app.core.holmes.log_listener import create_log_listener, HolmesLogListener
from app.core.workflow.reporter import (
    save_report as _save_report_fn,
    extract_layer_from_report as _extract_layer_fn,
    update_metrics_from_state as _update_metrics_fn,
)
from app.core.context.archive import ContextArchive
from app.core.remediation.approval import approval_store
from app.core.remediation.agent import RemediationAgentConfig, RemediationAgentExecutor
from app.core.remediation.executor import RemediationExecutor
from app.core.remediation.models import RemediationRuntimeConfig, normalize_remediation_mode
from app.core.remediation.plans import extract_remediation_plan

logger = logging.getLogger(__name__)


def _int_config(config: Dict[str, Any], key: str, default: int) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _float_config(config: Dict[str, Any], key: str, default: float) -> float:
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _invalid_remediation_plan_event(run_id: str, error: Exception) -> Dict[str, Any]:
    return {
        "type": "remediation_finished",
        "run_id": run_id,
        "status": "invalid_plan",
        "reason": f"invalid remediation plan: {error}",
    }


def _missing_structured_actions_reason(report: str, plan: Any) -> Optional[str]:
    """Detect report/plan mismatch without extracting commands from prose."""
    text = report or ""
    write_patterns = (
        r"\bkubectl\s+(?:apply|create|delete|patch|scale)\s+"
        r"(?:[A-Za-z0-9_.-]+|-[A-Za-z0-9_.-]+)",
        r"\bkubectl\s+set\s+"
        r"(?:env|image|resources|selector|serviceaccount|subject)\s+"
        r"(?:[A-Za-z0-9_.-]+/)?[A-Za-z0-9_.-]+",
        r"\bkubectl\s+rollout\s+(?:pause|restart|resume|undo)\s+"
        r"(?:[A-Za-z0-9_.-]+/)?[A-Za-z0-9_.-]+",
    )
    has_write_advice = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in write_patterns
    )
    if not has_write_advice:
        return None
    actions = getattr(plan, "actions", None) if plan is not None else None
    remediation_available = bool(getattr(plan, "remediation_available", False)) if plan is not None else False
    if plan is None:
        return "natural-language remediation advice exists but no structured remediation plan was emitted"
    if not remediation_available or not actions:
        return "natural-language remediation advice exists but structured remediation actions are missing or disabled"
    return None


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

    @staticmethod
    def _get_heartbeat_interval_seconds() -> float:
        """获取流式保活间隔；<=0 表示禁用。"""
        raw = os.environ.get("WORKFLOW_STREAM_HEARTBEAT_SECONDS", "15")
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 15.0

    @staticmethod
    def _join_worker_if_needed(
        worker: Optional[threading.Thread],
        *,
        timeout: float,
    ) -> bool:
        if worker is None:
            return False
        if worker is threading.current_thread():
            return worker.is_alive()
        if worker.is_alive():
            worker.join(timeout=timeout)
        return worker.is_alive()

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
        run_id: Optional[str] = None,
        cancel_event: Optional[threading.Event] = None,
        workflow_overrides: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict, None, None]:
        """
        流式执行工作流（SSE 兼容）

        Args:
            question: 用户问题
            run_id: 运行 ID（可选，不提供则自动生成）
            cancel_event: 取消信号（客户端断开时 set()，后台线程检测后停止）

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
        wf_config = copy.deepcopy(getattr(self.holmes_service, "workflow_config", {}) or {})
        if workflow_overrides:
            for key, value in workflow_overrides.items():
                if isinstance(value, dict) and isinstance(wf_config.get(key), dict):
                    merged = dict(wf_config.get(key, {}))
                    merged.update(value)
                    wf_config[key] = merged
                else:
                    wf_config[key] = value
        node_config = wf_config.get("nodes", {})
        query_mode = "full"
        if workflow_overrides:
            query_mode = str(workflow_overrides.get("query_mode", "full")).strip().lower() or "full"
        wf_config.pop("query_mode", None)
        if workflow_overrides and "query_mode" in workflow_overrides:
            wf_config["query_mode"] = query_mode
        evidence_cfg = wf_config.get("evidence", {}) if isinstance(wf_config, dict) else {}
        parallel_config = (
            evidence_cfg.get("parallel", {}) if isinstance(evidence_cfg, dict) else {}
        )
        workflow, node_instances = build_diagnosis_workflow(
            self.holmes_service, metrics, self.runbook_catalog,
            node_config=node_config,
            query_mode=query_mode,
            parallel_config=parallel_config,
        )

        # Propagate per-request metadata to every node. `current_run_id` must
        # not depend on ai_call availability because lite/template paths can
        # still archive artifacts or call LLM later in the node.
        for node in node_instances:
            node.cancel_event = cancel_event  # 传递取消信号
            node.current_run_id = run_id
            node.workflow_config_override = wf_config
            if self.ai_call:
                node.ai_call = self.ai_call
                node.tools = self.mcp_tools or []
                logger.debug("   🔧 [%s] ai_call=%s tools=%d",
                             node.node_id, type(node.ai_call).__name__, len(node.tools))

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
            "layer_handoff": None,
            "layer_archive_ref": None,
            "context_archive_ref": None,
            "context_budget": None,
            "tool_artifact_refs": [],
            "key_entities": [],
            "possible_scenarios": [],
            "evidence_items": [],
            "tool_results": [],
            "evidence_completeness": None,
            "evidence_analysis": None,
            "query_result": None,
            "evidence_facts": [],
            "evidence_conflicts": [],
            "missing_evidence": [],
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
        heartbeat_interval_s = self._get_heartbeat_interval_seconds()
        last_stream_event_ts = time.time()

        # 创建共享事件队列
        event_queue: queue.Queue = queue.Queue(maxsize=500)

        def _run_workflow_in_thread():
            """在后台线程中运行 LangGraph workflow.stream()"""
            try:
                with self._langfuse_session_scope(run_id):
                    for lg_event in workflow.stream(initial_state):
                        event_queue.put(("langgraph_event", lg_event))
                event_queue.put(("langgraph_done", None))
            except Exception as exc:
                event_queue.put(("langgraph_error", exc))

        worker: Optional[threading.Thread] = None
        try:
            # 设置节点级事件队列（per-request，并发安全）
            for node in node_instances:
                node.set_event_queue(event_queue)

            # 启动后台线程
            worker = threading.Thread(target=_run_workflow_in_thread, daemon=True)
            worker.start()

            workflow_done = False
            while not workflow_done:
                # 检查取消信号
                if cancel_event and cancel_event.is_set():
                    logger.info("🛑 [Workflow] 收到取消信号，停止工作流 (run_id=%s)", run_id)
                    workflow_done = True
                    break

                try:
                    item = event_queue.get(timeout=0.3)
                except queue.Empty:
                    now = time.time()
                    if (
                        heartbeat_interval_s > 0
                        and current_nodes
                        and worker.is_alive()
                        and now - last_stream_event_ts >= heartbeat_interval_s
                    ):
                        heartbeat_node_id = sorted(current_nodes)[0]
                        yield {
                            "type": "heartbeat",
                            "id": f"{run_id}-heartbeat-{seq}",
                            "run_id": run_id,
                            "seq": seq,
                            "ts_ms": int(now * 1000),
                            "node": heartbeat_node_id,
                            "node_name": self._get_node_display_name(heartbeat_node_id),
                        }
                        seq += 1
                        last_stream_event_ts = now
                    # 检查线程是否还活着
                    if not worker.is_alive():
                        workflow_done = True
                    continue

                tag, data = item

                if tag == "node_lifecycle":
                    node_id = data.get("node", "")
                    node_name = data.get("node_name", self._get_node_display_name(node_id))
                    ts = data.get("ts", time.time())

                    if data.get("phase") == "start":
                        if node_id and node_id not in node_start_times:
                            node_start_times[node_id] = ts
                            metrics.start_node(node_id, node_name, start_ts=ts)
                            current_nodes.add(node_id)
                            logger.info(f"📍 [{node_id}] {node_name} 开始...")
                            yield {
                                "type": "node_start",
                                "id": f"{run_id}-node_start-{node_id}",
                                "run_id": run_id,
                                "seq": seq,
                                "ts_ms": int(ts * 1000),
                                "node": node_id,
                                "node_name": node_name,
                            }
                            seq += 1
                            last_stream_event_ts = time.time()

                    elif data.get("phase") == "end" and node_id and node_id not in completed_nodes:
                        state_update = data.get("state_update") or {}
                        if state_update:
                            final_state.update(state_update)

                        metrics.finish_node(
                            node_id,
                            success=data.get("success", True),
                            error=data.get("error"),
                            end_ts=ts,
                        )
                        completed_nodes.add(node_id)
                        current_nodes.discard(node_id)

                        snapshot = self._extract_state_snapshot(final_state, node_id)
                        node_summary = self._format_node_summary(node_id, final_state, snapshot)
                        handoff = self._format_handoff_summary(node_id, final_state)
                        self._archive_node_transition(run_id, node_id, final_state, snapshot, handoff)
                        duration_s = metrics.nodes.get(node_id).duration_ms / 1000 if node_id in metrics.nodes else 0

                        logger.info(f"✅ [{node_id}] 完成 ({duration_s:.1f}s)")
                        if node_summary:
                            logger.info(f"   {node_summary}")
                        if handoff:
                            handoff_short = handoff[:120] + "..." if len(handoff) > 120 else handoff
                            logger.info(f"   📤 传递给下游: {handoff_short}")
                            logger.debug(f"   📤 [DEBUG] 完整传递数据:\n{handoff}")

                        yield {
                            "type": "node_complete",
                            "id": f"{run_id}-node_complete-{node_id}",
                            "run_id": run_id,
                            "seq": seq,
                            "ts_ms": int(ts * 1000),
                            "node": node_id,
                            "node_name": node_name,
                            "duration_seconds": round(duration_s, 3),
                            "state_snapshot": snapshot,
                            "handoff_summary": handoff,
                        }
                        seq += 1
                        last_stream_event_ts = time.time()

                elif tag == "thinking":
                    # 实时 thinking 事件 — 立刻 yield
                    node_id = data.get("node", "")

                    # 如果该节点还没有 node_start，先补发 node_start
                    if node_id and node_id not in node_start_times:
                        # ── 先 finish 上一个活跃节点（修复计时重叠） ──
                        now = time.time()
                        for prev_node in list(current_nodes):
                            if prev_node not in completed_nodes:
                                metrics.finish_node(prev_node, success=True, end_ts=now)
                                completed_nodes.add(prev_node)
                                prev_dur = now - node_start_times.get(prev_node, now)
                                snapshot = self._extract_state_snapshot(final_state, prev_node)
                                node_summary = self._format_node_summary(prev_node, final_state, snapshot)
                                handoff = self._format_handoff_summary(prev_node, final_state)
                                self._archive_node_transition(run_id, prev_node, final_state, snapshot, handoff)
                                logger.info(f"✅ [{prev_node}] 完成 ({prev_dur:.1f}s)")
                                if node_summary:
                                    logger.info(f"   {node_summary}")
                                if handoff:
                                    handoff_short = handoff[:120] + "..." if len(handoff) > 120 else handoff
                                    logger.info(f"   📤 传递给下游: {handoff_short}")
                                    logger.debug(f"   📤 [DEBUG] 完整传递数据:\n{handoff}")
                                yield {
                                    "type": "node_complete",
                                    "id": f"{run_id}-node_complete-{prev_node}",
                                    "run_id": run_id,
                                    "seq": seq,
                                    "ts_ms": int(now * 1000),
                                    "node": prev_node,
                                    "node_name": self._get_node_display_name(prev_node),
                                    "duration_seconds": round(prev_dur, 3),
                                    "state_snapshot": snapshot,
                                    "handoff_summary": handoff,
                                }
                                seq += 1
                                last_stream_event_ts = time.time()
                        current_nodes = set()

                        node_start_times[node_id] = time.time()
                        metrics.start_node(node_id, self._get_node_display_name(node_id))
                        current_nodes.add(node_id)
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
                        last_stream_event_ts = time.time()

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
                        **project_parallel_tool_event(data),
                    }
                    seq += 1
                    last_stream_event_ts = time.time()

                elif tag == "langgraph_event":
                    lg_event = data
                    new_nodes_in_this_event = set()

                    for node_name, updated_state in lg_event.items():
                        new_nodes_in_this_event.add(node_name)
                        final_state.update(updated_state)

                        # 节点开始（只记录一次）
                        if node_name not in node_start_times:
                            node_start_times[node_name] = time.time()
                            metrics.start_node(node_name, self._get_node_display_name(node_name))
                            current_nodes.add(node_name)
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
                            last_stream_event_ts = time.time()

                    # 检查是否有节点完成（跳过已被 thinking 分支 finish 的节点）
                    for node_name in current_nodes:
                        if node_name not in new_nodes_in_this_event and node_name not in completed_nodes:
                            node_duration = time.time() - node_start_times.get(node_name, time.time())
                            metrics.finish_node(node_name, success=True)
                            completed_nodes.add(node_name)

                            snapshot = self._extract_state_snapshot(final_state, node_name)
                            node_summary = self._format_node_summary(node_name, final_state, snapshot)
                            handoff = self._format_handoff_summary(node_name, final_state)
                            self._archive_node_transition(run_id, node_name, final_state, snapshot, handoff)

                            logger.info(f"✅ [{node_name}] 完成 ({node_duration:.1f}s)")
                            if node_summary:
                                logger.info(f"   {node_summary}")
                            if handoff:
                                handoff_short = handoff[:120] + "..." if len(handoff) > 120 else handoff
                                logger.info(f"   📤 传递给下游: {handoff_short}")
                                logger.debug(f"   📤 [DEBUG] 完整传递数据:\n{handoff}")

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
                            last_stream_event_ts = time.time()

                    current_nodes = new_nodes_in_this_event

                elif tag == "langgraph_done":
                    workflow_done = True

                elif tag == "langgraph_error":
                    raise data  # re-raise exception from worker thread

            # 等待线程结束
            self._join_worker_if_needed(worker, timeout=5)

            # Finalize 剩余节点（最后一个节点）
            for node_name in current_nodes:
                if node_name not in completed_nodes:
                    node_duration = time.time() - node_start_times.get(node_name, time.time())
                    metrics.finish_node(node_name, success=True)
                    completed_nodes.add(node_name)

                    snapshot = self._extract_state_snapshot(final_state, node_name)
                    node_summary = self._format_node_summary(node_name, final_state, snapshot)
                    handoff = self._format_handoff_summary(node_name, final_state)
                    self._archive_node_transition(run_id, node_name, final_state, snapshot, handoff)

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
                    last_stream_event_ts = time.time()
            
            # 更新指标
            self._update_metrics_from_state(metrics, final_state)
            metrics.rebuild_runtime_counts(final_state.get("thinking_events", []))

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
            
            # 最终报告只保留 Conclusion 的诊断内容。性能与调用统计仍在
            # metrics/event 中提供，不再追加到面向用户的根因报告。
            conclusion = final_state.get("conclusion_formatted") or final_state.get("conclusion") or ""
            full_answer = conclusion

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
            logger.info(f"   模型请求耗时: {metrics.total_llm_duration_ms/1000:.1f}s ({metrics.total_llm_calls} 次)")
            logger.info(
                "   工具耗时: 累计 %.1fs，关键路径 %.1fs "
                "(请求 %d，实际执行 %d，去重 %d，成功响应 %d，失败/未完成 %d)",
                metrics.total_tool_duration_ms / 1000,
                metrics.tool_wall_duration_ms / 1000,
                metrics.total_tool_calls,
                metrics.executed_tool_calls,
                metrics.deduplicated_tool_calls,
                metrics.successful_tool_calls,
                metrics.failed_tool_calls,
            )
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
            last_stream_event_ts = time.time()

            remediation_cfg = wf_config.get("remediation", {}) if isinstance(wf_config, dict) else {}
            remediation_enabled = False
            if isinstance(remediation_cfg, dict):
                remediation_enabled = bool(remediation_cfg.get("enabled", False))
            if remediation_enabled:
                approval_timeout = 600
                approval_mode = "review"
                remediation_executor_type = "deterministic"
                runtime_config = RemediationRuntimeConfig()
                if isinstance(remediation_cfg, dict):
                    try:
                        approval_timeout = int(remediation_cfg.get("approval_timeout_seconds") or 600)
                    except (TypeError, ValueError):
                        approval_timeout = 600
                    approval_mode = normalize_remediation_mode(remediation_cfg.get("mode"))
                    remediation_executor_type = str(
                        remediation_cfg.get("executor") or remediation_cfg.get("strategy") or "deterministic"
                    ).strip().lower()
                    runtime_config = RemediationRuntimeConfig(
                        executor=remediation_executor_type,
                        max_iterations=_int_config(remediation_cfg, "max_iterations", 4),
                        max_write_actions=_int_config(remediation_cfg, "max_write_actions", 2),
                        max_duration_seconds=_int_config(remediation_cfg, "max_duration_seconds", 900),
                        verify_settle_seconds=_float_config(remediation_cfg, "verify_settle_seconds", 0.0),
                    )
                plan = None
                invalid_plan_event = None
                try:
                    plan = extract_remediation_plan(full_answer)
                except ValueError as exc:
                    logger.warning(
                        "🛠️ invalid remediation plan | run_id=%s error=%s",
                        run_id,
                        exc,
                    )
                    invalid_plan_event = _invalid_remediation_plan_event(run_id, exc)
                if plan is not None:
                    final_state["remediation_plan"] = {
                        "remediation_available": plan.remediation_available,
                        "fix_type": plan.fix_type,
                        "risk_level": plan.risk_level,
                        "requires_human_approval": plan.requires_human_approval,
                        "issue_groups": plan.issue_groups,
                        "basis": plan.basis,
                        "actions": [action.__dict__ for action in plan.actions],
                        "stop_conditions": plan.stop_conditions,
                    }
                missing_actions_reason = None
                if invalid_plan_event is None:
                    missing_actions_reason = _missing_structured_actions_reason(full_answer, plan)
                    if missing_actions_reason:
                        logger.warning(
                            "🛠️ invalid remediation plan | run_id=%s error=%s",
                            run_id,
                            missing_actions_reason,
                        )
                        invalid_plan_event = _invalid_remediation_plan_event(
                            run_id,
                            ValueError(missing_actions_reason),
                        )
                if invalid_plan_event is not None:
                    seq += 1
                    event = {
                        **invalid_plan_event,
                        "id": f"{run_id}-remediation_finished-{seq}",
                        "seq": seq,
                        "ts_ms": int(time.time() * 1000),
                    }
                    yield event
                    final_state["remediation_result"] = invalid_plan_event
                    last_stream_event_ts = time.time()
                    remediation_run = None
                elif remediation_executor_type in {"react", "agent", "llm"}:
                    remediation_executor = RemediationAgentExecutor(
                        approval_store=approval_store,
                        ai_call=self.ai_call,
                    )
                    remediation_run = remediation_executor.run(
                        run_id=run_id,
                        plan=plan,
                        report=full_answer,
                        approval_timeout_seconds=approval_timeout,
                        approval_mode=approval_mode,
                        config=RemediationAgentConfig(
                            executor="react",
                            max_iterations=runtime_config.max_iterations,
                            max_write_actions=runtime_config.max_write_actions,
                            max_duration_seconds=runtime_config.max_duration_seconds,
                            verify_settle_seconds=runtime_config.verify_settle_seconds,
                        ),
                    )
                else:
                    remediation_executor = RemediationExecutor(approval_store=approval_store)
                    remediation_run = remediation_executor.run(
                        run_id=run_id,
                        plan=plan,
                        approval_timeout_seconds=approval_timeout,
                        approval_mode=approval_mode,
                    )
                last_remediation_event = None
                if remediation_run is not None:
                    for remediation_event in remediation_run:
                        last_remediation_event = remediation_event
                        seq += 1
                        event = {
                            **remediation_event,
                            "id": f"{run_id}-{remediation_event.get('type', 'remediation')}-{seq}",
                            "seq": seq,
                            "ts_ms": int(time.time() * 1000),
                        }
                        yield event
                        last_stream_event_ts = time.time()
                    if isinstance(last_remediation_event, dict):
                        final_state["remediation_result"] = last_remediation_event
            
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
            last_stream_event_ts = time.time()
        
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
            last_stream_event_ts = time.time()
        finally:
            # 设置取消信号（确保后台线程也能感知）
            if cancel_event:
                cancel_event.set()
            # 清除事件队列（实例级，无需类级别清理）+ 等待后台线程结束
            for node in node_instances:
                node.set_event_queue(None)
            worker_alive = self._join_worker_if_needed(
                worker,
                timeout=5,
            )
            if (
                worker_alive
                and worker is not threading.current_thread()
            ):
                logger.warning("⚠️ [Workflow] 后台线程未在 5s 内结束 (run_id=%s)", run_id)

    @staticmethod
    def _normalize_langfuse_session_id(run_id: str) -> Optional[str]:
        raw = str(run_id or "").strip()
        if not raw:
            return None
        ascii_text = raw.encode("ascii", errors="ignore").decode("ascii").strip()
        if not ascii_text:
            return None
        return ascii_text[:199]

    @contextmanager
    def _langfuse_session_scope(self, run_id: str):
        session_id = self._normalize_langfuse_session_id(run_id)
        if not session_id:
            with nullcontext():
                yield
            return

        try:
            from langfuse import propagate_attributes
        except Exception as exc:
            logger.debug("📉 [Workflow] Langfuse session propagation 不可用，直接执行: %s", exc)
            yield
            return

        logger.debug("📈 [Workflow] Langfuse session_id=%s", session_id)
        with propagate_attributes(session_id=session_id):
            yield
    
    def _get_node_display_name(self, node_id: str) -> str:
        """获取节点显示名称"""
        name_map = {
            "layer": "问题定位",
            "evidence": "证据链采集",
            "rca": "根因分析",
            "conclusion": "汇总总结",
            "remediation": "修复执行",
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
            evidence_analysis = state.get("evidence_analysis", "")
            collected = sum(1 for e in evidence_items if getattr(e, 'collected', False))
            count = len(evidence_items)
            try:
                analysis_data = json.loads(evidence_analysis) if evidence_analysis else {}
                if isinstance(analysis_data.get("plan_total"), int):
                    collected = int(analysis_data.get("plan_collected") or 0)
                    count = int(analysis_data.get("plan_total") or 0)
            except Exception:
                pass
            serialized_evidence_items = []
            for item in evidence_items:
                if hasattr(item, "to_dict") and callable(item.to_dict):
                    serialized_evidence_items.append(item.to_dict())
                elif isinstance(item, dict):
                    serialized_evidence_items.append(item)
                else:
                    serialized_evidence_items.append({
                        "id": getattr(item, "id", ""),
                        "description": getattr(item, "description", ""),
                        "level": str(getattr(getattr(item, "level", ""), "value", getattr(item, "level", ""))),
                        "collected": bool(getattr(item, "collected", False)),
                        "value": getattr(item, "value", None),
                        "source": getattr(item, "source", None),
                    })
            snapshot = {
                "evidence_count": count,
                "collected_count": collected,
                "completeness": state.get("evidence_completeness"),
                "evidence_analysis": evidence_analysis,
                "evidence_items": serialized_evidence_items,
            }
        elif node_name == "parallel_evidence":
            raw_inventory = [
                lane
                for lane in (state.get("parallel_lane_inventory") or [])
                if isinstance(lane, dict)
            ]
            raw_groups = [
                group
                for group in (state.get("group_results") or [])
                if isinstance(group, dict)
            ]
            ordered_inventory = sorted(
                raw_inventory,
                key=lambda lane: (
                    int(lane.get("presentation_index") or 0),
                    str(lane.get("group_id") or ""),
                ),
            )
            ordered_groups = sorted(
                raw_groups,
                key=lambda group: (
                    int(group.get("presentation_index") or 0),
                    str(group.get("group_id") or ""),
                ),
            )
            expected_ids = [
                str(lane.get("group_id") or "")
                for lane in ordered_inventory
                if str(lane.get("group_id") or "")
            ]
            terminal_ids = [
                str(group.get("group_id") or "")
                for group in ordered_groups
                if str(group.get("group_id") or "")
            ]
            expected_id_set = set(expected_ids)
            terminal_id_set = set(terminal_ids)
            duplicate_expected_ids = sorted({
                group_id
                for group_id in expected_ids
                if expected_ids.count(group_id) > 1
            })
            duplicate_ids = sorted({
                group_id
                for group_id in terminal_ids
                if terminal_ids.count(group_id) > 1
            })
            missing_ids = sorted(expected_id_set - terminal_id_set)
            unexpected_ids = sorted(terminal_id_set - expected_id_set)
            join_errors = []
            if duplicate_expected_ids:
                join_errors.append(
                    "duplicate expected group IDs: "
                    + ",".join(duplicate_expected_ids)
                )
            if duplicate_ids:
                join_errors.append(
                    "duplicate terminal group IDs: " + ",".join(duplicate_ids)
                )
            if missing_ids:
                join_errors.append(
                    "missing terminal group IDs: " + ",".join(missing_ids)
                )
            if unexpected_ids:
                join_errors.append(
                    "unexpected terminal group IDs: " + ",".join(unexpected_ids)
                )
            missing_artifact_ids = sorted({
                str(group.get("group_id") or "")
                for group in ordered_groups
                if str(group.get("group_id") or "") in expected_id_set
                and not isinstance(group.get("lane_diagnosis_artifact_ref"), dict)
            })
            if missing_artifact_ids:
                join_errors.append(
                    "missing lane artifact refs: "
                    + ",".join(missing_artifact_ids)
                )

            terminal_statuses = [
                str(
                    group.get("terminal_status")
                    or group.get("diagnostic_status")
                    or "inconclusive"
                ).lower()
                for group in ordered_groups
            ]
            snapshot = {
                "contract_version": "aiops.parallel-evidence-output.v2",
                # Compatibility alias retained for existing UI consumers.
                "group_count": len(ordered_groups),
                "expected_group_count": len(expected_id_set),
                "terminal_group_count": len(terminal_id_set),
                "join_complete": not join_errors,
                "diagnosed_count": terminal_statuses.count("diagnosed"),
                "inconclusive_count": terminal_statuses.count("inconclusive"),
                "error_count": terminal_statuses.count("error"),
                "errors": join_errors,
                "groups": [
                    {
                        "group_id": group.get("group_id"),
                        "presentation_index": group.get(
                            "presentation_index"
                        ),
                        "entities": group.get("entities") or [],
                        "diagnostic_status": group.get(
                            "diagnostic_status", "inconclusive"
                        ),
                        "artifact_ref": group.get(
                            "lane_diagnosis_artifact_ref"
                        ),
                        "snapshot_sha256": (
                            (
                                group.get("lane_diagnosis_artifact") or {}
                            ).get("artifact_refs")
                            or {}
                        ).get("snapshot", {}).get("sha256", ""),
                    }
                    for group in ordered_groups
                ],
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
            total = len(items)
            analysis = state.get("evidence_analysis", "")
            try:
                analysis_data = _json.loads(analysis) if analysis else {}
                if isinstance(analysis_data.get("plan_total"), int):
                    collected = int(analysis_data.get("plan_collected") or 0)
                    total = int(analysis_data.get("plan_total") or 0)
            except Exception:
                pass
            return (
                f"evidence_items={collected}/{total}\n"
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

    def _archive_node_transition(
        self,
        run_id: str,
        node_name: str,
        state: WorkflowState,
        snapshot: Dict[str, Any],
        handoff: str,
    ) -> None:
        """Archive node output and node-to-node handoff for post-run debugging."""
        if not run_id:
            return
        try:
            payload = {
                "node": node_name,
                "snapshot": snapshot,
                "state_keys": sorted([str(k) for k in state.keys()]),
            }
            handoff_payload = {
                "from": node_name,
                "handoff_summary": handoff,
                "snapshot": snapshot,
            }
            ContextArchive(run_id=run_id).write_node_artifacts(
                node_id=node_name,
                output_payload=payload,
                handoff_payload=handoff_payload if handoff else None,
            )
        except Exception as exc:
            logger.warning("⚠️ [Workflow] 写入 node transition archive 失败 node=%s: %s", node_name, exc)

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
