"""内置工具 — 不走 MCP，直接在 aiops-copilot 内部执行

当前包含：
- FetchRunbookTool: 读取本地 Runbook .md 文件（通过 ConfigMap 挂载）
"""
import os
import logging
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)

# Runbook 搜索路径（按优先级）
DEFAULT_RUNBOOK_DIRS = [
    "/app/knowledge_base/runbooks",      # K8s ConfigMap 挂载
    "knowledge_base/runbooks",           # 本地开发
]


class FetchRunbookTool(BaseTool):
    """获取 Runbook 诊断手册内容

    LLM 根据 catalog 中的 link 字段调用此工具，
    传入 runbook_id（如 'l3-imagepull-failed.md'），
    返回完整的诊断手册内容 + 执行指令。
    """
    name: str = "fetch_runbook"
    description: str = (
        "获取 Runbook 诊断手册。传入 runbook_id（如 'l3-imagepull-failed.md'）。"
        "返回手册内容后，你必须按照手册中的步骤使用工具执行诊断。"
    )
    runbook_dirs: list = Field(default_factory=lambda: list(DEFAULT_RUNBOOK_DIRS))

    def _run(self, runbook_id: str) -> str:
        """同步执行：读取本地 .md 文件"""
        safe_id = os.path.basename(runbook_id)
        logger.debug("📚 [fetch_runbook] 查找: %s", safe_id)

        auto_remediate = os.getenv("AUTO_REMEDIATE", "false").lower() in ("true", "1", "yes")

        for d in self.runbook_dirs:
            path = os.path.join(d, safe_id)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info("📚 [fetch_runbook] 找到: %s (%d 字符)", path, len(content))

                if auto_remediate:
                    suffix = (
                        "Note: the above are DIRECTIONS not ACTUAL RESULTS. "
                        "You now need to follow the steps outlined in the runbook "
                        "yourself USING TOOLS. "
                        "Anything that looks like an actual result in the above "
                        "<runbook> is just an EXAMPLE. "
                        "Now follow those steps and report back what you find."
                    )
                else:
                    suffix = (
                        "Note: the above runbook is for DIAGNOSTIC REFERENCE ONLY. "
                        "Follow the DIAGNOSTIC steps to gather evidence using tools, "
                        "but DO NOT execute any remediation/fix commands. "
                        "Report your findings and suggest fixes in your analysis."
                    )

                return f"<runbook>\n{content}\n</runbook>\n{suffix}"

        searched = ", ".join(self.runbook_dirs)
        logger.warning("⚠️ [fetch_runbook] 未找到: %s (搜索路径: %s)", safe_id, searched)
        return f"Error: Runbook '{safe_id}' not found in search paths: [{searched}]"

    async def _arun(self, runbook_id: str) -> str:
        """异步版本（直接调用同步，文件读取不需要异步）"""
        return self._run(runbook_id)


def get_builtin_tools(runbook_dirs: Optional[list] = None) -> list:
    """获取所有内置工具列表

    Args:
        runbook_dirs: Runbook 搜索路径列表（可选，默认使用 DEFAULT_RUNBOOK_DIRS）

    Returns:
        List[BaseTool]
    """
    dirs = runbook_dirs or list(DEFAULT_RUNBOOK_DIRS)
    tools = [
        FetchRunbookTool(runbook_dirs=dirs),
    ]
    # 标记为内置工具，方便 _log_loaded_resources 分组显示
    for t in tools:
        t._is_builtin = True
    logger.info("🔧 [内置工具] 加载 %d 个: %s", len(tools), ", ".join(t.name for t in tools))
    return tools
