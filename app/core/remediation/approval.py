"""In-memory human approval store for remediation interrupts."""

from __future__ import annotations

import secrets
import threading
import time
import uuid
from copy import deepcopy
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
    expires_at: float = 0.0
    owner: str = ""


class ApprovalStore:
    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._requests: Dict[Tuple[str, str], ApprovalRequest] = {}
        self._decisions: Dict[Tuple[str, str], ApprovalDecision] = {}
        self._closed: set[Tuple[str, str]] = set()

    def create_request(self, run_id: str, kind: str, title: str, payload: Dict[str, Any],
                       timeout_seconds: float = 600, owner: str = "") -> ApprovalRequest:
        approval_id = uuid.uuid4().hex[:12]
        request = ApprovalRequest(
            run_id=str(run_id),
            approval_id=approval_id,
            kind=str(kind),
            title=str(title),
            payload=deepcopy(payload or {}),
            expires_at=time.time() + max(0.0, float(timeout_seconds)),
            owner=owner,
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
        owner: str = "",
    ) -> bool:
        key = (str(run_id), str(approval_id))
        with self._condition:
            if key not in self._requests or key in self._closed or key in self._decisions:
                return False
            if self._requests[key].owner and not secrets.compare_digest(self._requests[key].owner, owner):
                return False
            if time.time() >= self._requests[key].expires_at:
                self._closed.add(key)
                return False
            self._decisions[key] = ApprovalDecision(
                approved=bool(approved),
                reviewer=str(reviewer or ""),
                reason=str(reason or ""),
            )
            self._condition.notify_all()
            return True

    def decision_status(self, run_id: str, approval_id: str, owner: str = "") -> str:
        """Read-only acknowledgement; never consumes or repeats a decision."""
        key = (run_id, approval_id)
        with self._condition:
            request = self._requests.get(key)
            if not request or (request.owner and not secrets.compare_digest(request.owner, owner)):
                return 'unavailable'
            decision = self._decisions.get(key)
            if decision is not None:
                return 'approved' if decision.approved else 'rejected'
            if time.time() >= request.expires_at:
                return 'expired'
            return 'unavailable' if key in self._closed else 'pending'

    def poll_decision(self, run_id: str, approval_id: str) -> Optional[ApprovalDecision]:
        key = (run_id, approval_id)
        with self._condition:
            if key in self._closed or key not in self._requests:
                return None
            decision = self._decisions.get(key)
            if decision is not None:
                self._closed.add(key)
            return decision

    def close(self, run_id: str, approval_id: str) -> None:
        with self._condition:
            self._closed.add((run_id, approval_id))
            self._condition.notify_all()

    def wait_for_decision(self, run_id: str, approval_id: str, timeout_seconds: float) -> Optional[ApprovalDecision]:
        key = (str(run_id), str(approval_id))
        deadline = time.time() + max(0.0, float(timeout_seconds))
        with self._condition:
            if key not in self._requests or key in self._closed:
                return None
            deadline = min(deadline, self._requests[key].expires_at)
            while key not in self._decisions:
                remaining = deadline - time.time()
                if remaining <= 0:
                    self._closed.add(key)
                    return None
                self._condition.wait(timeout=remaining)
                if key in self._closed:
                    return None
            self._closed.add(key)
            return self._decisions[key]


approval_store = ApprovalStore()
