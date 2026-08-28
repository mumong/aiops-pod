"""A2A executor that delegates each task to another A2A agent."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message

from a2a_test_agent.remote import (
    OperationsAgentClient,
    RemoteAgentError,
    RemoteTaskCancelled,
)

logger = logging.getLogger(__name__)


class DelegatingAgentExecutor(AgentExecutor):
    """Receive a standard A2A task and forward it through the official SDK."""

    def __init__(self, remote: OperationsAgentClient | Any) -> None:
        self.remote = remote
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._cancel_lock = asyncio.Lock()

    @staticmethod
    def _message(text: str, context: RequestContext):
        return new_agent_text_message(
            text,
            context_id=context.context_id,
            task_id=context.task_id,
        )

    @staticmethod
    def _metadata(context: RequestContext) -> dict[str, Any]:
        metadata = dict(context.metadata or {})
        if context.message and context.message.metadata:
            metadata.update(context.message.metadata)
        return metadata

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id
        if not task_id or not context_id:
            raise RemoteAgentError("A2A request is missing task_id or context_id")

        updater = TaskUpdater(event_queue, task_id, context_id)
        question = context.get_user_input().strip()
        if not question:
            await updater.reject(self._message("请求中没有可委派的文本内容。", context))
            return

        cancel_event = asyncio.Event()
        async with self._cancel_lock:
            self._cancel_events[task_id] = cancel_event

        async def report_progress(progress: str) -> None:
            if not cancel_event.is_set():
                await updater.start_work(
                    self._message(f"下游运维 Agent：{progress}", context)
                )

        try:
            if context.current_task is None:
                await updater.submit(self._message("委派任务已提交。", context))
            await updater.start_work(
                self._message("正在通过 A2A 协议调用运维 Agent。", context)
            )
            result = await self.remote.invoke(
                question,
                metadata=self._metadata(context),
                cancel_event=cancel_event,
                on_progress=report_progress,
            )
            if cancel_event.is_set():
                return

            await updater.add_artifact(
                [Part(root=TextPart(text=result.markdown))],
                artifact_id=f"{task_id}-delegated-report",
                name="delegated-kubernetes-aiops-report.md",
                metadata={
                    "content_type": "text/markdown; charset=utf-8",
                    "target_agent": result.agent_name,
                    "target_task_id": result.task_id,
                    "target_context_id": result.context_id,
                },
                last_chunk=True,
            )
            await updater.complete(
                self._message(
                    f"Agent-to-Agent 委派完成，下游 task_id={result.task_id}",
                    context,
                )
            )
        except RemoteTaskCancelled:
            return
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Delegated A2A task %s failed", task_id)
            await updater.failed(self._message(f"委派失败：{exc}", context))
        finally:
            async with self._cancel_lock:
                if self._cancel_events.get(task_id) is cancel_event:
                    self._cancel_events.pop(task_id, None)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id
        if not task_id or not context_id:
            raise RemoteAgentError("A2A cancel request is missing task_id or context_id")

        async with self._cancel_lock:
            cancel_event = self._cancel_events.get(task_id)
            if cancel_event:
                cancel_event.set()

        updater = TaskUpdater(event_queue, task_id, context_id)
        await updater.cancel(
            new_agent_text_message(
                "Agent-to-Agent 委派任务已取消。",
                context_id=context_id,
                task_id=task_id,
            )
        )
