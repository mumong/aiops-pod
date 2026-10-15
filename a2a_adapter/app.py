"""FastAPI application exposing the official A2A JSON-RPC protocol."""

from __future__ import annotations

import hmac
import logging
from typing import Any

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    HTTPAuthSecurityScheme,
    SecurityScheme,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from a2a_adapter.backend import AiopsBackendClient
from a2a_adapter.config import AdapterSettings
from a2a_adapter.executor import AiopsAgentExecutor

logger = logging.getLogger(__name__)


def build_agent_card(settings: AdapterSettings) -> AgentCard:
    security: list[dict[str, list[str]]] | None = None
    schemes: dict[str, SecurityScheme] | None = None
    if settings.api_token:
        security = [{"bearerAuth": []}]
        schemes = {
            "bearerAuth": SecurityScheme(
                root=HTTPAuthSecurityScheme(
                    scheme="Bearer",
                    bearer_format="opaque-token",
                    description="Bearer token configured through A2A_API_TOKEN",
                )
            )
        }

    return AgentCard(
        name=settings.agent_name,
        description=(
            "Evidence-driven Kubernetes AIOps agent for Pod anomaly detection, "
            "metrics queries, root-cause analysis, and Markdown diagnostic reports."
        ),
        url=f"{settings.public_url}/",
        version=settings.agent_version,
        protocol_version="0.3.0",
        preferred_transport="JSONRPC",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["text/markdown"],
        skills=[
            AgentSkill(
                id="kubernetes-diagnosis",
                name="Kubernetes anomaly diagnosis",
                description=(
                    "Inspect current Kubernetes and observability evidence, diagnose "
                    "abnormal Pods, and produce a root-cause report."
                ),
                tags=["kubernetes", "aiops", "pod", "root-cause-analysis"],
                examples=[
                    "请诊断 production 命名空间中的异常 Pod，说明根因和证据。",
                    "Why is my Pod in CrashLoopBackOff?",
                ],
            ),
            AgentSkill(
                id="kubernetes-query",
                name="Kubernetes and metrics query",
                description=(
                    "Query Kubernetes resource state and observability metrics. "
                    "Defaults to autonomous /query analysis; set aiops_mode=diagnosis for the legacy /ask workflow."
                ),
                tags=["kubernetes", "metrics", "prometheus", "query"],
                examples=["查询当前集群各 Node 的 CPU 和内存使用率。"],
            ),
        ],
        security=security,
        security_schemes=schemes,
    )


def create_app(
    settings: AdapterSettings | None = None,
    *,
    backend_client: AiopsBackendClient | Any | None = None,
) -> FastAPI:
    settings = settings or AdapterSettings.from_env()
    backend = backend_client or AiopsBackendClient(settings)
    executor = AiopsAgentExecutor(backend)
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )
    a2a_application = A2AFastAPIApplication(
        agent_card=build_agent_card(settings),
        http_handler=handler,
    )

    app = FastAPI(
        title=f"{settings.agent_name} A2A Server",
        version=settings.agent_version,
        description="Agent2Agent Protocol v0.3.0 adapter powered by a2a-sdk 0.3.25",
    )
    a2a_application.add_routes_to_app(app)

    @app.middleware("http")
    async def authenticate_rpc(request: Request, call_next):
        if settings.api_token and request.method == "POST" and request.url.path == "/":
            supplied = request.headers.get("Authorization", "")
            expected = f"Bearer {settings.api_token}"
            if not hmac.compare_digest(supplied, expected):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "invalid or missing bearer token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return await call_next(request)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, Any]:
        """Liveness: the adapter process can answer requests."""
        return {
            "status": "healthy",
            "protocol_version": "0.3.0",
            "sdk_version": "0.3.25",
        }

    @app.get("/ready", include_in_schema=False)
    async def ready():
        """Readiness: the adapter can reach an initialized AIOps backend."""
        backend_health = await backend.health()
        backend_ok = backend_health.get("status") == "healthy"
        payload = {
            "status": "ready" if backend_ok else "not-ready",
            "protocol_version": "0.3.0",
            "sdk_version": "0.3.25",
            "backend": backend_health,
        }
        if not backend_ok:
            return JSONResponse(status_code=503, content=payload)
        return payload

    app.state.adapter_settings = settings
    app.state.a2a_executor = executor
    app.state.a2a_task_store = task_store
    return app


app = create_app()
