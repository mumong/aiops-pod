"""Local artifact archive for workflow context.

Large raw tool outputs should live on disk and be referenced from workflow
state. This keeps LangGraph state and downstream prompts small.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_ARCHIVE_ROOT = "/tmp/aiops/context_archives"
REPORTS_ARCHIVE_ROOT = "/tmp/aiops/reports/context_archives"


def get_archive_root() -> str:
    configured = os.getenv("AIOPS_CONTEXT_ARCHIVE_ROOT", "").strip()
    if configured:
        return configured

    default_parent = Path(DEFAULT_ARCHIVE_ROOT).parent
    if default_parent.exists() and os.access(default_parent, os.W_OK):
        return DEFAULT_ARCHIVE_ROOT

    reports_parent = Path(REPORTS_ARCHIVE_ROOT).parent
    if reports_parent.exists() and os.access(reports_parent, os.W_OK):
        return REPORTS_ARCHIVE_ROOT

    return DEFAULT_ARCHIVE_ROOT


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip() or "unknown")
    return safe[:120] or "unknown"


class ContextArchive:
    """Writes raw, structured, and summary artifacts for a single run."""

    def __init__(self, run_id: str, root: Optional[str] = None):
        self.run_id = _safe_name(run_id or "unknown-run")
        self.root = Path(root or get_archive_root()) / self.run_id

    def write_text(self, relative_path: str, content: str) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or "", encoding="utf-8")
        return str(path)

    def write_json(self, relative_path: str, data: Any) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return str(path)

    def write_json_atomic(self, relative_path: str, data: Any) -> Dict[str, Any]:
        """Durably replace a JSON artifact and return its integrity metadata."""
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            default=str,
        ).encode("utf-8")
        temporary_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=path.parent,
                delete=False,
            ) as handle:
                temporary_path = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
            temporary_path = None
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary_path:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass
        return {
            "path": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }

    def write_layer_artifacts(self, full_analysis: str, handoff: Dict[str, Any]) -> Dict[str, str]:
        full_ref = self.write_text("layer/full_analysis.md", full_analysis or "")
        handoff = dict(handoff or {})
        handoff.setdefault("archive_ref", full_ref)
        handoff_ref = self.write_json("layer/handoff.json", handoff)
        return {"full_analysis_ref": full_ref, "handoff_ref": handoff_ref}

    def write_budget(self, node_id: str, budget: Dict[str, Any]) -> str:
        return self.write_json(f"budget/{_safe_name(node_id)}.json", budget)

    def write_node_artifacts(
        self,
        node_id: str,
        input_payload: Optional[Dict[str, Any]] = None,
        output_payload: Optional[Dict[str, Any]] = None,
        handoff_payload: Optional[Dict[str, Any]] = None,
        next_node_id: Optional[str] = None,
    ) -> Dict[str, str]:
        safe_node = _safe_name(node_id)
        refs: Dict[str, str] = {}
        if input_payload is not None:
            refs["input_ref"] = self.write_json(f"node_inputs/{safe_node}.input.json", input_payload)
        if output_payload is not None:
            refs["output_ref"] = self.write_json(f"node_outputs/{safe_node}.output.json", output_payload)
        if handoff_payload is not None:
            target = _safe_name(next_node_id or _next_node_name(node_id))
            refs["handoff_ref"] = self.write_json(f"handoff/{safe_node}-to-{target}.json", handoff_payload)
        return refs

    def write_tool_artifact(
        self,
        node_id: str,
        sequence: int,
        tool_name: str,
        raw: str,
        structured: Optional[Dict[str, Any]] = None,
        summary: str = "",
    ) -> Dict[str, str]:
        prefix = f"{sequence:03d}-{_safe_name(node_id)}-{_safe_name(tool_name)}"
        raw_ref = self.write_text(f"tools/{prefix}.raw.txt", raw or "")
        structured_ref = self.write_json(f"tools/{prefix}.structured.json", structured or {})
        summary_ref = self.write_text(f"tools/{prefix}.summary.txt", summary or "")
        return {
            "raw_ref": raw_ref,
            "structured_ref": structured_ref,
            "summary_ref": summary_ref,
        }


def _next_node_name(node_id: str) -> str:
    order = ["layer", "evidence", "rca", "conclusion"]
    try:
        idx = order.index(str(node_id))
    except ValueError:
        return "next"
    return order[idx + 1] if idx + 1 < len(order) else "final"
