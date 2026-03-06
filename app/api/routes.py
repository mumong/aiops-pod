#!/usr/bin/env python3
"""
API Routes - AIOps Copilot API 端点

设计原则：
1. 简单优先：GET 请求 + query parameter 即可使用
2. 灵活可选：POST 请求支持更多自定义选项
3. 流式输出：默认返回易读的纯文本流

API 使用示例：
    # 最简单的方式（推荐）
    curl "http://localhost:8000/ask?q=Pod一直重启怎么办"
    
    # 流式输出（默认）
    curl -N "http://localhost:8000/ask?q=磁盘满了"
    
    # POST 方式（自定义选项）
    curl -X POST "http://localhost:8000/ask" -d "q=Pod状态异常"
"""
import logging
from typing import Optional, Generator
from urllib.parse import unquote

from fastapi import HTTPException, Query, Form
from fastapi.responses import StreamingResponse, PlainTextResponse

from app.core.service import get_service
from app.core.holmes.artifacts import get_artifact_store

logger = logging.getLogger(__name__)


def fix_double_encoding(text: str) -> str:
    """
    修复客户端双重 UTF-8 编码的问题

    某些客户端会先 UTF-8 编码，再被错误地当作 Latin-1 解码，
    导致中文变成乱码。这个函数尝试修复这个问题。
    """
    try:
        # 尝试将错误的字符串编码回字节，再用正确的编码解码
        fixed = text.encode('latin-1').decode('utf-8')
        logger.debug(f"✅ 修复了双重编码: {text[:20]} -> {fixed[:20]}")
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 如果修复失败，说明原始数据就是正确的
        return text


def register_routes(app):
    """注册所有 API 路由"""
    
    # =========================================================================
    # 核心 API：/ask - 统一的查询入口
    # =========================================================================
    
    @app.get("/ask")
    async def ask_get(
        q: str = Query(..., description="问题内容", example="Pod一直重启怎么办"),
        stream: bool = Query(True, description="是否流式输出"),
        format: str = Query("text", description="输出格式: text(默认) 或 sse"),
        max_steps: int = Query(20, description="最大执行步数", ge=1, le=100),
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
        question = fix_double_encoding(q) # FastAPI 的 Query 已自动解码
        logger.info(f"📝 收到查询: {question[:80]}...")
        
        if stream:
            return _stream_response(question, format, max_steps)
        else:
            return await _sync_response(question, max_steps)
    
    @app.post("/ask")
    async def ask_post(
        q: str = Form(..., description="问题内容"),
        stream: bool = Form(True, description="是否流式输出"),
        format: str = Form("text", description="输出格式"),
        max_steps: int = Form(20, description="最大执行步数"),
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
        question = fix_double_encoding(q) # 解码 URL 编码的表单数据
        logger.info(f"📝 收到查询 (POST): {question[:80]}...")
        
        ###
        logger.info(f"📝 收到查询 (POST): {question[:80]}...")
        logger.info(f"📝 测试----收到查询 (POST): {q}")
        logger.info(f"🔍 调试 - 字符串长度: {len(q)}")
        logger.info(f"🔍 调试 - 前20字节: {q[:20].encode('utf-8')}")
        logger.info(f"🔍 调试 - repr: {repr(q[:50])}")
        ###

        if stream:
            return _stream_response(question, format, max_steps)
        else:
            return await _sync_response(question, max_steps)
    
    # =========================================================================
    # 便捷别名路由
    # =========================================================================
    
    @app.get("/q/{question:path}")
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
        logger.info(f"📝 收到查询 (路径): {question[:80]}...")
        
        if stream:
            return _stream_response(question, format, max_steps)
        else:
            return await _sync_response(question, max_steps)
    
    # =========================================================================
    # 兼容旧 API（保持向后兼容）
    # =========================================================================
    
    @app.post("/api/v1/query/stream")
    async def legacy_query_stream(request: dict):
        """
        [兼容] 旧版流式查询 API
        
        保留向后兼容，推荐使用 /ask
        """
        question = fix_double_encoding(request.get("question", ""))
        output_format = request.get("output_format", "text")
        max_steps = request.get("max_steps", 20)

        logger.info(f"📝 收到查询 (旧API): {question[:80]}...")
        return _stream_response(question, output_format, max_steps)
    
    @app.post("/api/v1/query")
    async def legacy_query(request: dict):
        """
        [兼容] 旧版同步查询 API
        
        保留向后兼容，推荐使用 /ask?stream=false
        """
        question = fix_double_encoding(request.get("question", ""))
        max_steps = request.get("max_steps", 20)

        logger.info(f"📝 收到查询 (旧API): {question[:80]}...")
        return await _sync_response(question, max_steps)
    
    # =========================================================================
    # 辅助端点
    # =========================================================================
    
    @app.get("/")
    async def root():
        """API 信息和使用说明"""
        return {
            "service": "AIOps Copilot",
            "version": "2.0.0",
            "status": "running",
            "usage": {
                "中文查询(推荐)": "curl -G 'http://HOST/ask' --data-urlencode 'q=你的问题'",
                "POST方式": "curl -X POST 'http://HOST/ask' -d 'q=你的问题'",
                "英文查询": "curl 'http://HOST/ask?q=your+question'",
            },
            "examples": [
                "curl -G 'http://localhost:30800/ask' --data-urlencode 'q=Pod一直重启'",
                "curl -X POST 'http://localhost:30800/ask' -d 'q=磁盘满了怎么清理'",
                "curl 'http://localhost:30800/ask?q=check+cluster+health'",
            ],
            "endpoints": {
                "/ask": "GET/POST - 主要查询入口",
                "/health": "GET - 健康检查",
                "/tools": "GET - 可用工具列表",
                "/runbooks": "GET - 可用 Runbooks",
            },
            "note": "中文问题需要 URL 编码，推荐使用 --data-urlencode 或 POST 方式"
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        service = get_service()
        return service.health_check()
    
    @app.get("/tools")
    async def list_tools():
        """列出所有可用的工具"""
        try:
            service = get_service()
            return service.get_tools_info()
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/tools/detail")
    async def list_tools_detail():
        """
        列出更详细的工具信息（按 toolset 分组，含尽可能多的 schema/描述）
        用途：排障、二次开发（例如你要做多集群能力时先摸清现有工具结构）
        """
        try:
            service = get_service()
            return service.get_tools_detail()
        except Exception as e:
            logger.error(f"获取工具详情失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/runbooks")
    async def list_runbooks():
        """列出所有可用的 Runbooks"""
        try:
            service = get_service()
            if service.merged_catalog and service.merged_catalog.catalog:
                runbooks = []
                for entry in service.merged_catalog.catalog:
                    if hasattr(entry, 'id'):
                        runbooks.append({
                            "id": entry.id,
                            "description": getattr(entry, 'description', ''),
                            "link": getattr(entry, 'link', '')
                        })
                return {"count": len(runbooks), "runbooks": runbooks}
            return {"count": 0, "runbooks": []}
        except Exception as e:
            logger.error(f"获取 Runbooks 失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/artifacts/{artifact_id}")
    async def get_artifact(artifact_id: str):
        """
        获取被截断的大输出全文（内存缓存，带 TTL）
        """
        store = get_artifact_store()
        artifact = store.get(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="artifact not found or expired")
        return PlainTextResponse(content=artifact.content, media_type=artifact.content_type)
    
    @app.get("/api/v1/mcp/status")
    async def get_mcp_status():
        """获取 MCP 服务器状态"""
        from app.core.mcp import get_mcp_manager
        manager = get_mcp_manager()
        return {"success": True, "servers": manager.get_status()}
    
    # =========================================================================
    # 内部辅助函数
    # =========================================================================
    
    # =========================================================================
    # 联邦查询 API：/federation/ask - 多集群并发诊断入口
    # =========================================================================

    @app.get("/federation/ask")
    async def federation_ask_get(
        q: str = Query(..., description="问题内容"),
        max_steps: int = Query(30, description="每个子集群最大执行步数", ge=1, le=100),
    ):
        """
        🌐 多集群联邦查询（GET 方式）

        并发调用所有已配置的子集群，汇总诊断报告后由 LLM 合成统一结论：

        ```bash
        curl -G "http://localhost:8000/federation/ask" --data-urlencode "q=哪个集群CPU利用率最高"
        ```
        """
        question = fix_double_encoding(q)
        logger.info(f"[FEDERATION] 收到联邦查询 (GET): {question[:80]}...")
        return _federation_stream_response(question, max_steps)

    @app.post("/federation/ask")
    async def federation_ask_post(
        q: str = Form(..., description="问题内容"),
        max_steps: int = Form(30, description="每个子集群最大执行步数"),
    ):
        """
        🌐 多集群联邦查询（POST 方式）

        ```bash
        curl -X POST "http://localhost:8000/federation/ask" -d "q=集群有什么问题" -d "max_steps=20"
        ```
        """
        question = fix_double_encoding(q)
        logger.info(f"[FEDERATION] 收到联邦查询 (POST): {question[:80]}...")
        return _federation_stream_response(question, max_steps)

    def _federation_stream_response(question: str, max_steps: int):
        """生成联邦查询流式响应"""

        def generate() -> Generator[str, None, None]:
            try:
                service = get_service()
                coordinator = service.federation_coordinator
                if coordinator is None:
                    yield (
                        "❌ 联邦查询未启用。\n\n"
                        "请在主集群 config.yaml 中设置 federation.enabled: true 并配置子集群列表。\n"
                        "若要查询单集群，请使用 /ask 端点。\n"
                    )
                    return
                logger.info(
                    f"[FEDERATION] 开始联邦查询, "
                    f"子集群数量: {len(coordinator._registry.get_enabled_agents())}, "
                    f"问题: {question[:60]}..."
                )
                yield from coordinator.ask_stream(question=question, max_steps=max_steps)
            except Exception as exc:
                logger.error(f"[FEDERATION] 联邦查询出错: {exc}", exc_info=True)
                yield f"\n❌ 联邦查询错误: {str(exc)}\n"

        return StreamingResponse(
            generate(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    def _stream_response(question: str, output_format: str, max_steps: int):
        """生成流式响应"""
        
        def generate() -> Generator[str, None, None]:
            try:
                service = get_service()
                yield from service.execute_query_stream(
                    question=question,
                    max_steps=max_steps,
                    output_format=output_format
                )
            except Exception as e:
                logger.error(f"流式查询出错: {e}", exc_info=True)
                yield f"\n❌ 错误: {str(e)}\n"
        
        media_type = "text/event-stream" if output_format == "sse" else "text/plain; charset=utf-8"
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    async def _sync_response(question: str, max_steps: int):
        """生成同步响应"""
        try:
            service = get_service()
            result = service.execute_query(
                question=question,
                max_steps=max_steps
            )
            
            if result.get("success"):
                return PlainTextResponse(
                    content=result.get("result", ""),
                    media_type="text/plain; charset=utf-8"
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error"))
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"查询出错: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))