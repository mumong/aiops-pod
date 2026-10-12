"""Owner-bound diagnosis/plan records on the existing reports volume.

The store transports evidence and exact plan versions; it never infers a repair.
Execution claims and supersession share a file lock, so an old approval cannot
start a command after a revision has been accepted.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


class RecordUnavailable(ValueError):
    pass


class PlanConflict(ValueError):
    pass


class RepairRecordStore:
    def __init__(self, root=None):
        self.root = Path(root or os.getenv("AIOPS_REPAIR_RECORD_ROOT") or
                         str(Path(os.getenv("REPORTS_DIR", "/tmp/aiops/reports")) / "repair_records"))

    @staticmethod
    def _owner(owner):
        if not owner:
            raise RecordUnavailable("修复记录需要有效的会话归属")
        return hashlib.sha256(owner.encode()).hexdigest()

    def _path(self, run_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", str(run_id)):
            raise RecordUnavailable("无效的诊断或方案记录标识")
        return self.root / f"{run_id}.json"

    @contextmanager
    def _locked(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".lock").open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _write(self, path, value):
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.root,
                                             prefix=".record-", delete=False) as handle:
                name = handle.name
                json.dump(value, handle, ensure_ascii=False, default=str)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)

    def _read(self, run_id, owner):
        try:
            value = json.loads(self._path(run_id).read_text())
        except (OSError, ValueError) as exc:
            raise RecordUnavailable("诊断或方案记录不存在或不可读取，请重新诊断") from exc
        if value.get("owner") != self._owner(owner):
            raise RecordUnavailable("诊断或方案记录不存在或不属于当前会话用户")
        return value

    def load(self, run_id, owner, kind=None):
        with self._locked():
            value = self._read(run_id, owner)
            if kind and value.get("kind") != kind:
                raise RecordUnavailable("引用记录类型不匹配")
            return self.public(value)

    @staticmethod
    def public(value):
        return deepcopy({k: v for k, v in value.items() if k != "owner"})

    def save(self, run_id, owner, session_id, kind, payload, *, source_run_id=None, previous_plan_id=None):
        if kind not in {"diagnosis", "plan", "repair_batch", "repair_job"}:
            raise ValueError("unsupported record kind")
        with self._locked():
            path = self._path(run_id)
            if path.exists():
                raise PlanConflict("运行记录已经存在，不能覆盖原诊断或方案")
            value = {"schema_version": 1, "run_id": run_id, "kind": kind,
                     "owner": self._owner(owner), "session_id": session_id,
                     "created_at": datetime.now(timezone.utc).isoformat(),
                     "source_run_id": source_run_id, "previous_plan_id": previous_plan_id,
                     "payload": deepcopy(payload), "execution_status": "ready" if kind == "plan" else None,
                     "execution_events": []}
            self._write(path, value)
            if session_id:
                key = hashlib.sha256((self._owner(owner) + ":" + session_id).encode()).hexdigest()
                self._write(self.root / f"session-{key}.json", {"run_id": run_id})
            return self.public(value)

    def latest(self, owner, session_id):
        key = hashlib.sha256((self._owner(owner) + ":" + session_id).encode()).hexdigest()
        try:
            pointer = json.loads((self.root / f"session-{key}.json").read_text())
        except (OSError, ValueError):
            return None
        return self.load(pointer["run_id"], owner)

    def update_payload(self, run_id, owner, update):
        """Atomic job metadata changes; immutable diagnosis/plan bodies stay intact."""
        with self._locked():
            value = self._read(run_id, owner)
            if value.get("kind") not in {"repair_batch", "repair_job"}:
                raise PlanConflict("诊断与方案正文不可覆盖")
            update(value["payload"])
            self._write(self._path(run_id), value)
            return self.public(value)

    def supersede(self, run_id, owner):
        with self._locked():
            value = self._read(run_id, owner)
            if value.get("kind") != "plan":
                raise RecordUnavailable("只能修改修复方案记录")
            if value.get("execution_status") == "executing":
                raise PlanConflict("原方案正在执行命令，请等待结果后再修改；已执行动作不会自动撤销")
            if value.get("execution_status") == "superseded":
                raise PlanConflict("原方案已被修改请求替代，请使用最新方案")
            prior = self.public(value)
            value["execution_status"] = "superseded"
            self._write(self._path(run_id), value)
            return prior

    def transition(self, run_id, owner, status, event=None):
        with self._locked():
            value = self._read(run_id, owner)
            if value.get("execution_status") == "superseded":
                return False
            value["execution_status"] = status
            if event:
                value["execution_events"].append(deepcopy(event))
            self._write(self._path(run_id), value)
            return True

    def current(self, run_id, owner):
        return self.load(run_id, owner)["execution_status"] != "superseded"


def diagnosis_payload(state, *, evidence_chars=64000):
    """Bounded, fair evidence projection; full results remain in their archives.

    Round-robin across groups prevents one large branch consuming the budget.
    Oversized bodies are explicitly marked, never presented as complete data.
    No fault names, expected diagnoses or mandatory tool sequence are used.
    """
    groups = [{"group_id": g.get("group_id"), "target": g.get("target"),
               "status": g.get("status"), "analysis": (g.get("material") or {}).get("analysis_draft"),
               "execution_incomplete": (g.get("material") or {}).get("execution_incomplete", []),
               "diagnosis_handoff": deepcopy(((g.get("material") or {}).get("protected_handoff") or {}).get("diagnosis_handoff")),
               "evidence": [], "omitted_results": 0}
              for g in state.get("autonomous_group_results") or []]
    by_id = {g["group_id"]: g for g in groups}
    shared = {"group_id": "shared", "evidence": [], "omitted_results": 0}
    queues = {g["group_id"]: [] for g in groups}
    queues["shared"] = []
    seen = set()
    for event in state.get("thinking_events") or []:
        if event.get("type") != "tool_result":
            continue
        ref = event.get("raw_ref")
        identity = ref or (event.get("lane_id"), event.get("tool_call_id"), event.get("tool_name"),
                           json.dumps(event.get("tool_args"), sort_keys=True, default=str))
        if identity in seen:
            continue
        seen.add(identity)
        gid = event.get("lane_id") if event.get("lane_id") in by_id else "shared"
        queues[gid].append(event)
    remaining = evidence_chars
    while any(queues.values()):
        for gid, queue in queues.items():
            if not queue:
                continue
            event = queue.pop(0)
            bucket = shared if gid == "shared" else by_id[gid]
            receipt = {k: event.get(k) for k in ("tool_name", "tool_args", "status", "semantic_success",
                                                 "timestamp", "raw_ref", "structured_ref")}
            body = event.get("result")
            text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, default=str)
            # Runbook text is reference guidance, not evidence; retain its address.
            cap = 0 if event.get("tool_name") == "fetch_runbook" else min(4000, max(0, remaining))
            receipt["result_excerpt"] = text[:cap]
            receipt["excerpt_truncated"] = len(text) > cap
            receipt["original_chars"] = len(text)
            remaining -= min(cap, len(text))
            if not cap and text:
                bucket["omitted_results"] += 1
            bucket["evidence"].append(receipt)
    return {"question": state.get("original_question") or state.get("question"),
            "diagnosis_handoff": deepcopy(state.get("diagnosis_handoff")),
            "request_contract": state.get("request_contract"),
            "report": state.get("conclusion"), "groups": groups, "shared_evidence": shared,
            "scope_note": "历史诊断及采样，不代表当前状态；摘录可能不完整，可按原文引用自主补读。",
            "excerpt_budget_chars": evidence_chars}
