"""A plain /ask (stream=false) must not tear down the shared service.

/ask passes max_steps=20 by default; execute_query reset config and ai_call whenever
max_steps != 50, so every sync request re-initialised the service (reloading all MCP
tools), and concurrent requests saw config=None mid-initialisation (live 2026-10-20,
first request after a restart: "'NoneType' object has no attribute
'get_runbook_catalog'"). max_steps is not read by the workflow; only an explicit
api_key/model asks for a new client.
"""

from app.core.service import HolmesService


def _service(monkeypatch):
    service = HolmesService.__new__(HolmesService)
    service.config, service.ai_call = object(), object()
    calls = []
    monkeypatch.setattr(service, "initialize", lambda **kw: calls.append(kw), raising=False)
    monkeypatch.setattr(service, "_wait_for_initialization", lambda: 0, raising=False)
    monkeypatch.setattr(service, "execute_query_stream", lambda **kw: iter(["ok"]), raising=False)
    return service, calls


def test_max_steps_alone_keeps_the_initialised_service(monkeypatch):
    service, _ = _service(monkeypatch)
    config, ai_call = service.config, service.ai_call
    service.execute_query(question="q", max_steps=20)
    assert service.config is config and service.ai_call is ai_call


def test_explicit_model_still_requests_a_new_client(monkeypatch):
    service, _ = _service(monkeypatch)
    service.execute_query(question="q", model="other/model")
    assert service.config is None and service.ai_call is None
