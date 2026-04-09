#!/usr/bin/env python3
"""
Holmes AI call wrapper - collect stream events into a response object.
"""

import logging
import queue
import time
from typing import Any, Dict, List, Optional

from holmes.utils.stream import StreamEvents

logger = logging.getLogger(__name__)


class StreamResponse:
    """Compatible with ai.call() return object."""

    def __init__(self, result: str, tool_calls: List[Dict],
                 iterations: int = 0, tool_call_count: int = 0,
                 duration_ms: float = 0.0, intermediate_events: Optional[List[Dict]] = None):
        self.result = result
        self.tool_calls = tool_calls
        self.iterations = iterations
        self.tool_call_count = tool_call_count
        self.duration_ms = duration_ms
        self.intermediate_events = intermediate_events or []


def call_with_stream(ai: Any, messages: list, logger_override=None) -> Any:
    """
    Call AI with streaming, collect all events, return final response.

    Returns object with:
    - result: str
    - tool_calls: list[dict]
    """
    log = logger_override or logger

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
    intermediate_events: List[Dict] = []

    # Detailed timing
    call_start = time.time()
    iteration_count = 0
    tool_call_count = 0
    current_tool_start = None
    current_tool_name = None

    log.info(
        "[call_wrapper] LLM call start | system_prompt=%d chars | user_prompt=%d chars | extra_msgs=%d",
        len(system_prompt), len(user_prompt or ""), len(msgs)
    )

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
                    intermediate_events.append({
                        "type": "ai_message",
                        "content": content[:500],
                        "iteration": iteration_count + 1,
                        "ts_ms": int(time.time() * 1000),
                    })

            elif stream_event.event == StreamEvents.START_TOOL:
                current_tool_start = time.time()
                current_tool_name = stream_event.data.get("tool_name", "unknown")
                tool_call_count += 1
                log.info(
                    "[call_wrapper]   tool_start #%d: %s (%.1fs elapsed)",
                    tool_call_count, current_tool_name, time.time() - call_start
                )
                intermediate_events.append({
                    "type": "tool_start",
                    "tool_name": current_tool_name,
                    "iteration": iteration_count + 1,
                    "ts_ms": int(time.time() * 1000),
                })

            elif stream_event.event == StreamEvents.TOOL_RESULT:
                tool_data = stream_event.data
                tool_duration = time.time() - current_tool_start if current_tool_start else 0
                tool_name = (tool_data.get("name") or tool_data.get("tool_name")
                             or current_tool_name or "unknown") if tool_data else "unknown"
                current_tool_start = None

                if tool_data:
                    result_dict = tool_data.get("result", {})

                    if isinstance(result_dict, dict):
                        result_str = result_dict.get("data") or str(result_dict)
                        error_str = result_dict.get("error")
                    else:
                        result_str = str(result_dict)
                        error_str = None

                    # 增强日志：输出工具结果预览
                    result_len = len(str(result_str)) if result_str else 0
                    status_icon = "❌" if error_str else "✅"
                    preview_len = 2000 if log.isEnabledFor(logging.DEBUG) else 500
                    preview = (str(result_str)[:preview_len] if result_str else "(empty)").replace("\n", "\\n")
                    log.info(
                        "[call_wrapper]   %s tool_done #%d: %s | %.1fs | len=%d | preview=%s",
                        status_icon, tool_call_count, tool_name, tool_duration, result_len, preview
                    )
                    if error_str:
                        log.warning(
                            "[call_wrapper]   ❌ tool_error #%d: %s | error=%s",
                            tool_call_count, tool_name, str(error_str)[:500]
                        )

                    final_tool_calls.append(
                        {
                            "tool_name": tool_name,
                            "result": str(result_str) if result_str else None,
                            "error": str(error_str) if error_str else None,
                        }
                    )

                    intermediate_events.append({
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "status": "error" if error_str else "success",
                        "result_preview": (str(result_str)[:200] if result_str else ""),
                        "result": str(result_str) if result_str else "",
                        "duration_seconds": round(tool_duration, 2),
                        "iteration": iteration_count + 1,
                        "ts_ms": int(time.time() * 1000),
                    })

            elif stream_event.event == StreamEvents.TOKEN_COUNT:
                iteration_count += 1
                elapsed = time.time() - call_start
                metadata = stream_event.data.get("metadata", {}) or {}
                usage = metadata.get("usage", {}) or {}
                tokens = usage.get("total_tokens", 0)
                log.info(
                    "[call_wrapper]   iteration #%d done | tokens=%d | %.1fs elapsed",
                    iteration_count, tokens, elapsed
                )
                intermediate_events.append({
                    "type": "iteration_end",
                    "iteration": iteration_count,
                    "elapsed_seconds": round(elapsed, 2),
                    "ts_ms": int(time.time() * 1000),
                })

            elif stream_event.event == StreamEvents.ANSWER_END:
                final_result = "".join(all_content)
                break

        if final_result is None:
            final_result = "".join(all_content)

        total_elapsed = time.time() - call_start
        log.info(
            "[call_wrapper] done | total=%.1fs | iterations=%d | tool_calls=%d | result=%d chars",
            total_elapsed, iteration_count, tool_call_count, len(final_result)
        )

        return StreamResponse(final_result, final_tool_calls,
                              iterations=iteration_count,
                              tool_call_count=tool_call_count,
                              duration_ms=total_elapsed * 1000,
                              intermediate_events=intermediate_events)

    except Exception as e:
        total_elapsed = time.time() - call_start
        log.error("[call_wrapper] failed (%.1fs): %s", total_elapsed, e, exc_info=True)
        log.warning("fallback to non-streaming call")
        return ai.call(messages)


def call_with_stream_and_queue(
    ai: Any,
    messages: list,
    event_queue: queue.Queue,
    node_id: str,
    logger_override=None,
) -> Any:
    """
    Call AI with streaming, collect events, and simultaneously push each
    intermediate_event to *event_queue* for real-time consumption.

    The queue receives tuples: ("thinking", {event_dict with node=node_id})

    Returns the same StreamResponse as call_with_stream.
    """
    log = logger_override or logger

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
    intermediate_events: List[Dict] = []

    call_start = time.time()
    iteration_count = 0
    tool_call_count = 0
    current_tool_start = None
    current_tool_name = None

    log.info(
        "[call_wrapper+queue] LLM call start | node=%s | system_prompt=%d chars | user_prompt=%d chars",
        node_id, len(system_prompt), len(user_prompt or "")
    )

    def _push(event: Dict):
        """Push event to queue with node tag."""
        tagged = {**event, "node": node_id}
        intermediate_events.append(tagged)
        try:
            event_queue.put_nowait(("thinking", tagged))
        except Exception:
            pass  # queue full — drop silently

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
                    _push({
                        "type": "ai_message",
                        "content": content[:500],
                        "iteration": iteration_count + 1,
                        "ts_ms": int(time.time() * 1000),
                    })

            elif stream_event.event == StreamEvents.START_TOOL:
                current_tool_start = time.time()
                current_tool_name = stream_event.data.get("tool_name", "unknown")
                tool_call_count += 1
                log.info(
                    "[call_wrapper+queue]   tool_start #%d: %s (%.1fs elapsed)",
                    tool_call_count, current_tool_name, time.time() - call_start
                )
                _push({
                    "type": "tool_start",
                    "tool_name": current_tool_name,
                    "iteration": iteration_count + 1,
                    "ts_ms": int(time.time() * 1000),
                })

            elif stream_event.event == StreamEvents.TOOL_RESULT:
                tool_data = stream_event.data
                tool_duration = time.time() - current_tool_start if current_tool_start else 0
                tool_name = (tool_data.get("name") or tool_data.get("tool_name")
                             or current_tool_name or "unknown") if tool_data else "unknown"

                current_tool_start = None

                if tool_data:
                    result_dict = tool_data.get("result", {})
                    if isinstance(result_dict, dict):
                        result_str = result_dict.get("data") or str(result_dict)
                        error_str = result_dict.get("error")
                    else:
                        result_str = str(result_dict)
                        error_str = None

                    # 增强日志：输出工具结果预览（INFO 级别 500 字符，DEBUG 级别 2000 字符）
                    result_len = len(str(result_str)) if result_str else 0
                    status_icon = "❌" if error_str else "✅"
                    preview_len = 2000 if log.isEnabledFor(logging.DEBUG) else 500
                    preview = (str(result_str)[:preview_len] if result_str else "(empty)").replace("\n", "\\n")
                    log.info(
                        "[call_wrapper+queue]   %s tool_done #%d: %s | %.1fs | len=%d | preview=%s",
                        status_icon, tool_call_count, tool_name, tool_duration, result_len, preview
                    )
                    if error_str:
                        log.warning(
                            "[call_wrapper+queue]   ❌ tool_error #%d: %s | error=%s",
                            tool_call_count, tool_name, str(error_str)[:500]
                        )

                    final_tool_calls.append({
                        "tool_name": tool_name,
                        "result": str(result_str) if result_str else None,
                        "error": str(error_str) if error_str else None,
                    })

                    _push({
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "status": "error" if error_str else "success",
                        "result_preview": (str(result_str)[:200] if result_str else ""),
                        "result": str(result_str) if result_str else "",
                        "duration_seconds": round(tool_duration, 2),
                        "iteration": iteration_count + 1,
                        "ts_ms": int(time.time() * 1000),
                    })

            elif stream_event.event == StreamEvents.TOKEN_COUNT:
                iteration_count += 1
                elapsed = time.time() - call_start
                _push({
                    "type": "iteration_end",
                    "iteration": iteration_count,
                    "elapsed_seconds": round(elapsed, 2),
                    "ts_ms": int(time.time() * 1000),
                })

            elif stream_event.event == StreamEvents.ANSWER_END:
                final_result = "".join(all_content)
                break

        if final_result is None:
            final_result = "".join(all_content)

        total_elapsed = time.time() - call_start
        log.info(
            "[call_wrapper+queue] done | node=%s | total=%.1fs | iterations=%d | tool_calls=%d",
            node_id, total_elapsed, iteration_count, tool_call_count
        )

        return StreamResponse(final_result, final_tool_calls,
                              iterations=iteration_count,
                              tool_call_count=tool_call_count,
                              duration_ms=total_elapsed * 1000,
                              intermediate_events=intermediate_events)

    except Exception as e:
        total_elapsed = time.time() - call_start
        log.error("[call_wrapper+queue] failed (%.1fs): %s", total_elapsed, e, exc_info=True)
        log.warning("fallback to non-streaming call")
        return ai.call(messages)
