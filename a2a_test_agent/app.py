"""A real A2A server that delegates to the Kubernetes operations A2A server."""

from __future__ import annotations

import hmac
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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

from a2a_test_agent.config import TestAgentSettings
from a2a_test_agent.executor import DelegatingAgentExecutor
from a2a_test_agent.remote import OperationsAgentClient


def build_agent_card(settings: TestAgentSettings) -> AgentCard:
    security: list[dict[str, list[str]]] | None = None
    schemes: dict[str, SecurityScheme] | None = None
    if settings.api_token:
        security = [{"bearerAuth": []}]
        schemes = {
            "bearerAuth": SecurityScheme(
                root=HTTPAuthSecurityScheme(
                    scheme="Bearer",
                    bearer_format="opaque-token",
                    description="Bearer token configured through TEST_AGENT_API_TOKEN",
                )
            )
        }

    return AgentCard(
        name=settings.agent_name,
        description=(
            "A protocol test and delegation agent. It accepts an A2A request, "
            "discovers the configured Kubernetes AIOps Agent, invokes it through "
            "the official A2A SDK, and returns its Markdown artifact."
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
                id="delegate-kubernetes-aiops",
                name="Delegate Kubernetes operations diagnosis",
                description=(
                    "Delegate Kubernetes diagnosis and metrics questions to a remote "
                    "operations Agent over Agent2Agent Protocol."
                ),
                tags=["a2a", "delegation", "kubernetes", "aiops", "test"],
                examples=[
                    "请调用运维 Agent 诊断 production 命名空间中的异常 Pod。",
                    "查询当前集群各 Node CPU 使用率。",
                ],
            )
        ],
        security=security,
        security_schemes=schemes,
    )


def create_app(
    settings: TestAgentSettings | None = None,
    *,
    remote_client: OperationsAgentClient | Any | None = None,
) -> FastAPI:
    settings = settings or TestAgentSettings.from_env()
    remote = remote_client or OperationsAgentClient(settings)
    executor = DelegatingAgentExecutor(remote)
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)
    protocol_app = A2AFastAPIApplication(
        agent_card=build_agent_card(settings),
        http_handler=handler,
    )

    app = FastAPI(
        title=f"{settings.agent_name} A2A Server",
        version=settings.agent_version,
        description="A2A-to-A2A integration test service using a2a-sdk 0.3.25",
    )
    protocol_app.add_routes_to_app(app)

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
        return {
            "status": "healthy",
            "role": "a2a-delegating-agent",
            "protocol_version": "0.3.0",
            "sdk_version": "0.3.25",
        }

    @app.get("/ready", include_in_schema=False)
    async def ready():
        target = await remote.health()
        target_ok = target.get("status") == "healthy"
        payload = {
            "status": "ready" if target_ok else "not-ready",
            "role": "a2a-delegating-agent",
            "target": target,
        }
        if not target_ok:
            return JSONResponse(status_code=503, content=payload)
        return payload

    app.state.test_agent_settings = settings
    app.state.remote_agent_client = remote
    app.state.a2a_executor = executor
    app.state.a2a_task_store = task_store
    return app


app = create_app()
