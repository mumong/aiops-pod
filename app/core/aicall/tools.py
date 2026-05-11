"""MCP 工具加载：使用 langchain-mcp-adapters 连接 MCP SSE 服务"""
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


PROMETHEUS_QUERY_TOOLS = {
    "execute_prometheus_instant_query",
    "execute_prometheus_range_query",
}

INVALID_PROMETHEUS_TIME_VALUES = {
    "",
    "now",
    "now()",
    "current",
    "latest",
}


def _sanitize_mcp_tool_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize MCP transport arguments before they reach the MCP server.

    Prometheus instant query uses server-side current time when `time` is
    omitted. Literal values like `now()` are valid PromQL concepts in some
    contexts but invalid for the HTTP API `time` parameter, so remove them at
    the transport boundary. This does not alter diagnostic meaning.
    """
    sanitized = dict(args or {})
    if tool_name not in PROMETHEUS_QUERY_TOOLS:
        return sanitized

    if "time" in sanitized:
        raw_time = sanitized.get("time")
        normalized_time = str(raw_time or "").strip().lower()
        if normalized_time in INVALID_PROMETHEUS_TIME_VALUES:
            sanitized.pop("time", None)

    return sanitized


def _log_sanitized_args(tool_name: str, original: Dict[str, Any], sanitized: Dict[str, Any]) -> None:
    if sanitized == original:
        return
    removed = sorted(set(original.keys()) - set(sanitized.keys()))
    logger.info(
        "🧼 [MCP-Tools] sanitized args | tool=%s removed=%s sanitized=%s",
        tool_name,
        removed,
        sanitized,
    )


def _wrap_mcp_tool_for_transport(tool: Any) -> Any:
    """Wrap selected MCP tools with transport-safe argument normalization."""
    tool_name = str(getattr(tool, "name", "") or "")
    if tool_name not in PROMETHEUS_QUERY_TOOLS:
        return tool

    from langchain_core.tools import StructuredTool

    async def _acoroutine(**kwargs: Any) -> Any:
        sanitized = _sanitize_mcp_tool_args(tool_name, kwargs)
        _log_sanitized_args(tool_name, kwargs, sanitized)
        return await tool.ainvoke(sanitized)

    def _func(**kwargs: Any) -> Any:
        sanitized = _sanitize_mcp_tool_args(tool_name, kwargs)
        _log_sanitized_args(tool_name, kwargs, sanitized)
        return tool.invoke(sanitized)

    wrapped = StructuredTool.from_function(
        func=_func,
        coroutine=_acoroutine,
        name=tool_name,
        description=getattr(tool, "description", "") or "",
        args_schema=getattr(tool, "args_schema", None),
        return_direct=getattr(tool, "return_direct", False),
        # The wrapper returns the underlying MCP result as message content.
        # Keeping an upstream "content_and_artifact" contract here would make
        # LangChain expect a two-tuple from this adapter and fail before AICall
        # can archive the actual tool output.
        response_format="content",
    )
    wrapped.metadata = dict(getattr(tool, "metadata", None) or {})
    return wrapped


async def load_mcp_tools(mcp_servers_config: Dict[str, Any]) -> List:
    """从 MCP 配置加载所有工具为 LangChain BaseTool

    Args:
        mcp_servers_config: config.yaml 中 mcp_servers 块，格式:
            server_name:
              description: "..."
              config:
                url: "http://host:port/sse"
                mode: "sse"
              enabled: true

    Returns:
        List[BaseTool] — 所有已连接 MCP 服务器的工具列表
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    if not mcp_servers_config:
        logger.info("🔧 [MCP-Tools] 无 MCP 服务器配置")
        return []

    # Build connections dict for MultiServerMCPClient
    connections: Dict[str, dict] = {}
    for name, server_cfg in mcp_servers_config.items():
        if not server_cfg.get("enabled", False):
            logger.debug("   ⏭️ [MCP-Tools] 跳过已禁用: %s", name)
            continue

        config = server_cfg.get("config", {})
        url = config.get("url", "")
        if not url:
            logger.warning("   ⚠️ [MCP-Tools] %s 无 url，跳过", name)
            continue

        connections[name] = {
            "transport": "sse",
            "url": url,
        }
        logger.debug("   📡 [MCP-Tools] 注册: %s → %s", name, url)

    if not connections:
        logger.info("🔧 [MCP-Tools] 无已启用的 MCP 服务器")
        return []

    # 逐个 server 连接并加载工具，记录每个 server 的工具列表
    all_tools: List = []
    server_tool_map: Dict[str, List[str]] = {}
    failed_servers: List[str] = []

    for srv_name, conn_cfg in connections.items():
        try:
            client = MultiServerMCPClient({srv_name: conn_cfg})
            tools = await client.get_tools()
            tool_names = [t.name for t in tools]
            server_tool_map[srv_name] = tool_names
            # 给每个工具打上 server_name 标签，供 _log_loaded_resources 按 server 分组
            wrapped_tools = []
            for t in tools:
                t.metadata = {**(t.metadata or {}), "server_name": srv_name}
                wrapped_tools.append(_wrap_mcp_tool_for_transport(t))
            all_tools.extend(wrapped_tools)
            logger.info("   ✅ [%s] %d 个工具: %s",
                       srv_name, len(tools), ", ".join(tool_names))
        except Exception as e:
            failed_servers.append(srv_name)
            logger.error("   ❌ [%s] 连接失败: %s", srv_name, e)

    if failed_servers:
        logger.warning("⚠️ [MCP-Tools] %d 个服务器连接失败: %s",
                       len(failed_servers), ", ".join(failed_servers))

    # 汇总输出：按 server 分组的工具清单
    logger.info("=" * 50)
    logger.info("📋 [MCP-Tools] 工具加载汇总: %d 个工具 (来自 %d/%d 个服务器)",
                len(all_tools), len(server_tool_map), len(connections))
    logger.info("-" * 50)
    for srv_name, tool_names in server_tool_map.items():
        logger.info("   📡 [%s] %d 个工具:", srv_name, len(tool_names))
        for tn in tool_names:
            logger.info("      - %s", tn)
    if failed_servers:
        logger.info("   ❌ 连接失败: %s", ", ".join(failed_servers))
    logger.info("=" * 50)

    return all_tools
