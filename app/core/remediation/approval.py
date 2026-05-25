"""In-memory human approval store for remediation interrupts."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reviewer: str = ""
    reason: str = ""
    decided_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class ApprovalRequest:
    run_id: str
    approval_id: str
    kind: str
    title: str
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)


class ApprovalStore:
    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._requests: Dict[Tuple[str, str], ApprovalRequest] = {}
        self._decisions: Dict[Tuple[str, str], ApprovalDecision] = {}

    def create_request(self, run_id: str, kind: str, title: str, payload: Dict[str, Any]) -> ApprovalRequest:
        approval_id = uuid.uuid4().hex[:12]
        request = ApprovalRequest(
            run_id=str(run_id),
            approval_id=approval_id,
            kind=str(kind),
            title=str(title),
            payload=dict(payload or {}),
        )
        with self._condition:
            self._requests[(request.run_id, request.approval_id)] = request
            self._condition.notify_all()
        return request

    def resolve(
        self,
        run_id: str,
        approval_id: str,
        approved: bool,
        reviewer: str = "",
        reason: str = "",
    ) -> bool:
        key = (str(run_id), str(approval_id))
        with self._condition:
            if key not in self._requests:
                return False
            self._decisions[key] = ApprovalDecision(
                approved=bool(approved),
                reviewer=str(reviewer or ""),
                reason=str(reason or ""),
            )
            self._condition.notify_all()
            return True

    def wait_for_decision(self, run_id: str, approval_id: str, timeout_seconds: float) -> Optional[ApprovalDecision]:
        key = (str(run_id), str(approval_id))
        deadline = time.time() + max(0.0, float(timeout_seconds))
        with self._condition:
            while key not in self._decisions:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._condition.wait(timeout=remaining)
            return self._decisions[key]


approval_store = ApprovalStore()

