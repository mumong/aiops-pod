#!/usr/bin/env python3
"""
API Routes - AIOps Copilot API 端点

设计原则：
1. 简单优先：GET 请求 + query parameter 即可使用
2. 灵活可选：POST 请求支持更多自定义选项
3. 流式输出：默认返回易读的纯文本流

路由按职责拆分：
- ask_routes:        /ask、/query、/q/{question}、/remediation/approve
- info_routes:       /、/health、/tools、/runbooks、/artifacts、/api/v1/mcp/status、/reports
- repair_routes:     /repair/*

API 使用示例：
    # 最简单的方式（推荐）
    curl "http://localhost:8000/ask?q=Pod一直重启怎么办"

    # 流式输出（默认）
    curl -N "http://localhost:8000/ask?q=磁盘满了"

    # POST 方式（自定义选项）
    curl -X POST "http://localhost:8000/ask" -d "q=Pod状态异常"
"""

# get_service 保留在本模块：各路由模块经 app.api.common.current_service 在调用时
# 从这里解析，测试通过 monkeypatch "app.api.routes.get_service" 替换服务。
from app.api import ask_routes, info_routes
from app.api.common import fix_double_encoding  # noqa: F401  (向后兼容的导出)
from app.core.service import get_service  # noqa: F401


def register_routes(app):
    """注册所有 API 路由（顺序即匹配与 OpenAPI 顺序）"""
    from app.api.repair_routes import register_repair_routes

    register_repair_routes(app)

    app.include_router(ask_routes.router)
    app.include_router(info_routes.router)
