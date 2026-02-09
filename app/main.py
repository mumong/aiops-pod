#!/usr/bin/env python3
"""
HolmesGPT API Server
FastAPI 应用入口，只负责应用配置和启动
"""
import os
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import register_routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# 确保相关模块的日志也能输出
logging.getLogger('app.core.service').setLevel(logging.INFO)
logging.getLogger('app.core.mcp.manager').setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    from app.core import get_service
    from app.core.mcp import auto_start_mcp_servers, shutdown_mcp_servers, get_mcp_manager
    
    logger.info("=" * 60)
    logger.info("🚀 K8s AIOps Copilot 启动中...")
    logger.info("=" * 60)
    
    # ==================== 1. 启动 MCP 服务器（可选） ====================
    # 默认不自动启动本地 MCP 子进程：生产环境更常见的模式是直接连接第三方/独立部署的 MCP Server
    # 如确实需要在本进程内自动拉起（例如本地开发跑 bridge），设置：
    #   export MCP_AUTO_START_LOCAL=true
    logger.info("")
    logger.info("📡 [步骤 1/2] MCP 服务器连接/启动检查...")
    logger.info("-" * 40)

    auto_start_local = os.getenv("MCP_AUTO_START_LOCAL", "false").lower() in ("1", "true", "yes", "on")
    if auto_start_local:
        try:
            mcp_results = await auto_start_mcp_servers()

            if mcp_results:
                success_count = sum(1 for v in mcp_results.values() if v)
                total_count = len(mcp_results)

                for name, success in mcp_results.items():
                    status_icon = "✅" if success else "❌"
                    logger.info(f"   {status_icon} {name}: {'启动成功' if success else '启动失败'}")

                logger.info(f"   📊 本地 MCP 子进程: {success_count}/{total_count} 个启动成功")
            else:
                logger.info("   📭 没有配置需要自动启动的本地 MCP 服务器")

            # 等待 MCP 服务器完全启动
            if any(mcp_results.values()):
                logger.info("   ⏳ 等待本地 MCP 服务器就绪...")
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"   ❌ 本地 MCP 启动失败: {e}", exc_info=True)
    else:
        logger.info("   ℹ️ 已禁用本地 MCP auto-start（默认）。将直接使用配置中的第三方 MCP URL 连接。")
    
    # ==================== 2. 初始化 HolmesGPT ====================
    logger.info("")
    logger.info("🤖 [步骤 2/2] 初始化 HolmesGPT...")
    logger.info("-" * 40)
    
    try:
        service = get_service()
        init_timeout = int(os.getenv("HOLMES_INIT_TIMEOUT_SECONDS", "0"))  # 默认不超时
        
        if init_timeout > 0:
            # 有超时：异步初始化，到时间就继续
            init_task = asyncio.create_task(asyncio.to_thread(service.initialize))
            done, pending = await asyncio.wait({init_task}, timeout=init_timeout)
            if pending:
                logger.warning(
                    "   ⚠️ HolmesGPT 初始化超时（%ss），先继续启动服务；初始化将在后台继续运行",
                    init_timeout,
                )
                # 不取消任务，让它在后台继续
        else:
            # 无超时：同步等待初始化完成
            logger.info("   📌 等待 HolmesGPT 完全初始化（无超时限制）...")
            service.initialize()
            logger.info("   ✅ HolmesGPT 初始化完成")
    except Exception as e:
        logger.error(f"   ❌ HolmesGPT 初始化失败: {e}", exc_info=True)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ 服务启动完成!")
    logger.info("=" * 60)
    
    yield
    
    # ==================== 清理资源 ====================
    logger.info("")
    logger.info("🛑 正在关闭服务...")
    
    try:
        await shutdown_mcp_servers()
        logger.info("✅ MCP 服务器已关闭")
    except Exception as e:
        logger.error(f"关闭 MCP 服务器时出错: {e}")
    
    logger.info("👋 服务已停止")


# 创建 FastAPI 应用
app = FastAPI(
    title="HolmesGPT API Server",
    description="智能运维 Copilot API 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
register_routes(app)


def create_app() -> FastAPI:
    """创建并返回 FastAPI 应用实例"""
    return app


def main():
    """启动 API 服务器"""
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"🚀 启动 AIOps Copilot API 服务器")
    logger.info(f"   地址: http://{host}:{port}")
    logger.info(f"")
    logger.info(f"   📖 使用方式:")
    logger.info(f"   curl -G 'http://{host}:{port}/ask' --data-urlencode 'q=你的问题'")
    logger.info(f"   curl -X POST 'http://{host}:{port}/ask' -d 'q=你的问题'")
    logger.info(f"")
    logger.info(f"   🔗 其他端点:")
    logger.info(f"   API 文档: http://{host}:{port}/docs")
    logger.info(f"   健康检查: http://{host}:{port}/health")
    
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
    }
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        log_config=log_config,
        use_colors=True
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
