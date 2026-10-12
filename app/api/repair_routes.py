"""Transport-independent repair workspaces. Ownership uses the existing cookie."""
import re

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.core.remediation.jobs import repair_jobs
from app.core.remediation.records import RecordUnavailable, PlanConflict
from app.core.service import get_service


class StartRepair(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnosis_run_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    question: str = Field(default="基于该诊断生成本组修复方案，必要时自主核实证据和读取 Runbook。", min_length=1, max_length=8000)


class RepairFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1)
    feedback: str = Field(min_length=1, max_length=8000)


def register_repair_routes(app):
    def owner(request):
        value = request.cookies.get("aiops_query_owner", "")
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            raise HTTPException(401, "请使用原诊断会话的身份访问修复记录")
        return value

    def call(fn, *args):
        try:
            return fn(*args)
        except RecordUnavailable as exc:
            raise HTTPException(404, str(exc)) from exc
        except PlanConflict as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/repair/batches")
    def start(request: Request, body: StartRepair):
        identity = owner(request)
        return call(repair_jobs.start, get_service(), identity, body.diagnosis_run_id, body.question)

    @app.get("/repair/batches/{batch_id}")
    def batch(request: Request, batch_id: str):
        return call(repair_jobs.batch, batch_id, owner(request))

    @app.get("/repair/jobs/{job_id}")
    def detail(request: Request, job_id: str):
        return call(repair_jobs.detail, job_id, owner(request))

    @app.post("/repair/jobs/{job_id}/feedback")
    def feedback(request: Request, job_id: str, body: RepairFeedback):
        identity = owner(request)
        if not body.feedback.strip():
            raise HTTPException(422, "反馈内容不能为空")
        return call(repair_jobs.revise, get_service(), identity, job_id, body.version, body.feedback)

    @app.post("/repair/jobs/{job_id}/cancel")
    def cancel(request: Request, job_id: str):
        return call(repair_jobs.cancel, job_id, owner(request))
