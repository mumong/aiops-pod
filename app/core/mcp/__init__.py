"""
MCP 相关模块（可选：本地 auto-start + 状态管理）

说明：
- 默认生产模式通常只“连接第三方 MCP Server（HTTP/SSE）”，不需要本地拉起子进程
- 本包仅负责“本地 auto-start”这一可选能力（用于本地开发/同 Pod 部署 bridge 等场景）
"""

from .manager import (
    MCPServerInfo,
    MCPServerManager,
    get_mcp_manager,
    auto_start_mcp_servers,
    shutdown_mcp_servers,
    shutdown_mcp_servers_sync,
)
from .mcp_patch import patch_mcp_toolset, unpatch_mcp_toolset

__all__ = [
    "MCPServerInfo",
    "MCPServerManager",
    "get_mcp_manager",
    "auto_start_mcp_servers",
    "shutdown_mcp_servers",
    "shutdown_mcp_servers_sync",
    "patch_mcp_toolset",
    "unpatch_mcp_toolset",
]


