"""辅助端点：服务信息、健康检查、工具/Runbook 清单、大输出全文、MCP 状态与诊断报告。"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.api.common import current_service, logger
from app.core.holmes.artifacts import get_artifact_store
from app.core.paths import get_app_version

router = APIRouter()


def _reports_dir() -> Path:
    return Path(os.environ.get("REPORTS_DIR", "/tmp/aiops/reports"))


@router.get("/")
async def root():
    """API 信息和使用说明"""
    return {
        "service": "AIOps Copilot",
        "version": get_app_version(),
        "status": "running",
        "usage": {
            "诊断入口": "curl -G 'http://HOST/ask' --data-urlencode 'q=你的诊断问题'",
            "轻量查询": "curl -G 'http://HOST/query' --data-urlencode 'q=你的查询问题'",
            "POST方式": "curl -X POST 'http://HOST/ask' -d 'q=你的问题'",
        },
        "examples": [
            "curl -G 'http://localhost:30800/ask' --data-urlencode 'q=Pod一直重启'",
            "curl -G 'http://localhost:30800/query' --data-urlencode 'q=集群 CPU 和内存使用率是多少'",
            "curl -X POST 'http://localhost:30800/ask' -d 'q=磁盘满了怎么清理'",
        ],
        "endpoints": {
            "/ask": "GET/POST - 诊断入口（layer -> evidence -> rca -> conclusion）",
            "/query": "GET/POST - 轻量查询入口（layer -> conclusion）",
            "/federation/ask": "GET/POST - 多集群诊断广播入口",
            "/federation/query": "GET/POST - 多集群查询广播入口",
            "/health": "GET - 健康检查",
            "/tools": "GET - 可用工具列表",
            "/runbooks": "GET - 可用 Runbooks",
        },
        "note": "中文问题需要 URL 编码，推荐使用 --data-urlencode 或 POST 方式",
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    service = current_service()
    return service.health_check()


@router.get("/tools")
async def list_tools():
    """列出所有可用的工具"""
    try:
        service = current_service()
        return service.get_tools_info()
    except Exception as e:
        logger.error("获取工具列表失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/tools/detail")
async def list_tools_detail():
    """
    列出更详细的工具信息（按 toolset 分组，含尽可能多的 schema/描述）
    用途：排障、二次开发（例如你要做多集群能力时先摸清现有工具结构）
    """
    try:
        service = current_service()
        return service.get_tools_detail()
    except Exception as e:
        logger.error("获取工具详情失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/runbooks")
async def list_runbooks():
    """列出所有可用的 Runbooks"""
    try:
        service = current_service()
        if service.merged_catalog and service.merged_catalog.catalog:
            runbooks = []
            for entry in service.merged_catalog.catalog:
                if hasattr(entry, "id"):
                    runbooks.append(
                        {
                            "id": entry.id,
                            "description": getattr(entry, "description", ""),
                            "link": getattr(entry, "link", ""),
                        }
                    )
            return {"count": len(runbooks), "runbooks": runbooks}
        return {"count": 0, "runbooks": []}
    except Exception as e:
        logger.error("获取 Runbooks 失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """
    获取被截断的大输出全文（内存缓存，带 TTL）
    """
    store = get_artifact_store()
    artifact = store.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact not found or expired")
    return PlainTextResponse(content=artifact.content, media_type=artifact.content_type)


@router.get("/api/v1/mcp/status")
async def get_mcp_status():
    """获取 MCP 服务器状态"""
    from app.core.mcp import get_mcp_manager

    manager = get_mcp_manager()
    return {"success": True, "servers": manager.get_status()}


# =========================================================================
# 报告查看 API：/reports - 查看保存的子集群诊断报告
# =========================================================================


@router.get("/reports")
async def list_reports(
    cluster: Optional[str] = Query(None, description="按集群名称过滤"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=500),
):
    """
    📄 列出已保存的子集群诊断报告

    ```bash
    # 列出所有报告
    curl "http://localhost:8000/reports"

    # 按集群过滤
    curl "http://localhost:8000/reports?cluster=cluster-24"

    # 限制数量
    curl "http://localhost:8000/reports?limit=10"
    ```
    """
    reports_dir = _reports_dir()
    if not reports_dir.exists():
        return {"count": 0, "reports": []}

    files = sorted(reports_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)

    if cluster:
        files = [f for f in files if f.name.startswith(f"{cluster}_")]

    files = files[:limit]

    report_list = []
    for f in files:
        stat = f.stat()
        report_list.append(
            {
                "filename": f.name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return {"count": len(report_list), "reports": report_list}


@router.get("/reports/{filename}")
async def get_report(filename: str):
    """
    📄 查看具体报告内容

    ```bash
    curl "http://localhost:8000/reports/cluster-24_20260309_143000.md"
    ```
    """
    reports_dir = _reports_dir()
    filepath = reports_dir / filename

    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail=f"报告不存在: {filename}")

    # 防止路径穿越
    if not filepath.resolve().is_relative_to(reports_dir.resolve()):
        raise HTTPException(status_code=403, detail="禁止访问")

    content = filepath.read_text(encoding="utf-8")
    return PlainTextResponse(content=content, media_type="text/plain; charset=utf-8")
