"""内置工具 — 不走 MCP，直接在 aiops-copilot 内部执行

当前包含：
- FetchRunbookTool: 读取本地 Runbook .md 文件（通过 ConfigMap 挂载）
- ReadContextArchiveTool: 按归档路径读取本地 context archive 文件
"""

import logging
import os
from pathlib import Path
from typing import Literal, Optional

from langchain_core.tools import BaseTool
from pydantic import Field

from app.core.context.archive import (
    DEFAULT_ARCHIVE_ROOT,
    REPORTS_ARCHIVE_ROOT,
    get_archive_root,
)
from app.core.context.budget import estimate_tokens
from app.core.context.evidence_policy import EvidencePolicy

logger = logging.getLogger(__name__)

# Runbook 搜索路径（按优先级）
DEFAULT_RUNBOOK_DIRS = [
    "/app/knowledge_base/runbooks",  # K8s ConfigMap 挂载
    "knowledge_base/runbooks",  # 本地开发
]

DEFAULT_ENABLED_RUNBOOK_IDS = [
    "pod-evicted",
    "pod-volume-mount-failed",
    "pod-pending-unschedulable",
    "pod-node-lost-unknown",
    "pod-terminating-stuck",
    "pod-oomkilled",
    "pod-crashloop-runtime",
    "pod-imagepull-failed",
    "pod-sandbox-create-failed",
    "pod-config-error",
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
    传入 runbook_id（如 'pod-imagepull-failed.md'），
    返回完整的诊断手册内容 + 执行指令。
    """

    name: str = "fetch_runbook"
    description: str = (
        "获取 Runbook 诊断手册。传入 runbook_id（如 'pod-imagepull-failed.md'）。"
        "返回手册内容后，你必须按照手册中的步骤使用工具执行诊断。"
    )
    runbook_dirs: list = Field(default_factory=lambda: list(DEFAULT_RUNBOOK_DIRS))
    allowed_runbook_ids: list = Field(default_factory=lambda: list(DEFAULT_ENABLED_RUNBOOK_IDS))

    def _run(self, runbook_id: str) -> str:
        """同步执行：读取本地 .md 文件"""
        safe_id = os.path.basename(runbook_id)
        normalized_id = safe_id[:-3] if safe_id.endswith(".md") else safe_id
        logger.debug("[fetch_runbook] 查找: %s", safe_id)

        if self.allowed_runbook_ids and normalized_id not in set(self.allowed_runbook_ids):
            logger.warning("[fetch_runbook] 已禁用: %s", safe_id)
            return f"Error: Runbook '{safe_id}' is disabled by the current runtime profile"

        for d in self.runbook_dirs:
            path = os.path.join(d, safe_id)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info("[fetch_runbook] 找到: %s (%d 字符)", path, len(content))

                suffix = (
                    "Note: the above runbook is for diagnostic reference and repair planning. "
                    "Follow diagnostic steps to gather current evidence using tools. "
                    "Do not execute remediation commands during evidence collection. "
                    "If evidence confirms a repairable branch, use the remediation guidance "
                    "to propose structured remediation actions for the workflow executor."
                )

                return f"<runbook>\n{content}\n</runbook>\n{suffix}"

        searched = ", ".join(self.runbook_dirs)
        logger.warning("[fetch_runbook] 未找到: %s (搜索路径: %s)", safe_id, searched)
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
        "view=compact 可按 json_pointer 读取 JSON 子树，start/limit 分页；"
        "search 为记录/文本行的字面关键词搜索，fields 支持字段名（name）或相对 JSON pointer（/containers/0/name）。"
        "查找已知对象/字段时可用 compact+search/fields，避免顺序遍历无关记录；"
        "search 扫描所选子树从 start 开始的记录，查全子树时 start=0。"
        "返回 view_complete 和 next_start；索引未展示的数据不代表不存在。"
        "view_complete=true 且 integrity=lossless_received_response 表示结构压紧但无遗漏，可直接使用已展示证据。"
        "lossless_selected_subtree 只表示 json_pointer 所选子树完整，不代表整份响应或上游数据完整。"
        "仅允许读取 context archive 根目录下的文件。"
    )
    allowed_roots: list = Field(default_factory=_default_archive_roots)
    default_length: int = 12000
    max_length: int = 40000
    evidence_budget_tokens: Optional[int] = Field(
        default_factory=lambda: EvidencePolicy.from_env().result_tokens
    )

    def _run(
        self,
        archive_path: str,
        offset: int = 0,
        length: Optional[int] = None,
        view: Literal["raw", "compact"] = "raw",
        json_pointer: str = "",
        start: int = 0,
        limit: int = 50,
        search: str = "",
        fields: Optional[list[str]] = None,
        max_tokens: int = 4096,
    ) -> str:
        requested = (archive_path or "").strip()
        if not requested:
            return "Error: archive_path is required"

        target = Path(requested).expanduser()
        try:
            resolved = target.resolve(strict=False)
        except Exception:
            logger.debug("_run: falling back after error", exc_info=True)
            resolved = target

        allowed = []
        for root in self.allowed_roots:
            text = str(root).strip()
            if not text:
                continue
            try:
                allowed.append(Path(text).expanduser().resolve(strict=False))
            except Exception:
                logger.debug("_run: falling back after error", exc_info=True)
                continue

        if not any(self._is_relative_to(resolved, root) for root in allowed):
            allowed_text = ", ".join(str(p) for p in allowed)
            logger.warning("[read_context_archive] 非法路径: %s", requested)
            runbook_id = Path(str(requested)).name
            if runbook_id.endswith(".md"):
                # Live: the model asked this tool for a runbook; point it at the right one.
                return (
                    f"Error: '{requested}' 不是归档路径。Runbook 请用 fetch_runbook(runbook_id="
                    f"'{runbook_id[:-3]}') 读取；本工具只读取 raw_ref/summary_ref 等归档文件。"
                )
            return f"Error: archive_path '{requested}' is not under allowed archive roots: [{allowed_text}]"

        if not resolved.is_file():
            logger.warning("[read_context_archive] 文件不存在: %s", resolved)
            return f"Error: archive file not found: {resolved}"

        try:
            content = resolved.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("[read_context_archive] 读取失败: %s | %s", resolved, exc)
            return f"Error: failed to read archive file '{resolved}': {exc}"

        if view == "compact" or json_pointer or search or fields:
            from app.core.context.evidence_view import build_evidence_view, compact_json

            result = build_evidence_view(
                content,
                str(resolved),
                max_tokens=min(max_tokens, self.evidence_budget_tokens or 16384),
                json_pointer=json_pointer,
                start=start,
                limit=limit,
                search=search,
                fields=fields,
            )
            if result.get("status") in {
                "invalid_pointer",
                "invalid_selector",
                "view_budget_too_small",
            }:
                # Same failure protocol as path/IO errors below, so the loop and
                # UI do not report an invalid archive lookup as successful data.
                return "Error: archive view: " + compact_json(result)
            return compact_json(result)

        safe_offset = max(0, int(offset or 0))
        requested_length = self.default_length if length is None else int(length)
        safe_length = max(200, min(requested_length, self.max_length))
        snippet = content[safe_offset : safe_offset + safe_length]
        if self.evidence_budget_tokens is not None:
            # Explicit raw reads remain available, but cannot refill the context
            # with a 40k-character payload. Return the exact next byte-free char
            # cursor; no re-summarization of already selected archive evidence.
            allowance = max(
                128, self.evidence_budget_tokens - estimate_tokens(str(resolved)) - 200
            )
            low, high = 0, len(snippet)
            while low < high:
                mid = (low + high + 1) // 2
                if estimate_tokens(snippet[:mid]) <= allowance:
                    low = mid
                else:
                    high = mid - 1
            snippet = snippet[:low]
        truncated = safe_offset + len(snippet) < len(content)
        logger.info(
            "[read_context_archive] 读取: %s | offset=%d length=%d total=%d truncated=%s",
            resolved,
            safe_offset,
            safe_length,
            len(content),
            truncated,
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

    async def _arun(
        self,
        archive_path: str,
        offset: int = 0,
        length: Optional[int] = None,
        view: Literal["raw", "compact"] = "raw",
        json_pointer: str = "",
        start: int = 0,
        limit: int = 50,
        search: str = "",
        fields: Optional[list[str]] = None,
        max_tokens: int = 4096,
    ) -> str:
        return self._run(
            archive_path=archive_path,
            offset=offset,
            length=length,
            view=view,
            json_pointer=json_pointer,
            start=start,
            limit=limit,
            search=search,
            fields=fields,
            max_tokens=max_tokens,
        )

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False


class LegacyReadContextArchiveTool(ReadContextArchiveTool):
    """Keep the old tool schema/description intact while the trial is disabled."""

    evidence_budget_tokens: Optional[int] = None

    description: str = (
        "读取 context archive 里的已落盘文件。"
        "传入 archive_path（例如 raw_ref/summary_ref/archive_ref/handoff_ref/input_ref/output_ref 指向的绝对路径），"
        "可选 offset 和 length 用于分段读取大文件。"
        "仅允许读取 context archive 根目录下的文件。"
    )

    def _run(self, archive_path: str, offset: int = 0, length: Optional[int] = None) -> str:
        return super()._run(archive_path=archive_path, offset=offset, length=length, view="raw")

    async def _arun(self, archive_path: str, offset: int = 0, length: Optional[int] = None) -> str:
        return self._run(archive_path=archive_path, offset=offset, length=length)


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
        (
            ReadContextArchiveTool()
            if os.getenv("AIOPS_EVIDENCE_VIEW_MODE", "legacy").lower() == "compact"
            else LegacyReadContextArchiveTool()
        ),
    ]
    # 标记为内置工具，方便 _log_loaded_resources 分组显示
    for t in tools:
        t._is_builtin = True
    logger.info("[内置工具] 加载 %d 个: %s", len(tools), ", ".join(t.name for t in tools))
    return tools
