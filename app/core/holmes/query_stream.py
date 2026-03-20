#!/usr/bin/env python3
"""
Holmes 查询流式输出实现（从 HolmesService 中抽离）

目标：
- 保持输出与行为不变
- 将大段流式处理逻辑与 HolmesService 解耦，service.py 仅负责编排/状态管理
"""

import time
import logging
import uuid
from datetime import datetime
from typing import Optional, Generator, Any

from holmes.core.prompt import build_initial_ask_messages
from holmes.utils.stream import StreamEvents

from app.core.prompts import SYSTEM_PROMPT
from app.core.holmes.streaming import create_sse_message_cn, format_duration
from app.core.holmes.event_mapper import iter_internal_events
from app.core.constants import (
    DEFAULT_MAX_STEPS,
    MAX_QUESTION_DISPLAY_LENGTH,
)
from app.core.config_helpers import should_reset_config, reset_service_config
from app.core.text_helpers import truncate_question
from app.core.holmes.metrics_extractor import DiagnosisMetrics

logger = logging.getLogger(__name__)


def execute_query_stream_sse(
    service: Any,
    question: str,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    output_format: str = "sse",
) -> Generator[str, None, None]:
    """
    SSE 格式流式输出（JSON SSE events）
    新实现：基于统一内部事件协议，保证每一步可解析且一定有 final。
    """
    total_start_time = time.time()
    timing_stats = {"initialization": 0, "message_building": 0, "total": 0}
    final_content = ""

    try:
        # 初始化阶段
        init_start = time.time()

        if should_reset_config(api_key, model, max_steps):
            reset_service_config(service)

        service.initialize(api_key=api_key, model=model, max_steps=max_steps)
        timing_stats["initialization"] = time.time() - init_start

        final_system_prompt = system_prompt or SYSTEM_PROMPT

        logger.info("=" * 60)
        logger.info(f"📝 [流式查询] 问题: {truncate_question(question)}")
        logger.info(f"⏱️  初始化耗时: {format_duration(timing_stats['initialization'])}")

        yield create_sse_message_cn(
            "run_start",
            {
                "message": "🚀 开始处理查询...",
                "question": truncate_question(question),
                "phase": "initialization",
                "init_time": format_duration(timing_stats["initialization"]),
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 消息构建阶段
        msg_build_start = time.time()

        runbook_catalog = service.merged_catalog if service.merged_catalog else service.config.get_runbook_catalog()

        messages = build_initial_ask_messages(
            initial_user_prompt=question,
            file_paths=None,
            tool_executor=service.ai.tool_executor,
            runbooks=runbook_catalog,
            system_prompt_additions=final_system_prompt if final_system_prompt else None,
        )

        timing_stats["message_building"] = time.time() - msg_build_start
        logger.info(f"⏱️  消息构建耗时: {format_duration(timing_stats['message_building'])}")

        # 提取 prompts
        sys_prompt = ""
        user_prompt = None
        msgs = []

        for msg in messages:
            if msg.get("role") == "system":
                sys_prompt = msg.get("content", "")
            elif msg.get("role") == "user":
                if user_prompt is None:
                    user_prompt = msg.get("content", "")
                else:
                    msgs.append(msg)
            else:
                msgs.append(msg)

        # LLM 调用阶段
        final_content = None
        llm_iteration_start_time = time.time()

        logger.info("-" * 60)
        logger.info("🤖 开始 LLM 迭代（SSE events）...")

        run_id = uuid.uuid4().hex[:16]
        for ev in iter_internal_events(
            service=service,
            question=question,
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            msgs=msgs if msgs else None,
            run_id=run_id,
        ):
            # 保持对外为 SSE：event: <type> / data: <json>
            if ev.get("type") == "final":
                final_content = ev.get("answer") or ""
            yield create_sse_message_cn(ev["type"], ev)

        # 统计汇总
        timing_stats["total"] = time.time() - total_start_time
        logger.info(f"✅ SSE events 查询完成，总耗时: {format_duration(timing_stats['total'])}")

        # 保留兼容事件：stream_end（旧前端/脚本可能依赖）
        yield create_sse_message_cn("stream_end", {"success": True, "result": final_content, "run_id": run_id})

    except Exception as e:
        total_time = time.time() - total_start_time
        logger.error(f"❌ 执行查询时出错 (耗时 {format_duration(total_time)}): {e}", exc_info=True)
        yield create_sse_message_cn("error", {"success": False, "error": str(e)})


def execute_query_stream_text(
    service: Any,
    question: str,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> Generator[str, None, None]:
    """
    易读纯文本流式输出（专为 curl 等命令行优化）
    新实现：渲染统一内部事件协议，保证 text 与 SSE 看到的步骤一致。
    """
    total_start_time = time.time()

    def emit(text: str) -> str:
        return f"{text}\n"

    try:
        init_start = time.time()

        if should_reset_config(api_key, model, max_steps):
            reset_service_config(service)

        service.initialize(api_key=api_key, model=model, max_steps=max_steps)
        init_duration = time.time() - init_start

        final_system_prompt = system_prompt or SYSTEM_PROMPT

        yield emit("=" * 70)
        yield emit("🔍 HolmesGPT 流式查询")
        yield emit("=" * 70)
        yield emit(f"📝 问题: {truncate_question(question)}")
        yield emit(f"⏱️  初始化: {format_duration(init_duration)}")
        yield emit("-" * 70)
        yield emit("")

        msg_build_start = time.time()

        runbook_catalog = service.merged_catalog if service.merged_catalog else service.config.get_runbook_catalog()

        messages = build_initial_ask_messages(
            initial_user_prompt=question,
            file_paths=None,
            tool_executor=service.ai.tool_executor,
            runbooks=runbook_catalog,
            system_prompt_additions=final_system_prompt if final_system_prompt else None,
        )

        msg_build_duration = time.time() - msg_build_start

        sys_prompt = ""
        user_prompt = None
        msgs = []

        for msg in messages:
            if msg.get("role") == "system":
                sys_prompt = msg.get("content", "")
            elif msg.get("role") == "user":
                if user_prompt is None:
                    user_prompt = msg.get("content", "")
                else:
                    msgs.append(msg)
            else:
                msgs.append(msg)

        yield emit(f"⏱️  消息构建: {format_duration(msg_build_duration)}")
        yield emit("")
        yield emit("🤖 开始 LLM 迭代...")
        yield emit("")

        run_id = uuid.uuid4().hex[:16]
        final_answer = ""
        final_status = "unknown"
        diagnosis_metrics: Optional[DiagnosisMetrics] = None

        for ev in iter_internal_events(
            service=service,
            question=question,
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            msgs=msgs if msgs else None,
            run_id=run_id,
        ):
            t = ev.get("type")
            if t == "tool_start":
                yield emit(f"  🔧 [{ev.get('iteration')}] 调用工具: {ev.get('tool_name')}")
            elif t == "tool_result":
                status = ev.get("status") or "unknown"
                status_icon = "✅" if status == "success" else "❌"
                dur = ev.get("duration_seconds")
                dur_text = format_duration(dur) if isinstance(dur, (int, float)) else "-"
                yield emit(f"  {status_icon} [{ev.get('iteration')}] 完成: {ev.get('tool_name')} ({dur_text})")
                if ev.get("description"):
                    yield emit(f"       📋 {str(ev.get('description'))[:80]}")
                if ev.get("error"):
                    yield emit(f"       ⚠️ 错误: {str(ev.get('error'))[:120]}")
                if ev.get("result_truncated") and ev.get("artifact_id"):
                    yield emit(f"       📎 输出过长已截断，可通过 /artifacts/{ev.get('artifact_id')} 获取全文")
            elif t == "ai_message":
                yield emit(f"  💬 [{ev.get('iteration')}] AI:")
                for line in str(ev.get("content", "")).split("\n"):
                    yield emit(f"     {line}")
            elif t == "ai_reasoning":
                yield emit(f"  💭 [{ev.get('iteration')}] 推理:")
                for line in str(ev.get("reasoning", "")).split("\n"):
                    yield emit(f"     {line}")
            elif t == "iteration_end":
                usage = ev.get("usage") or {}
                tokens = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0
                elapsed = format_duration(ev.get("elapsed_seconds", 0))
                yield emit(f"  📊 [{ev.get('iteration')}] 迭代完成 | Token: {tokens} | 已用时: {elapsed}")
                yield emit("")
            elif t == "blocked":
                yield emit(f"  ⚠️ [{ev.get('iteration')}] 执行被阻塞: {ev.get('reason')}")
                pending = ev.get("pending_approvals") or []
                for item in pending[:10]:
                    yield emit(f"     - {item}")
                yield emit("")
            elif t == "error":
                yield emit(f"  ❌ [{ev.get('iteration')}] 错误: {ev.get('error')}")
                yield emit("")
            elif t == "metrics":
                # 从 metrics 事件重建 DiagnosisMetrics 用于最终输出
                m = ev.get("diagnosis_metrics", {})
                diagnosis_metrics = DiagnosisMetrics(
                    run_id=m.get("run_id", ""),
                    mttr_seconds=m.get("mttr_seconds", 0),
                    layer=m.get("layer"),
                    layer_name=m.get("layer_name", ""),
                    confidence_score=m.get("confidence_score", 0),
                    evidence_collected=m.get("evidence_collected", 0),
                    evidence_total=m.get("evidence_total", 0),
                    runbooks_referenced=m.get("runbooks_referenced", []),
                    tool_calls_count=m.get("tool_calls_count", 0),
                    is_diagnosis=m.get("is_diagnosis", False),
                )
            elif t == "final":
                final_status = ev.get("status") or "unknown"
                final_answer = ev.get("answer") or ""

        total_time = time.time() - total_start_time

        yield emit("-" * 70)
        yield emit("")
        yield emit("🎯 最终答案:")
        yield emit("-" * 50)

        if final_answer:
            for line in final_answer.split("\n"):
                yield emit(f"  {line}")
        else:
            yield emit(f"  (无可用最终内容，状态: {final_status})")

        yield emit("-" * 50)

        # 追加质量指标表（与工作流模式输出格式一致）
        if diagnosis_metrics:
            metrics_block = diagnosis_metrics.format_metrics_block()
            for line in metrics_block.split("\n"):
                yield emit(f"  {line}")

        yield emit("")
        yield emit(f"📊 总耗时: {format_duration(total_time)} | run_id: {run_id} | status: {final_status}")
        yield emit("=" * 70)
        yield emit(f"✅ 完成! 总耗时: {format_duration(total_time)}")
        yield emit("=" * 70)

    except Exception as e:
        total_time = time.time() - total_start_time
        logger.error(f"❌ 执行查询时出错: {e}", exc_info=True)
        yield emit("")
        yield emit(f"❌ 错误: {str(e)}")
        yield emit(f"⏱️  耗时: {format_duration(total_time)}")


