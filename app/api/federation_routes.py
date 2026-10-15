"""多集群联邦入口：/federation/{ask,query}（广播聚合）与 /federation/{ask,query}/v2（Agent-to-Agent）。

GET（Query 参数）与 POST（Form 表单）保留各自的参数声明，
响应统一由 ``_federation_stream_response`` / ``_federation_agent_stream_response`` 生成。
"""

from typing import Generator

from fastapi import APIRouter, Form, Query

from app.api.common import current_service, fix_double_encoding, logger, streaming_response

router = APIRouter()


def _disabled_message(prefix: str, endpoint_path: str) -> str:
    single_cluster_endpoint = "/query" if endpoint_path == "/query" else "/ask"
    return (
        f"❌ {prefix}未启用。\n\n"
        "请在主集群 config.yaml 中设置 federation.enabled: true 并配置子集群列表。\n"
        f"若要查询单集群，请使用 {single_cluster_endpoint} 端点。\n"
    )


def _federation_stream_response(
    question: str,
    max_steps: int,
    conclusion_max_tokens: int,
    endpoint_path: str = "/ask",
):
    """生成联邦查询流式响应"""

    def generate() -> Generator[str, None, None]:
        try:
            service = current_service()
            coordinator = service.federation_coordinator
            if coordinator is None:
                yield _disabled_message("联邦查询", endpoint_path)
                return
            logger.info(
                "[FEDERATION] 开始联邦查询, 子集群数量: %s, 端点: %s, 问题: %s...",
                len(coordinator._registry.get_enabled_agents()),
                endpoint_path,
                question[:60],
            )
            yield from coordinator.ask_stream(
                question=question,
                max_steps=max_steps,
                conclusion_max_tokens=conclusion_max_tokens,
                endpoint_path=endpoint_path,
            )
        except Exception as exc:
            logger.error("[FEDERATION] 联邦查询出错: %s", exc, exc_info=True)
            yield f"\n❌ 联邦查询错误: {str(exc)}\n"

    return streaming_response(generate())


def _federation_agent_stream_response(
    question: str,
    max_steps: int,
    endpoint_path: str = "/ask",
):
    """生成 Agent-to-Agent 联邦查询流式响应

    ``max_steps`` 仅为保持接口参数而接收，Agent 循环步数由其自身配置控制。
    """

    def generate() -> Generator[str, None, None]:
        try:
            service = current_service()
            agent = service.federation_agent
            if agent is None:
                yield _disabled_message("Agent-to-Agent 联邦查询", endpoint_path)
                return
            logger.info(
                "[FEDERATION A2A] 开始 Agent-to-Agent 查询, 端点: %s, 问题: %s...",
                endpoint_path,
                question[:60],
            )
            yield from agent.ask_stream(question=question, endpoint_path=endpoint_path)
        except Exception as exc:
            logger.error("[FEDERATION A2A] Agent-to-Agent 查询出错: %s", exc, exc_info=True)
            yield f"\n❌ Agent-to-Agent 查询错误: {str(exc)}\n"

    return streaming_response(generate())


def _broadcast(q, max_steps, conclusion_max_tokens, endpoint_path, log_message):
    question = fix_double_encoding(q)
    logger.info(log_message, question[:80])
    return _federation_stream_response(
        question, max_steps, conclusion_max_tokens, endpoint_path=endpoint_path
    )


def _agent_to_agent(q, max_steps, endpoint_path, log_message):
    question = fix_double_encoding(q)
    logger.info(log_message, question[:80])
    return _federation_agent_stream_response(question, max_steps, endpoint_path=endpoint_path)


# =========================================================================
# 联邦查询 API：/federation/ask - 多集群并发诊断入口
# =========================================================================


@router.get("/federation/ask")
async def federation_ask_get(
    q: str = Query(..., description="问题内容"),
    max_steps: int = Query(30, description="每个子集群最大执行步数", ge=1, le=100),
    conclusion_max_tokens: int = Query(8192, description="子集群诊断结论最大 token 数", ge=0),
):
    """
    🌐 多集群联邦查询（GET 方式）

    并发调用所有已配置的子集群，汇总诊断报告后由 LLM 合成统一结论：

    ```bash
    curl -G "http://localhost:8000/federation/ask" --data-urlencode "q=哪个集群CPU利用率最高"
    ```
    """
    return _broadcast(
        q, max_steps, conclusion_max_tokens, "/ask", "[FEDERATION] 收到联邦查询 (GET): %s..."
    )


@router.post("/federation/ask")
async def federation_ask_post(
    q: str = Form(..., description="问题内容"),
    max_steps: int = Form(30, description="每个子集群最大执行步数"),
    conclusion_max_tokens: int = Form(8192, description="子集群诊断结论最大 token 数"),
):
    """
    🌐 多集群联邦查询（POST 方式）

    ```bash
    curl -X POST "http://localhost:8000/federation/ask" -d "q=集群有什么问题" -d "max_steps=20"
    ```
    """
    return _broadcast(
        q, max_steps, conclusion_max_tokens, "/ask", "[FEDERATION] 收到联邦查询 (POST): %s..."
    )


# =========================================================================
# 联邦查询 API：/federation/query - 多集群并发查询入口
# =========================================================================


@router.get("/federation/query")
async def federation_query_get(
    q: str = Query(..., description="查询内容"),
    max_steps: int = Query(30, description="每个子集群最大执行步数", ge=1, le=100),
    conclusion_max_tokens: int = Query(8192, description="子集群查询结论最大 token 数", ge=0),
):
    return _broadcast(
        q,
        max_steps,
        conclusion_max_tokens,
        "/query",
        "[FEDERATION] 收到联邦查询模式请求 (GET): %s...",
    )


@router.post("/federation/query")
async def federation_query_post(
    q: str = Form(..., description="查询内容"),
    max_steps: int = Form(30, description="每个子集群最大执行步数"),
    conclusion_max_tokens: int = Form(8192, description="子集群查询结论最大 token 数"),
):
    return _broadcast(
        q,
        max_steps,
        conclusion_max_tokens,
        "/query",
        "[FEDERATION] 收到联邦查询模式请求 (POST): %s...",
    )


# =========================================================================
# Agent-to-Agent 联邦查询 API：/federation/{ask,query}/v2 - 智能路由
# =========================================================================


@router.get("/federation/ask/v2")
async def federation_ask_v2_get(
    q: str = Query(..., description="问题内容"),
    max_steps: int = Query(30, description="Agent 最大执行步数", ge=1, le=100),
):
    """
    🤖 Agent-to-Agent 联邦查询（GET 方式）

    使用 HolmesGPT Tool Calling 实现真正的智能路由：
    - 主 Agent 理解用户意图，决定查询哪些集群
    - 针对不同集群发送不同问题
    - 支持选择性查询（如"查询集群 1、3、5"）

    ```bash
    curl -G "http://localhost:8000/federation/ask/v2" --data-urlencode "q=查询 cluster-24 的 CPU"
    ```
    """
    return _agent_to_agent(
        q, max_steps, "/ask", "[FEDERATION A2A] 收到 Agent-to-Agent 查询 (GET): %s..."
    )


@router.post("/federation/ask/v2")
async def federation_ask_v2_post(
    q: str = Form(..., description="问题内容"),
    max_steps: int = Form(30, description="Agent 最大执行步数"),
):
    """
    🤖 Agent-to-Agent 联邦查询（POST 方式）

    ```bash
    curl -X POST "http://localhost:8000/federation/ask/v2" -d "q=查询集群 1 的 memory 和集群 3 的 cpu"
    ```
    """
    return _agent_to_agent(
        q, max_steps, "/ask", "[FEDERATION A2A] 收到 Agent-to-Agent 查询 (POST): %s..."
    )


@router.get("/federation/query/v2")
async def federation_query_v2_get(
    q: str = Query(..., description="查询内容"),
    max_steps: int = Query(30, description="Agent 最大执行步数", ge=1, le=100),
):
    return _agent_to_agent(
        q, max_steps, "/query", "[FEDERATION A2A] 收到 Agent-to-Agent 查询模式请求 (GET): %s..."
    )


@router.post("/federation/query/v2")
async def federation_query_v2_post(
    q: str = Form(..., description="查询内容"),
    max_steps: int = Form(30, description="Agent 最大执行步数"),
):
    return _agent_to_agent(
        q, max_steps, "/query", "[FEDERATION A2A] 收到 Agent-to-Agent 查询模式请求 (POST): %s..."
    )
