#!/usr/bin/env python3
"""
统一的输出事件协议（高内聚、与 holmesgpt 事件解耦）

目标：
- SSE/文本输出都基于同一套“内部事件”
- 任何情况下都能产出 final（成功/失败/阻塞），避免 DSML 片段被当成最终答案
- 对超大输出做 preview + 可选 artifact_id（后续可扩展为持久化）
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


REPORT_MARKERS = ("## 📍 问题定位", "## 🕵️ 证据链", "## 🎯 根因结论", "## 🛠️ 修复建议")


def is_dsml(text: str) -> bool:
    if not text:
        return False
    return "<｜DSML｜" in text or "<|DSML|" in text


def is_structured_report(text: str) -> bool:
    if not text:
        return False
    return all(m in text for m in REPORT_MARKERS)


def preview_text(text: Optional[str], *, max_chars: int) -> Tuple[Optional[str], bool]:
    if text is None:
        return None, False
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def make_event_id(run_id: str, kind: str, seq: int) -> str:
    raw = f"{run_id}:{kind}:{seq}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:12]


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class FinalSelection:
    """对“最终答案来源”的选择结果"""

    content: str
    source: str  # "framework" | "last_ai"
    reason: str


def select_final_answer(
    *,
    framework_content: str,
    last_ai_content: str,
    saw_approval_required: bool,
) -> FinalSelection:
    """
    选择最终输出：
    - 仍以 framework ANSWER_END 为准
    - 但当 framework 是“短总结”，last_ai 是“完整结构化报告”时，优先 last_ai
    - 遇到 approval/DSML 时，不把工具调用草稿当最终答案
    """

    framework = framework_content or ""
    last_ai = last_ai_content or ""

    if saw_approval_required:
        # 被阻塞时，最终答案交给上层去构造“阻塞说明”，避免输出工具调用片段
        return FinalSelection(content=framework, source="framework", reason="approval_required")

    if is_dsml(framework) and not is_dsml(last_ai) and last_ai:
        return FinalSelection(content=last_ai, source="last_ai", reason="framework_contains_dsml")

    last_is_report = is_structured_report(last_ai)
    framework_is_report = is_structured_report(framework)

    if last_is_report and not framework_is_report and not is_dsml(last_ai):
        return FinalSelection(content=last_ai, source="last_ai", reason="prefer_structured_report_from_last_ai")

    if len(framework) < 200 and last_ai and not is_dsml(last_ai):
        return FinalSelection(content=last_ai, source="last_ai", reason="framework_too_short")

    return FinalSelection(content=framework, source="framework", reason="default_framework")


