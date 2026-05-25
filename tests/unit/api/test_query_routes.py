import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.api.routes import register_routes


class _FakeService:
    def __init__(self):
        self.stream_calls = []
        self.sync_calls = []
        self.merged_catalog = None

    def health_check(self):
        return {"status": "healthy"}

    def get_tools_info(self):
        return {"success": True}

    def get_tools_detail(self):
        return {"success": True}

    def execute_query_stream(self, **kwargs):
        self.stream_calls.append(kwargs)
        yield "ok"

    def execute_query(self, **kwargs):
        self.sync_calls.append(kwargs)
        return {"success": True, "result": "ok"}


def _build_client(monkeypatch):
    fake_service = _FakeService()
    app = FastAPI()
    register_routes(app)
    monkeypatch.setattr("app.api.routes.get_service", lambda: fake_service)
    return TestClient(app), fake_service


def test_ask_route_uses_full_diagnosis_workflow(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/ask", params={"q": "我的集群有什么问题？", "stream": "false"})

    assert response.status_code == 200
    assert len(fake_service.sync_calls) == 1
    overrides = fake_service.sync_calls[0]["workflow_overrides"]
    assert overrides["query_mode"] == "full"
    assert overrides["nodes"] == {
        "layer": True,
        "evidence": True,
        "rca": True,
        "conclusion": True,
    }
    assert "remediation" not in overrides


def test_ask_route_can_enable_remediation(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/ask", params={"q": "我的集群有什么问题？", "stream": "true", "remediate": "true"})

    assert response.status_code == 200
    assert response.text == "ok"
    overrides = fake_service.stream_calls[0]["workflow_overrides"]
    assert overrides["remediation"] == {"enabled": True}


def test_ask_route_rejects_sync_remediation(monkeypatch):
    client, _fake_service = _build_client(monkeypatch)

    response = client.get("/ask", params={"q": "我的集群有什么问题？", "stream": "false", "remediate": "true"})

    assert response.status_code == 400


def test_query_route_uses_direct_query_workflow(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/query", params={"q": "集群 CPU 使用率是多少", "stream": "false"})

    assert response.status_code == 200
    assert len(fake_service.sync_calls) == 1
    overrides = fake_service.sync_calls[0]["workflow_overrides"]
    assert overrides["query_mode"] == "direct"
    assert overrides["nodes"] == {
        "layer": True,
        "evidence": False,
        "rca": False,
        "conclusion": True,
    }


def test_query_stream_route_sets_query_title(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/query", params={"q": "集群 CPU 使用率是多少", "stream": "true"})

    assert response.status_code == 200
    assert len(fake_service.stream_calls) == 1
    assert fake_service.stream_calls[0]["workflow_title"] == "工作流查询模式"


def test_remediation_approve_route_resolves_request(monkeypatch):
    client, _fake_service = _build_client(monkeypatch)
    from app.core.remediation.approval import approval_store

    request = approval_store.create_request("run-api", "action", "执行修复", {"action_id": "a1"})

    response = client.post(
        "/remediation/approve",
        data={
            "run_id": "run-api",
            "approval_id": request.approval_id,
            "approved": "true",
            "reviewer": "tester",
            "reason": "ok",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    decision = approval_store.wait_for_decision("run-api", request.approval_id, timeout_seconds=0.01)
    assert decision is not None
    assert decision.approved is True
    assert decision.reviewer == "tester"


def test_ui_page_contains_remediation_approval_flow(monkeypatch):
    client, _fake_service = _build_client(monkeypatch)

    response = client.get("/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "/ask" in response.text
    assert "format=sse" in response.text
    assert "remediate=true" in response.text
    assert "/remediation/approve" in response.text
    assert "approval_id" in response.text
    assert "Approve" in response.text
    assert "Reject" in response.text
