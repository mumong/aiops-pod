"""/ready is 503 until the service is initialized with every MCP server connected."""

from app.api.info_routes import readiness


def test_readiness_requires_initialized_and_all_mcp_servers():
    assert (
        readiness({"ai_initialized": True, "mcp_failed_servers": [], "status": "healthy"})[0]
        == 200
    )
    code, body = readiness(
        {"ai_initialized": True, "mcp_failed_servers": ["prometheus_tool"], "status": "healthy"}
    )
    assert (
        code == 503
        and body["mcp_failed_servers"] == ["prometheus_tool"]
        and body["ready"] is False
    )
    assert readiness({"ai_initialized": False, "status": "initializing"})[0] == 503
