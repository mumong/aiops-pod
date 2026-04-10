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

    # Connect and load tools
    all_tools: List = []
    try:
        logger.info("🔄 [MCP-Tools] 连接 %d 个 MCP 服务器...", len(connections))
        client = MultiServerMCPClient(connections)
        all_tools = await client.get_tools()
        tool_names = [t.name for t in all_tools]
        logger.info("✅ [MCP-Tools] 加载 %d 个工具: %s",
                    len(all_tools), ", ".join(tool_names[:10]))
        if len(tool_names) > 10:
            logger.debug("   ... 完整列表: %s", ", ".join(tool_names))
    except Exception as e:
        logger.error("❌ [MCP-Tools] 加载失败: %s", e, exc_info=True)

    return all_tools
