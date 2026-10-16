"""单集群诊断/查询入口：/ask、/query、/q/{question} 以及修复审批。

GET（Query 参数）与 POST（Form 表单）保留各自的参数声明，
请求处理统一走 ``_handle_session_query``。
"""

import re
import secrets
import threading
from typing import Generator, Optional

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from starlette.concurrency import run_in_threadpool

from app.api.common import current_service, fix_double_encoding, logger, streaming_response

router = APIRouter()

SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]+$"
DIAGNOSIS_TITLE = "工作流诊断模式"
QUERY_TITLE = "工作流查询模式"


# =========================================================================
# 内部辅助函数
# =========================================================================


def _diagnosis_workflow_overrides() -> dict:
    return {
        "query_mode": "auto",
        "nodes": {"layer": True, "evidence": True, "rca": True, "conclusion": True},
    }


def _query_workflow_overrides() -> dict:
    return {"query_mode": "auto"}


def _query_session_owner(request, session_id, overrides):
    # Explicit UI context is a record identifier, never an archive file path.
    diagnosis_id = request.query_params.get("diagnosis_run_id")
    plan_id = request.query_params.get("plan_run_id")
    if diagnosis_id and plan_id:
        raise HTTPException(status_code=400, detail="诊断引用与方案修改引用不能同时指定")
    for reference in (diagnosis_id, plan_id):
        if reference and not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", reference):
            raise HTTPException(status_code=400, detail="无效的修复来源记录标识")
    if (diagnosis_id or plan_id) and not session_id:
        raise HTTPException(status_code=400, detail="修复记录引用需要 session_id")
    overrides["_diagnosis_run_id"] = diagnosis_id
    overrides["_plan_run_id"] = plan_id
    if not session_id:
        return None
    owner = request.cookies.get("aiops_query_owner", "")
    if not re.fullmatch(r"[0-9a-f]{64}", owner):
        owner = secrets.token_hex(32)
    overrides["_query_session_key"] = (owner, session_id)
    return owner


def _query_session_cookie(request, response, owner):
    if owner:
        response.set_cookie(
            "aiops_query_owner",
            owner,
            httponly=True,
            samesite="strict",
            secure=request.url.scheme == "https",
            max_age=86400,
            path="/",
        )
    return response


def _stream_response(
    question: str,
    output_format: str,
    max_steps: int,
    workflow_overrides: Optional[dict] = None,
    workflow_title: str = DIAGNOSIS_TITLE,
):
    """生成流式响应（支持客户端断开时取消后台工作流）"""
    cancel_event = threading.Event()

    def generate() -> Generator[str, None, None]:
        try:
            service = current_service()
            yield from service.execute_query_stream(
                question=question,
                max_steps=max_steps,
                output_format=output_format,
                cancel_event=cancel_event,
                workflow_overrides=workflow_overrides,
                workflow_title=workflow_title,
            )
        except GeneratorExit:
            # 客户端断开连接（curl Ctrl+C）
            logger.info("客户端断开连接，触发取消信号")
            cancel_event.set()
        except Exception as e:
            logger.error("流式查询出错: %s", e, exc_info=True)
            yield f"\n❌ 错误: {str(e)}\n"
        finally:
            # 确保取消信号被设置（无论正常结束还是异常）
            cancel_event.set()

    media_type = "text/event-stream" if output_format == "sse" else "text/plain; charset=utf-8"
    return streaming_response(generate(), media_type=media_type, cancel_event=cancel_event)


async def _sync_response(
    question: str,
    max_steps: int,
    workflow_overrides: Optional[dict] = None,
    workflow_title: str = DIAGNOSIS_TITLE,
):
    """生成同步响应"""
    try:
        service = current_service()
        # execute_query is synchronous and runs for minutes; off the event loop, or
        # /health, SSE heartbeats and every other request hang until it returns.
        result = await run_in_threadpool(
            service.execute_query,
            question=question,
            max_steps=max_steps,
            workflow_overrides=workflow_overrides,
            workflow_title=workflow_title,
        )

        if result.get("success"):
            return PlainTextResponse(
                content=result.get("result", ""), media_type="text/plain; charset=utf-8"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("查询出错: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _respond(question, stream, output_format, max_steps, overrides, title):
    if stream:
        return _stream_response(question, output_format, max_steps, overrides, title)
    return await _sync_response(question, max_steps, overrides, title)


async def _handle_session_query(
    request, q, stream, output_format, max_steps, session_id, overrides, title, log_message
):
    """/ask 与 /query 的 GET/POST 共用实现。"""
    question = fix_double_encoding(q)  # FastAPI 的 Query 已自动解码
    logger.info(log_message, question[:80])
    owner = _query_session_owner(request, session_id, overrides)
    response = await _respond(question, stream, output_format, max_steps, overrides, title)
    return _query_session_cookie(request, response, owner)


# =========================================================================
# 核心 API：/ask - 诊断入口
# =========================================================================


@router.get("/ask")
async def ask_get(
    request: Request,
    q: str = Query(..., description="问题内容", example="Pod一直重启怎么办"),
    stream: bool = Query(True, description="是否流式输出"),
    format: str = Query("text", description="输出格式: text(默认) 或 sse"),
    max_steps: int = Query(20, description="最大执行步数", ge=1, le=100),
    remediate: Optional[bool] = Query(
        None, description="已废弃；修复流程由 workflow.remediation 配置控制"
    ),
    session_id: Optional[str] = Query(
        None, min_length=16, max_length=128, pattern=SESSION_ID_PATTERN
    ),
):
    """
    🔍 智能运维查询（GET 方式）

    最简单的使用方式，直接在 URL 中传入问题：

    ```bash
    # 基本用法
    curl "http://localhost:8000/ask?q=Pod一直重启"

    # 流式输出（默认开启）
    curl -N "http://localhost:8000/ask?q=磁盘满了怎么清理"

    # 非流式输出
    curl "http://localhost:8000/ask?q=查看集群状态&stream=false"
    ```
    """
    return await _handle_session_query(
        request,
        q,
        stream,
        format,
        max_steps,
        session_id,
        _diagnosis_workflow_overrides(),
        DIAGNOSIS_TITLE,
        "收到查询: %s...",
    )


@router.post("/ask")
async def ask_post(
    request: Request,
    q: str = Form(..., description="问题内容"),
    stream: bool = Form(True, description="是否流式输出"),
    format: str = Form("text", description="输出格式"),
    max_steps: int = Form(20, description="最大执行步数"),
    remediate: Optional[bool] = Form(
        None, description="已废弃；修复流程由 workflow.remediation 配置控制"
    ),
    session_id: Optional[str] = Form(
        None, min_length=16, max_length=128, pattern=SESSION_ID_PATTERN
    ),
):
    """
    🔍 智能运维查询（POST 表单方式）

    支持表单提交，适合复杂问题：

    ```bash
    curl -X POST "http://localhost:8000/ask" -d "q=Pod一直重启"

    curl -X POST "http://localhost:8000/ask" \\
      -d "q=查看 namespace kube-system 下所有 Pod 状态" \\
      -d "max_steps=30"
    ```
    """
    return await _handle_session_query(
        request,
        q,
        stream,
        format,
        max_steps,
        session_id,
        _diagnosis_workflow_overrides(),
        DIAGNOSIS_TITLE,
        "收到查询 (POST): %s...",
    )


# =========================================================================
# 轻量查询 API：/query - QUERY 专用入口
# =========================================================================


@router.get("/query")
async def query_get(
    request: Request,
    q: str = Query(..., description="查询内容", example="集群 CPU 和内存使用率是多少"),
    stream: bool = Query(True, description="是否流式输出"),
    format: str = Query("text", description="输出格式: text(默认) 或 sse"),
    max_steps: int = Query(20, description="最大执行步数", ge=1, le=100),
    session_id: Optional[str] = Query(
        None, min_length=16, max_length=128, pattern=SESSION_ID_PATTERN
    ),
):
    return await _handle_session_query(
        request,
        q,
        stream,
        format,
        max_steps,
        session_id,
        _query_workflow_overrides(),
        QUERY_TITLE,
        "收到轻量查询: %s...",
    )


@router.post("/query")
async def query_post(
    request: Request,
    q: str = Form(..., description="查询内容"),
    stream: bool = Form(True, description="是否流式输出"),
    format: str = Form("text", description="输出格式"),
    max_steps: int = Form(20, description="最大执行步数"),
    session_id: Optional[str] = Form(
        None, min_length=16, max_length=128, pattern=SESSION_ID_PATTERN
    ),
):
    return await _handle_session_query(
        request,
        q,
        stream,
        format,
        max_steps,
        session_id,
        _query_workflow_overrides(),
        QUERY_TITLE,
        "收到轻量查询 (POST): %s...",
    )


# =========================================================================
# 便捷别名路由
# =========================================================================


@router.get("/q/{question:path}")
async def ask_path(
    question: str,
    stream: bool = Query(True),
    format: str = Query("text"),
    max_steps: int = Query(20, ge=1, le=100),
):
    """
    🔍 路径参数方式查询

    更简洁的 URL 风格：

    ```bash
    curl "http://localhost:8000/q/Pod一直重启怎么办"
    curl -N "http://localhost:8000/q/磁盘使用率查询"
    ```

    注意：问题中的特殊字符需要 URL 编码
    """
    question = fix_double_encoding(question)  # 修复双重编码
    logger.info("收到查询 (路径): %s...", question[:80])
    # 路径别名不参与会话/修复引用：不注入 session 相关 overrides，也不下发 cookie。
    return await _respond(
        question, stream, format, max_steps, _diagnosis_workflow_overrides(), DIAGNOSIS_TITLE
    )


@router.post("/remediation/approve")
async def remediation_approve(
    request: Request,
    run_id: str = Form(..., description="诊断 run_id"),
    approval_id: str = Form(..., description="审批 ID"),
    approved: bool = Form(..., description="是否同意"),
    reviewer: str = Form("", description="审批人"),
    reason: str = Form("", description="审批原因"),
):
    from app.core.remediation.approval import approval_store

    ok = approval_store.resolve(
        run_id=run_id,
        approval_id=approval_id,
        approved=approved,
        reviewer=reviewer,
        reason=reason,
        owner=request.cookies.get("aiops_query_owner", ""),
    )
    if not ok:
        logger.warning(
            "remediation approval not found | run_id=%s approval_id=%s approved=%s reviewer=%s",
            run_id,
            approval_id,
            approved,
            reviewer,
        )
        raise HTTPException(status_code=404, detail="approval request not found")
    logger.info(
        "remediation approval resolved | run_id=%s approval_id=%s approved=%s reviewer=%s reason=%s",
        run_id,
        approval_id,
        approved,
        reviewer,
        reason,
    )
    return {
        "success": True,
        "run_id": run_id,
        "approval_id": approval_id,
        "approved": approved,
    }
