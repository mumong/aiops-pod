#!/usr/bin/env python3
"""
Holmes Tool 调用结果日志补丁

在 Holmes 的 Tool.invoke() 返回前，将每次工具调用的「实际输出」和「错误信息」
打到 app 的 logger，便于在 Pod 日志中直接看到 MCP 工具的输出和失败原因，无需 /show N。
适用于所有调用路径（流式 / 同步 / 控制台）。
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 单条日志中结果预览的最大字符数（避免刷屏）
MAX_OUTPUT_PREVIEW_CHARS = 800
# 错误信息最大长度
MAX_ERROR_CHARS = 500

_original_invoke = None


def _patched_invoke(self, params: Dict, context: Any):
    """包装 Tool.invoke：在原逻辑执行后，将输出与错误写入 app logger。"""
    result = _original_invoke(self, params=params, context=context)

    try:
        output_str = (
            result.get_stringified_data()
            if hasattr(result, "get_stringified_data")
            else str(result)
        )
        status = getattr(result, "status", None)
        status_str = str(getattr(status, "value", status)) if status is not None else "unknown"
        error_str = getattr(result, "error", None)
        if error_str is not None:
            error_str = str(error_str)

        tool_label = f"{self.name}"
        if context and getattr(context, "tool_number", None):
            tool_label = f"#{context.tool_number} {tool_label}"

        # 结果预览（截断，并单行化便于日志）
        preview = (output_str or "").replace("\n", " ").strip()
        if len(preview) > MAX_OUTPUT_PREVIEW_CHARS:
            preview = preview[:MAX_OUTPUT_PREVIEW_CHARS] + " ... (已截断)"

        # 判定是否为失败（Holmes 的 StructuredToolResultStatus）
        try:
            from holmes.core.tools import StructuredToolResultStatus
            is_error = status != StructuredToolResultStatus.SUCCESS or bool(error_str and str(error_str).strip())
        except Exception:
            is_error = status_str not in ("success", "enabled") or bool(error_str and str(error_str).strip())
        icon = "❌" if is_error else "✅"

        logger.info(
            "🔧 [工具结果] %s %s | status=%s | 输出预览: %s",
            icon,
            tool_label,
            status_str,
            preview or "<空>",
        )
        if error_str and str(error_str).strip():
            err_preview = (error_str[:MAX_ERROR_CHARS] + " ...") if len(error_str) > MAX_ERROR_CHARS else error_str
            logger.error("🔧 [工具错误] %s 错误详情: %s", tool_label, err_preview)
    except Exception as e:
        logger.debug("工具结果日志输出时出错（不影响主流程）: %s", e)

    return result


def apply_tool_result_logging_patch() -> bool:
    """对 holmes.core.tools.Tool.invoke 打补丁，使每次工具调用后输出结果/错误到 app logger。"""
    global _original_invoke
    try:
        from holmes.core.tools import Tool

        if _original_invoke is None:
            _original_invoke = Tool.invoke
            Tool.invoke = _patched_invoke
            logger.info("✅ 已启用工具调用结果日志补丁（输出与错误将写入本 logger）")
            return True
        return True
    except Exception as e:
        logger.warning("⚠️ 工具结果日志补丁未应用: %s", e)
        return False
