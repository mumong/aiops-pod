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


def test_repair_source_identifier_is_forwarded_and_requires_session(monkeypatch):
    client, service = _build_client(monkeypatch)
    assert (
        client.get("/ask", params={"q": "repair", "diagnosis_run_id": "run1"}).status_code == 400
    )
    params = {"q": "repair", "diagnosis_run_id": "run1", "session_id": "a" * 32}
    assert client.get("/ask", params=params).status_code == 200
    assert service.stream_calls[-1]["workflow_overrides"]["_diagnosis_run_id"] == "run1"
    assert client.get("/query", params={**params, "plan_run_id": "plan1"}).status_code == 400
    assert (
        client.get("/query", params={**params, "diagnosis_run_id": "../escape"}).status_code == 400
    )


def test_query_session_cookie_isolation_and_validation(monkeypatch):
    client, service = _build_client(monkeypatch)
    params = {"q": "pods", "session_id": "a" * 32}
    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    first = service.stream_calls[-1]["workflow_overrides"]["_query_session_key"]
    client.get("/query", params=params)
    assert service.stream_calls[-1]["workflow_overrides"]["_query_session_key"] == first
    client.cookies.clear()
    client.get("/query", params=params)
    assert service.stream_calls[-1]["workflow_overrides"]["_query_session_key"][0] != first[0]
    assert client.get("/query", params={"q": "x", "session_id": "../bad"}).status_code == 422
    client.post("/query", data=params)
    assert "_query_session_key" in service.stream_calls[-1]["workflow_overrides"]


def test_ask_route_uses_task_routing_with_diagnosis_available(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/ask", params={"q": "我的集群有什么问题？", "stream": "false"})

    assert response.status_code == 200
    assert len(fake_service.sync_calls) == 1
    overrides = fake_service.sync_calls[0]["workflow_overrides"]
    assert overrides["query_mode"] == "auto"
    assert overrides["nodes"] == {
        "layer": True,
        "evidence": True,
        "rca": True,
        "conclusion": True,
    }
    assert "remediation" not in overrides


def test_ask_route_ignores_legacy_remediate_parameter(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get(
        "/ask", params={"q": "我的集群有什么问题？", "stream": "true", "remediate": "true"}
    )

    assert response.status_code == 200
    assert response.text == "ok"
    overrides = fake_service.stream_calls[0]["workflow_overrides"]
    assert "remediation" not in overrides


def test_ask_route_does_not_reject_sync_with_legacy_remediate_parameter(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get(
        "/ask", params={"q": "我的集群有什么问题？", "stream": "false", "remediate": "true"}
    )

    assert response.status_code == 200
    assert len(fake_service.sync_calls) == 1
    overrides = fake_service.sync_calls[0]["workflow_overrides"]
    assert "remediation" not in overrides


def test_query_route_uses_intent_router_and_server_remediation_policy(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/query", params={"q": "集群 CPU 使用率是多少", "stream": "false"})

    assert response.status_code == 200
    assert len(fake_service.sync_calls) == 1
    overrides = fake_service.sync_calls[0]["workflow_overrides"]
    assert overrides["query_mode"] == "auto"
    assert "remediation" not in overrides


def test_ask_and_query_share_owner_scoped_session_identity(monkeypatch):
    client, service = _build_client(monkeypatch)
    params = {"q": "pods", "session_id": "a" * 32}
    client.get("/query", params=params)
    key = service.stream_calls[-1]["workflow_overrides"]["_query_session_key"]
    client.get("/ask", params=params)
    assert service.stream_calls[-1]["workflow_overrides"]["_query_session_key"] == key
    client.post("/ask", data=params)
    assert service.stream_calls[-1]["workflow_overrides"]["_query_session_key"] == key


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
    decision = approval_store.wait_for_decision(
        "run-api", request.approval_id, timeout_seconds=0.01
    )
    assert decision is not None
    assert decision.approved is True
    assert decision.reviewer == "tester"


def test_root_usage_does_not_advertise_legacy_remediate_gate(monkeypatch):
    client, _fake_service = _build_client(monkeypatch)

    response = client.get("/")

    assert response.status_code == 200
    assert "remediate=true" not in response.text
    assert "/ask" in response.text


def test_repair_on_request_is_accepted_on_ask_and_query_and_needs_a_session(monkeypatch):
    # The A2A adapter sends repair=on_request on every call (query or diagnosis mode).
    client, service = _build_client(monkeypatch)
    session = {"session_id": "a" * 32}
    for path in ("/ask", "/query"):
        assert client.get(path, params={"q": "修复", "repair": "on_request"}).status_code == 400
        assert (
            client.get(path, params={"q": "修复", "repair": "on_request", **session}).status_code
            == 200
        )
        overrides = service.stream_calls[-1]["workflow_overrides"]
        assert overrides["_repair_on_request"] is True and "_auto_repair_plan" not in overrides
        client.post(path, data={"q": "修复", "repair": "on_request", **session})
        assert service.stream_calls[-1]["workflow_overrides"]["_repair_on_request"] is True
    assert client.get("/query", params={"q": "x", "repair": "plan", **session}).status_code == 422
    plain = client.get("/ask", params={"q": "集群有什么问题", **session})
    assert plain.status_code == 200
    assert "_repair_on_request" not in service.stream_calls[-1]["workflow_overrides"]
