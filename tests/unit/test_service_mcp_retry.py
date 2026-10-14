import time
from types import SimpleNamespace
from unittest.mock import patch

from app.core import service as service_module
from app.core.service import HolmesService


def _tool(name):
    return SimpleNamespace(name=name)


def _service_with_failed(failed, existing=("a",)):
    service = HolmesService()
    service.mcp_tools = [_tool(n) for n in existing]
    service._mcp_servers_config = {name: {"enabled": True, "config": {"url": "u"}} for name in failed}
    service._mcp_failed_servers = list(failed)
    service._mcp_retry_after = 0.0
    return service


def test_retry_adds_recovered_tools_and_clears_failed():
    service = _service_with_failed(["k8s"])

    async def fake_load(cfg, failed):
        assert list(cfg) == ["k8s"]
        return [_tool("kubectl_get"), _tool("a"), _tool("kubectl_top_pods")]

    with patch("app.core.aicall.tools.load_mcp_tools", fake_load):
        service._retry_failed_mcp_servers()

    assert [t.name for t in service.mcp_tools] == ["a", "kubectl_get"]
    assert service._mcp_failed_servers == []


def test_retry_is_rate_limited_and_keeps_still_failed():
    service = _service_with_failed(["k8s"])
    calls = []

    async def fake_load(cfg, failed):
        calls.append(cfg)
        failed.extend(cfg)
        return []

    with patch("app.core.aicall.tools.load_mcp_tools", fake_load):
        service._retry_failed_mcp_servers()
        service._retry_failed_mcp_servers()  # within interval: no second attempt

    assert len(calls) == 1
    assert service._mcp_failed_servers == ["k8s"]
    assert service._mcp_retry_after > time.monotonic() + service_module.MCP_RETRY_INTERVAL_SECONDS - 5


def test_no_retry_when_nothing_failed():
    service = _service_with_failed([])
    with patch("app.core.aicall.tools.load_mcp_tools", side_effect=AssertionError("must not load")):
        service._retry_failed_mcp_servers()


def test_stream_waits_for_init_and_fails_fast_when_init_failed():
    import threading

    service = HolmesService()
    # init attempt finished with failure -> no 60s wait
    service._init_finished.set()
    started = time.monotonic()
    chunks = list(service.execute_query_stream("q", output_format="text"))
    assert time.monotonic() - started < 1
    assert "初始化超时或失败" in "".join(chunks)

    # init in progress -> wakes up as soon as it finishes
    service = HolmesService()
    timer = threading.Timer(0.2, service._init_finished.set)
    timer.start()
    started = time.monotonic()
    waited = service._wait_for_initialization(timeout=5)
    assert 0.1 < waited < 2
