"""Transport-independent repair workspaces. Ownership uses the existing cookie."""

import re
from typing import List, Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.core.remediation.audit import read_audit
from app.core.remediation.jobs import repair_jobs
from app.core.remediation.policy import CommandPolicy, check_command
from app.core.remediation.records import PlanConflict, RecordUnavailable
from app.core.remediation.settings import (
    ADMIN_TOKEN_HEADER,
    admin_token_configured,
    admin_token_matches,
    repair_settings,
)
from app.core.service import get_service


class StartRepair(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnosis_run_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    question: str = Field(
        default="基于该诊断生成本组修复方案，必要时自主核实证据和读取 Runbook。",
        min_length=1,
        max_length=8000,
    )


class RepairFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1)
    feedback: str = Field(min_length=1, max_length=8000)


class PolicyCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    commands: List[str] = Field(min_length=1, max_length=50)


class ModeOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = Field(pattern=r"^(review|auto)$")
    reason: str = Field(default="", max_length=300)
    ttl_minutes: Optional[int] = Field(default=None, ge=1, le=24 * 60)
    approval_timeout_seconds: Optional[int] = Field(default=None, ge=10, le=3600)
    changed_by: str = Field(default="", max_length=100)


def _remediation_config():
    service = get_service()
    workflow = getattr(service, "workflow_config", None) or {}
    cfg = workflow.get("remediation") if isinstance(workflow, dict) else None
    return cfg if isinstance(cfg, dict) else {}


def _policy_view():
    cfg = _remediation_config()
    effective = repair_settings.effective(cfg)
    return {
        **effective,
        "rules": CommandPolicy.from_config(cfg).summary(),
        "runtime_switch": {
            "available": admin_token_configured(),
            "header": ADMIN_TOKEN_HEADER,
            "note": "需要在 Secret 中配置 AIOPS_ADMIN_TOKEN；覆盖按 ttl_minutes 自动到期，回到配置值",
        },
    }


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
        return call(
            repair_jobs.start, get_service(), identity, body.diagnosis_run_id, body.question
        )

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
        return call(
            repair_jobs.revise, get_service(), identity, job_id, body.version, body.feedback
        )

    @app.post("/repair/jobs/{job_id}/cancel")
    def cancel(request: Request, job_id: str):
        return call(repair_jobs.cancel, job_id, owner(request))

    # ---- safety controls: visible to reviewers and acceptance testers ---------
    def admin(request):
        if not admin_token_configured():
            raise HTTPException(403, "运行时开关未启用：请在 Secret 中配置 AIOPS_ADMIN_TOKEN")
        if not admin_token_matches(request.headers.get(ADMIN_TOKEN_HEADER)):
            raise HTTPException(403, "管理员令牌无效")

    @app.get("/repair/policy")
    def policy(request: Request):
        return _policy_view()

    @app.post("/repair/policy/check")
    def policy_check(request: Request, body: PolicyCheck):
        """Dry evaluation only: nothing is executed, nothing is recorded as a plan."""
        policy = CommandPolicy.from_config(_remediation_config())
        return {
            "results": [check_command(command, policy).as_dict() for command in body.commands],
            "mode": repair_settings.effective(_remediation_config())["mode"],
        }

    @app.put("/repair/policy/mode")
    def policy_mode(request: Request, body: ModeOverride):
        admin(request)
        try:
            return repair_settings.set_override(
                mode=body.mode,
                reason=body.reason,
                ttl_minutes=body.ttl_minutes,
                changed_by=body.changed_by or request.client.host
                if request.client
                else body.changed_by,
                config=_remediation_config(),
                approval_timeout_seconds=body.approval_timeout_seconds,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.delete("/repair/policy/mode")
    def policy_mode_clear(request: Request):
        admin(request)
        return repair_settings.clear_override(
            changed_by=request.client.host if request.client else "admin",
            config=_remediation_config(),
        )

    @app.get("/repair/audit")
    def audit(request: Request, limit: int = 100, kind: Optional[str] = None):
        if not admin_token_matches(request.headers.get(ADMIN_TOKEN_HEADER)):
            # A diagnosis session owner may read the trail too; anonymous callers may not.
            owner(request)
        return {"events": read_audit(limit=max(1, min(int(limit), 1000)), kind=kind)}
