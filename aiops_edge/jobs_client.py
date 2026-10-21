"""Center-side client for the edge runner's asynchronous jobs (spec FR-017).

Submission is idempotent (the key is fixed per run, action and stage), so it is
retried through tunnel errors. Once submitted, the job runs on the edge even if
the tunnel drops; we keep polling until a deadline. If the result cannot be
established by then, ``RemoteResultUnknown`` is raised - the command may have
taken effect, so it is never resubmitted.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from aiops_edge.clusters import Cluster
from aiops_edge.tunnel import EdgeError

TRANSIENT = {"cluster_unreachable", "timeout", "runner_error"}


class RemoteResultUnknown(RuntimeError):
    """The command was submitted but its outcome could not be confirmed."""


class RemoteJobs:
    def __init__(
        self,
        tunnel: Any,
        *,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        poll_seconds: float = 3.0,
    ) -> None:
        self.tunnel, self.clock, self.sleep, self.poll_seconds = tunnel, clock, sleep, poll_seconds

    @classmethod
    def from_config(cls) -> "RemoteJobs":
        from aiops_edge.clusters import load_config
        from aiops_edge.tunnel import TunnelClient

        return cls(TunnelClient.from_access(load_config().xnet))

    def reachable(self, cluster: Cluster) -> bool:
        try:
            self.tunnel.request(cluster, "/healthz", None, method="GET", timeout=5)
            return True
        except EdgeError:
            return False

    def _submit(self, cluster: Cluster, payload: Dict[str, Any], deadline: float) -> str:
        last = ""
        while True:
            try:
                return self.tunnel.request(cluster, "/v1/jobs", payload)["job_id"]
            except EdgeError as exc:
                if exc.code not in TRANSIENT:
                    rule = exc.detail.get("rule")
                    raise RuntimeError(
                        f"边缘 runner 拒绝执行：{exc.code}{f'（{rule}）' if rule else ''}：{exc.message}"
                    ) from None
                last = f"{exc.code}: {exc.message}"
            if self.clock() >= deadline:
                # Submission may have reached the runner before the tunnel failed.
                raise RemoteResultUnknown(
                    f"命令提交时与集群 {cluster.name} 的连接中断（{last}），无法确认是否已开始执行，结果未知；"
                    "请复查资源状态，不会自动重新提交"
                )
            self.sleep(self.poll_seconds)

    def run(
        self,
        cluster: Cluster,
        argv: List[str],
        *,
        key: str,
        approval_id: str = "",
        timeout_s: int = 60,
        deadline_s: float = 600,
    ) -> str:
        deadline = self.clock() + deadline_s
        payload = {
            "idempotency_key": key,
            "argv": list(argv),
            "approval_id": approval_id,
            "timeout_s": timeout_s,
        }
        job_id = self._submit(cluster, payload, deadline)
        last: Optional[str] = None
        while True:
            try:
                job = self.tunnel.request(cluster, f"/v1/jobs/{job_id}", None, method="GET")
            except EdgeError as exc:
                if exc.code == "not_found":
                    # The runner Pod was recreated and its job records went with it.
                    raise RemoteResultUnknown(
                        f"集群 {cluster.name} 上任务 {job_id} 的记录已不存在（runner 已重建），"
                        "命令可能已部分生效，结果未知；请复查资源状态，不会自动重新提交"
                    ) from None
                last = f"{exc.code}: {exc.message}"
                job = None
            if job is not None:
                status = job.get("status")
                if status == "succeeded":
                    return job.get("stdout") or ""
                if status == "failed":
                    raise RuntimeError(
                        (job.get("stderr") or job.get("stdout") or "kubectl failed")[:3000]
                    )
                if status == "unknown":
                    raise RemoteResultUnknown(
                        f"任务 {job_id} 结果未知：{(job.get('stderr') or '').strip()}；不会自动重新提交"
                    )
            if self.clock() >= deadline:
                raise RemoteResultUnknown(
                    f"命令已在集群 {cluster.name} 提交（任务 {job_id}），在时限内无法确认结果"
                    f"{f'（最后错误 {last}）' if last else ''}，结果未知；请复查资源状态，不会自动重新提交"
                )
            self.sleep(self.poll_seconds)
