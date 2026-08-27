"""Async SSE client for the existing AIOps FastAPI service."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx
from httpx_sse import aconnect_sse

from a2a_adapter.config import AdapterSettings


class BackendError(RuntimeError):
    """Raised when the existing AIOps service cannot complete a request."""


@dataclass(frozen=True)
class BackendEvent:
    name: str
    data: dict[str, Any]


class AiopsBackendClient:
    """Calls /ask or /query and converts its SSE records to typed events."""

    def __init__(
        self,
        settings: AdapterSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._transport = transport

    async def stream(
        self,
        question: str,
        *,
        mode: str,
        cancel_event: asyncio.Event,
    ) -> AsyncIterator[BackendEvent]:
        endpoint = "/query" if mode == "query" else "/ask"
        url = f"{self.settings.backend_url}{endpoint}"
        timeout = httpx.Timeout(
            self.settings.request_timeout_seconds,
            connect=self.settings.connect_timeout_seconds,
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            transport=self._transport,
        ) as client:
            try:
                async with aconnect_sse(
                    client,
                    "POST",
                    url,
                    data={
                        "q": question,
                        "stream": "true",
                        "format": "sse",
                        "max_steps": str(self.settings.max_steps),
                    },
                ) as event_source:
                    event_source.response.raise_for_status()
                    async for event in event_source.aiter_sse():
                        if cancel_event.is_set():
                            return
                        try:
                            payload = json.loads(event.data) if event.data else {}
                        except json.JSONDecodeError as exc:
                            raise BackendError(
                                f"invalid SSE JSON for event {event.event or 'message'}"
                            ) from exc
                        if not isinstance(payload, dict):
                            raise BackendError(
                                f"invalid SSE payload for event {event.event or 'message'}"
                            )
                        yield BackendEvent(event.event or "message", payload)
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:500]
                raise BackendError(
                    f"AIOps backend returned HTTP {exc.response.status_code}: {body}"
                ) from exc
            except httpx.HTTPError as exc:
                raise BackendError(f"AIOps backend request failed: {exc}") from exc

    async def health(self) -> dict[str, Any]:
        timeout = httpx.Timeout(5.0, connect=self.settings.connect_timeout_seconds)
        async with httpx.AsyncClient(
            timeout=timeout,
            transport=self._transport,
        ) as client:
            try:
                response = await client.get(f"{self.settings.backend_url}/health")
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else {"status": "unknown"}
            except (httpx.HTTPError, ValueError) as exc:
                return {"status": "unavailable", "error": str(exc)}
