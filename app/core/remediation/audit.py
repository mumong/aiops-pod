"""Append-only audit trail for repair safety events.

One JSON line per event under the repair record root (``audit.jsonl``): command
denials, approval decisions, executed commands and mode changes. Derived data for
reviewers and acceptance tests; a write failure never affects the repair itself.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
_lock = threading.Lock()

EVENT_KINDS = ("command_denied", "approval_decided", "command_executed", "mode_changed")


def audit_root() -> Path:
    return Path(
        os.getenv("AIOPS_REPAIR_RECORD_ROOT")
        or str(Path(os.getenv("REPORTS_DIR", "/tmp/aiops/reports")) / "repair_records")
    )


def audit_path() -> Path:
    return audit_root() / "audit.jsonl"


def audit_event(kind: str, **fields: Any) -> Optional[Dict[str, Any]]:
    """Record one event; returns the record or ``None`` when writing failed."""
    record: Dict[str, Any] = {"ts": time.time(), "kind": kind}
    for key, value in fields.items():
        if value is None:
            continue
        text = value if isinstance(value, (int, float, bool, dict, list)) else str(value)
        if isinstance(text, str) and len(text) > 600:
            text = text[:600] + "…"
        record[key] = text
    try:
        path = audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str)
        with _lock, path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return record
    except Exception as exc:  # derived data only
        logger.warning("repair audit write failed: %s", exc)
        return None


def read_audit(limit: int = 200, kind: Optional[str] = None) -> List[Dict[str, Any]]:
    """Latest events first; bounded for the API."""
    try:
        lines = audit_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: List[Dict[str, Any]] = []
    for line in reversed(lines):
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if kind and item.get("kind") != kind:
            continue
        out.append(item)
        if len(out) >= max(1, int(limit)):
            break
    return out
