"""Effective repair execution settings: config baseline plus a TTL-bound runtime override.

The review/auto switch is a global safety posture, not a per-request parameter.
An administrator can override the configured mode for a bounded time (break-glass
pattern); the override is persisted under the repair record root so a restart
does not silently change posture, expires on its own, and every change is audited.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.remediation.audit import audit_event, audit_root
from app.core.remediation.models import normalize_remediation_mode

MAX_TTL_MINUTES = 24 * 60
DEFAULT_TTL_MINUTES = 60
ADMIN_TOKEN_ENV = "AIOPS_ADMIN_TOKEN"
ADMIN_TOKEN_HEADER = "X-AIOps-Admin-Token"


def admin_token_configured() -> bool:
    return bool((os.getenv(ADMIN_TOKEN_ENV) or "").strip())


def admin_token_matches(candidate: Optional[str]) -> bool:
    expected = (os.getenv(ADMIN_TOKEN_ENV) or "").strip()
    return bool(expected) and secrets.compare_digest(expected, (candidate or "").strip())


class RepairSettings:
    def __init__(self, path: Optional[Path] = None):
        self._path = Path(path) if path else audit_root() / "settings.json"
        self._lock = threading.Lock()
        self._override: Optional[Dict[str, Any]] = self._load()

    # ---- persistence -------------------------------------------------------
    def _load(self) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        override = data.get("override") if isinstance(data, dict) else None
        return override if isinstance(override, dict) and override.get("mode") else None

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps({"override": self._override}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass  # in-memory override still applies until restart

    def _live_override(self) -> Optional[Dict[str, Any]]:
        override = self._override
        if override and float(override.get("expires_at") or 0) <= time.time():
            self._override = None
            self._save()
            return None
        return override

    # ---- queries -----------------------------------------------------------
    def effective(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Mode, timeout and provenance the executor must use right now."""
        cfg = config if isinstance(config, dict) else {}
        config_mode = normalize_remediation_mode(cfg.get("mode"))
        try:
            config_timeout = int(cfg.get("approval_timeout_seconds", 600))
        except (TypeError, ValueError):
            config_timeout = 600
        with self._lock:
            override = self._live_override()
        result = {
            "enabled": bool(cfg.get("enabled", False)),
            "mode": config_mode,
            "config_mode": config_mode,
            "mode_source": "config",
            "approval_timeout_seconds": config_timeout,
            "override": None,
        }
        if override:
            result.update(
                mode=normalize_remediation_mode(override.get("mode")),
                mode_source="runtime",
                override={
                    k: override.get(k)
                    for k in ("mode", "reason", "changed_by", "changed_at", "expires_at")
                },
            )
            if override.get("approval_timeout_seconds"):
                result["approval_timeout_seconds"] = int(override["approval_timeout_seconds"])
        return result

    # ---- changes -----------------------------------------------------------
    def set_override(
        self,
        *,
        mode: str,
        reason: str,
        ttl_minutes: Optional[int],
        changed_by: str,
        config: Optional[Dict[str, Any]],
        approval_timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        wanted = str(mode or "").strip().lower()
        if wanted not in {"review", "auto"}:
            raise ValueError("mode 必须是 review 或 auto")
        ttl = int(ttl_minutes if ttl_minutes is not None else DEFAULT_TTL_MINUTES)
        if ttl < 1 or ttl > MAX_TTL_MINUTES:
            raise ValueError(f"ttl_minutes 必须在 1 到 {MAX_TTL_MINUTES} 之间")
        timeout = None
        if approval_timeout_seconds is not None:
            timeout = int(approval_timeout_seconds)
            if timeout < 10 or timeout > 3600:
                raise ValueError("approval_timeout_seconds 必须在 10 到 3600 之间")
        now = time.time()
        override = {
            "mode": wanted,
            "reason": str(reason or "").strip()[:300],
            "changed_by": str(changed_by or "").strip()[:100] or "admin",
            "changed_at": now,
            "expires_at": now + ttl * 60,
            "approval_timeout_seconds": timeout,
        }
        with self._lock:
            self._override = override
            self._save()
        audit_event(
            "mode_changed",
            mode=wanted,
            source="runtime",
            reason=override["reason"],
            changed_by=override["changed_by"],
            ttl_minutes=ttl,
            approval_timeout_seconds=timeout,
        )
        return self.effective(config)

    def clear_override(
        self, *, changed_by: str, config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        with self._lock:
            had = self._override is not None
            self._override = None
            self._save()
        if had:
            audit_event(
                "mode_changed",
                mode=normalize_remediation_mode((config or {}).get("mode")),
                source="config",
                reason="runtime override cleared",
                changed_by=str(changed_by or "admin")[:100],
            )
        return self.effective(config)


repair_settings = RepairSettings()
