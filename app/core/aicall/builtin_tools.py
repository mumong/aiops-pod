"""内置工具 — 不走 MCP，直接在 aiops-copilot 内部执行

当前包含：
- FetchRunbookTool: 读取本地 Runbook .md 文件（通过 ConfigMap 挂载）
- ReadContextArchiveTool: 按归档路径读取本地 context archive 文件
"""
import os
import logging
from pathlib import Path
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import Field

from app.core.context.archive import (
    DEFAULT_ARCHIVE_ROOT,
    REPORTS_ARCHIVE_ROOT,
    get_archive_root,
)

logger = logging.getLogger(__name__)

# Runbook 搜索路径（按优先级）
DEFAULT_RUNBOOK_DIRS = [
    "/app/knowledge_base/runbooks",      # K8s ConfigMap 挂载
    "knowledge_base/runbooks",           # 本地开发
]

DEFAULT_ENABLED_RUNBOOK_IDS = [
    "l0-volume-limit",
    "pod-volume-mount-failed",
    "l1-taint-node",
    "pod-node-lost-unknown",
    "pod-terminating-stuck",
    "l2-oomkilled",
    "pod-crashloop-runtime",
    "l3-imagepull-failed",
    "pod-sandbox-create-failed",
    "l4-config-bootstrap-fail",
    "pod-notready-probe-failed",
    "private-k8s-query-promql-reference",
]


def _default_archive_roots() -> list:
    roots = []
    for candidate in [get_archive_root(), DEFAULT_ARCHIVE_ROOT, REPORTS_ARCHIVE_ROOT]:
        text = str(candidate).strip()
        if text and text not in roots:
            roots.append(text)
    return roots


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
    allowed_runbook_ids: list = Field(default_factory=lambda: list(DEFAULT_ENABLED_RUNBOOK_IDS))

    def _run(self, runbook_id: str) -> str:
        """同步执行：读取本地 .md 文件"""
        safe_id = os.path.basename(runbook_id)
        normalized_id = safe_id[:-3] if safe_id.endswith(".md") else safe_id
        logger.debug("📚 [fetch_runbook] 查找: %s", safe_id)

        if self.allowed_runbook_ids and normalized_id not in set(self.allowed_runbook_ids):
            logger.warning("⚠️ [fetch_runbook] 已禁用: %s", safe_id)
            return f"Error: Runbook '{safe_id}' is disabled by the current runtime profile"

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


class ReadContextArchiveTool(BaseTool):
    """读取 context archive 中已落盘的文件内容。"""

    name: str = "read_context_archive"
    description: str = (
        "读取 context archive 里的已落盘文件。"
        "传入 archive_path（例如 raw_ref/summary_ref/archive_ref/handoff_ref/input_ref/output_ref 指向的绝对路径），"
        "可选 offset 和 length 用于分段读取大文件。"
        "仅允许读取 context archive 根目录下的文件。"
    )
    allowed_roots: list = Field(default_factory=_default_archive_roots)
    default_length: int = 12000
    max_length: int = 40000

    def _run(self, archive_path: str, offset: int = 0, length: Optional[int] = None) -> str:
        requested = (archive_path or "").strip()
        if not requested:
            return "Error: archive_path is required"

        target = Path(requested).expanduser()
        try:
            resolved = target.resolve(strict=False)
        except Exception:
            resolved = target

        allowed = []
        for root in self.allowed_roots:
            text = str(root).strip()
            if not text:
                continue
            try:
                allowed.append(Path(text).expanduser().resolve(strict=False))
            except Exception:
                continue

        if not any(self._is_relative_to(resolved, root) for root in allowed):
            allowed_text = ", ".join(str(p) for p in allowed)
            logger.warning("⚠️ [read_context_archive] 非法路径: %s", requested)
            return f"Error: archive_path '{requested}' is not under allowed archive roots: [{allowed_text}]"

        if not resolved.is_file():
            logger.warning("⚠️ [read_context_archive] 文件不存在: %s", resolved)
            return f"Error: archive file not found: {resolved}"

        try:
            content = resolved.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("⚠️ [read_context_archive] 读取失败: %s | %s", resolved, exc)
            return f"Error: failed to read archive file '{resolved}': {exc}"

        safe_offset = max(0, int(offset or 0))
        requested_length = self.default_length if length is None else int(length)
        safe_length = max(200, min(requested_length, self.max_length))
        snippet = content[safe_offset:safe_offset + safe_length]
        truncated = safe_offset + safe_length < len(content)
        logger.info(
            "📦 [read_context_archive] 读取: %s | offset=%d length=%d total=%d truncated=%s",
            resolved, safe_offset, safe_length, len(content), truncated,
        )

        suffix = ""
        if truncated:
            suffix = (
                f"\n[truncated] total_chars={len(content)} "
                f"returned_chars={len(snippet)} next_offset={safe_offset + len(snippet)}"
            )

        return (
            "<context_archive>\n"
            f"archive_path: {resolved}\n"
            f"offset: {safe_offset}\n"
            f"returned_chars: {len(snippet)}\n"
            f"total_chars: {len(content)}\n"
            "content:\n"
            f"{snippet}\n"
            "</context_archive>"
            f"{suffix}"
        )

    async def _arun(self, archive_path: str, offset: int = 0, length: Optional[int] = None) -> str:
        return self._run(archive_path=archive_path, offset=offset, length=length)

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False


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
        ReadContextArchiveTool(),
    ]
    # 标记为内置工具，方便 _log_loaded_resources 分组显示
    for t in tools:
        t._is_builtin = True
    logger.info("🔧 [内置工具] 加载 %d 个: %s", len(tools), ", ".join(t.name for t in tools))
    return tools
