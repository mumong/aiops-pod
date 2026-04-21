import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.api.routes import register_routes


class _FakeCoordinator:
    def __init__(self):
        self.calls = []
        self._registry = type(
            "_Registry",
            (),
            {"get_enabled_agents": lambda self: [object(), object()]},
        )()

    def ask_stream(self, **kwargs):
        self.calls.append(kwargs)
        yield "coordinator-ok"


class _FakeAgent:
    def __init__(self):
        self.calls = []

    def ask_stream(self, **kwargs):
        self.calls.append(kwargs)
        yield "agent-ok"


class _FakeService:
    def __init__(self):
        self.federation_coordinator = _FakeCoordinator()
        self.federation_agent = _FakeAgent()
        self.merged_catalog = None

    def health_check(self):
        return {"status": "healthy"}

    def get_tools_info(self):
        return {"success": True}

    def get_tools_detail(self):
        return {"success": True}


def _build_client(monkeypatch):
    fake_service = _FakeService()
    app = FastAPI()
    register_routes(app)
    monkeypatch.setattr("app.api.routes.get_service", lambda: fake_service)
    return TestClient(app), fake_service


def test_federation_query_route_uses_query_endpoint_path(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/federation/query", params={"q": "哪个集群 CPU 最高"})

    assert response.status_code == 200
    assert len(fake_service.federation_coordinator.calls) == 1
    call = fake_service.federation_coordinator.calls[0]
    assert call["endpoint_path"] == "/query"


def test_federation_ask_route_keeps_ask_endpoint_path(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/federation/ask", params={"q": "我的多集群有什么问题"})

    assert response.status_code == 200
    assert len(fake_service.federation_coordinator.calls) == 1
    call = fake_service.federation_coordinator.calls[0]
    assert call["endpoint_path"] == "/ask"


def test_federation_query_v2_route_uses_query_endpoint_path(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/federation/query/v2", params={"q": "查询 cluster-a 的 CPU"})

    assert response.status_code == 200
    assert len(fake_service.federation_agent.calls) == 1
    call = fake_service.federation_agent.calls[0]
    assert call["endpoint_path"] == "/query"


def test_federation_ask_v2_route_keeps_ask_endpoint_path(monkeypatch):
    client, fake_service = _build_client(monkeypatch)

    response = client.get("/federation/ask/v2", params={"q": "分析 cluster-a 的问题"})

    assert response.status_code == 200
    assert len(fake_service.federation_agent.calls) == 1
    call = fake_service.federation_agent.calls[0]
    assert call["endpoint_path"] == "/ask"
