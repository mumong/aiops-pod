"""A2A AgentExecutor backed by the existing AIOps SSE API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message

from a2a_adapter.backend import AiopsBackendClient, BackendError

logger = logging.getLogger(__name__)


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
        self._cancel_lock = asyncio.Lock()

    @staticmethod
    def _mode(context: RequestContext) -> str:
        """Default to autonomous QUERY; explicit diagnosis/ask retains the legacy route."""
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
        question = context.get_user_input().strip()
        if not question:
            await updater.reject(self._message("请求中没有可处理的文本内容。", context))
            return

        cancel_event = await self._register(task_id)
        backend_run_id = ""
        final_answer = ""
        mode = self._mode(context)

        try:
            if context.current_task is None:
                await updater.submit(self._message("任务已提交。", context))
            await updater.start_work(
                self._message(
                    "正在执行自主运维查询与分析。" if mode == "query" else "正在执行 Kubernetes AIOps 诊断。",
                    context,
                )
            )

            async for event in self.backend.stream(
                question,
                mode=mode,
                cancel_event=cancel_event,
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
                elif event.name == "thinking" and event.data.get("thinking_type") == "runtime_status":
                    content = str(event.data.get("content") or "")
                    if content:
                        await updater.start_work(self._message(content, context))
                elif event.name == "final":
                    final_answer = str(event.data.get("answer") or "").strip()
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
            await updater.complete(
                self._message(
                    f"诊断完成。后端 run_id={backend_run_id}"
                    if backend_run_id
                    else "诊断完成。",
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
