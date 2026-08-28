"""Tests for a real A2A client -> delegator -> operations Agent chain."""

from __future__ import annotations

import asyncio
import socket
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
import pytest
import uvicorn

pytest.importorskip(
    "a2a",
    reason="A2A tests run in the isolated requirements.a2a-dev.txt environment",
)

from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.types import TaskState

from a2a_adapter.app import create_app as create_operations_app
from a2a_adapter.backend import BackendEvent
from a2a_adapter.config import AdapterSettings
from a2a_test_agent.app import create_app as create_test_agent_app
from a2a_test_agent.config import TestAgentSettings
from a2a_test_agent.remote import RemoteResult


class FakeRemoteAgent:
    def __init__(self) -> None:
        self.calls = []

    async def health(self):
        return {
            "status": "healthy",
            "url": "http://operations.test",
            "agent_name": "Fake Operations Agent",
            "protocol_version": "0.3.0",
        }

    async def invoke(self, question, *, metadata, cancel_event, on_progress):
        self.calls.append({"question": question, "metadata": metadata})
        await on_progress("正在检查集群。")
        return RemoteResult(
            markdown="# 委派诊断报告\n\nPod 当前正常。",
            task_id="target-task-1",
            context_id="target-context-1",
            agent_name="Fake Operations Agent",
        )


class NetworkBackend:
    def __init__(self) -> None:
        self.calls = []

    async def health(self):
        return {"status": "healthy"}

    async def stream(self, question, *, mode, cancel_event):
        self.calls.append({"question": question, "mode": mode})
        yield BackendEvent("run_start", {"run_id": "real-network-run-1"})
        yield BackendEvent("node_start", {"node": "evidence"})
        yield BackendEvent(
            "final",
            {
                "answer": (
                    "# 真实 Agent-to-Agent 测试报告\n\n"
                    "请求已经通过测试 Agent 到达运维 Agent。"
                )
            },
        )
        yield BackendEvent("run_end", {})


def _settings() -> TestAgentSettings:
    return TestAgentSettings(
        target_url="http://operations.test",
        public_url="http://delegator.test",
        agent_version="test-version",
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@asynccontextmanager
async def _serve(app, port: int) -> AsyncIterator[None]:
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            lifespan="off",
        )
    )
    task = asyncio.create_task(server.serve())
    try:
        for _ in range(200):
            if server.started:
                break
            if task.done():
                await task
            await asyncio.sleep(0.01)
        else:
            raise TimeoutError(f"uvicorn did not start on port {port}")
        yield
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=5)


@pytest.mark.asyncio
async def test_delegator_agent_card_readiness_and_artifact_metadata():
    remote = FakeRemoteAgent()
    app = create_test_agent_app(_settings(), remote_client=remote)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://delegator.test"
    ) as client:
        card = await client.get("/.well-known/agent-card.json")
        ready = await client.get("/ready")
        response = await client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "delegate-1",
                "method": "message/send",
                "params": {
                    "message": {
                        "kind": "message",
                        "role": "user",
                        "messageId": "message-1",
                        "parts": [{"kind": "text", "text": "查询 Node CPU"}],
                    },
                    "metadata": {"aiops_mode": "query"},
                    "configuration": {"blocking": True},
                },
            },
        )

    assert card.status_code == 200
    assert card.json()["skills"][0]["id"] == "delegate-kubernetes-aiops"
    assert ready.status_code == 200
    assert ready.json()["target"]["agent_name"] == "Fake Operations Agent"
    result = response.json()["result"]
    assert result["status"]["state"] == "completed"
    artifact = result["artifacts"][0]
    assert artifact["parts"][0]["text"].startswith("# 委派诊断报告")
    assert artifact["metadata"]["target_task_id"] == "target-task-1"
    assert remote.calls == [
        {"question": "查询 Node CPU", "metadata": {"aiops_mode": "query"}}
    ]


@pytest.mark.asyncio
async def test_real_http_two_hop_agent_to_agent_chain_with_official_sdk():
    """Use real TCP sockets for both A2A hops, not ASGI in-process transport."""
    operations_port = _free_port()
    delegator_port = _free_port()
    operations_url = f"http://127.0.0.1:{operations_port}"
    delegator_url = f"http://127.0.0.1:{delegator_port}"
    backend = NetworkBackend()

    operations_app = create_operations_app(
        AdapterSettings(
            backend_url="http://unused.test",
            public_url=operations_url,
            agent_version="network-test",
        ),
        backend_client=backend,
    )
    delegator_app = create_test_agent_app(
        TestAgentSettings(
            target_url=operations_url,
            public_url=delegator_url,
            agent_version="network-test",
        )
    )

    async with _serve(operations_app, operations_port), _serve(
        delegator_app, delegator_port
    ):
        async with httpx.AsyncClient(timeout=10) as http_client:
            client = await ClientFactory.connect(
                delegator_url,
                client_config=ClientConfig(
                    streaming=True,
                    httpx_client=http_client,
                    accepted_output_modes=["text/markdown"],
                ),
            )
            events = [
                event
                async for event in client.send_message(
                    create_text_message_object(content="查询各 Node CPU 使用率"),
                    request_metadata={"aiops_mode": "query"},
                )
            ]

    final_task, final_update = events[-1]
    assert final_task.status.state == TaskState.completed
    assert final_update.status.state == TaskState.completed
    assert "真实 Agent-to-Agent 测试报告" in (
        final_task.artifacts[0].parts[0].root.text
    )
    assert final_task.artifacts[0].metadata["target_task_id"]
    assert backend.calls == [
        {"question": "查询各 Node CPU 使用率", "mode": "query"}
    ]
