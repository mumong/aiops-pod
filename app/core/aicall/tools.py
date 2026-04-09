"""MCP 工具加载：使用 langchain-mcp-adapters 连接 MCP SSE 服务"""
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


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
        logger.info("[tools] No MCP servers configured")
        return []

    # Build connections dict for MultiServerMCPClient
    connections: Dict[str, dict] = {}
    for name, server_cfg in mcp_servers_config.items():
        if not server_cfg.get("enabled", False):
            logger.debug("[tools] Skipping disabled MCP server: %s", name)
            continue

        config = server_cfg.get("config", {})
        url = config.get("url", "")
        if not url:
            logger.warning("[tools] MCP server %s has no url, skipping", name)
            continue

        connections[name] = {
            "transport": "sse",
            "url": url,
        }
        logger.info("[tools] Registered MCP server: %s → %s", name, url)

    if not connections:
        logger.info("[tools] No enabled MCP servers found")
        return []

    # Connect and load tools
    all_tools: List = []
    try:
        async with MultiServerMCPClient(connections) as client:
            all_tools = await client.get_tools()
        logger.info("[tools] Loaded %d tools from %d MCP servers",
                    len(all_tools), len(connections))
    except Exception as e:
        logger.error("[tools] Failed to load MCP tools: %s", e, exc_info=True)

    return all_tools
