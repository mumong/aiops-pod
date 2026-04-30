"""Server-side token usage probes for OpenAI-compatible chat endpoints.

This module is intentionally opt-in. It sends a real chat completion request
with `max_tokens=1` and reads `usage.prompt_tokens`, so the result reflects the
model gateway's tokenizer and chat template instead of a local estimate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class UsageProbeResult:
    prompt_tokens: Optional[int]
    total_tokens: Optional[int]
    completion_tokens: Optional[int]
    source: str
    accuracy: str
    error: str = ""


class OpenAIUsageProbe:
    """Probe prompt token usage through `/chat/completions` usage metadata."""

    def __init__(self, api_base: str, api_key: str = "", timeout: float = 30.0):
        self.api_base = (api_base or "").rstrip("/")
        self.api_key = api_key or ""
        self.timeout = timeout

    def count_prompt_tokens(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> UsageProbeResult:
        if not self.api_base:
            return UsageProbeResult(None, None, None, "usage_probe", "unknown", "api_base is empty")

        payload: Dict[str, Any] = {
            "model": (model or "").split("/", 1)[-1],
            "messages": messages,
            "max_tokens": 1,
            "temperature": 0,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                return UsageProbeResult(
                    None,
                    None,
                    None,
                    "usage_probe:/chat/completions",
                    "unknown",
                    f"HTTP {response.status_code}: {response.text[:500]}",
                )
            usage = (response.json() or {}).get("usage") or {}
            prompt_tokens = usage.get("prompt_tokens")
            if prompt_tokens is None:
                return UsageProbeResult(
                    None,
                    usage.get("total_tokens"),
                    usage.get("completion_tokens"),
                    "usage_probe:/chat/completions",
                    "unknown",
                    "response.usage.prompt_tokens missing",
                )
            return UsageProbeResult(
                int(prompt_tokens),
                int(usage["total_tokens"]) if usage.get("total_tokens") is not None else None,
                int(usage["completion_tokens"]) if usage.get("completion_tokens") is not None else None,
                "usage_probe:/chat/completions",
                "exact",
            )
        except Exception as exc:
            return UsageProbeResult(None, None, None, "usage_probe:/chat/completions", "unknown", str(exc))

