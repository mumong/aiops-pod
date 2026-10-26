"""A2A AgentExecutor backed by the existing AIOps SSE API."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part, TaskState, TextPart
from a2a.utils import new_agent_parts_message, new_agent_text_message

from a2a_adapter.backend import AiopsBackendClient, BackendError

logger = logging.getLogger(__name__)

# Repair job statuses that can still change (mirrors the backend's ACTIVE_JOB_STATUSES).
ACTIVE_JOB_STATUSES = frozenset(
    {"queued", "planning", "planned", "awaiting_approval", "executing", "verifying"}
)
_DECISION = re.compile(
    r"(批准|同意|approve|拒绝|驳回|reject)\s*[:：]?\s*([A-Za-z0-9_-]{6,64})", re.I
)


def clarification_needed(final: dict[str, Any]) -> bool:
    """The backend asked the caller a question instead of answering (e.g. which cluster)."""
    answer = final.get("query_answer")
    return final.get("request_route") == "clarify" or (
        isinstance(answer, dict) and answer.get("status") == "clarify"
    )


def group_label(group_id: str) -> str:
    match = re.fullmatch(r"g(\d+)", str(group_id or ""))
    return (
        f"异常组 {match.group(1)}"
        if match
        else ("整体诊断" if group_id == "single" else str(group_id))
    )


class AiopsAgentExecutor(AgentExecutor):
    """Translate A2A tasks into isolated /ask or /query executions."""

    _PROGRESS_LABELS = {
        "layer": "正在识别问题范围和当前异常",
        "evidence": "正在采集诊断证据",
        "parallel_evidence": "正在并行采集各异常对象的证据",
        "rca": "正在分析根因",
        "conclusion": "正在生成诊断报告",
        "query_collect": "正在根据问题自主查询与分析",
    }

    def __init__(self, backend: AiopsBackendClient) -> None:
        self.backend = backend
        self._cancel_events: dict[str, asyncio.Event] = {}
        # task_id -> repair batch it is paused on (also recoverable from task history).
        self._waiting_batches: dict[str, str] = {}
        self._cancel_lock = asyncio.Lock()

    @staticmethod
    def _mode(context: RequestContext) -> str:
        """Default to autonomous QUERY; diagnosis/ask keeps /ask; repair adds a repair batch."""
        candidates: list[Any] = [
            context.metadata.get("aiops_mode"),
            context.metadata.get("mode"),
        ]
        if context.message and context.message.metadata:
            candidates.extend(
                [
                    context.message.metadata.get("aiops_mode"),
                    context.message.metadata.get("mode"),
                ]
            )
        for value in candidates:
            mode = str(value or "").strip().lower()
            if mode == "query":
                return "query"
            if mode in {"diagnosis", "ask"}:
                return "diagnosis"
            if mode == "repair":
                return "repair"
        return "query"

    @staticmethod
    def _message(text: str, context: RequestContext):
        return new_agent_text_message(
            text,
            context_id=context.context_id,
            task_id=context.task_id,
        )

    async def _register(self, task_id: str) -> asyncio.Event:
        cancel_event = asyncio.Event()
        async with self._cancel_lock:
            self._cancel_events[task_id] = cancel_event
        return cancel_event

    async def _unregister(self, task_id: str, cancel_event: asyncio.Event) -> None:
        async with self._cancel_lock:
            if self._cancel_events.get(task_id) is cancel_event:
                self._cancel_events.pop(task_id, None)

    def _session_id(self, context: RequestContext) -> str | None:
        """One backend session per A2A context, so "修复刚刚的问题" finds its diagnosis."""
        if not getattr(getattr(self.backend, "settings", None), "backend_api_token", ""):
            return None
        digest = hashlib.sha256(str(context.context_id).encode()).hexdigest()[:32]
        return f"a2a-{digest}"

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task_id = context.task_id
        context_id = context.context_id
        if not task_id or not context_id:
            raise BackendError("A2A request is missing task_id or context_id")

        updater = TaskUpdater(event_queue, task_id, context_id)
        task = context.current_task
        question = context.get_user_input().strip()
        mode = self._mode(context)
        if task is not None and task.status.state == TaskState.input_required:
            asked = self._clarification_of(context)
            if asked is None:
                await self._resume_repair(context, updater)
                return
            # The reply completes the original request; both go to the backend together,
            # so the answer does not depend on backend session memory.
            question = f"{asked['question']}\n（补充说明：{question}）"
            mode = asked.get("mode") or mode
        if not question:
            await updater.reject(self._message("请求中没有可处理的文本内容。", context))
            return

        session_id = self._session_id(context)
        if mode == "repair" and not session_id:
            await updater.reject(
                self._message(
                    "修复需要适配器以 API 身份访问后端（配置 A2A_BACKEND_API_TOKEN 与后端 "
                    "AIOPS_API_TOKENS）。",
                    context,
                )
            )
            return
        cancel_event = await self._register(task_id)
        backend_run_id = ""
        final_answer = ""
        repair_batch: dict[str, Any] | None = None

        try:
            if context.current_task is None:
                await updater.submit(self._message("任务已提交。", context))
            await updater.start_work(
                self._message(
                    "正在执行自主运维查询与分析。"
                    if mode == "query"
                    else "正在执行 Kubernetes AIOps 诊断。",
                    context,
                )
            )

            extra: dict[str, Any] = {}
            if session_id:
                extra["session_id"] = session_id
            if mode == "repair":
                extra["repair_plan"] = True
            async for event in self.backend.stream(
                question,
                mode=mode,
                cancel_event=cancel_event,
                **extra,
            ):
                if cancel_event.is_set():
                    return

                if event.name == "run_start":
                    backend_run_id = str(event.data.get("run_id") or "")
                elif event.name == "node_start":
                    node = str(event.data.get("node") or "")
                    label = self._PROGRESS_LABELS.get(node)
                    if label:
                        await updater.start_work(self._message(label, context))
                elif (
                    event.name == "thinking"
                    and event.data.get("thinking_type") == "runtime_status"
                ):
                    content = str(event.data.get("content") or "")
                    if content:
                        await updater.start_work(self._message(content, context))
                elif event.name == "final":
                    final_answer = str(event.data.get("answer") or "").strip()
                    if final_answer and clarification_needed(event.data):
                        await self._ask_to_clarify(context, updater, final_answer, question, mode)
                        return
                    if isinstance(event.data.get("repair_batch"), dict):
                        repair_batch = event.data["repair_batch"]
                    if final_answer:
                        await updater.add_artifact(
                            [Part(root=TextPart(text=final_answer))],
                            artifact_id=f"{task_id}-report",
                            name="kubernetes-aiops-report.md",
                            metadata={
                                "content_type": "text/markdown; charset=utf-8",
                                "backend_run_id": backend_run_id,
                                "aiops_mode": mode,
                            },
                            last_chunk=True,
                        )
                elif event.name == "error":
                    message = event.data.get("error") or "AIOps backend workflow failed"
                    raise BackendError(str(message))

            if cancel_event.is_set():
                return
            if not final_answer:
                raise BackendError("AIOps backend ended without a final answer")
            if mode == "repair" and repair_batch and repair_batch.get("batch_id"):
                await self._follow_batch(context, updater, repair_batch["batch_id"], cancel_event)
                return
            await updater.complete(
                self._message(
                    f"诊断完成。后端 run_id={backend_run_id}" if backend_run_id else "诊断完成。",
                    context,
                )
            )
        except asyncio.CancelledError:
            if not cancel_event.is_set():
                logger.info("A2A task %s execution coroutine was cancelled", task_id)
            raise
        except Exception as exc:
            logger.exception("A2A task %s failed", task_id)
            await updater.failed(self._message(f"执行失败：{exc}", context))
        finally:
            await self._unregister(task_id, cancel_event)

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task_id = context.task_id
        context_id = context.context_id
        if not task_id or not context_id:
            raise BackendError("A2A cancel request is missing task_id or context_id")

        async with self._cancel_lock:
            cancel_event = self._cancel_events.get(task_id)
            if cancel_event:
                cancel_event.set()

        updater = TaskUpdater(event_queue, task_id, context_id)
        await updater.cancel(
            new_agent_text_message(
                "任务已取消。",
                context_id=context_id,
                task_id=task_id,
            )
        )

    # ---- clarification: the backend's question pauses the task in input-required ------

    async def _ask_to_clarify(self, context, updater, text, question, mode) -> None:
        message = new_agent_parts_message(
            [
                Part(root=TextPart(text=text)),
                Part(
                    root=DataPart(
                        data={"aiops_clarification": {"question": question, "mode": mode}}
                    )
                ),
            ],
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await updater.requires_input(message, final=True)

    @staticmethod
    def _clarification_of(context: RequestContext) -> dict[str, Any] | None:
        """The request this paused task asked about, if its latest pause was a question.

        The SDK moves the pausing message into history when the reply arrives; a repair
        approval pause (batch_id) is newer than any earlier question and wins.
        """
        task = context.current_task
        messages = [*(task.history or []), task.status.message] if task else []
        for message in reversed([m for m in messages if m is not None]):
            for part in message.parts or []:
                data = getattr(part.root, "data", None)
                if not isinstance(data, dict):
                    continue
                if isinstance(data.get("aiops_clarification"), dict):
                    return data["aiops_clarification"]
                if data.get("batch_id"):
                    return None
        return None

    # ---- repair skill: batch progress, human approval via input-required ------------

    async def _follow_batch(
        self,
        context: RequestContext,
        updater: TaskUpdater,
        batch_id: str,
        cancel_event: asyncio.Event,
    ) -> None:
        """Push batch progress; pause for approval (input-required); finish with results."""
        last = ""
        async for snapshot in self.backend.batch_events(batch_id, cancel_event):
            groups = snapshot.get("groups") or []
            line = "；".join(
                f"{group_label(g.get('group_id'))}：{g.get('status')}" for g in groups
            )
            if line and line != last:
                await updater.start_work(self._message(f"修复批次 {batch_id}：{line}", context))
                last = line
            pending = [
                g
                for g in groups
                if g.get("status") == "awaiting_approval" and g.get("pending_approval_id")
            ]
            if pending:
                await self._ask_for_approval(context, updater, batch_id, pending)
                return
        if cancel_event.is_set():
            return
        await self._finish_batch(context, updater, batch_id)

    async def _ask_for_approval(self, context, updater, batch_id, pending) -> None:
        approvals, lines = (
            [],
            [f"修复批次 `{batch_id}` 有待审批的动作（审批前已通过高危命令规则检查）："],
        )
        for group in pending:
            job = await self.backend.job(group["job_id"])
            approval = job.get("approval") or {}
            action = approval.get("payload") or {}
            approvals.append(
                {
                    "job_id": group["job_id"],
                    "group_id": group.get("group_id"),
                    "cluster": action.get("cluster"),
                    "approval_id": group["pending_approval_id"],
                    "description": action.get("description"),
                    "risk": action.get("risk"),
                    "dry_run_command": action.get("dry_run_command"),
                    "execute_command": action.get("execute_command"),
                    "verify_command": action.get("verify_command"),
                    "rollback_advice": action.get("rollback_advice"),
                    "expires_at": approval.get("expires_at"),
                }
            )
            lines += [
                "",
                f"**{group_label(group.get('group_id'))}**"
                + (f" · 集群 {action['cluster']}" if action.get("cluster") else "")
                + f" · approval_id=`{group['pending_approval_id']}`",
                f"- 动作：{action.get('description') or '—'}（风险：{action.get('risk') or '—'}）",
                f"- 执行命令：`{action.get('execute_command') or '—'}`",
                f"- 回滚建议：{action.get('rollback_advice') or '—'}",
            ]
        lines += [
            "",
            "请在本任务中回复审批决定：DataPart "
            '`{"approval_id": "...", "approved": true, "reviewer": "名字"}`，'
            "或文本 `批准 <approval_id>` / `拒绝 <approval_id>`。超时未审批的动作不会执行。",
        ]
        message = new_agent_parts_message(
            [
                Part(root=TextPart(text="\n".join(lines))),
                Part(root=DataPart(data={"batch_id": batch_id, "approvals": approvals})),
            ],
            context_id=context.context_id,
            task_id=context.task_id,
        )
        self._waiting_batches[str(context.task_id)] = batch_id
        await updater.requires_input(message, final=True)

    def _batch_of(self, context: RequestContext) -> str | None:
        """The batch this paused task waits on: registered here, else our own messages."""
        known = self._waiting_batches.get(str(context.task_id))
        if known:
            return known
        task = context.current_task
        messages = [*(task.history or []), task.status.message] if task else []
        for message in reversed([m for m in messages if m is not None]):
            for part in message.parts or []:
                data = getattr(part.root, "data", None)
                if isinstance(data, dict) and data.get("batch_id"):
                    return str(data["batch_id"])
        return None

    @staticmethod
    def _decisions(context: RequestContext) -> list[dict[str, Any]]:
        decisions: list[dict[str, Any]] = []
        for part in (context.message.parts if context.message else []) or []:
            data = getattr(part.root, "data", None)
            if isinstance(data, dict):
                items = (
                    data.get("decisions") if isinstance(data.get("decisions"), list) else [data]
                )
                decisions += [d for d in items if isinstance(d, dict) and d.get("approval_id")]
        for verb, approval_id in _DECISION.findall(context.get_user_input() or ""):
            decisions.append(
                {
                    "approval_id": approval_id,
                    "approved": verb.lower() in {"批准", "同意", "approve"},
                }
            )
        # One decision per approval: callers often send the text and the DataPart form of
        # the same answer, and a second submission of a decided approval is a backend 404.
        # The first (DataPart, then text order) wins.
        unique: dict[str, dict[str, Any]] = {}
        for decision in decisions:
            unique.setdefault(str(decision["approval_id"]), decision)
        return list(unique.values())

    async def _resume_repair(self, context: RequestContext, updater: TaskUpdater) -> None:
        batch_id = self._batch_of(context)
        decisions = self._decisions(context)
        if not batch_id or not decisions:
            await updater.requires_input(
                self._message(
                    "没有识别到审批决定。请回复 DataPart {approval_id, approved, reviewer} "
                    "或文本 `批准 <approval_id>` / `拒绝 <approval_id>`。",
                    context,
                ),
                final=True,
            )
            return
        cancel_event = await self._register(context.task_id)
        try:
            batch = await self.backend.batch(batch_id)
            by_approval = {
                g.get("pending_approval_id"): g.get("job_id")
                for g in batch.get("groups") or []
                if g.get("pending_approval_id")
            }
            for decision in decisions:
                job_id = by_approval.get(decision["approval_id"])
                if not job_id:
                    await updater.start_work(
                        self._message(
                            f"审批 {decision['approval_id']} 已失效或不属于本批次，已跳过。",
                            context,
                        )
                    )
                    continue
                await self.backend.approve(
                    job_id,
                    decision["approval_id"],
                    bool(decision.get("approved")),
                    str(decision.get("reviewer") or ""),
                    str(decision.get("reason") or ""),
                )
                verdict = "批准" if decision.get("approved") else "拒绝"
                await updater.start_work(
                    self._message(f"已{verdict} {decision['approval_id']}，继续执行。", context)
                )
            await self._follow_batch(context, updater, batch_id, cancel_event)
        except Exception as exc:
            logger.exception("A2A repair task %s failed", context.task_id)
            await updater.failed(self._message(f"修复流程失败：{exc}", context))
        finally:
            await self._unregister(context.task_id, cancel_event)

    async def _finish_batch(self, context, updater, batch_id) -> None:
        self._waiting_batches.pop(str(context.task_id), None)
        batch = await self.backend.batch(batch_id)
        lines = [f"# 修复结果 · 批次 {batch_id}", ""]
        results = []
        for group in batch.get("groups") or []:
            job = await self.backend.job(group["job_id"])
            outcome = job.get("result") or job.get("recovery") or {}
            reason = outcome.get("reason") if isinstance(outcome, dict) else None
            results.append(
                {
                    "job_id": group["job_id"],
                    "group_id": group.get("group_id"),
                    "status": job.get("status"),
                    "reason": reason or job.get("error"),
                }
            )
            lines.append(
                f"- **{group_label(group.get('group_id'))}**：{job.get('status')}"
                + (f" — {reason or job.get('error')}" if (reason or job.get("error")) else "")
            )
        await updater.add_artifact(
            [
                Part(root=TextPart(text="\n".join(lines))),
                Part(root=DataPart(data={"batch_id": batch_id, "results": results})),
            ],
            artifact_id=f"{context.task_id}-repair",
            name="kubernetes-aiops-repair.md",
            last_chunk=True,
        )
        await updater.complete(self._message(f"修复批次 {batch_id} 已结束。", context))
