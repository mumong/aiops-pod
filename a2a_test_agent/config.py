"""Environment-backed configuration for the A2A test delegator agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


def _absolute_http_url(name: str, value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be an absolute http(s) URL")
    return normalized


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _positive_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class TestAgentSettings:
    """Settings for an A2A server that is also an A2A client."""

    __test__ = False

    target_url: str = "http://127.0.0.1:8001"
    target_token: str = ""
    public_url: str = "http://127.0.0.1:8002"
    host: str = "0.0.0.0"
    port: int = 8002
    request_timeout_seconds: float = 1800.0
    api_token: str = ""
    agent_name: str = "A2A Operations Test Delegator"
    agent_version: str = "1.0.0"

    @classmethod
    def from_env(cls) -> "TestAgentSettings":
        return cls(
            target_url=_absolute_http_url(
                "TEST_AGENT_TARGET_URL",
                os.getenv("TEST_AGENT_TARGET_URL", "http://127.0.0.1:8001"),
            ),
            target_token=os.getenv("TEST_AGENT_TARGET_TOKEN", "").strip(),
            public_url=_absolute_http_url(
                "TEST_AGENT_PUBLIC_URL",
                os.getenv("TEST_AGENT_PUBLIC_URL", "http://127.0.0.1:8002"),
            ),
            host=os.getenv("TEST_AGENT_HOST", "0.0.0.0").strip() or "0.0.0.0",
            port=_positive_int("TEST_AGENT_PORT", 8002),
            request_timeout_seconds=_positive_float("TEST_AGENT_REQUEST_TIMEOUT_SECONDS", 1800.0),
            api_token=os.getenv("TEST_AGENT_API_TOKEN", "").strip(),
            agent_name=os.getenv("TEST_AGENT_NAME", "A2A Operations Test Delegator").strip()
            or "A2A Operations Test Delegator",
            agent_version=os.getenv(
                "TEST_AGENT_VERSION", os.getenv("APP_VERSION", "1.0.0")
            ).strip()
            or "1.0.0",
        )
