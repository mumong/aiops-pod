"""HMAC request signatures between the center and the edge runner.

Anyone holding xnet's tunnel client certificate can reach any edge Service, so
the runner accepts only requests signed with our own shared key
(contracts/runner-api.md).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from typing import Dict, Mapping, Optional

HEADER_TS = "X-AIOps-Timestamp"
HEADER_NONCE = "X-AIOps-Nonce"
HEADER_SIG = "X-AIOps-Signature"
MAX_SKEW_SECONDS = 60


def _payload(ts: str, nonce: str, method: str, path: str, body: bytes) -> bytes:
    digest = hashlib.sha256(body or b"").hexdigest()
    return "\n".join((ts, nonce, method.upper(), path, digest)).encode()


def sign(
    key: bytes,
    method: str,
    path: str,
    body: bytes,
    *,
    now: Optional[float] = None,
    nonce: Optional[str] = None,
) -> Dict[str, str]:
    ts = str(int(time.time() if now is None else now))
    nonce = nonce or secrets.token_hex(16)
    sig = hmac.new(key, _payload(ts, nonce, method, path, body), hashlib.sha256).hexdigest()
    return {HEADER_TS: ts, HEADER_NONCE: nonce, HEADER_SIG: sig}


class NonceCache:
    """Remembers nonces for ``ttl`` seconds to refuse replays."""

    def __init__(self, ttl: int = 300) -> None:
        self.ttl = ttl
        self._seen: Dict[str, float] = {}
        self._lock = threading.Lock()

    def seen(self, nonce: str, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            for old in [n for n, t in self._seen.items() if now - t > self.ttl]:
                del self._seen[old]
            if nonce in self._seen:
                return True
            self._seen[nonce] = now
            return False


def _header(headers: Mapping[str, str], name: str) -> str:
    getter = getattr(headers, "get", None)
    value = getter(name) if getter else None
    if value is None:
        lowered = name.lower()
        value = next((v for k, v in headers.items() if k.lower() == lowered), None)
    return value or ""


def verify(
    key: bytes,
    headers: Mapping[str, str],
    method: str,
    path: str,
    body: bytes,
    *,
    now: Optional[float] = None,
    cache: NonceCache,
) -> Optional[str]:
    """Return None when the request is authentic, otherwise the refusal reason."""
    ts, nonce, sig = (_header(headers, h) for h in (HEADER_TS, HEADER_NONCE, HEADER_SIG))
    if not (ts and nonce and sig):
        return "missing signature headers"
    try:
        skew = abs((time.time() if now is None else now) - int(ts))
    except ValueError:
        return "bad timestamp"
    if skew > MAX_SKEW_SECONDS:
        return f"timestamp skew {int(skew)}s exceeds {MAX_SKEW_SECONDS}s"
    expected = hmac.new(key, _payload(ts, nonce, method, path, body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return "bad signature"
    if cache.seen(nonce, now):
        return "replayed nonce"
    return None
