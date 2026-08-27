"""Official a2a-sdk client used to delegate to the operations agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx
from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.types import Message, Task, TaskIdParams, TaskState

from a2a_test_agent.config import TestAgentSettings


class RemoteAgentError(RuntimeError):
    """The target A2A agent could not complete the delegated task."""


class RemoteTaskCancelled(RuntimeError):
    """The caller canceled the local task while the target was running."""


@dataclass(frozen=True)
class RemoteResult:
    markdown: str
    task_id: str
    context_id: str
    agent_name: str


ProgressCallback = Callable[[str], Awaitable[None]]


def _text_from_parts(parts: list[Any] | None) -> list[str]:
    texts: list[str] = []
    for part in parts or []:
        root = getattr(part, "root", part)
        if getattr(root, "kind", None) == "text":
            value = str(getattr(root, "text", "")).strip()
            if value:
                texts.append(value)
    return texts


def _task_artifact_text(task: Task) -> str:
    sections: list[str] = []
    for artifact in task.artifacts or []:
        sections.extend(_text_from_parts(artifact.parts))
    return "\n\n".join(sections).strip()


def _task_status_message(task: Task) -> str:
    message = task.status.message
    if not message:
        return ""
    return "\n".join(_text_from_parts(message.parts)).strip()


class OperationsAgentClient:
    """Discover and invoke the configured operations Agent over A2A."""

    def __init__(self, settings: TestAgentSettings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        if not self.settings.target_token:
            return {}
        return {"Authorization": f"Bearer {self.settings.target_token}"}

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                headers=self._headers(),
                timeout=min(self.settings.request_timeout_seconds, 10.0),
            ) as http_client:
                client = await ClientFactory.connect(
                    self.settings.target_url,
                    client_config=ClientConfig(
                        streaming=True,
                        httpx_client=http_client,
                        accepted_output_modes=["text/markdown"],
                    ),
                )
                card = await client.get_card()
            return {
                "status": "healthy",
                "url": self.settings.target_url,
                "agent_name": card.name,
                "protocol_version": card.protocol_version,
            }
        except Exception as exc:
            return {
                "status": "unavailable",
                "url": self.settings.target_url,
                "error": str(exc),
            }

    async def invoke(
        self,
        question: str,
        *,
        metadata: dict[str, Any],
        cancel_event: asyncio.Event,
        on_progress: ProgressCallback,
    ) -> RemoteResult:
        async with httpx.AsyncClient(
            headers=self._headers(),
            timeout=self.settings.request_timeout_seconds,
        ) as http_client:
            client = await ClientFactory.connect(
                self.settings.target_url,
                client_config=ClientConfig(
                    streaming=True,
                    httpx_client=http_client,
                    accepted_output_modes=["text/markdown"],
                ),
            )
            card = await client.get_card()
            message = create_text_message_object(content=question)
            final_task: Task | None = None

            async for result in client.send_message(
                message,
                request_metadata=metadata or None,
            ):
                if isinstance(result, Message):
                    direct_text = "\n\n".join(_text_from_parts(result.parts)).strip()
                    if not direct_text:
                        raise RemoteAgentError(
                            f"target agent {card.name!r} returned an empty message"
                        )
                    return RemoteResult(
                        markdown=direct_text,
                        task_id=result.task_id or "",
                        context_id=result.context_id or "",
                        agent_name=card.name,
                    )

                task, update = result
                final_task = task

                if cancel_event.is_set():
                    try:
                        await client.cancel_task(TaskIdParams(id=task.id))
                    except Exception:
                        pass
                    raise RemoteTaskCancelled("delegated task was canceled")

                progress = _task_status_message(task)
                if progress and task.status.state in {
                    TaskState.submitted,
                    TaskState.working,
                }:
                    await on_progress(progress)

            if cancel_event.is_set():
                raise RemoteTaskCancelled("delegated task was canceled")
            if final_task is None:
                raise RemoteAgentError(f"target agent {card.name!r} returned no task")
            if final_task.status.state != TaskState.completed:
                detail = _task_status_message(final_task) or "no error detail"
                raise RemoteAgentError(
                    f"target task ended as {final_task.status.state.value}: {detail}"
                )

            markdown = _task_artifact_text(final_task)
            if not markdown:
                raise RemoteAgentError(
                    f"target task {final_task.id} completed without a text artifact"
                )
            return RemoteResult(
                markdown=markdown,
                task_id=final_task.id,
                context_id=final_task.context_id,
                agent_name=card.name,
            )
