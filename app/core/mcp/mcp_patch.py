#!/usr/bin/env python3
"""
MCP Toolset Patch - 修复工具列表获取问题

根本原因分析：
1. HolmesGPT 的 MCP toolset 在 prerequisites_callable 中调用 asyncio.run()
2. 某些 MCP 服务器在初始化后需要时间准备工具列表
3. 可能存在异步上下文管理器没有正确清理的问题
4. anyio TaskGroup 抛出的异常被包装在 ExceptionGroup 中

解决方案：
1. 在 list_tools() 前添加延迟
2. 添加详细的错误日志
3. 添加重试机制
4. 正确处理 ExceptionGroup 异常
"""
import asyncio
import logging
import sys
from typing import Any

try:
    # Python 3.11+
    ExceptionGroup = ExceptionGroup  # type: ignore
except NameError:
    # Python 3.10 及更早版本，使用 exceptiongroup 包
    try:
        from exceptiongroup import ExceptionGroup
    except ImportError:
        ExceptionGroup = None  # type: ignore

logger = logging.getLogger(__name__)

# 保存原始方法的引用
_original_get_server_tools = None


def _extract_exception_from_group(exc: Any) -> tuple[str, Exception]:
    """
    从 ExceptionGroup 中提取真实的异常信息
    
    Returns:
        (error_message, original_exception)
    """
    if ExceptionGroup and isinstance(exc, ExceptionGroup):
        # 提取第一个子异常
        exceptions = exc.exceptions if hasattr(exc, 'exceptions') else []
        if exceptions:
            first_exc = exceptions[0]
            # 如果子异常也是 ExceptionGroup，递归提取
            if isinstance(first_exc, ExceptionGroup):
                return _extract_exception_from_group(first_exc)
            
            error_type = type(first_exc).__name__
            error_msg = str(first_exc)
            return f"{error_type}: {error_msg}", first_exc
        
        return f"ExceptionGroup: {exc}", exc
    else:
        error_type = type(exc).__name__
        error_msg = str(exc)
        return f"{error_type}: {error_msg}", exc


async def _patched_get_server_tools(self):
    """
    修补后的 _get_server_tools 方法
    添加延迟、错误处理和重试机制，正确处理 ExceptionGroup
    """
    from holmes.plugins.toolsets.mcp.toolset_mcp import get_initialized_mcp_session
    
    server_name = self.name
    max_retries = 2
    result = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"[MCP] 正在获取 {server_name} 的工具列表 (尝试 {attempt + 1}/{max_retries})...")
            
            async with get_initialized_mcp_session(self) as session:
                # 等待服务器完全初始化
                await asyncio.sleep(1.5)
                
                # 调用 list_tools
                result = await session.list_tools()
                
                tool_count = len(result.tools) if result and hasattr(result, 'tools') else 0
                logger.info(f"[MCP] ✅ {server_name} 成功返回 {tool_count} 个工具")
                
                if tool_count == 0:
                    logger.warning(f"[MCP] ⚠️ {server_name} 返回的工具列表为空")
                    if attempt < max_retries - 1:
                        logger.info(f"[MCP] 等待 2 秒后重试...")
                        await asyncio.sleep(2)
                        continue
                
                return result
                
        except BaseException as e:
            # 提取真实的错误信息（处理 ExceptionGroup）
            error_msg, original_exc = _extract_exception_from_group(e)
            
            logger.error(f"[MCP] ❌ {server_name} 获取工具列表失败 (尝试 {attempt + 1}/{max_retries})")
            logger.error(f"[MCP]    错误详情: {error_msg}")
            
            # 输出详细的堆栈信息到 debug 日志
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(f"[MCP] 完整堆栈:\n{traceback.format_exc()}")
            
            if attempt < max_retries - 1:
                logger.info(f"[MCP] 等待 2 秒后重试...")
                await asyncio.sleep(2)
            else:
                logger.error(f"[MCP] {server_name} 所有重试均失败，最后错误: {error_msg}")
                raise
    
    # 如果所有尝试都返回空列表，返回最后一次的结果
    return result


def patch_mcp_toolset():
    """
    为 MCP toolset 打补丁，添加初始化延迟和错误处理
    """
    try:
        # 强制输出到 stderr，确保日志可见
        print("=" * 60, file=sys.stderr)
        print("🔧 [MCP PATCH] 开始应用 MCP toolset 补丁...", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        from holmes.plugins.toolsets.mcp.toolset_mcp import RemoteMCPToolset
        
        global _original_get_server_tools
        if _original_get_server_tools is None:
            # 保存原始方法
            _original_get_server_tools = RemoteMCPToolset._get_server_tools
            
            # 替换为修补后的方法
            RemoteMCPToolset._get_server_tools = _patched_get_server_tools
            
            msg = "✅ [MCP PATCH] MCP toolset 补丁已成功应用（添加延迟、错误处理和重试机制）"
            logger.info(msg)
            print(msg, file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            return True
        else:
            msg = "⚠️ [MCP PATCH] 补丁已经应用过了，跳过"
            logger.warning(msg)
            print(msg, file=sys.stderr)
            return True
    except ImportError as e:
        msg = f"⚠️ [MCP PATCH] 无法导入 MCP toolset，跳过补丁: {e}"
        logger.warning(msg)
        print(msg, file=sys.stderr)
        return False
    except Exception as e:
        msg = f"❌ [MCP PATCH] 应用 MCP toolset 补丁失败: {e}"
        logger.error(msg)
        print(msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def unpatch_mcp_toolset():
    """
    移除 MCP toolset 补丁
    """
    try:
        from holmes.plugins.toolsets.mcp.toolset_mcp import RemoteMCPToolset
        
        global _original_get_server_tools
        if _original_get_server_tools is not None:
            RemoteMCPToolset._get_server_tools = _original_get_server_tools
            _original_get_server_tools = None
            logger.info("✅ MCP toolset 补丁已移除")
            return True
    except Exception as e:
        logger.error(f"❌ 移除 MCP toolset 补丁失败: {e}")
        return False
