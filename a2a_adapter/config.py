"""Environment-backed configuration for the standalone A2A adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


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


def _absolute_http_url(name: str, value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be an absolute http(s) URL")
    return normalized


@dataclass(frozen=True)
class AdapterSettings:
    """Runtime settings kept separate from the HolmesGPT process."""

    backend_url: str = "http://127.0.0.1:8000"
    public_url: str = "http://127.0.0.1:8001"
    host: str = "0.0.0.0"
    port: int = 8001
    max_steps: int = 20
    request_timeout_seconds: float = 1800.0
    connect_timeout_seconds: float = 10.0
    api_token: str = ""
    agent_name: str = "Kubernetes AIOps Copilot"
    agent_version: str = "1.0.0"

    @classmethod
    def from_env(cls) -> "AdapterSettings":
        return cls(
            backend_url=_absolute_http_url(
                "A2A_BACKEND_URL",
                os.getenv("A2A_BACKEND_URL", "http://127.0.0.1:8000"),
            ),
            public_url=_absolute_http_url(
                "A2A_PUBLIC_URL",
                os.getenv("A2A_PUBLIC_URL", "http://127.0.0.1:8001"),
            ),
            host=os.getenv("A2A_HOST", "0.0.0.0").strip() or "0.0.0.0",
            port=_positive_int("A2A_PORT", 8001),
            max_steps=_positive_int("A2A_MAX_STEPS", 20),
            request_timeout_seconds=_positive_float(
                "A2A_REQUEST_TIMEOUT_SECONDS", 1800.0
            ),
            connect_timeout_seconds=_positive_float(
                "A2A_CONNECT_TIMEOUT_SECONDS", 10.0
            ),
            api_token=os.getenv("A2A_API_TOKEN", "").strip(),
            agent_name=os.getenv(
                "A2A_AGENT_NAME", "Kubernetes AIOps Copilot"
            ).strip()
            or "Kubernetes AIOps Copilot",
            agent_version=os.getenv(
                "A2A_AGENT_VERSION", os.getenv("APP_VERSION", "1.0.0")
            ).strip()
            or "1.0.0",
        )
