"""Tests for MCP tool loading"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.aicall.tools import load_mcp_tools


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


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
