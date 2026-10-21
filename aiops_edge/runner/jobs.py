"""Asynchronous repair jobs on the edge runner (contracts/runner-api.md).

A job is created once per idempotency key and never run twice under the same
key. Records live in memory and in the state directory (emptyDir), so a
container restart keeps them; a job that was still running when the runner
went away is reported as ``unknown`` - its command may or may not have taken
effect, and saying "failed" or "succeeded" would be a guess.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

RETENTION_SECONDS = 24 * 3600


class JobStore:
    def __init__(self, directory: str) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._keys: Dict[str, str] = {}
        self._load()

    def _path(self, job_id: str) -> Path:
        return self.dir / f"{job_id}.json"

    def _save(self, job: Dict[str, Any]) -> None:
        tmp = self._path(job["job_id"]).with_suffix(".tmp")
        tmp.write_text(json.dumps(job, ensure_ascii=False))
        os.replace(tmp, self._path(job["job_id"]))

    def _load(self) -> None:
        now = time.time()
        for path in self.dir.glob("*.json"):
            try:
                job = json.loads(path.read_text())
            except (OSError, ValueError):
                continue
            if now - float(job.get("created_at") or now) > RETENTION_SECONDS:
                path.unlink(missing_ok=True)
                continue
            if job.get("status") == "running":
                job.update(
                    status="unknown",
                    stderr=(job.get("stderr") or "")
                    + "runner 在任务执行期间重启，命令可能已部分生效，结果未知，请复查资源状态\n",
                    finished_at=now,
                )
                self._save(job)
            self._jobs[job["job_id"]] = job
            self._keys[job["idempotency_key"]] = job["job_id"]

    def by_key(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job_id = self._keys.get(key)
            return dict(self._jobs[job_id]) if job_id else None

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def create(self, key: str, argv: List[str], approval_id: str) -> Dict[str, Any]:
        """New running job, or the existing one for this key (``created`` tells which)."""
        with self._lock:
            existing = self._keys.get(key)
            if existing:
                return {**self._jobs[existing], "created": False}
            job = {
                "job_id": uuid.uuid4().hex[:16],
                "idempotency_key": key,
                "argv": argv,
                "approval_id": approval_id,
                "status": "running",
                "created_at": time.time(),
                "stdout": "",
                "stderr": "",
            }
            self._jobs[job["job_id"]] = job
            self._keys[key] = job["job_id"]
            self._save(job)
            return {**job, "created": True}

    def finish(self, job_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.update(result)
            job["status"] = "succeeded" if int(result.get("exit_code") or 0) == 0 else "failed"
            job["finished_at"] = time.time()
            self._save(job)
