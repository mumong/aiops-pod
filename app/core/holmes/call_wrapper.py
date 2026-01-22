#!/usr/bin/env python3
"""
Holmes AI 调用包装（从 HolmesService 中抽离）

目标：
- HolmesService 只保留编排逻辑
- 这层只负责把 ai.call_stream 的事件收集成一个“类似 response”的对象
"""

import logging
from typing import Any, Dict, List, Optional

from holmes.utils.stream import StreamEvents

logger = logging.getLogger(__name__)


class StreamResponse:
    """与 ai.call() 返回对象形态兼容的轻量响应"""

    def __init__(self, result: str, tool_calls: List[Dict]):
        self.result = result
        self.tool_calls = tool_calls


def call_with_stream(ai: Any, messages: list, logger_override=None) -> Any:
    """
    使用流式输出调用 AI，收集所有事件后返回最终响应

    返回对象具备：
    - result: str
    - tool_calls: list[dict]
    """
    log = logger_override or logger

    # 从 messages 中提取 system_prompt 和 user_prompt
    system_prompt = ""
    user_prompt = None
    msgs = []

    for msg in messages:
        if msg.get("role") == "system":
            system_prompt = msg.get("content", "")
        elif msg.get("role") == "user":
            if user_prompt is None:
                user_prompt = msg.get("content", "")
            else:
                msgs.append(msg)
        else:
            msgs.append(msg)

    final_result: Optional[str] = None
    final_tool_calls: List[Dict] = []
    all_content: List[str] = []

    try:
        for stream_event in ai.call_stream(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            msgs=msgs if msgs else None,
        ):
            if stream_event.event == StreamEvents.AI_MESSAGE:
                content = stream_event.data.get("content", "")
                if content:
                    all_content.append(content)

            elif stream_event.event == StreamEvents.TOOL_RESULT:
                tool_data = stream_event.data
                if tool_data:
                    tool_name = tool_data.get("name") or tool_data.get("tool_name") or "unknown"
                    result_dict = tool_data.get("result", {})

                    if isinstance(result_dict, dict):
                        result_str = result_dict.get("data") or str(result_dict)
                        error_str = result_dict.get("error")
                    else:
                        result_str = str(result_dict)
                        error_str = None

                    final_tool_calls.append(
                        {
                            "tool_name": tool_name,
                            "result": str(result_str) if result_str else None,
                            "error": str(error_str) if error_str else None,
                        }
                    )

            elif stream_event.event == StreamEvents.ANSWER_END:
                final_result = "".join(all_content)
                break

        if final_result is None:
            final_result = "".join(all_content)

        return StreamResponse(final_result, final_tool_calls)

    except Exception as e:
        log.error(f"流式输出处理失败: {e}", exc_info=True)
        log.warning("回退到非流式输出")
        return ai.call(messages)


