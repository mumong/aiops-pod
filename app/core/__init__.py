"""
Core 模块
核心业务逻辑，包括 HolmesGPT 服务、Runbook 管理、提示词配置和 MCP 服务器管理
"""

from .environment import (
    get_config_file_path,
    get_environment,
    is_running_in_kubernetes,
    log_environment_info,
)
from .mcp import (
    MCPServerManager,
    auto_start_mcp_servers,
    get_mcp_manager,
    shutdown_mcp_servers,
    shutdown_mcp_servers_sync,
)
from .prompts import SYSTEM_PROMPT
from .runbook import RunbookManager
from .service import HolmesService, get_service

__all__ = [
    "HolmesService",
    "get_service",
    "RunbookManager",
    "SYSTEM_PROMPT",
    "MCPServerManager",
    "get_mcp_manager",
    "auto_start_mcp_servers",
    "shutdown_mcp_servers",
    "shutdown_mcp_servers_sync",
]

