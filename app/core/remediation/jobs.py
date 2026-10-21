"""Owner-bound grouped repair jobs, independent of the browser transport.

Reuse diagnosis groups, workflow planning and the existing execution policy.
Only planning is parallel; command invocations share a serial execution lock.
Records survive restart; active jobs are not replayed automatically after restart.
"""

import hashlib
import threading
import time
import uuid
from copy import deepcopy

from app.core.log_context import log_context
from app.core.remediation.group_context import repairable_groups
from app.core.remediation.progress import PlanningProgress
from app.core.remediation.records import PlanConflict, RecordUnavailable, RepairRecordStore
from app.core.workflow.group_runner import iter_group_results, resolve_lane_workers

# Job statuses that can still change; anything else is a final outcome.
ACTIVE_JOB_STATUSES = frozenset(
    {"queued", "planning", "planned", "awaiting_approval", "executing", "verifying"}
)


class RepairJobs:
    def __init__(self, store=None):
        self.store = store or RepairRecordStore()
        self.instance = uuid.uuid4().hex
        self.lock = threading.RLock()
        self.cancellations = {}

    def _update(self, job_id, owner, **fields):
        if "status" in fields:
            fields["status_started_at"] = time.time()
        return self.store.update_payload("job-" + job_id, owner, lambda p: p.update(fields))[
            "payload"
        ]

    def _new_job(
        self, batch_id, owner, diagnosis_id, group, *, version=1, previous=None, feedback=None
    ):
        job_id = uuid.uuid4().hex[:16]
        payload = {
            "job_id": job_id,
            "batch_id": batch_id,
            "group_id": group["group_id"],
            "target": group.get("target"),
            "diagnosis_run_id": diagnosis_id,
            "version": version,
            "previous_plan_id": previous,
            "status": "queued",
            "instance": self.instance,
            "events": [],
            "approval": None,
            "error": None,
            "created_at": time.time(),
            "status_started_at": time.time(),
            "feedback": feedback,
            "previous_job_id": group.get("job_id"),
            "diagnosis_summary": group.get("summary"),
        }
        self.store.save("job-" + job_id, owner, None, "repair_job", payload)
        self.cancellations[job_id] = threading.Event()
        return payload

    def start(self, service, owner, diagnosis_id, question, group_ids=None):
        """One durable batch per (diagnosis, selected groups); retries return the same batch.

        Only groups whose RCA left something unresolved get a job; a healthy diagnosis
        is refused instead of planning repairs for nothing. ``group_ids`` narrows the
        batch (a chat request naming one Pod must not plan, or auto-execute, the rest).
        """
        source = self.store.load(diagnosis_id, owner, "diagnosis")
        groups = repairable_groups(source)
        if group_ids is not None:
            wanted = set(group_ids)
            groups = [g for g in groups if g["group_id"] in wanted]
        if not groups:
            raise PlanConflict("该诊断未发现需要修复的异常组，无需生成修复方案")
        # One durable workspace per diagnosis: retries must not launch writes twice.
        batch_id = "batch-" + diagnosis_id
        if group_ids is not None and len(groups) < len(repairable_groups(source)):
            batch_id += (
                "-"
                + hashlib.sha1(
                    ",".join(sorted(g["group_id"] for g in groups)).encode()
                ).hexdigest()[:8]
            )
        with self.lock:
            try:
                return self.batch(batch_id, owner)
            except RecordUnavailable:
                pass
            jobs = [self._new_job(batch_id, owner, diagnosis_id, group) for group in groups]
            self.store.save(
                batch_id,
                owner,
                None,
                "repair_batch",
                {
                    "batch_id": batch_id,
                    "diagnosis_run_id": diagnosis_id,
                    "jobs": [job["job_id"] for job in jobs],
                },
            )
        threading.Thread(
            target=self._plan_batch, args=(service, owner, jobs, question), daemon=True
        ).start()
        return self.batch(batch_id, owner)

    def _plan_batch(self, service, owner, jobs, question):
        # Same limit as the diagnosis lanes (workflow.evidence.parallel.max_workers).
        parallel = ((getattr(service, "workflow_config", None) or {}).get("evidence") or {}).get(
            "parallel"
        ) or {}
        workers = resolve_lane_workers(parallel.get("max_workers"))
        for job, result, error in iter_group_results(
            jobs, lambda item: self._plan(service, owner, item, question), max_workers=workers
        ):
            if error:
                self._update(
                    job["job_id"],
                    owner,
                    status="failed",
                    error="修复规划任务失败，请根据运行 ID 检查日志。",
                )
                import logging

                logging.getLogger(__name__).error("repair job %s failed: %s", job["job_id"], error)
                self.cancellations.pop(job["job_id"], None)
            elif result:
                threading.Thread(
                    target=self._execute, args=(service, owner, job), daemon=True
                ).start()
            else:
                self.cancellations.pop(job["job_id"], None)

    def _plan(self, service, owner, job, question):
        from app.core.workflow.executor import WorkflowExecutor

        self._update(job["job_id"], owner, status="planning")
        executor = WorkflowExecutor(holmes_service=service)
        executor.ai_call = service._build_request_scoped_ai_call()
        executor.mcp_tools = service.mcp_tools or []
        overrides = {
            "query_mode": "auto",
            "_query_session_key": (owner, "repair-" + job["job_id"]),
            "_repair_group_id": job["group_id"],
            "_defer_repair_execution": True,
            "_diagnosis_run_id": job["diagnosis_run_id"],
        }
        if job.get("previous_plan_id"):
            overrides.pop("_diagnosis_run_id")
            overrides.update(_plan_run_id=job["previous_plan_id"], _repair_revision_claimed=True)
        final = None
        progress = PlanningProgress()
        for event in executor.execute_stream(
            question, job["job_id"], self.cancellations[job["job_id"]], overrides
        ):
            if progress.add(event):
                self._update(job["job_id"], owner, planning_progress=progress.snapshot())
            if event.get("type") == "final":
                final = event
            elif event.get("type") == "error":
                self._update(
                    job["job_id"],
                    owner,
                    status="failed",
                    approval=None,
                    error=event.get("error") or "修复规划失败，本次运行已终止。",
                )
                return False
            elif event.get("type") in {"node_start", "node_complete"}:
                self._update(job["job_id"], owner, stage=event.get("node_name"))
        self._update(job["job_id"], owner, planning_progress=progress.snapshot(final=True))
        if self.cancellations[job["job_id"]].is_set():
            self._update(job["job_id"], owner, status="cancelled")
            return False
        if not final or not final.get("repair_record") or not final.get("repair_plan"):
            raise RuntimeError("no persisted structured repair plan")
        failure = final["repair_plan"].get("planning_error")
        if failure:
            self._update(
                job["job_id"],
                owner,
                status="failed",
                approval=None,
                error=failure["message"],
                error_code=failure["code"],
            )
            return False
        self._update(job["job_id"], owner, status="planned")
        return True

    def _execute(self, service, owner, job):
        with log_context(run=job["job_id"]):
            return self._execute_in_context(service, owner, job)

    def _execute_in_context(self, service, owner, job):
        from app.core.remediation.pod_executor import PodRepairExecutor, run_argv
        from app.core.remediation.policy import CommandPolicy
        from app.core.remediation.recovery import RecoveryConfig
        from app.core.remediation.settings import repair_settings

        job_id = job["job_id"]
        try:
            cfg = deepcopy((service.workflow_config or {}).get("remediation") or {})
            # Config baseline + TTL-bound runtime override, decided once per job and recorded.
            effective = repair_settings.effective(cfg)
            self._update(
                job_id, owner, mode=effective["mode"], mode_source=effective["mode_source"]
            )
            if not effective["enabled"]:
                self._update(job_id, owner, status="execution_disabled")
                return
            record = self.store.load(job_id, owner, "plan")

            def runner(args, cluster=None):
                if self.cancellations[job_id].is_set() or not self.store.current(job_id, owner):
                    raise RuntimeError("任务已取消或方案已替代，未执行命令")
                # Single-cluster calls stay exactly as before.
                return run_argv(args, cluster=cluster) if cluster else run_argv(args)

            for event in PodRepairExecutor(runner=runner).run(
                job_id,
                record["payload"].get("draft"),
                owner=owner,
                mode=effective["mode"],
                timeout=int(effective["approval_timeout_seconds"]),
                cancel=self.cancellations[job_id],
                policy=CommandPolicy.from_config(cfg),
                request_contract=record["payload"].get("request_contract"),
                record_store=self.store,
                recovery=RecoveryConfig.from_config(cfg),
                max_duration=int(cfg.get("max_duration_seconds") or 0),
            ):
                kind = event.get("type")
                if kind == "remediation_approval_required":
                    self._update(job_id, owner, status="awaiting_approval", approval=event)
                elif kind == "remediation_recovery":

                    def observe(payload, event=event):
                        if payload.get("status") != "verifying":
                            payload["status_started_at"] = time.time()
                        payload.update(status="verifying", approval=None, recovery=event)

                    self.store.update_payload("job-" + job_id, owner, observe)
                elif kind in {"remediation_tool_start", "remediation_tool_result"}:

                    def append(payload, event=event):
                        if payload.get("status") != "executing":
                            payload["status_started_at"] = time.time()
                        payload.update(status="executing", approval=None)
                        payload["events"].append(event)

                    self.store.update_payload("job-" + job_id, owner, append)
                elif kind == "remediation_status":
                    # e.g. multi-cluster: target cluster unreachable, waiting before executing
                    self._update(job_id, owner, status_note=event.get("message") or "")
                elif kind == "remediation_finished":
                    self._update(
                        job_id, owner, status=event["status"], approval=None, result=event
                    )
        except Exception:
            import logging

            logging.getLogger(__name__).exception("repair execution job %s failed", job_id)
            self._update(
                job_id,
                owner,
                status="failed",
                approval=None,
                error="修复执行任务失败，请检查记录和当前资源状态。",
            )
        finally:
            self.cancellations.pop(job_id, None)

    def detail(self, job_id, owner, *, include_history=True):
        job = self.store.load("job-" + job_id, owner, "repair_job")["payload"]
        if job["instance"] != self.instance and job["status"] in {
            "queued",
            "planning",
            "planned",
            "awaiting_approval",
            "executing",
            "verifying",
        }:
            job.update(
                status="interrupted",
                approval=None,
                error="服务已重启，任务未自动重放；请核实当前状态后修改方案或重新规划。",
            )
        try:
            plan = self.store.load(job_id, owner, "plan")
            job["plan"] = plan["payload"].get("draft")
            if plan["execution_status"] == "superseded":
                job.update(status="superseded", approval=None)
        except RecordUnavailable:
            job["plan"] = None
        job.pop("instance", None)
        job["server_time"] = time.time()
        if job.get("approval"):
            from app.core.remediation.approval import approval_store

            job["approval"]["decision_status"] = approval_store.decision_status(
                job_id, job["approval"]["approval_id"], owner
            )
        history, previous, seen = (
            [],
            job.get("previous_job_id") or job.get("previous_plan_id"),
            {job_id},
        )
        while include_history and previous and previous not in seen:
            seen.add(previous)
            try:
                prior = self.store.load("job-" + previous, owner, "repair_job")["payload"]
            except RecordUnavailable:
                break
            if prior.get("group_id") != job.get("group_id") or prior.get("batch_id") != job.get(
                "batch_id"
            ):
                break
            entry = {k: prior.get(k) for k in ("job_id", "version", "feedback", "status")}
            try:
                entry["plan"] = self.store.load(previous, owner, "plan")["payload"].get("draft")
            except RecordUnavailable:
                entry["plan"] = None
            history.append(entry)
            previous = prior.get("previous_job_id") or prior.get("previous_plan_id")
        job["history"] = list(reversed(history))
        return job

    def batch(self, batch_id, owner):
        batch = self.store.load(batch_id, owner, "repair_batch")["payload"]
        batch["groups"] = []
        for job_id in batch.pop("jobs"):
            job = self.detail(job_id, owner, include_history=False)
            batch["groups"].append(
                {
                    k: job.get(k)
                    for k in (
                        "job_id",
                        "group_id",
                        "version",
                        "target",
                        "status",
                        "stage",
                        "error",
                        "mode",
                        "mode_source",
                        "diagnosis_summary",
                    )
                }
            )
            # API clients approve with this id (POST /repair/jobs/{job_id}/approve).
            batch["groups"][-1]["pending_approval_id"] = (job.get("approval") or {}).get(
                "approval_id"
            )
        return batch

    def revise(self, service, owner, job_id, version, feedback):
        with self.lock:
            old = self.detail(job_id, owner)
            if old["version"] != version:
                raise PlanConflict("方案版本已变化，请刷新后修改")
            # This atomic claim competes with execution; no model routing involved.
            if old.get("plan"):
                self.store.supersede(job_id, owner)
            elif old["status"] not in {"failed", "interrupted", "cancelled"}:
                raise PlanConflict("方案仍在生成，请等待完成或停止后再修改")
            batch = self.store.load(old["batch_id"], owner, "repair_batch")["payload"]
            if job_id not in batch["jobs"]:
                raise PlanConflict("方案已被替代，请刷新后修改")
            if job_id in self.cancellations:
                self.cancellations[job_id].set()
            new = self._new_job(
                old["batch_id"],
                owner,
                old["diagnosis_run_id"],
                old,
                version=version + 1,
                previous=job_id if old.get("plan") else None,
                feedback={
                    "role": "user",
                    "text": feedback,
                    "source_job_id": job_id,
                    "source_version": version,
                    "target_version": version + 1,
                    "submitted_at": time.time(),
                },
            )

            def replace(payload):
                payload["jobs"] = [
                    new["job_id"] if value == job_id else value for value in payload["jobs"]
                ]

            self.store.update_payload(old["batch_id"], owner, replace)
        threading.Thread(
            target=self._plan_batch, args=(service, owner, [new], feedback), daemon=True
        ).start()
        return {"job_id": new["job_id"], "group_id": new["group_id"], "version": new["version"]}

    def cancel(self, job_id, owner):
        job = self.detail(job_id, owner)
        event = self.cancellations.get(job_id)
        if event:
            event.set()
        return {
            "job_id": job_id,
            "status": job["status"],
            "message": "已请求停止后续操作；正在执行的命令可能已经生效，不会自动回滚。",
        }


repair_jobs = RepairJobs()
