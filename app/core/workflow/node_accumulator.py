"""
节点级事件积累器

包装 HolmesGPT 的 call_stream，捕获 agent loop 中所有工具结果和 AI 消息，
确保节点级别的数据完整性，不受 LLM 上下文窗口压缩/截断影响。

设计原则：
- 在 Python 内存中积累，不受 LLM token 限制
- 工具结果保留完整原始数据（不截断）
- 自动选择最佳 AI 内容作为 LLM 总结候选
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from holmes.utils.stream import StreamEvents

logger = logging.getLogger(__name__)

DSML_MARKERS = ("<｜DSML｜", "<|DSML|")


def _is_dsml(text: str) -> bool:
    return any(m in text for m in DSML_MARKERS) if text else False


@dataclass
class ToolData:
    """单次工具调用的完整结果"""
    tool_name: str
    description: str
    result_data: str
    status: str
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "tool_name": self.tool_name,
            "description": self.description,
            "result_data": self.result_data,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class AccumulatedResult:
    """一个节点内 HolmesGPT loop 的全部积累输出"""
    tool_results: List[ToolData] = field(default_factory=list)
    ai_messages: List[str] = field(default_factory=list)
    answer_end_content: str = ""
    best_ai_content: str = ""
    full_content: str = ""
    iteration_count: int = 0


class NodeEventAccumulator:
    """
    节点级事件积累器

    用法::

        acc = NodeEventAccumulator()
        result = acc.run(ai, system_prompt=..., user_prompt=..., msgs=...)
        # result.tool_results  -> 所有工具数据（完整）
        # result.best_ai_content -> 最详细的 AI 分析
        # result.answer_end_content -> 框架最终输出
    """

    def run(
        self,
        ai: Any,
        system_prompt: str = "",
        user_prompt: Optional[str] = None,
        msgs: Optional[list] = None,
    ) -> AccumulatedResult:
        result = AccumulatedResult()

        current_tool_name: Optional[str] = None
        current_tool_start: Optional[float] = None

        try:
            for stream_event in ai.call_stream(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                msgs=msgs,
            ):
                et = stream_event.event
                ed = stream_event.data or {}

                if et == StreamEvents.START_TOOL:
                    current_tool_name = ed.get("tool_name", "unknown")
                    current_tool_start = time.time()

                elif et == StreamEvents.TOOL_RESULT:
                    tool_name = (
                        ed.get("name")
                        or ed.get("tool_name")
                        or current_tool_name
                        or "unknown"
                    )
                    description = ed.get("description", "")
                    raw_result = ed.get("result", {})

                    if isinstance(raw_result, dict):
                        result_str = raw_result.get("data") or str(raw_result)
                        status = raw_result.get("status", "success")
                    else:
                        result_str = str(raw_result)
                        status = "success"

                    duration = None
                    if current_tool_start is not None:
                        duration = round(time.time() - current_tool_start, 3)

                    result.tool_results.append(ToolData(
                        tool_name=tool_name,
                        description=description,
                        result_data=result_str or "",
                        status=str(status),
                        duration_seconds=duration,
                    ))

                    current_tool_name = None
                    current_tool_start = None

                elif et == StreamEvents.AI_MESSAGE:
                    content = ed.get("content", "") or ""
                    if content and not _is_dsml(content):
                        result.ai_messages.append(content)
                        if len(content) > len(result.best_ai_content):
                            result.best_ai_content = content

                elif et == StreamEvents.TOKEN_COUNT:
                    result.iteration_count += 1

                elif et == StreamEvents.ANSWER_END:
                    result.answer_end_content = ed.get("content", "") or ""
                    break

        except Exception as e:
            logger.error("NodeEventAccumulator.run 出错: %s", e, exc_info=True)

        all_parts = list(result.ai_messages)
        if result.answer_end_content and not _is_dsml(result.answer_end_content):
            all_parts.append(result.answer_end_content)
        result.full_content = "\n\n".join(all_parts)

        if not result.best_ai_content and result.answer_end_content:
            result.best_ai_content = result.answer_end_content

        logger.info(
            "📦 积累器完成: %d 次工具调用, %d 条 AI 消息, best_ai=%d 字符, answer_end=%d 字符",
            len(result.tool_results),
            len(result.ai_messages),
            len(result.best_ai_content),
            len(result.answer_end_content),
        )

        return result
