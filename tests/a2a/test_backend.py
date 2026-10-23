import asyncio
from urllib.parse import parse_qs

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

pytest.importorskip(
    "a2a",
    reason="A2A tests run in the isolated requirements/a2a-dev.txt environment",
)

from a2a_adapter.backend import AiopsBackendClient, BackendError
from a2a_adapter.config import AdapterSettings


def _settings() -> AdapterSettings:
    return AdapterSettings(
        backend_url="http://backend.test",
        public_url="http://a2a.test",
        request_timeout_seconds=5,
        connect_timeout_seconds=1,
    )


@pytest.mark.asyncio
async def test_backend_parses_aiops_sse_and_uses_query_fast_path():
    backend_app = FastAPI()
    received = {}

    @backend_app.post("/query")
    async def query(request: Request):
        form = parse_qs((await request.body()).decode())
        received.update({key: values[0] for key, values in form.items()})

        async def records():
            yield 'event: run_start\ndata: {"run_id":"run-123"}\n\n'
            yield 'event: final\ndata: {"answer":"CPU 正常"}\n\n'

        return StreamingResponse(records(), media_type="text/event-stream")

    client = AiopsBackendClient(_settings(), transport=httpx.ASGITransport(app=backend_app))
    events = [
        event
        async for event in client.stream(
            "查询 CPU",
            mode="query",
            cancel_event=asyncio.Event(),
        )
    ]

    assert [event.name for event in events] == ["run_start", "final"]
    assert events[1].data["answer"] == "CPU 正常"
    assert received == {
        "q": "查询 CPU",
        "stream": "true",
        "format": "sse",
        "max_steps": "20",
    }


@pytest.mark.asyncio
async def test_backend_rejects_non_json_sse_payload():
    backend_app = FastAPI()

    @backend_app.post("/ask")
    async def ask():
        return StreamingResponse(
            iter(["event: final\ndata: not-json\n\n"]),
            media_type="text/event-stream",
        )

    client = AiopsBackendClient(_settings(), transport=httpx.ASGITransport(app=backend_app))

    with pytest.raises(BackendError, match="invalid SSE JSON"):
        _ = [
            event
            async for event in client.stream(
                "诊断",
                mode="diagnosis",
                cancel_event=asyncio.Event(),
            )
        ]


@pytest.mark.asyncio
async def test_backend_health_reports_unavailable_without_raising():
    backend_app = FastAPI()

    @backend_app.get("/health")
    async def health():
        return Response(status_code=503)

    client = AiopsBackendClient(_settings(), transport=httpx.ASGITransport(app=backend_app))
    result = await client.health()

    assert result["status"] == "unavailable"
