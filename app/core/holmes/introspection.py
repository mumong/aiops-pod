#!/usr/bin/env python3
"""
Holmes 运行时资源信息输出（工具集、MCP、Runbook 等）

这一块逻辑与 FastAPI/路由无关，但在服务启动时很有价值，
因此从 HolmesService 中抽离，降低耦合、便于复用。
"""

from typing import Any, Optional

from holmes.plugins.runbooks import RunbookCatalog


def log_loaded_resources(ai: Any, merged_catalog: Optional[RunbookCatalog], logger) -> None:
    """输出加载的资源信息（工具集、MCP 服务器、工具、Runbook）"""
    if not ai or not getattr(ai, "tool_executor", None):
        return

    tool_executor = ai.tool_executor
    toolsets = tool_executor.toolsets

    # 1) 输出工具集信息（按类型分类）
    builtin_toolsets = []
    mcp_servers = []

    for toolset in toolsets:
        toolset_class_name = toolset.__class__.__name__.lower()
        is_mcp = (
            "mcp" in toolset_class_name
            or (hasattr(toolset, "type") and str(toolset.type).lower() == "mcp")
            or (hasattr(toolset, "__module__") and "mcp" in toolset.__module__.lower())
        )

        if is_mcp:
            mcp_servers.append(toolset)
        else:
            builtin_toolsets.append(toolset)

    # 内置工具集
    if builtin_toolsets:
        enabled_builtin = [ts for ts in builtin_toolsets if getattr(ts, "enabled", False)]
        if enabled_builtin:
            successful_toolsets = []
            failed_toolsets = []
            for toolset in enabled_builtin:
                toolset_tools = []
                if hasattr(toolset, "tools") and toolset.tools:
                    toolset_tools = [t.name for t in toolset.tools if hasattr(t, "name")]
                registered_tools = [t for t in toolset_tools if t in tool_executor.tools_by_name]

                status_str = str(toolset.status.value) if hasattr(toolset.status, "value") else str(toolset.status)
                if status_str == "enabled" and registered_tools:
                    successful_toolsets.append((toolset, len(registered_tools)))
                else:
                    failed_toolsets.append((toolset, status_str, len(toolset_tools), len(registered_tools)))

            if successful_toolsets:
                logger.info(f"📦 内置工具集 ({len(successful_toolsets)} 个已启用并可用):")
                for toolset, tool_count in successful_toolsets:
                    logger.info(f"   ✅ {toolset.name} ({tool_count} 个工具)")

            if failed_toolsets:
                logger.warning(f"⚠️  内置工具集 ({len(failed_toolsets)} 个配置但未成功加载):")
                for toolset, status, total_tools, registered_tools in failed_toolsets:
                    error_msg = getattr(toolset, "error", "未知错误")
                    logger.warning(
                        f"   ❌ {toolset.name} (状态: {status}, 工具: {registered_tools}/{total_tools}, 错误: {str(error_msg)[:100]})"
                    )

    # MCP 服务器（远程 toolsets）
    if mcp_servers:
        enabled_mcp = [ts for ts in mcp_servers if getattr(ts, "enabled", False)]
        if enabled_mcp:
            logger.info(f"🌐 MCP 服务器 ({len(enabled_mcp)} 个已连接):")
            for toolset in enabled_mcp:
                tool_count = len(toolset.tools) if hasattr(toolset, "tools") else 0
                status_value = getattr(getattr(toolset, "status", None), "value", "")
                status_icon = "✅" if status_value == "enabled" else "❌"
                
                # 详细调试信息
                logger.info(f"   {status_icon} {toolset.name} ({tool_count} 个工具)")
                logger.info(f"      - 状态: {status_value}")
                logger.info(f"      - 启用: {getattr(toolset, 'enabled', False)}")
                logger.info(f"      - 配置: {getattr(toolset, '_mcp_config', None)}")
                logger.info(f"      - 工具列表: {[t.name for t in toolset.tools] if hasattr(toolset, 'tools') and toolset.tools else '[]'}")
                
                # 如果有错误信息，输出
                if hasattr(toolset, "error") and toolset.error:
                    logger.error(f"      - 错误: {toolset.error}")
        else:
            logger.info("🌐 MCP 服务器: 无已启用的服务器")
    else:
        logger.info("🌐 MCP 服务器: 未配置")

    # 2) 输出工具统计
    all_tools = list(tool_executor.tools_by_name.keys())
    if all_tools:
        tool_counts = {}
        for toolset in toolsets:
            if getattr(toolset, "enabled", False) and hasattr(toolset, "tools"):
                toolset_tools = [t.name for t in toolset.tools if hasattr(t, "name")]
                registered_tools = [t for t in toolset_tools if t in tool_executor.tools_by_name]
                if registered_tools:
                    tool_counts[toolset.name] = len(registered_tools)

        logger.info(f"🔧 可用工具: 总计 {len(all_tools)} 个（已注册）")
        if tool_counts:
            sorted_counts = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for toolset_name, count in sorted_counts:
                logger.info(f"   • {toolset_name}: {count} 个工具")
            if len(tool_counts) > 10:
                logger.info(f"   ... 还有 {len(tool_counts) - 10} 个工具集")

    # 3) 输出 Runbook 信息
    if merged_catalog and merged_catalog.catalog:
        logger.info(f"📚 Runbook 知识库: {len(merged_catalog.catalog)} 个")
        for entry in merged_catalog.catalog[:5]:
            if hasattr(entry, "title"):
                title = entry.title
            elif isinstance(entry, dict):
                title = entry.get("title", "Unknown")
            else:
                title = str(entry)
            logger.info(f"   • {title}")
        if len(merged_catalog.catalog) > 5:
            logger.info(f"   ... 还有 {len(merged_catalog.catalog) - 5} 个 runbook")
    else:
        logger.info("📚 Runbook 知识库: 未配置")


