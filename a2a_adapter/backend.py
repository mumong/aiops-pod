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

    def _headers(self) -> dict[str, str]:
        """The adapter acts as one API principal on the backend (AIOPS_API_TOKENS)."""
        token = self.settings.backend_api_token
        return {"Authorization": f"Bearer {token}"} if token else {}

    async def stream(
        self,
        question: str,
        *,
        mode: str,
        cancel_event: asyncio.Event,
        session_id: str | None = None,
        repair_plan: bool = False,
    ) -> AsyncIterator[BackendEvent]:
        """``mode`` query -> /query; diagnosis / repair -> /ask (repair adds repair=plan)."""
        endpoint = "/query" if mode == "query" else "/ask"
        url = f"{self.settings.backend_url}{endpoint}"
        form = {
            "q": question,
            "stream": "true",
            "format": "sse",
            "max_steps": str(self.settings.max_steps),
        }
        if session_id:
            form["session_id"] = session_id
        if repair_plan:
            form["repair"] = "plan"
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
                    client, "POST", url, data=form, headers=self._headers()
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

    async def _json(self, method: str, path: str, body: dict | None = None) -> dict[str, Any]:
        timeout = httpx.Timeout(60.0, connect=self.settings.connect_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, transport=self._transport) as client:
            try:
                response = await client.request(
                    method,
                    f"{self.settings.backend_url}{path}",
                    json=body,
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise BackendError(
                    f"AIOps backend returned HTTP {exc.response.status_code}: "
                    f"{exc.response.text[:500]}"
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise BackendError(f"AIOps backend request failed: {exc}") from exc
        if not isinstance(data, dict):
            raise BackendError(f"unexpected response for {path}")
        return data

    async def batch(self, batch_id: str) -> dict[str, Any]:
        return await self._json("GET", f"/repair/batches/{batch_id}")

    async def job(self, job_id: str) -> dict[str, Any]:
        return await self._json("GET", f"/repair/jobs/{job_id}")

    async def approve(
        self, job_id: str, approval_id: str, approved: bool, reviewer: str = "", reason: str = ""
    ) -> dict[str, Any]:
        return await self._json(
            "POST",
            f"/repair/jobs/{job_id}/approve",
            {
                "approval_id": approval_id,
                "approved": approved,
                "reviewer": reviewer,
                "reason": reason,
            },
        )

    async def batch_events(
        self, batch_id: str, cancel_event: asyncio.Event
    ) -> AsyncIterator[dict[str, Any]]:
        """Batch snapshots from GET /repair/batches/{id}/events until it ends."""
        url = f"{self.settings.backend_url}/repair/batches/{batch_id}/events"
        timeout = httpx.Timeout(
            self.settings.request_timeout_seconds, connect=self.settings.connect_timeout_seconds
        )
        async with httpx.AsyncClient(timeout=timeout, transport=self._transport) as client:
            try:
                async with aconnect_sse(client, "GET", url, headers=self._headers()) as source:
                    source.response.raise_for_status()
                    async for event in source.aiter_sse():
                        if cancel_event.is_set() or event.event == "end":
                            return
                        if event.event == "error":
                            raise BackendError(f"repair batch stream failed: {event.data}")
                        if event.event == "batch" and event.data:
                            yield json.loads(event.data)
            except httpx.HTTPStatusError as exc:
                raise BackendError(
                    f"AIOps backend returned HTTP {exc.response.status_code}: "
                    f"{exc.response.text[:500]}"
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
