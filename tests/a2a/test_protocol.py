import asyncio
from uuid import uuid4

import httpx
import pytest

pytest.importorskip(
    "a2a",
    reason="A2A tests run in the isolated requirements.a2a-dev.txt environment",
)

from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.types import TaskState

from a2a_adapter.app import create_app
from a2a_adapter.backend import BackendEvent
from a2a_adapter.config import AdapterSettings


class FakeBackend:
    def __init__(self):
        self.calls = []

    async def health(self):
        return {"status": "healthy"}

    async def stream(self, question, *, mode, cancel_event):
        self.calls.append({"question": question, "mode": mode})
        yield BackendEvent("run_start", {"run_id": "backend-run-1"})
        yield BackendEvent("node_start", {"node": "evidence"})
        yield BackendEvent("final", {"answer": "# 诊断报告\n\nPod 当前正常。"})
        yield BackendEvent("run_end", {})


class BlockingBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.started = asyncio.Event()
        self.cancelled = False

    async def stream(self, question, *, mode, cancel_event):
        self.calls.append({"question": question, "mode": mode})
        self.started.set()
        yield BackendEvent("run_start", {"run_id": "backend-slow"})
        try:
            while not cancel_event.is_set():
                await asyncio.sleep(0.01)
        finally:
            self.cancelled = cancel_event.is_set()


class UnavailableBackend(FakeBackend):
    async def health(self):
        return {"status": "unavailable", "error": "connection refused"}


class ControlledBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def stream(self, question, *, mode, cancel_event):
        self.calls.append({"question": question, "mode": mode})
        self.started.set()
        yield BackendEvent("run_start", {"run_id": "backend-controlled"})
        await self.release.wait()
        yield BackendEvent("final", {"answer": "# 完成"})


class ErrorBackend(FakeBackend):
    async def stream(self, question, *, mode, cancel_event):
        yield BackendEvent("error", {"error": "simulated backend failure"})


def _settings(token: str = "") -> AdapterSettings:
    return AdapterSettings(
        backend_url="http://backend.test",
        public_url="http://a2a.test",
        api_token=token,
        agent_version="test-version",
    )


def _message_request(
    *,
    method: str = "message/send",
    text: str = "请诊断异常 Pod",
    blocking: bool = True,
    metadata: dict | None = None,
):
    params = {
        "message": {
            "kind": "message",
            "role": "user",
            "messageId": str(uuid4()),
            "parts": [{"kind": "text", "text": text}],
        },
        "configuration": {"blocking": blocking},
    }
    if metadata:
        params["metadata"] = metadata
    return {
        "jsonrpc": "2.0",
        "id": str(uuid4()),
        "method": method,
        "params": params,
    }


@pytest.mark.asyncio
async def test_agent_card_is_discoverable_and_declares_protocol_capabilities():
    app = create_app(_settings(), backend_client=FakeBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        response = await client.get("/.well-known/agent-card.json")

    assert response.status_code == 200
    card = response.json()
    assert card["protocolVersion"] == "0.3.0"
    assert card["preferredTransport"] == "JSONRPC"
    assert card["capabilities"]["streaming"] is True
    assert {skill["id"] for skill in card["skills"]} == {
        "kubernetes-diagnosis",
        "kubernetes-query",
    }


@pytest.mark.asyncio
async def test_health_is_live_but_readiness_requires_healthy_backend():
    app = create_app(_settings(), backend_client=UnavailableBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        health = await client.get("/health")
        ready = await client.get("/ready")

    assert health.status_code == 200
    assert health.json()["sdk_version"] == "0.3.25"
    assert ready.status_code == 503
    assert ready.json()["status"] == "not-ready"


@pytest.mark.asyncio
async def test_message_send_returns_completed_task_and_markdown_artifact():
    backend = FakeBackend()
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        response = await client.post("/", json=_message_request())

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["kind"] == "task"
    assert result["status"]["state"] == "completed"
    assert result["artifacts"][0]["name"] == "kubernetes-aiops-report.md"
    assert result["artifacts"][0]["parts"][0]["text"].startswith("# 诊断报告")
    assert result["artifacts"][0]["metadata"]["backend_run_id"] == "backend-run-1"
    assert backend.calls == [{"question": "请诊断异常 Pod", "mode": "diagnosis"}]


@pytest.mark.asyncio
async def test_official_a2a_sdk_client_discovers_and_streams_task():
    app = create_app(_settings(), backend_client=FakeBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://a2a.test",
        timeout=None,
    ) as http_client:
        client = await ClientFactory.connect(
            "http://a2a.test",
            client_config=ClientConfig(
                streaming=True,
                httpx_client=http_client,
                accepted_output_modes=["text/markdown"],
            ),
        )
        events = [
            event
            async for event in client.send_message(
                create_text_message_object(content="请诊断异常 Pod")
            )
        ]

    final_task, final_update = events[-1]
    assert final_task.status.state == TaskState.completed
    assert final_update.status.state == TaskState.completed
    assert final_task.artifacts[0].parts[0].root.text.startswith("# 诊断报告")


@pytest.mark.asyncio
async def test_query_metadata_routes_to_existing_query_endpoint():
    backend = FakeBackend()
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        response = await client.post(
            "/",
            json=_message_request(
                text="查询 CPU",
                metadata={"aiops_mode": "query"},
            ),
        )

    assert response.status_code == 200
    assert response.json()["result"]["status"]["state"] == "completed"
    assert backend.calls == [{"question": "查询 CPU", "mode": "query"}]


@pytest.mark.asyncio
async def test_message_stream_emits_standard_a2a_sse_updates():
    app = create_app(_settings(), backend_client=FakeBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        response = await client.post(
            "/", json=_message_request(method="message/stream")
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"kind":"status-update"' in response.text
    assert '"kind":"artifact-update"' in response.text
    assert '"state":"completed"' in response.text


@pytest.mark.asyncio
async def test_tasks_get_returns_persisted_completed_task():
    app = create_app(_settings(), backend_client=FakeBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        sent = await client.post("/", json=_message_request())
        task_id = sent.json()["result"]["id"]
        fetched = await client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "get-1",
                "method": "tasks/get",
                "params": {"id": task_id},
            },
        )

    assert fetched.status_code == 200
    assert fetched.json()["result"]["id"] == task_id
    assert fetched.json()["result"]["status"]["state"] == "completed"


@pytest.mark.asyncio
async def test_tasks_resubscribe_receives_future_updates_for_running_task():
    backend = ControlledBackend()
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        sent = await client.post("/", json=_message_request(blocking=False))
        task_id = sent.json()["result"]["id"]
        await asyncio.wait_for(backend.started.wait(), timeout=1)
        subscription = asyncio.create_task(
            client.post(
                "/",
                json={
                    "jsonrpc": "2.0",
                    "id": "subscribe-1",
                    "method": "tasks/resubscribe",
                    "params": {"id": task_id},
                },
            )
        )
        await asyncio.sleep(0.02)
        backend.release.set()
        response = await asyncio.wait_for(subscription, timeout=1)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"state":"completed"' in response.text


@pytest.mark.asyncio
async def test_tasks_cancel_stops_running_backend_and_returns_canceled_task():
    backend = BlockingBackend()
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        sent = await client.post(
            "/", json=_message_request(blocking=False)
        )
        task = sent.json()["result"]
        await asyncio.wait_for(backend.started.wait(), timeout=1)
        canceled = await client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "cancel-1",
                "method": "tasks/cancel",
                "params": {"id": task["id"]},
            },
        )
        await asyncio.sleep(0)

    assert canceled.status_code == 200
    assert canceled.json()["result"]["status"]["state"] == "canceled"
    assert backend.cancelled is True


@pytest.mark.asyncio
async def test_rpc_bearer_auth_and_agent_card_security_declaration():
    app = create_app(_settings(token="secret-token"), backend_client=FakeBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        card = await client.get("/.well-known/agent-card.json")
        denied = await client.post("/", json=_message_request())
        allowed = await client.post(
            "/",
            json=_message_request(),
            headers={"Authorization": "Bearer secret-token"},
        )

    assert card.json()["security"] == [{"bearerAuth": []}]
    assert denied.status_code == 401
    assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_empty_message_is_rejected_as_a2a_task():
    app = create_app(_settings(), backend_client=FakeBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        response = await client.post("/", json=_message_request(text=""))

    assert response.status_code == 200
    assert response.json()["result"]["status"]["state"] == "rejected"


@pytest.mark.asyncio
async def test_backend_error_becomes_failed_a2a_task():
    app = create_app(_settings(), backend_client=ErrorBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        response = await client.post("/", json=_message_request())

    assert response.status_code == 200
    status = response.json()["result"]["status"]
    assert status["state"] == "failed"
    assert "simulated backend failure" in status["message"]["parts"][0]["text"]
