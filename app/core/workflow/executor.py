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
import logging
import os
import queue
import re
import threading
import time
import uuid
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Optional, Tuple

from app.core.context.archive import ContextArchive
from app.core.diagnostics.report import write_run_report
from app.core.log_context import log_context
from app.core.remediation.agent import RemediationAgentConfig, RemediationAgentExecutor
from app.core.remediation.approval import approval_store
from app.core.remediation.executor import RemediationExecutor
from app.core.remediation.models import RemediationRuntimeConfig, normalize_remediation_mode
from app.core.remediation.plans import extract_remediation_plan
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.metrics import WorkflowMetrics
from app.core.workflow.reporter import (
    save_report as _save_report_fn,
)
from app.core.workflow.reporter import (
    update_metrics_from_state as _update_metrics_fn,
)
from app.core.workflow.state import WorkflowState
from app.core.workflow.stream_contract import (
    project_parallel_tool_event,
    project_query_tool_event,
    workflow_outcome,
)

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
    has_write_advice = any(re.search(pattern, text, re.IGNORECASE) for pattern in write_patterns)
    if not has_write_advice:
        return None
    actions = getattr(plan, "actions", None) if plan is not None else None
    remediation_available = (
        bool(getattr(plan, "remediation_available", False)) if plan is not None else False
    )
    if plan is None:
        return "natural-language remediation advice exists but no structured remediation plan was emitted"
    if not remediation_available or not actions:
        return "natural-language remediation advice exists but structured remediation actions are missing or disabled"
    return None


class _StreamTranslator:
    """Translate worker-queue items into SSE node/thinking/heartbeat events.

    Owns the per-run stream state: the monotonically increasing ``seq``, node
    timing bookkeeping and the merged ``final_state``. Node completion can be
    observed three ways (explicit lifecycle ``end``, the first thinking event
    of the next node, or the next LangGraph event), and every path funnels
    through :meth:`_complete_node` so snapshots, handoffs and archives match.
    """

    def __init__(
        self,
        executor: "WorkflowExecutor",
        run_id: str,
        metrics: WorkflowMetrics,
        final_state: WorkflowState,
        query_mode: str,
        *,
        heartbeat_interval_s: float,
    ):
        self.executor = executor
        self.run_id = run_id
        self.metrics = metrics
        self.final_state = final_state
        self.query_mode = query_mode
        self.heartbeat_interval_s = heartbeat_interval_s
        self.seq = 0
        self.last_event_ts = time.time()
        self.completed_nodes: set = set()
        self.current_nodes: set = set()
        self.node_start_times: Dict[str, float] = {}

    def next_seq(self) -> int:
        """Pre-increment ``seq`` for terminal events (final/remediation/run_end/error)."""
        self.seq += 1
        return self.seq

    def _emit(self, event: Dict[str, Any]) -> Generator[Dict, None, None]:
        """Yield a stream event stamped with the current seq, then advance."""
        yield event
        self.seq += 1
        self.last_event_ts = time.time()

    # ── main loop ──────────────────────────────────────────────────────

    def pump(
        self,
        event_queue: queue.Queue,
        worker: threading.Thread,
        cancel_event: Optional[threading.Event],
    ) -> Generator[Dict, None, None]:
        """Consume the worker queue until the graph finishes, fails or is cancelled."""
        while True:
            if cancel_event and cancel_event.is_set():
                logger.info("[Workflow] 收到取消信号，停止工作流 (run_id=%s)", self.run_id)
                return

            try:
                tag, data = event_queue.get(timeout=0.3)
            except queue.Empty:
                yield from self._maybe_heartbeat(worker)
                if not worker.is_alive():
                    return
                continue

            if tag == "node_lifecycle":
                yield from self._on_lifecycle(data)
            elif tag == "thinking":
                yield from self._on_thinking(data)
            elif tag == "langgraph_event":
                yield from self._on_langgraph_event(data)
            elif tag == "langgraph_done":
                return
            elif tag == "langgraph_error":
                raise data  # re-raise exception from worker thread

    def _maybe_heartbeat(self, worker: threading.Thread) -> Generator[Dict, None, None]:
        now = time.time()
        if (
            self.heartbeat_interval_s > 0
            and self.current_nodes
            and worker.is_alive()
            and now - self.last_event_ts >= self.heartbeat_interval_s
        ):
            # Name the stage actually running: the latest-started unfinished node (a
            # finished node can linger in current_nodes via a trailing LangGraph update).
            active = [n for n in self.current_nodes if n not in self.completed_nodes] or list(
                self.current_nodes
            )
            heartbeat_node_id = max(active, key=lambda n: (self.node_start_times.get(n, 0.0), n))
            yield {
                "type": "heartbeat",
                "id": f"{self.run_id}-heartbeat-{self.seq}",
                "run_id": self.run_id,
                "seq": self.seq,
                "ts_ms": int(now * 1000),
                "node": heartbeat_node_id,
                "node_name": self.executor._get_node_display_name(heartbeat_node_id),
            }
            self.seq += 1
            self.last_event_ts = now

    # ── queue item handlers ────────────────────────────────────────────

    def _on_lifecycle(self, data: Dict[str, Any]) -> Generator[Dict, None, None]:
        """Precise node timing reported by the graph's lifecycle wrapper."""
        node_id = data.get("node", "")
        node_name = data.get("node_name", self.executor._get_node_display_name(node_id))
        ts = data.get("ts", time.time())

        if data.get("phase") == "start":
            if node_id and node_id not in self.node_start_times:
                yield from self._start_node(node_id, node_name, ts=ts)

        elif data.get("phase") == "end" and node_id and node_id not in self.completed_nodes:
            state_update = data.get("state_update") or {}
            if state_update:
                self.final_state.update(state_update)
            self.metrics.finish_node(
                node_id,
                success=data.get("success", True),
                error=data.get("error"),
                end_ts=ts,
            )
            self.current_nodes.discard(node_id)
            duration_s = (
                self.metrics.nodes.get(node_id).duration_ms / 1000
                if node_id in self.metrics.nodes
                else 0
            )
            yield from self._complete_node(
                node_id, node_name=node_name, ts=ts, duration_s=duration_s
            )

    def _on_thinking(self, data: Dict[str, Any]) -> Generator[Dict, None, None]:
        """Real-time thinking event; synthesizes node_start for unseen nodes."""
        node_id = data.get("node", "")

        if node_id and node_id not in self.node_start_times:
            # ── 先 finish 上一个活跃节点（修复计时重叠） ──
            now = time.time()
            for prev_node in list(self.current_nodes):
                if prev_node not in self.completed_nodes:
                    self.metrics.finish_node(prev_node, success=True, end_ts=now)
                    prev_dur = now - self.node_start_times.get(prev_node, now)
                    yield from self._complete_node(
                        prev_node,
                        node_name=self.executor._get_node_display_name(prev_node),
                        ts=now,
                        duration_s=prev_dur,
                    )
            self.current_nodes = set()
            yield from self._start_node(node_id, self.executor._get_node_display_name(node_id))

        yield from self._emit(self._thinking_event(node_id, data))

    def _on_langgraph_event(self, lg_event: Dict[str, Any]) -> Generator[Dict, None, None]:
        """Fallback timing from LangGraph updates: a node absent from the next
        update is considered complete (skips nodes already finished above)."""
        new_nodes_in_this_event = set()
        for node_name, updated_state in lg_event.items():
            new_nodes_in_this_event.add(node_name)
            self.final_state.update(updated_state)
            if node_name not in self.node_start_times:
                yield from self._start_node(
                    node_name, self.executor._get_node_display_name(node_name)
                )

        for node_name in self.current_nodes:
            if node_name not in new_nodes_in_this_event and node_name not in self.completed_nodes:
                yield from self._complete_inferred_node(node_name)

        self.current_nodes = new_nodes_in_this_event

    def finalize_open_nodes(self) -> Generator[Dict, None, None]:
        """Finalize 剩余节点（最后一个节点）。"""
        for node_name in self.current_nodes:
            if node_name not in self.completed_nodes:
                yield from self._complete_inferred_node(node_name, include_handoff=False)

    # ── event builders ─────────────────────────────────────────────────

    def _start_node(
        self,
        node_id: str,
        node_name: str,
        *,
        ts: Optional[float] = None,
    ) -> Generator[Dict, None, None]:
        """Record and emit node_start. ``ts`` is the lifecycle-reported start;
        without it the start is observed now."""
        if ts is None:
            self.node_start_times[node_id] = time.time()
            self.metrics.start_node(node_id, node_name)
        else:
            self.node_start_times[node_id] = ts
            self.metrics.start_node(node_id, node_name, start_ts=ts)
        self.current_nodes.add(node_id)
        logger.info("[%s] %s 开始...", node_id, node_name)
        yield from self._emit(
            {
                "type": "node_start",
                "id": f"{self.run_id}-node_start-{node_id}",
                "run_id": self.run_id,
                "seq": self.seq,
                "ts_ms": int((time.time() if ts is None else ts) * 1000),
                "node": node_id,
                "node_name": node_name,
            }
        )

    def _complete_inferred_node(
        self,
        node_name: str,
        *,
        include_handoff: bool = True,
    ) -> Generator[Dict, None, None]:
        """Complete a node whose end was inferred rather than reported."""
        node_duration = time.time() - self.node_start_times.get(node_name, time.time())
        self.metrics.finish_node(node_name, success=True)
        yield from self._complete_node(
            node_name,
            node_name=self.executor._get_node_display_name(node_name),
            ts=None,
            duration_s=node_duration,
            include_handoff=include_handoff,
        )

    def _complete_node(
        self,
        node_id: str,
        *,
        node_name: str,
        ts: Optional[float],
        duration_s: float,
        include_handoff: bool = True,
    ) -> Generator[Dict, None, None]:
        """Snapshot, archive, log and emit node_complete for a finished node.

        ``ts=None`` stamps the event with the current time.
        ``include_handoff=False`` (end-of-run finalization) omits the handoff
        log lines and event field.
        """
        executor = self.executor
        self.completed_nodes.add(node_id)
        snapshot = executor._extract_state_snapshot(self.final_state, node_id)
        node_summary = executor._format_node_summary(node_id, self.final_state, snapshot)
        handoff = executor._format_handoff_summary(node_id, self.final_state)
        executor._archive_node_transition(
            self.run_id, node_id, self.final_state, snapshot, handoff
        )

        logger.info("[%s] 完成 (%.1fs)", node_id, duration_s)
        if node_summary:
            logger.info("   %s", node_summary)
        if include_handoff and handoff:
            handoff_short = handoff[:120] + "..." if len(handoff) > 120 else handoff
            logger.info("   传递给下游: %s", handoff_short)
            logger.debug("   [DEBUG] 完整传递数据:\n%s", handoff)

        event = {
            "type": "node_complete",
            "id": f"{self.run_id}-node_complete-{node_id}",
            "run_id": self.run_id,
            "seq": self.seq,
            "ts_ms": int((time.time() if ts is None else ts) * 1000),
            "node": node_id,
            "node_name": node_name,
            "duration_seconds": round(duration_s, 3),
            "state_snapshot": snapshot,
        }
        if include_handoff:
            event["handoff_summary"] = handoff
        yield from self._emit(event)

    def _thinking_event(self, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "thinking",
            "id": f"{self.run_id}-thinking-{node_id}-{self.seq}",
            "run_id": self.run_id,
            "node": node_id,
            "node_name": self.executor._get_node_display_name(node_id),
            "thinking_type": data.get("type", ""),
            "tool_name": data.get("tool_name"),
            "content": data.get("content"),
            **(
                {"full_content": data["full_content"]}
                if data.get("type") == "ai_message" and data.get("full_content") is not None
                else {}
            ),
            "status": data.get("status"),
            "result_preview": data.get("result_preview"),
            "duration_seconds": data.get("duration_seconds"),
            "iteration": data.get("iteration"),
            "ts_ms": data.get("ts_ms", int(time.time() * 1000)),
            **project_parallel_tool_event(data),
            **(project_query_tool_event(data) if self.query_mode in {"auto", "direct"} else {}),
        }


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
        self.ai_call = None  # Set externally to enable aicall path
        self.mcp_tools = []  # Set externally (list of tool defs for aicall)
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

    def execute_stream(self, question, run_id=None, cancel_event=None, workflow_overrides=None):
        from app.core.query_sessions import SessionBusy, query_sessions
        from app.core.remediation.records import PlanConflict, RecordUnavailable, RepairRecordStore

        overrides = dict(workflow_overrides or {})
        key = overrides.pop("_query_session_key", None)
        if not key:
            yield from self._execute_stream(question, run_id, cancel_event, overrides)
            return
        try:
            store = RepairRecordStore()
            diagnosis_id, plan_id = (
                overrides.get("_diagnosis_run_id"),
                overrides.get("_plan_run_id"),
            )
            record = (
                store.load(plan_id or diagnosis_id, key[0], "plan" if plan_id else "diagnosis")
                if plan_id or diagnosis_id
                else store.latest(key[0], key[1])
            )
            context = {}
            if record:
                if record["kind"] == "plan":
                    context["previous_plan"] = record
                    if record.get("source_run_id"):
                        context["diagnosis"] = store.load(
                            record["source_run_id"], key[0], "diagnosis"
                        )
                else:
                    context["diagnosis"] = record
            group_id = overrides.get("_repair_group_id")
            if group_id and context.get("diagnosis"):
                from app.core.remediation.group_context import scoped_diagnosis

                context["diagnosis"] = scoped_diagnosis(context["diagnosis"], group_id)
            if plan_id and not overrides.get("_repair_revision_claimed"):
                context["previous_plan"] = store.supersede(plan_id, key[0])
                # The previous waiting executor observes supersession and releases
                # its session reservation. Do not race a second active writer.
                deadline = time.monotonic() + 5
                while query_sessions.is_busy(key) and time.monotonic() < deadline:
                    time.sleep(0.1)
            overrides["_repair_context"] = context
            overrides["_repair_entry_requested"] = bool(diagnosis_id or plan_id)
            overrides["_record_session_id"] = key[1]
            with query_sessions.checkout(key) as (memory, commit):
                if not memory and record:
                    payload = (
                        (context.get("diagnosis") or record)["payload"]
                        if group_id
                        else record["payload"]
                    )
                    memory = {
                        "turns": [
                            {
                                "question": payload.get("question") or "历史修复方案",
                                "answer": (
                                    (context.get("diagnosis") or {})
                                    .get("payload", {})
                                    .get("report")
                                    if group_id
                                    else payload.get("report")
                                )
                                or (payload.get("draft") or {}).get("answer", ""),
                                "request_contract": payload.get("request_contract"),
                                "observed_at": record["created_at"],
                            }
                        ]
                    }
                overrides["_remediation_owner"] = key[0]
                overrides["_query_session_context"] = memory
                for event in self._execute_stream(question, run_id, cancel_event, overrides):
                    snapshot = event.pop("_query_session_memory", None)
                    if event.get("type") == "run_start":
                        event["session_id"] = key[1]
                        event["session_memory"] = "restored" if memory else "empty"
                    if event.get("type") == "final" and snapshot is not None:
                        saved = not (cancel_event and cancel_event.is_set()) and commit(snapshot)
                        event["session_id"] = key[1]
                        event["session_memory"] = "saved" if saved else "not_saved"
                        if not saved:
                            event["answer"] += (
                                "\n\n会话记忆未保存（已取消或超过缓存容量），下轮请明确查询对象。"
                            )
                    yield event
        except (SessionBusy, RecordUnavailable, PlanConflict) as exc:
            yield {"type": "error", "error": str(exc), "session_id": key[1]}

    def _execute_stream(
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
        overrides = workflow_overrides or {}

        metrics = self._start_metrics(run_id, question)
        wf_config, query_mode = self._resolve_workflow_config(workflow_overrides)
        workflow, node_instances = self._build_request_workflow(
            metrics,
            wf_config,
            query_mode,
            run_id,
            cancel_event,
        )

        total_start = time.time()
        initial_state = self._build_initial_state(question, run_id, overrides)

        logger.info("工作流开始: run_id=%s", run_id)
        yield {
            "type": "run_start",
            "id": f"{run_id}-run_start",
            "run_id": run_id,
            "seq": 0,
            "ts_ms": int(time.time() * 1000),
            "question": question,
            "timestamp": datetime.now().isoformat(),
        }

        stream = _StreamTranslator(
            self,
            run_id,
            metrics,
            initial_state.copy(),
            query_mode,
            heartbeat_interval_s=self._get_heartbeat_interval_seconds(),
        )
        # 共享事件队列：不设上限，消费者提前退出（断连）时生产者不会阻塞在 put()
        # 而错过取消信号；取消后工作线程会很快收敛，积压有界。
        event_queue: queue.Queue = queue.Queue()

        worker: Optional[threading.Thread] = None
        try:
            # 设置节点级事件队列（per-request，并发安全）
            for node in node_instances:
                node.set_event_queue(event_queue)

            worker = threading.Thread(
                target=self._run_workflow_worker,
                args=(workflow, initial_state, event_queue, run_id),
                daemon=True,
            )
            worker.start()

            yield from stream.pump(event_queue, worker, cancel_event)
            self._join_worker_if_needed(worker, timeout=5)
            yield from stream.finalize_open_nodes()

            yield from self._finish_run(
                question,
                run_id,
                metrics,
                stream,
                wf_config,
                query_mode,
                overrides,
                cancel_event,
                total_start,
            )

        except Exception as e:
            logger.error("工作流执行失败: %s", e, exc_info=True)
            metrics.success = False
            metrics.errors.append(str(e))
            metrics.finish()

            from app.core.aicall.errors import model_error_code, model_transport_message

            public_error = model_transport_message(e)
            error_code = model_error_code(e)
            seq = stream.next_seq()
            yield {
                "type": "error",
                "id": f"{run_id}-error",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "error": public_error or str(e),
                **({"error_code": error_code} if error_code else {}),
            }
        finally:
            # Normal completion is not user cancellation. Only stop a still
            # running worker when its consumer exits early.
            if cancel_event and worker is not None and worker.is_alive():
                cancel_event.set()
            # 清除事件队列（实例级，无需类级别清理）+ 等待后台线程结束
            for node in node_instances:
                node.set_event_queue(None)
            worker_alive = self._join_worker_if_needed(
                worker,
                timeout=5,
            )
            if worker_alive and worker is not threading.current_thread():
                logger.warning("[Workflow] 后台线程未在 5s 内结束 (run_id=%s)", run_id)

    # ── per-request preparation ────────────────────────────────────────

    def _start_metrics(self, run_id: str, question: str) -> WorkflowMetrics:
        """每次请求独立创建指标；若注入了共享 metrics 则重置后复用。"""
        if self.metrics is None:
            return WorkflowMetrics(run_id=run_id, question=question)
        metrics = self.metrics
        metrics.run_id = run_id
        metrics.question = question
        metrics.start_time = time.time()
        return metrics

    def _resolve_workflow_config(
        self,
        workflow_overrides: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], str]:
        """Merge per-request overrides into a private copy of workflow_config.

        Returns ``(wf_config, query_mode)``. Dict overrides are shallow-merged
        into the matching config section; ``query_mode`` is normalized and only
        kept in the config when the request set it explicitly.
        """
        wf_config = copy.deepcopy(getattr(self.holmes_service, "workflow_config", {}) or {})
        if workflow_overrides:
            for key, value in workflow_overrides.items():
                if isinstance(value, dict) and isinstance(wf_config.get(key), dict):
                    merged = dict(wf_config.get(key, {}))
                    merged.update(value)
                    wf_config[key] = merged
                else:
                    wf_config[key] = value
        query_mode = "auto"
        if workflow_overrides:
            query_mode = (
                str(workflow_overrides.get("query_mode", "auto")).strip().lower() or "auto"
            )
        wf_config.pop("query_mode", None)
        if workflow_overrides and "query_mode" in workflow_overrides:
            wf_config["query_mode"] = query_mode
        return wf_config, query_mode

    def _build_request_workflow(
        self,
        metrics: WorkflowMetrics,
        wf_config: Dict[str, Any],
        query_mode: str,
        run_id: str,
        cancel_event: Optional[threading.Event],
    ) -> Tuple[Any, list]:
        """每次请求重建 workflow（并发安全，避免共享节点实例）并下发请求元数据。"""
        evidence_cfg = wf_config.get("evidence", {}) if isinstance(wf_config, dict) else {}
        parallel_config = (
            evidence_cfg.get("parallel", {}) if isinstance(evidence_cfg, dict) else {}
        )
        workflow, node_instances = build_diagnosis_workflow(
            self.holmes_service,
            metrics,
            self.runbook_catalog,
            node_config=wf_config.get("nodes", {}),
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
                logger.debug(
                    "   [%s] ai_call=%s tools=%d",
                    node.node_id,
                    type(node.ai_call).__name__,
                    len(node.tools),
                )
        return workflow, node_instances

    @staticmethod
    def _build_initial_state(
        question: str,
        run_id: str,
        overrides: Dict[str, Any],
    ) -> WorkflowState:
        return {
            "repair_context": overrides.get("_repair_context"),
            "repair_entry_requested": bool(overrides.get("_repair_entry_requested")),
            "repair_auto_plan": bool(overrides.get("_auto_repair_plan")),
            "question": question,
            "original_question": question,
            "request_time_utc": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "layer": None,
            "layers": [],
            "layer_confidence": None,
            "layer_reasoning": None,
            "layer_analysis": None,
            "layer_handoff": None,
            "context_budget": None,
            "tool_artifact_refs": [],
            "key_entities": [],
            "possible_scenarios": [],
            "evidence_items": [],
            "tool_results": [],
            "evidence_completeness": None,
            "evidence_analysis": None,
            "missing_evidence": [],
            "deterministic_decision": None,
            "root_cause": None,
            "causal_chain": None,
            "rca_analysis": None,
            "primary_runbook_id": None,
            "conclusion": None,
            "conclusion_formatted": None,
            "errors": [],
            "warnings": [],
            "thinking_events": [],
            "query_session_context": overrides.get("_query_session_context", {}),
        }

    def _run_workflow_worker(
        self,
        workflow: Any,
        initial_state: WorkflowState,
        event_queue: queue.Queue,
        run_id: str,
    ) -> None:
        """在后台线程中运行 LangGraph workflow.stream()，结果写入事件队列。"""
        try:
            with log_context(run=run_id), self._langfuse_session_scope(run_id):
                for lg_event in workflow.stream(initial_state):
                    event_queue.put(("langgraph_event", lg_event))
            event_queue.put(("langgraph_done", None))
        except Exception as exc:
            event_queue.put(("langgraph_error", exc))

    # ── run completion ─────────────────────────────────────────────────

    def _finish_run(
        self,
        question: str,
        run_id: str,
        metrics: WorkflowMetrics,
        stream: "_StreamTranslator",
        wf_config: Dict[str, Any],
        query_mode: str,
        overrides: Dict[str, Any],
        cancel_event: Optional[threading.Event],
        total_start: float,
    ) -> Generator[Dict, None, None]:
        """Finalize metrics, emit ``final``, run remediation, emit ``run_end``."""
        final_state = stream.final_state

        self._update_metrics_from_state(metrics, final_state)
        metrics.rebuild_runtime_counts(final_state.get("thinking_events", []))
        outcome = workflow_outcome(final_state)
        metrics.success = outcome == "success"
        metrics.finish()

        conclusion, full_answer, public_metrics = self._compose_answer(
            metrics,
            final_state,
            query_mode,
        )
        task_route = final_state.get("request_route")
        self._save_report(final_state.get("layer"), question, full_answer)
        self._log_timing_breakdown(metrics)
        write_run_report(
            run_id,
            final_state=final_state,
            node_durations_ms={k: v.duration_ms for k, v in metrics.nodes.items()},
            elapsed_seconds=time.time() - total_start,
            outcome=outcome,
        )

        dispatch = final_state.get("remediation_dispatch")
        if dispatch:
            # Chat repair handed to per-group jobs: no single-agent plan record or inline run.
            repair_record, record_store, record_failed = None, None, False
        else:
            repair_record, record_store, record_failed = self._persist_repair_record(
                run_id,
                question,
                final_state,
                overrides,
            )
        repair_batch, batch_note = self._start_repair_batch(
            question, final_state, overrides, repair_record
        )
        if batch_note:
            full_answer += f"\n\n{batch_note}"
        if record_failed:
            if task_route == "remediation":
                final_state["remediation_draft"] = None
            full_answer += "\n\n诊断/方案记录保存失败，本次不会自动执行修复，请重试。"

        seq = stream.next_seq()
        yield {
            "type": "final",
            "id": f"{run_id}-final",
            "run_id": run_id,
            "seq": seq,
            "ts_ms": int(time.time() * 1000),
            "status": outcome,
            "answer": full_answer,
            "answer_source": "workflow",
            "elapsed_seconds": round(time.time() - total_start, 3),
            "metrics": public_metrics,
            "request_route": task_route,
            "request_contract": final_state.get("request_contract"),
            "request_error": final_state.get("request_error"),
            "focused_result": final_state.get("focused_result"),
            "query_answer": final_state.get("query_answer"),
            "diagnosis_cases": final_state.get("diagnosis_cases"),
            "diagnosis_overview": final_state.get("diagnosis_overview"),
            "diagnosis_footer": full_answer[len(conclusion) :]
            if final_state.get("diagnosis_cases") is not None
            else None,
            "repair_record": (
                {
                    "run_id": run_id,
                    "kind": repair_record["kind"],
                    "source_run_id": repair_record.get("source_run_id"),
                    "repairable": self._record_repairable(repair_record),
                }
                if repair_record
                else None
            ),
            "repair_plan": final_state.get("remediation_draft")
            if task_route == "remediation"
            else None,
            "repair_batch": repair_batch,
            **(
                {"_query_session_memory": final_state.get("query_session_memory")}
                if overrides.get("_query_session_context") is not None
                else {}
            ),
        }

        if not dispatch:
            yield from self._remediation_events(
                run_id,
                stream,
                wf_config,
                overrides,
                full_answer,
                cancel_event,
                record_store if repair_record else None,
            )

        seq = stream.next_seq()
        yield {
            "type": "run_end",
            "id": f"{run_id}-run_end",
            "run_id": run_id,
            "seq": seq,
            "ts_ms": int(time.time() * 1000),
            "elapsed_seconds": round(time.time() - total_start, 3),
        }

    @staticmethod
    def _compose_answer(
        metrics: WorkflowMetrics,
        final_state: WorkflowState,
        query_mode: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Return ``(conclusion, full_answer, public_metrics)``.

        Conclusion 只负责根因报告正文；Runbook 使用与执行耗时来自确定性
        WorkflowMetrics，在工作流全部结束后统一追加。质量评分是否展示仍由
        METRICS_ENABLED 控制，避免让 LLM 编造运行统计。
        """
        from app.core.workflow.metrics import METRICS_ENABLED

        conclusion = final_state.get("conclusion_formatted") or final_state.get("conclusion") or ""
        stats_block = metrics.format_stats_block()
        task_route = final_state.get("request_route")
        lightweight_task = query_mode in {"auto", "direct"} or task_route in {
            "focused",
            "query",
            "clarify",
            "stop",
        }
        metrics_block = metrics.format_metrics_block(
            enabled=METRICS_ENABLED and not lightweight_task
        )
        public_metrics = metrics.get_summary()
        if lightweight_task:
            public_metrics = {
                key: public_metrics[key]
                for key in ("run_id", "performance", "nodes", "success", "errors")
            }
            public_metrics["diagnosis_metrics_applicable"] = False
        return conclusion, f"{conclusion}\n{stats_block}\n{metrics_block}", public_metrics

    @staticmethod
    def _log_timing_breakdown(metrics: WorkflowMetrics) -> None:
        logger.info("工作流完成: 耗时 %s", metrics.mttr_formatted)
        logger.info("=" * 60)
        logger.info("[耗时分析] 各节点耗时明细:")
        for node in metrics.nodes.values():
            pct = (
                (node.duration_ms / metrics.total_duration_ms * 100)
                if metrics.total_duration_ms > 0
                else 0
            )
            logger.info("   %s: %.1fs (%.0f%%)", node.node_name, node.duration_ms / 1000, pct)
        logger.info(
            "   模型请求耗时: %.1fs (%s 次)",
            metrics.total_llm_duration_ms / 1000,
            metrics.total_llm_calls,
        )
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
        logger.info("   总计: %.1fs", metrics.total_duration_seconds)
        logger.info("=" * 60)

    @staticmethod
    def _record_repairable(record: Dict[str, Any]) -> bool:
        """Whether a saved record still has something to repair (diagnosis: an open group)."""
        if record.get("kind") != "diagnosis":
            return True
        from app.core.remediation.group_context import repairable_groups

        return bool(repairable_groups(record))

    def _repair_mode_is_auto(self) -> bool:
        """Effective remediation mode (config plus any runtime override) is auto and enabled."""
        from app.core.remediation.settings import repair_settings

        wf_config = getattr(self.holmes_service, "workflow_config", None) or {}
        cfg = wf_config.get("remediation") if isinstance(wf_config, dict) else None
        effective = repair_settings.effective(cfg if isinstance(cfg, dict) else {})
        return bool(effective["enabled"]) and effective["mode"] == "auto"

    def _start_repair_batch(
        self,
        question: str,
        final_state: WorkflowState,
        overrides: Dict[str, Any],
        repair_record: Optional[Dict[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Start the per-group repair batch a request asked for; ``(batch, note)``.

        Two entries share the button's batch: a chat repair request the remediation node
        dispatched, and ``/ask ... repair=plan`` after a deep diagnosis. Planning only:
        every command still goes through policy, approval or auto mode, and recovery.
        """
        dispatch = final_state.get("remediation_dispatch")
        owner = overrides.get("_remediation_owner")
        if dispatch:
            diagnosis_id, group_ids = dispatch.get("diagnosis_run_id"), dispatch.get("group_ids")
            if not group_ids:
                return None, ""
        elif (
            overrides.get("_auto_repair_plan")
            and repair_record
            and repair_record.get("kind") == "diagnosis"
        ):
            diagnosis_id, group_ids = repair_record["run_id"], None
        elif (
            repair_record
            and repair_record.get("kind") == "diagnosis"
            and self._repair_mode_is_auto()
            and self._record_repairable(repair_record)
        ):
            # auto mode: plan, approve and run without a click; only a blocked command
            # waits for a person (the job ends as blocked and takes feedback).
            diagnosis_id, group_ids = repair_record["run_id"], None
        else:
            return None, ""
        if not owner:
            return None, "修复任务需要会话身份（session_id），本次未创建。"
        from app.core.remediation.jobs import repair_jobs
        from app.core.remediation.records import PlanConflict, RecordUnavailable

        try:
            batch = repair_jobs.start(
                self.holmes_service, owner, diagnosis_id, question, group_ids=group_ids
            )
        except (PlanConflict, RecordUnavailable) as exc:
            return None, str(exc)
        return (
            {
                "batch_id": batch["batch_id"],
                "diagnosis_run_id": diagnosis_id,
                "groups": [
                    {k: g.get(k) for k in ("group_id", "job_id", "status", "target")}
                    for g in batch.get("groups") or []
                ],
            },
            "",
        )

    @staticmethod
    def _persist_repair_record(
        run_id: str,
        question: str,
        final_state: WorkflowState,
        overrides: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Any, bool]:
        """Save the diagnosis/plan record for session-owned repair flows.

        Returns ``(record, store, failed)``; ``record`` is None when the run
        produces no record or persistence failed.
        """
        record_owner = overrides.get("_remediation_owner")
        task_route = final_state.get("request_route")
        if not (record_owner and task_route in {"full_diagnosis", "remediation"}):
            return None, None, False
        from app.core.remediation.records import RepairRecordStore, diagnosis_payload

        store = RepairRecordStore()
        context = overrides.get("_repair_context") or {}
        try:
            record = store.save(
                run_id,
                record_owner,
                overrides.get("_record_session_id"),
                "diagnosis" if task_route == "full_diagnosis" else "plan",
                diagnosis_payload(final_state)
                if task_route == "full_diagnosis"
                else {
                    "question": question,
                    "request_contract": final_state.get("request_contract"),
                    "draft": final_state.get("remediation_draft"),
                    "group_id": overrides.get("_repair_group_id"),
                },
                source_run_id=(context.get("diagnosis") or {}).get("run_id"),
                previous_plan_id=(context.get("previous_plan") or {}).get("run_id"),
            )
        except Exception:
            logger.exception("Repair record persistence failed; execution disabled for this run")
            return None, store, True
        return record, store, False

    # ── remediation ────────────────────────────────────────────────────

    def _remediation_events(
        self,
        run_id: str,
        stream: "_StreamTranslator",
        wf_config: Dict[str, Any],
        overrides: Dict[str, Any],
        full_answer: str,
        cancel_event: Optional[threading.Event],
        record_store: Any,
    ) -> Generator[Dict, None, None]:
        """Run the configured remediation executor after the final answer."""
        final_state = stream.final_state
        remediation_cfg = wf_config.get("remediation", {}) if isinstance(wf_config, dict) else {}
        remediation_enabled = False
        if isinstance(remediation_cfg, dict):
            remediation_enabled = bool(remediation_cfg.get("enabled", False))
        if overrides.get("_defer_repair_execution"):
            remediation_enabled = False
        if final_state.get("request_route") in {
            "focused",
            "query",
            "clarify",
            "stop",
            "full_diagnosis",
        }:
            # A read-only task must not become a write workflow because the
            # final prose happens to contain a remediation-shaped block.
            remediation_enabled = False
        if not remediation_enabled:
            return
        if (
            final_state.get("request_route") in {"remediation", "full_diagnosis"}
            or remediation_cfg.get("executor") == "pod"
        ):
            yield from self._pod_remediation_events(
                run_id,
                stream,
                remediation_cfg,
                overrides,
                cancel_event,
                record_store,
            )
            return
        yield from self._plan_remediation_events(run_id, stream, remediation_cfg, full_answer)

    def _pod_remediation_events(
        self,
        run_id: str,
        stream: "_StreamTranslator",
        remediation_cfg: Dict[str, Any],
        overrides: Dict[str, Any],
        cancel_event: Optional[threading.Event],
        record_store: Any,
    ) -> Generator[Dict, None, None]:
        from app.core.remediation.pod_executor import PodRepairExecutor
        from app.core.remediation.policy import CommandPolicy
        from app.core.remediation.recovery import RecoveryConfig
        from app.core.remediation.settings import repair_settings

        final_state = stream.final_state
        policy = CommandPolicy.from_config(remediation_cfg)
        effective = repair_settings.effective(remediation_cfg)
        for repair_event in PodRepairExecutor().run(
            run_id,
            final_state.get("remediation_draft"),
            owner=overrides.get("_remediation_owner", ""),
            mode=effective["mode"],
            timeout=int(effective["approval_timeout_seconds"]),
            cancel=cancel_event,
            policy=policy,
            request_contract=final_state.get("request_contract"),
            record_store=record_store,
            recovery=RecoveryConfig.from_config(remediation_cfg),
            max_duration=_int_config(remediation_cfg, "max_duration_seconds", 0),
        ):
            seq = stream.next_seq()
            yield {
                **repair_event,
                "id": f"{run_id}-repair-{seq}",
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
            }
            if repair_event.get("type") == "remediation_finished":
                final_state["remediation_result"] = repair_event

    @staticmethod
    def _plan_remediation_settings(
        remediation_cfg: Any,
    ) -> Tuple[int, str, str, RemediationRuntimeConfig]:
        """Return ``(approval_timeout, approval_mode, executor_type, runtime_config)``."""
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
            remediation_executor_type = (
                str(
                    remediation_cfg.get("executor")
                    or remediation_cfg.get("strategy")
                    or "deterministic"
                )
                .strip()
                .lower()
            )
            runtime_config = RemediationRuntimeConfig(
                executor=remediation_executor_type,
                max_iterations=_int_config(remediation_cfg, "max_iterations", 4),
                max_write_actions=_int_config(remediation_cfg, "max_write_actions", 2),
                max_duration_seconds=_int_config(remediation_cfg, "max_duration_seconds", 900),
                verify_settle_seconds=_float_config(remediation_cfg, "verify_settle_seconds", 0.0),
            )
        return approval_timeout, approval_mode, remediation_executor_type, runtime_config

    @staticmethod
    def _validate_remediation_plan(
        run_id: str,
        full_answer: str,
        final_state: WorkflowState,
    ) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Parse the report's structured plan; return ``(plan, invalid_plan_event)``.

        A parsed plan is recorded in ``final_state["remediation_plan"]``.
        """
        plan = None
        invalid_plan_event = None
        try:
            plan = extract_remediation_plan(full_answer)
        except ValueError as exc:
            logger.warning(
                "invalid remediation plan | run_id=%s error=%s",
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
        if invalid_plan_event is None:
            missing_actions_reason = _missing_structured_actions_reason(full_answer, plan)
            if missing_actions_reason:
                logger.warning(
                    "invalid remediation plan | run_id=%s error=%s",
                    run_id,
                    missing_actions_reason,
                )
                invalid_plan_event = _invalid_remediation_plan_event(
                    run_id,
                    ValueError(missing_actions_reason),
                )
        return plan, invalid_plan_event

    def _plan_remediation_events(
        self,
        run_id: str,
        stream: "_StreamTranslator",
        remediation_cfg: Dict[str, Any],
        full_answer: str,
    ) -> Generator[Dict, None, None]:
        """Extract the structured plan from the report and execute it."""
        final_state = stream.final_state
        approval_timeout, approval_mode, remediation_executor_type, runtime_config = (
            self._plan_remediation_settings(remediation_cfg)
        )
        plan, invalid_plan_event = self._validate_remediation_plan(
            run_id, full_answer, final_state
        )

        if invalid_plan_event is not None:
            seq = stream.next_seq()
            yield {
                **invalid_plan_event,
                "id": f"{run_id}-remediation_finished-{seq}",
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
            }
            final_state["remediation_result"] = invalid_plan_event
            return

        if remediation_executor_type in {"react", "agent", "llm"}:
            remediation_run = RemediationAgentExecutor(
                approval_store=approval_store,
                ai_call=self.ai_call,
            ).run(
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
            remediation_run = RemediationExecutor(approval_store=approval_store).run(
                run_id=run_id,
                plan=plan,
                approval_timeout_seconds=approval_timeout,
                approval_mode=approval_mode,
            )
        last_remediation_event = None
        for remediation_event in remediation_run:
            last_remediation_event = remediation_event
            seq = stream.next_seq()
            yield {
                **remediation_event,
                "id": f"{run_id}-{remediation_event.get('type', 'remediation')}-{seq}",
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
            }
        if isinstance(last_remediation_event, dict):
            final_state["remediation_result"] = last_remediation_event

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
            logger.debug("[Workflow] Langfuse session propagation 不可用，直接执行: %s", exc)
            yield
            return

        logger.debug("[Workflow] Langfuse session_id=%s", session_id)
        with propagate_attributes(session_id=session_id):
            yield

    def _get_node_display_name(self, node_id: str) -> str:
        """获取节点显示名称"""
        name_map = {
            "request_router": "理解用户任务",
            "focused": "按问题查询与分析",
            "query_collect": "自主运维查询与分析",
            "layer": "问题定位",
            "evidence": "证据链采集",
            "rca": "根因分析",
            "conclusion": "汇总总结",
            "remediation": "修复与执行",
        }
        return name_map.get(node_id, node_id)

    def _extract_state_snapshot(self, state: WorkflowState, node_name: str) -> Dict[str, Any]:
        """提取状态快照（用于调试和日志）

        设计：
        - 包含完整的分析 JSON (layer_analysis, evidence_analysis, rca_analysis)
        - 用于 service.py 中收集并显示所有节点的完整输出
        """
        snapshot = {}

        # Live parallel node output. Without autonomous_group_results (the node
        # failed before returning) parallel_evidence has no snapshot.
        if node_name == "parallel_evidence" and state.get("autonomous_group_results") is not None:
            return {
                "autonomous_groups": state.get("autonomous_groups"),
                "groups": [
                    {k: result.get(k) for k in ("group_id", "target", "status", "error", "run_id")}
                    for result in state.get("autonomous_group_results") or []
                ],
            }

        if state.get("query_draft") is not None and node_name in {"layer", "evidence", "rca"}:
            return {
                "question": state.get("original_question") or state.get("question"),
                "autonomous_groups": state.get("autonomous_groups"),
                "request_contract": state.get("request_contract"),
                "diagnosis_handoff": state.get("diagnosis_handoff"),
                "analysis_draft": state.get("query_draft"),
            }

        if node_name == "request_router":
            snapshot = {
                "request_route": state.get("request_route"),
                "request_contract": state.get("request_contract"),
                "request_error": state.get("request_error"),
            }
        elif node_name == "focused":
            snapshot = {
                "focused_result": state.get("focused_result"),
                "conclusion": state.get("conclusion"),
            }
        elif node_name == "layer":
            layers = state.get("layers", [])
            snapshot = {
                "layer": str(state.get("layer", "")),
                "layers": [l.value if hasattr(l, "value") else str(l) for l in layers],
                "layer_confidence": state.get("layer_confidence"),
                "layer_reasoning": state.get("layer_reasoning") or "",
                "layer_analysis": state.get("layer_analysis", ""),
                "key_entities": state.get("key_entities", []),
                "possible_scenarios": state.get("possible_scenarios", []),
            }
        elif node_name == "evidence":
            evidence_items = state.get("evidence_items", [])
            evidence_analysis = state.get("evidence_analysis", "")
            collected = sum(1 for e in evidence_items if getattr(e, "collected", False))
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
                    serialized_evidence_items.append(
                        {
                            "id": getattr(item, "id", ""),
                            "description": getattr(item, "description", ""),
                            "level": str(
                                getattr(
                                    getattr(item, "level", ""), "value", getattr(item, "level", "")
                                )
                            ),
                            "collected": bool(getattr(item, "collected", False)),
                            "value": getattr(item, "value", None),
                            "source": getattr(item, "source", None),
                        }
                    )
            snapshot = {
                "evidence_count": count,
                "collected_count": collected,
                "completeness": state.get("evidence_completeness"),
                "evidence_analysis": evidence_analysis,
                "evidence_items": serialized_evidence_items,
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

    def _format_node_summary(self, node_name: str, state: WorkflowState, snapshot: Dict) -> str:
        """格式化节点摘要（用于日志输出）"""
        if "analysis_draft" in snapshot:
            return "阶段分析已完成，证据与判断见阶段输出"
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

        if state.get("diagnosis_handoff") is not None and node_name in {
            "layer",
            "evidence",
            "rca",
        }:
            return _json.dumps(state["diagnosis_handoff"], ensure_ascii=False)

        if state.get("query_draft") is not None and node_name in {"layer", "evidence", "rca"}:
            return (
                f"用户问题：{state.get('original_question') or state.get('question', '')}\n"
                f"本阶段分析草稿（非程序核验结论）：\n{state.get('query_draft', '')}"
            )

        if node_name == "layer":
            layer = state.get("layer", "?")
            layers = state.get("layers", [])
            scenarios = state.get("possible_scenarios", [])
            entities = state.get("key_entities", [])
            analysis = state.get("layer_analysis", "")
            reasoning = state.get("layer_reasoning", "")
            layers_str = (
                "+".join(l.value if hasattr(l, "value") else str(l) for l in layers)
                if layers
                else str(layer)
            )
            return (
                f"layer={layer}, layers={layers_str}\n"
                f"   scenarios={scenarios}\n"
                f"   entities={_json.dumps(entities, ensure_ascii=False)}\n"
                f"   reasoning={reasoning}\n"
                f"   layer_analysis={analysis}"
            )
        elif node_name == "evidence":
            items = state.get("evidence_items", [])
            collected = sum(1 for e in items if getattr(e, "collected", False))
            total = len(items)
            analysis = state.get("evidence_analysis", "")
            try:
                analysis_data = _json.loads(analysis) if analysis else {}
                if isinstance(analysis_data.get("plan_total"), int):
                    collected = int(analysis_data.get("plan_collected") or 0)
                    total = int(analysis_data.get("plan_total") or 0)
            except Exception:
                pass
            return f"evidence_items={collected}/{total}\n   evidence_analysis={analysis}"
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
            logger.warning(
                "[Workflow] 写入 node transition archive 失败 node=%s: %s", node_name, exc
            )

    def _update_metrics_from_state(self, metrics: WorkflowMetrics, state: WorkflowState):
        """从最终状态更新指标"""
        _update_metrics_fn(
            metrics,
            state,
            runbook_catalog=self.runbook_catalog,
            holmes_service=self.holmes_service,
        )
