#!/usr/bin/env python3
"""
Holmes StreamEvents -> 统一内部事件（schema）映射层

设计要点：
- 高内聚：只负责“把 Holmes 事件转成我们的事件”
- 低耦合：上层可选择 SSE 渲染、文本渲染、WebSocket 等
- 可扩展：后续可在这里做 tool 输出裁剪、异常分类、artifact 存储等
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Generator, Optional, List

from holmes.utils.stream import StreamEvents

from app.core.holmes.artifacts import get_artifact_store
from app.core.holmes.event_schema import (
    is_dsml,
    make_event_id,
    now_ms,
    preview_text,
    select_final_answer,
)
from app.core.skills import evaluate_deterministic_decision, format_decision_markdown


def iter_internal_events(
    *,
    service: Any,
    question: str,
    system_prompt: str,
    user_prompt: Optional[str],
    msgs: Optional[list],
    run_id: str,
    max_preview_chars: int = 1200,
) -> Generator[Dict, None, None]:
    """
    产生统一内部事件 dict：
      {type, id, run_id, seq, ts_ms, ...payload }
    """

    seq = 0

    def emit(event_type: str, payload: Dict) -> Dict:
        nonlocal seq
        seq += 1
        return {
            "type": event_type,
            "id": make_event_id(run_id, event_type, seq),
            "run_id": run_id,
            "seq": seq,
            "ts_ms": now_ms(),
            **payload,
        }

    total_start = time.time()
    iteration_count = 0
    current_tool_start = None
    current_tool_name = None
    llm_iteration_start = time.time()
    saw_approval_required = False
    saw_errors = False

    last_ai_content = ""
    framework_final = ""
    internal_events: List[Dict] = []

    ev_run_start = emit(
        "run_start",
        {
            "question": question,
            "timestamp": datetime.now().isoformat(),
        },
    )
    internal_events.append(ev_run_start)
    yield ev_run_start

    for stream_event in service.ai.call_stream(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        msgs=msgs,
    ):
        et = stream_event.event
        ed = stream_event.data or {}

        if et == StreamEvents.START_TOOL:
            current_tool_start = time.time()
            current_tool_name = ed.get("tool_name", "unknown")
            ev_tool_start = emit(
                "tool_start",
                {
                    "iteration": iteration_count + 1,
                    "tool_name": current_tool_name,
                    "tool_id": ed.get("id", ""),
                },
            )
            internal_events.append(ev_tool_start)
            yield ev_tool_start

        elif et == StreamEvents.TOOL_RESULT:
            tool_name = ed.get("name") or ed.get("tool_name") or current_tool_name or "unknown"
            result_dict = ed.get("result", {})
            description = ed.get("description", "")

            duration_s = None
            if current_tool_start:
                duration_s = time.time() - current_tool_start

            status = "success"
            error_str = None
            result_str = None

            if isinstance(result_dict, dict):
                status = result_dict.get("status", status)
                error_str = result_dict.get("error")
                result_str = result_dict.get("data")
            else:
                result_str = str(result_dict)

            if error_str or status != "success":
                saw_errors = True

            # 对结果做 preview + artifact 存储（仅当我们确实拿到了全文）
            artifact_id = None
            preview, truncated = preview_text(str(result_str) if result_str is not None else None, max_chars=max_preview_chars)
            if truncated and result_str:
                artifact_id = get_artifact_store().put(str(result_str))

            ev_tool_result = emit(
                "tool_result",
                {
                    "iteration": iteration_count + 1,
                    "tool_name": tool_name,
                    "status": status,
                    "description": description,
                    "duration_seconds": round(duration_s, 3) if duration_s is not None else None,
                    "error": str(error_str) if error_str else None,
                    "result_preview": preview,
                    "result_truncated": truncated,
                    "artifact_id": artifact_id,
                },
            )
            internal_events.append(ev_tool_result)
            yield ev_tool_result

            current_tool_start = None
            current_tool_name = None

        elif et == StreamEvents.AI_MESSAGE:
            content = ed.get("content", "") or ""
            reasoning = ed.get("reasoning", "") or ""

            # 记录 last_ai_content 用于最终选择（但不让 DSML 覆盖）
            if content and not is_dsml(content):
                last_ai_content = content

            if reasoning:
                ev_reasoning = emit("ai_reasoning", {"iteration": iteration_count + 1, "reasoning": reasoning})
                internal_events.append(ev_reasoning)
                yield ev_reasoning
            if content:
                ev_msg = emit("ai_message", {"iteration": iteration_count + 1, "content": content})
                internal_events.append(ev_msg)
                yield ev_msg

        elif et == StreamEvents.TOKEN_COUNT:
            iter_duration = time.time() - llm_iteration_start if llm_iteration_start else None
            iteration_count += 1
            llm_iteration_start = time.time()

            metadata = ed.get("metadata", {}) or {}
            usage = metadata.get("usage", {}) or {}
            ev_iter_end = emit(
                "iteration_end",
                {
                    "iteration": iteration_count,
                    "duration_seconds": round(iter_duration, 3) if iter_duration is not None else None,
                    "usage": usage,
                    "elapsed_seconds": round(time.time() - total_start, 3),
                },
            )
            internal_events.append(ev_iter_end)
            yield ev_iter_end

        elif et == StreamEvents.CONVERSATION_HISTORY_COMPACTED:
            ev_hist = emit("history_compacted", {"iteration": iteration_count + 1})
            internal_events.append(ev_hist)
            yield ev_hist

        elif et == StreamEvents.APPROVAL_REQUIRED:
            saw_approval_required = True
            pending = ed.get("pending_approvals", [])
            ev_blocked = emit(
                "blocked",
                {
                    "iteration": iteration_count + 1,
                    "reason": "approval_required",
                    "pending_approvals": pending,
                },
            )
            internal_events.append(ev_blocked)
            yield ev_blocked

        elif et == StreamEvents.ERROR:
            saw_errors = True
            ev_error = emit(
                "error",
                {
                    "iteration": iteration_count + 1,
                    "error": ed.get("msg", "未知错误"),
                },
            )
            internal_events.append(ev_error)
            yield ev_error

        elif et == StreamEvents.ANSWER_END:
            framework_final = ed.get("content", "") or ""
            break

    # 生成 final（保证闭环）
    selection = select_final_answer(
        framework_content=framework_final,
        last_ai_content=last_ai_content,
        saw_approval_required=saw_approval_required,
    )

    # 若最终仍是 DSML，则判定为“被阻塞/未完成”，输出可读的 final
    final_status = "success"
    final_content = selection.content or ""
    final_reason = selection.reason

    # 软拦截：基于 tool_result 等事件做确定性规则判定，并将结果附加到最终答案
    # 注意：不阻断、不抛错；若无法判定则跳过。
    try:
        decision = evaluate_deterministic_decision(question, internal_events)
        if decision:
            # 先发一个事件，方便 SSE/调试消费
            ev_det = emit("deterministic_decision", decision.to_dict())
            internal_events.append(ev_det)
            yield ev_det

            # 将 deterministic appendix 附加到最终内容（不改变主报告内容）
            final_content = (final_content or "") + format_decision_markdown(decision)
    except Exception:
        # 软拦截必须“永远不影响主流程”
        pass

    if saw_approval_required:
        final_status = "blocked"
        if not final_content or is_dsml(final_content):
            final_content = "本次执行被策略阻塞（需要用户批准/允许的操作）。请查看 blocked 事件中的 pending_approvals，并用 format=sse 解析每一步。"

    if is_dsml(final_content):
        final_status = "incomplete"
        final_reason = "final_contains_dsml"
        final_content = "本次执行未能生成可读的最终结论（模型停留在工具调用草稿/DSML）。请回看 tool_result/error/blocked 事件定位失败点。"

    ev_final = emit(
        "final",
        {
            "status": final_status,
            "answer": final_content,
            "answer_source": selection.source,
            "answer_reason": final_reason,
            "had_errors": saw_errors,
            "elapsed_seconds": round(time.time() - total_start, 3),
        },
    )
    internal_events.append(ev_final)
    yield ev_final

    ev_end = emit("run_end", {"elapsed_seconds": round(time.time() - total_start, 3)})
    internal_events.append(ev_end)
    yield ev_end


