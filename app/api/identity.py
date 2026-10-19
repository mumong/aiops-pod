"""Caller identity: the browser's owner cookie, or an API token for scripts and agents.

Diagnosis records, repair jobs and approvals are bound to an *owner* (64 hex chars).
The browser gets it as the HttpOnly cookie ``aiops_query_owner``. API callers (curl,
CI, the A2A adapter) instead send ``Authorization: Bearer <token>`` or
``X-AIOps-API-Token: <token>``; tokens come from the Secret ``AIOPS_API_TOKENS`` as
``name=token`` pairs and each name maps to a stable owner, so a principal keeps its
records across requests without a cookie jar. A token that does not match is a 401,
never a silent fallback to the cookie.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import HTTPException, Request

API_TOKENS_ENV = "AIOPS_API_TOKENS"
API_TOKEN_HEADER = "X-AIOps-API-Token"
OWNER_COOKIE = "aiops_query_owner"
_OWNER = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class Principal:
    name: str
    owner: str


def principal_owner(name: str) -> str:
    """Stable owner of an API principal (same name, same records)."""
    return hashlib.sha256(f"aiops-api-principal:{name}".encode()).hexdigest()


def _configured_tokens() -> Dict[str, str]:
    tokens = {}
    for item in os.getenv(API_TOKENS_ENV, "").split(","):
        name, sep, token = item.strip().partition("=")
        if sep and name.strip() and token.strip():
            tokens[token.strip()] = name.strip()
    return tokens


def _presented_token(request: Request) -> Optional[str]:
    header = request.headers.get(API_TOKEN_HEADER)
    if header:
        return header.strip()
    authorization = request.headers.get("Authorization") or ""
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "bearer" and value.strip():
        return value.strip()
    return None


def principal(request: Request) -> Optional[Principal]:
    """The API principal of this request, None for browser (cookie) requests."""
    presented = _presented_token(request)
    if presented is None:
        return None
    for token, name in _configured_tokens().items():
        if secrets.compare_digest(token, presented):
            return Principal(name=name, owner=principal_owner(name))
    raise HTTPException(401, "API 令牌无效或未配置（AIOPS_API_TOKENS）")


def cookie_owner(request: Request) -> str:
    value = request.cookies.get(OWNER_COOKIE, "")
    return value if _OWNER.fullmatch(value) else ""


def request_owner(request: Request) -> str:
    """Owner of this request: the API principal's, else the browser cookie's ('' if none)."""
    found = principal(request)
    return found.owner if found else cookie_owner(request)
