"""Status-only recovery watch after repair commands have run.

"Command succeeded" is not "Pod recovered". After the executor has run the
approved commands it observes the target with read-only ``kubectl get`` calls
until the Pod state satisfies a generic recovery condition or the configured
timeout passes. The judgement uses only Pod status (phase, Ready, container
waiting reasons, restart count, deletion), never fault names, so it applies to
every scenario the same way. Timeouts are reported as such, with the last
observation, instead of being dressed up as success or failure.
"""

from __future__ import annotations

import json
import shlex
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional


@dataclass(frozen=True)
class RecoveryConfig:
    timeout_seconds: int = 180
    poll_seconds: int = 5
    settle_seconds: int = 20

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]]) -> Optional["RecoveryConfig"]:
        """``workflow.remediation.recovery``; ``None`` (or timeout 0) disables the watch."""
        raw = (config or {}).get("recovery") if isinstance(config, dict) else None
        if not isinstance(raw, dict):
            return None

        def number(key: str, default: int, low: int, high: int) -> int:
            try:
                value = int(raw.get(key, default))
            except (TypeError, ValueError):
                value = default
            return max(low, min(high, value))

        timeout = number("timeout_seconds", 180, 0, 3600)
        if timeout <= 0:
            return None
        return cls(
            timeout_seconds=timeout,
            poll_seconds=number("poll_seconds", 5, 1, 60),
            settle_seconds=number("settle_seconds", 20, 0, 600),
        )


def pod_snapshot(pod: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The handful of status facts the recovery judgement reads."""
    if not isinstance(pod, dict):
        return {"exists": False}
    status = pod.get("status") or {}
    metadata = pod.get("metadata") or {}
    ready = any(
        c.get("type") == "Ready" and str(c.get("status")) == "True"
        for c in status.get("conditions") or []
    )
    restarts = 0
    waiting: List[str] = []
    terminated: List[str] = []
    for container in list(status.get("containerStatuses") or []) + list(
        status.get("initContainerStatuses") or []
    ):
        restarts += int(container.get("restartCount") or 0)
        state = container.get("state") or {}
        if "waiting" in state:
            waiting.append(str((state["waiting"] or {}).get("reason") or "Waiting"))
        if "terminated" in state and str(status.get("phase")) not in {"Succeeded"}:
            terminated.append(str((state["terminated"] or {}).get("reason") or "Terminated"))
    return {
        "exists": True,
        "pod": metadata.get("name"),
        "uid": metadata.get("uid"),
        "phase": status.get("phase"),
        "ready": ready,
        "reason": status.get("reason") or (waiting[0] if waiting else None),
        "waiting_reasons": waiting,
        "terminated_reasons": terminated,
        "restarts": restarts,
        "deletion_timestamp": metadata.get("deletionTimestamp"),
    }


def judge(before: Dict[str, Any], now: Dict[str, Any], *, stable_seconds: float, settle_seconds: int):
    """``("recovered" | "pending", reason)`` from two snapshots and how long the good state held."""
    if before.get("deletion_timestamp") and not now.get("exists"):
        return "recovered", "原 Pod 已完成删除"
    if not now.get("exists"):
        return "pending", "目标 Pod 当前不存在，等待替代实例"
    if now.get("deletion_timestamp"):
        return "pending", "Pod 仍在删除中（deletionTimestamp 已设置）"
    if now.get("phase") == "Succeeded":
        return "recovered", "Pod 已成功完成（Succeeded）"
    if now.get("phase") != "Running":
        return "pending", f"phase={now.get('phase')}，原因 {now.get('reason') or '未知'}"
    if not now.get("ready"):
        return "pending", "Running 但 Ready=False" + (
            f"，容器 {','.join(now.get('waiting_reasons') or [])}" if now.get("waiting_reasons") else ""
        )
    if now.get("waiting_reasons"):
        return "pending", f"容器仍处于等待状态：{','.join(now['waiting_reasons'])}"
    if int(now.get("restarts") or 0) > int(before.get("restarts") or 0) and before.get("uid") == now.get("uid"):
        # Restarts after the repair on the same Pod: not stable yet; the clock restarts below.
        return "pending", f"修复后重启计数仍在增加（{before.get('restarts')}→{now.get('restarts')}）"
    if stable_seconds < settle_seconds:
        return "pending", f"Running/Ready 已保持 {int(stable_seconds)} 秒，需稳定 {settle_seconds} 秒"
    return "recovered", f"Running/Ready 且 {settle_seconds} 秒内无新增重启"


class RecoveryWatch:
    """Polls one or more repair targets with the executor's command runner."""

    def __init__(
        self,
        runner: Callable[[List[str]], str],
        config: RecoveryConfig,
        *,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.runner, self.config, self.clock, self.sleep = runner, config, clock, sleep

    # ---- observation -------------------------------------------------------
    def _get_json(self, argv: List[str]) -> Optional[Dict[str, Any]]:
        try:
            text = self.runner(argv)
        except Exception as exc:  # NotFound is a valid observation; other errors are unknown
            message = str(exc)
            if "NotFound" in message or "not found" in message:
                return None
            raise
        try:
            value = json.loads(text) if isinstance(text, str) else None
        except ValueError as exc:
            raise RuntimeError("kubectl 返回内容不是 JSON，无法判断恢复状态") from exc
        return value if isinstance(value, dict) else None

    def observe(self, target: Dict[str, Any]) -> Dict[str, Any]:
        namespace, pod = str(target.get("namespace") or ""), str(target.get("pod") or "")
        snapshot = pod_snapshot(
            self._get_json(shlex.split(f"kubectl get pod/{pod} -n {namespace} -o json"))
        )
        if snapshot.get("exists") and not snapshot.get("deletion_timestamp"):
            return snapshot
        replacement = self._replacement(target)
        if replacement is not None:
            replacement["replaced"] = pod
            return replacement
        return snapshot

    def _replacement(self, target: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Newest non-deleting Pod selected by the target's controller, if known."""
        kind, name = str(target.get("owner_kind") or "").lower(), str(target.get("owner_name") or "")
        namespace = str(target.get("namespace") or "")
        if not kind or not name:
            return None
        owner = self._get_json(shlex.split(f"kubectl get {kind}/{name} -n {namespace} -o json"))
        if not owner:
            return None
        labels = ((owner.get("spec") or {}).get("selector") or {}).get("matchLabels") or {}
        if not labels:
            return None
        selector = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        listing = self._get_json(shlex.split(f"kubectl get pods -n {namespace} -l {selector} -o json"))
        items = [
            item
            for item in (listing or {}).get("items") or []
            if not (item.get("metadata") or {}).get("deletionTimestamp")
            and (item.get("metadata") or {}).get("name") != target.get("pod")
        ]
        if not items:
            return None
        items.sort(key=lambda item: str((item.get("metadata") or {}).get("creationTimestamp") or ""))
        return pod_snapshot(items[-1])

    # ---- loop ----------------------------------------------------------------
    def run(self, targets: List[Dict[str, Any]], before: Dict[str, Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield ``remediation_recovery`` progress events; return the summary via StopIteration."""
        started = self.clock()
        deadline = started + self.config.timeout_seconds
        good_since: Dict[str, Optional[float]] = {t["group_id"]: None for t in targets}
        outcome: Dict[str, Dict[str, Any]] = {}
        pending = {t["group_id"]: t for t in targets}
        while pending:
            now = self.clock()
            for group_id, target in list(pending.items()):
                try:
                    observed = self.observe(target)
                except Exception as exc:
                    outcome[group_id] = {
                        "group_id": group_id,
                        "status": "needs_followup",
                        "reason": f"无法观测恢复状态：{str(exc)[:200]}",
                        "before": before.get(group_id),
                        "after": None,
                        "elapsed_seconds": int(now - started),
                        "timed_out": False,
                    }
                    pending.pop(group_id)
                    continue
                prior = before.get(group_id) or {}
                verdict, reason = judge(prior, observed, stable_seconds=0, settle_seconds=0)
                if verdict == "recovered" and observed.get("exists"):
                    # Running/Ready must hold for settle_seconds; the clock restarts on regression.
                    since = good_since[group_id]
                    if since is None:
                        since = good_since[group_id] = now
                    verdict, reason = judge(
                        prior,
                        observed,
                        stable_seconds=now - since,
                        settle_seconds=self.config.settle_seconds,
                    )
                    if verdict == "recovered" and observed.get("restarts", 0) > prior.get("restarts", 0) and prior.get("uid") == observed.get("uid"):
                        good_since[group_id] = now
                else:
                    good_since[group_id] = None
                yield {
                    "type": "remediation_recovery",
                    "group_id": group_id,
                    "observed": observed,
                    "verdict": verdict,
                    "reason": reason,
                    "elapsed_seconds": int(now - started),
                    "timeout_seconds": self.config.timeout_seconds,
                }
                if verdict == "recovered":
                    outcome[group_id] = {
                        "group_id": group_id,
                        "status": "recovered",
                        "reason": reason,
                        "before": prior,
                        "after": observed,
                        "elapsed_seconds": int(now - started),
                        "timed_out": False,
                    }
                    pending.pop(group_id)
                elif now >= deadline:
                    outcome[group_id] = {
                        "group_id": group_id,
                        "status": "not_recovered",
                        "reason": f"超时未恢复（{self.config.timeout_seconds} 秒）：{reason}",
                        "before": prior,
                        "after": observed,
                        "elapsed_seconds": int(now - started),
                        "timed_out": True,
                    }
                    pending.pop(group_id)
            if pending:
                self.sleep(self.config.poll_seconds)
        statuses = {item["status"] for item in outcome.values()}
        status = (
            "recovered"
            if statuses == {"recovered"}
            else "not_recovered"
            if "not_recovered" in statuses
            else "needs_followup"
        )
        return {
            "status": status,
            "targets": [outcome[t["group_id"]] for t in targets if t["group_id"] in outcome],
            "timeout_seconds": self.config.timeout_seconds,
            "settle_seconds": self.config.settle_seconds,
        }
