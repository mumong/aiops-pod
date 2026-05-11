"""Tests for MCP tool loading"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.aicall.tools import load_mcp_tools


def _run(coro):
    return asyncio.run(coro)


def test_load_mcp_tools_empty_config():
    assert _run(load_mcp_tools({})) == []


def test_load_mcp_tools_none_config():
    assert _run(load_mcp_tools(None)) == []


def test_load_mcp_tools_disabled_server():
    config = {
        "k8s": {
            "description": "K8s MCP",
            "config": {"url": "http://localhost:8093/sse", "mode": "sse"},
            "enabled": False,
        }
    }
    assert _run(load_mcp_tools(config)) == []


def test_load_mcp_tools_no_url():
    config = {
        "broken": {
            "description": "No URL",
            "config": {"mode": "sse"},
            "enabled": True,
        }
    }
    assert _run(load_mcp_tools(config)) == []


def test_load_mcp_tools_builds_correct_connections():
    """Verify MultiServerMCPClient receives correct connection config."""
    config = {
        "k8s": {
            "description": "K8s MCP",
            "config": {"url": "http://localhost:8093/sse", "mode": "sse"},
            "enabled": True,
        },
        "disabled": {
            "description": "Disabled",
            "config": {"url": "http://localhost:9999/sse"},
            "enabled": False,
        },
    }

    mock_tools = [MagicMock(name="kubectl_get"), MagicMock(name="kubectl_describe")]

    with patch("langchain_mcp_adapters.client.MultiServerMCPClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get_tools = AsyncMock(return_value=mock_tools)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_instance

        result = _run(load_mcp_tools(config))

        MockClient.assert_called_once()
        connections = MockClient.call_args[0][0]
        assert "k8s" in connections
        assert "disabled" not in connections
        assert connections["k8s"]["transport"] == "sse"
        assert connections["k8s"]["url"] == "http://localhost:8093/sse"
        assert result == mock_tools


def test_prometheus_instant_query_removes_invalid_now_time_before_mcp_call():
    from app.core.aicall.tools import _sanitize_mcp_tool_args

    sanitized = _sanitize_mcp_tool_args(
        "execute_prometheus_instant_query",
        {
            "query": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "time": "now()",
        },
    )

    assert sanitized == {
        "query": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
    }


def test_prometheus_range_query_keeps_real_time_bounds():
    from app.core.aicall.tools import _sanitize_mcp_tool_args

    sanitized = _sanitize_mcp_tool_args(
        "execute_prometheus_range_query",
        {
            "query": "up",
            "start": "2026-05-09T10:00:00Z",
            "end": "2026-05-09T10:05:00Z",
            "step": "30s",
        },
    )

    assert sanitized["start"] == "2026-05-09T10:00:00Z"
    assert sanitized["end"] == "2026-05-09T10:05:00Z"


def test_prometheus_wrapper_uses_content_response_format():
    from app.core.aicall.tools import _wrap_mcp_tool_for_transport

    upstream = MagicMock()
    upstream.name = "execute_prometheus_instant_query"
    upstream.description = "Prometheus instant query"
    upstream.args_schema = None
    upstream.return_direct = False
    upstream.metadata = {"server_name": "prometheus"}
    upstream.response_format = "content_and_artifact"

    wrapped = _wrap_mcp_tool_for_transport(upstream)

    assert wrapped.name == "execute_prometheus_instant_query"
    assert wrapped.response_format == "content"
    assert wrapped.metadata == {"server_name": "prometheus"}
