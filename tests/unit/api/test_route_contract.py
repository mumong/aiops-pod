"""Characterization tests for HTTP routes not covered elsewhere.

They pin request parsing, forwarded arguments and response shapes so the
route modules can be reorganized without changing observable behavior.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.api.routes import register_routes

DIAGNOSIS_NODES = {"layer": True, "evidence": True, "rca": True, "conclusion": True}


class _Entry:
    def __init__(self, entry_id, description="", link=""):
        self.id = entry_id
        self.description = description
        self.link = link


class _FakeService:
    def __init__(self):
        self.stream_calls = []
        self.sync_calls = []
        self.sync_result = {"success": True, "result": "sync-ok"}
        self.merged_catalog = None

    def health_check(self):
        return {"status": "healthy"}

    def get_tools_info(self):
        return {"tools": ["a"]}

    def get_tools_detail(self):
        return {"toolsets": {"x": []}}

    def execute_query_stream(self, **kwargs):
        self.stream_calls.append(kwargs)
        yield "stream-ok"

    def execute_query(self, **kwargs):
        self.sync_calls.append(kwargs)
        return self.sync_result


def _build_client(monkeypatch):
    fake_service = _FakeService()
    app = FastAPI()
    register_routes(app)
    monkeypatch.setattr("app.api.routes.get_service", lambda: fake_service)
    return TestClient(app), fake_service, app


def test_route_table_order_and_names_are_stable(monkeypatch):
    _client, _service, app = _build_client(monkeypatch)
    table = [
        (route.path, sorted(route.methods), route.name)
        for route in app.routes
        if getattr(route, "endpoint", None) is not None
        and route.path not in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    ]
    assert table == [
        ("/repair/batches", ["POST"], "start"),
        ("/repair/batches/{batch_id}", ["GET"], "batch"),
        ("/repair/jobs/{job_id}", ["GET"], "detail"),
        ("/repair/jobs/{job_id}/feedback", ["POST"], "feedback"),
        ("/repair/jobs/{job_id}/approve", ["POST"], "approve"),
        ("/repair/batches/{batch_id}/events", ["GET"], "batch_events"),
        ("/repair/jobs/{job_id}/cancel", ["POST"], "cancel"),
        ("/repair/policy", ["GET"], "policy"),
        ("/repair/policy/check", ["POST"], "policy_check"),
        ("/repair/policy/mode", ["PUT"], "policy_mode"),
        ("/repair/policy/mode", ["DELETE"], "policy_mode_clear"),
        ("/repair/audit", ["GET"], "audit"),
        ("/ask", ["GET"], "ask_get"),
        ("/ask", ["POST"], "ask_post"),
        ("/query", ["GET"], "query_get"),
        ("/query", ["POST"], "query_post"),
        ("/q/{question:path}", ["GET"], "ask_path"),
        ("/remediation/approve", ["POST"], "remediation_approve"),
        ("/", ["GET"], "root"),
        ("/health", ["GET"], "health_check"),
        ("/ready", ["GET"], "ready_check"),
        ("/tools", ["GET"], "list_tools"),
        ("/tools/detail", ["GET"], "list_tools_detail"),
        ("/runbooks", ["GET"], "list_runbooks"),
        ("/artifacts/{artifact_id}", ["GET"], "get_artifact"),
        ("/runs/{run_id}", ["GET"], "get_run_report"),
        ("/runs/{run_id}/report.md", ["GET"], "get_run_report_markdown"),
        ("/api/v1/mcp/status", ["GET"], "get_mcp_status"),
        ("/reports", ["GET"], "list_reports"),
        ("/reports/{filename}", ["GET"], "get_report"),
    ]


def test_path_route_uses_diagnosis_overrides_without_session_keys(monkeypatch):
    client, service, _app = _build_client(monkeypatch)

    response = client.get("/q/pod/crash loop", params={"max_steps": 7})

    assert response.status_code == 200
    assert response.text == "stream-ok"
    call = service.stream_calls[-1]
    assert call["question"] == "pod/crash loop"
    assert call["max_steps"] == 7
    assert call["output_format"] == "text"
    assert call["workflow_title"] == "工作流诊断模式"
    assert call["workflow_overrides"] == {"query_mode": "auto", "nodes": DIAGNOSIS_NODES}
    assert "set-cookie" not in response.headers


def test_path_route_sync_and_validation(monkeypatch):
    client, service, _app = _build_client(monkeypatch)

    response = client.get("/q/hello", params={"stream": "false"})
    assert response.status_code == 200
    assert response.text == "sync-ok"
    assert service.sync_calls[-1]["workflow_overrides"] == {
        "query_mode": "auto",
        "nodes": DIAGNOSIS_NODES,
    }
    assert service.sync_calls[-1]["workflow_title"] == "工作流诊断模式"
    assert client.get("/q/hello", params={"max_steps": 0}).status_code == 422


def test_ask_post_form_forwards_arguments_and_sse_media_type(monkeypatch):
    client, service, _app = _build_client(monkeypatch)

    response = client.post("/ask", data={"q": "disk full", "format": "sse", "max_steps": "33"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    call = service.stream_calls[-1]
    assert call["question"] == "disk full"
    assert call["max_steps"] == 33
    assert call["output_format"] == "sse"
    assert call["workflow_title"] == "工作流诊断模式"
    assert call["workflow_overrides"] == {
        "query_mode": "auto",
        "nodes": DIAGNOSIS_NODES,
        "_diagnosis_run_id": None,
        "_plan_run_id": None,
    }


def test_post_forms_keep_unbounded_max_steps(monkeypatch):
    # GET enforces 1..100; POST forms never did. Pin both sides.
    client, service, _app = _build_client(monkeypatch)
    assert client.get("/ask", params={"q": "x", "max_steps": 101}).status_code == 422
    assert client.post("/ask", data={"q": "x", "max_steps": "101"}).status_code == 200
    assert client.post("/query", data={"q": "x", "max_steps": "0"}).status_code == 200
    assert client.post("/ask", data={}).status_code == 422


def test_query_post_sync_and_overrides(monkeypatch):
    client, service, _app = _build_client(monkeypatch)

    response = client.post("/query", data={"q": "cpu", "stream": "false"})

    assert response.status_code == 200
    assert response.text == "sync-ok"
    call = service.sync_calls[-1]
    assert call["workflow_title"] == "工作流查询模式"
    assert call["workflow_overrides"] == {
        "query_mode": "auto",
        "_diagnosis_run_id": None,
        "_plan_run_id": None,
    }


def test_sync_failure_maps_to_500(monkeypatch):
    client, service, _app = _build_client(monkeypatch)
    service.sync_result = {"success": False, "error": "boom"}

    response = client.get("/ask", params={"q": "x", "stream": "false"})

    assert response.status_code == 500
    assert response.json() == {"detail": "boom"}


def test_info_routes(monkeypatch):
    client, service, _app = _build_client(monkeypatch)

    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/tools").json() == {"tools": ["a"]}
    assert client.get("/tools/detail").json() == {"toolsets": {"x": []}}
    assert client.get("/runbooks").json() == {"count": 0, "runbooks": []}
    service.merged_catalog = type(
        "_Catalog", (), {"catalog": [_Entry("rb1", "desc", "l.md"), object()]}
    )()
    assert client.get("/runbooks").json() == {
        "count": 1,
        "runbooks": [{"id": "rb1", "description": "desc", "link": "l.md"}],
    }


def test_tools_error_maps_to_500(monkeypatch):
    client, service, _app = _build_client(monkeypatch)

    def _fail():
        raise RuntimeError("tools down")

    service.get_tools_info = _fail
    response = client.get("/tools")
    assert response.status_code == 500
    assert response.json() == {"detail": "tools down"}


def test_artifact_route(monkeypatch):
    client, _service, _app = _build_client(monkeypatch)
    from app.core.holmes.artifacts import get_artifact_store

    artifact_id = get_artifact_store().put("full output")
    response = client.get(f"/artifacts/{artifact_id}")
    assert response.status_code == 200
    assert response.text == "full output"
    assert client.get("/artifacts/missing").status_code == 404


def test_mcp_status_route(monkeypatch):
    client, service, _app = _build_client(monkeypatch)
    service.mcp_status = lambda: {"success": True, "servers": {"es": {"status": "connected"}}}

    assert client.get("/api/v1/mcp/status").json()["servers"] == {"es": {"status": "connected"}}


def test_mcp_status_reports_the_running_modes_servers(monkeypatch):
    """It read the legacy MCP manager, which the AICall mode never fills: always {}."""
    from app.core.service import HolmesService

    service = HolmesService.__new__(HolmesService)
    service.initialize = lambda: None
    service._mcp_servers_config = {
        "k8s": {"enabled": True, "config": {"url": "http://mcp:8093/sse"}},
        "es": {"enabled": True, "config": {"url": "http://mcp:8088/sse"}},
        "old": {"enabled": False},
    }
    service._mcp_failed_servers = ["es"]
    service.mcp_tools = [type("T", (), {"name": "kubectl_describe"})()]
    status = service.mcp_status()
    assert {k: v["status"] for k, v in status["servers"].items()} == {
        "k8s": "connected",
        "es": "failed",
        "old": "disabled",
    }
    assert status["failed"] == ["es"] and status["mcp_tools"] == 1


def test_reports_routes(monkeypatch, tmp_path):
    client, _service, _app = _build_client(monkeypatch)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "missing"))
    assert client.get("/reports").json() == {"count": 0, "reports": []}

    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    (tmp_path / "c1_1.md").write_text("report one", encoding="utf-8")
    (tmp_path / "c2_1.md").write_text("report two", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("x", encoding="utf-8")

    listing = client.get("/reports").json()
    assert listing["count"] == 2
    assert {item["filename"] for item in listing["reports"]} == {"c1_1.md", "c2_1.md"}
    filtered = client.get("/reports", params={"cluster": "c1"}).json()
    assert [item["filename"] for item in filtered["reports"]] == ["c1_1.md"]
    assert client.get("/reports", params={"limit": 1}).json()["count"] == 1
    assert client.get("/reports", params={"limit": 0}).status_code == 422

    response = client.get("/reports/c1_1.md")
    assert response.status_code == 200
    assert response.text == "report one"
    assert client.get("/reports/nope.md").status_code == 404
