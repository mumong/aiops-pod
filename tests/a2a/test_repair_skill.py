"""A2A repair skill: per-group plans, input-required approval, resume in the same task."""

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

pytest.importorskip(
    "a2a",
    reason="A2A tests run in the isolated requirements/a2a-dev.txt environment",
)

from a2a_adapter.app import create_app
from a2a_adapter.backend import BackendEvent
from a2a_adapter.config import AdapterSettings


class RepairBackend:
    """Backend double for /ask repair=plan, batch events, job detail and approval."""

    def __init__(self):
        self.settings = SimpleNamespace(backend_api_token="tok-a2a")
        self.calls, self.approvals = [], []
        self.status = "awaiting_approval"
        self.plans_a_batch = True  # the backend decided this request is a repair
        self.stale_snapshot = False

    async def health(self):
        return {"status": "healthy"}

    async def stream(
        self,
        question,
        *,
        mode,
        cancel_event,
        session_id=None,
        repair_plan=False,
        repair_on_request=False,
    ):
        self.calls.append(
            {
                "question": question,
                "mode": mode,
                "session_id": session_id,
                "repair_plan": repair_plan,
                "repair_on_request": repair_on_request,
            }
        )
        yield BackendEvent("run_start", {"run_id": "diag-1"})
        final = {"answer": "# 诊断\n\n异常组 1：探针端口错误"}
        if self.plans_a_batch:
            final["repair_batch"] = {"batch_id": "batch-diag-1", "diagnosis_run_id": "diag-1"}
        yield BackendEvent("final", final)

    def _groups(self):
        return [
            {
                "job_id": "job-1",
                "group_id": "g1",
                "status": self.status,
                "pending_approval_id": "appr-123456"
                if self.status == "awaiting_approval"
                else None,
            }
        ]

    async def batch_events(self, batch_id, cancel_event):
        if self.stale_snapshot and self.approvals:
            # Right after an approval the backend can still list it as pending.
            yield {
                "batch_id": batch_id,
                "groups": [
                    {
                        "job_id": "job-1",
                        "group_id": "g1",
                        "status": "awaiting_approval",
                        "pending_approval_id": "appr-123456",
                    }
                ],
            }
        yield {"batch_id": batch_id, "groups": self._groups()}

    async def batch(self, batch_id):
        return {"batch_id": batch_id, "groups": self._groups()}

    async def job(self, job_id):
        if self.status == "awaiting_approval":
            return {
                "job_id": job_id,
                "status": self.status,
                "approval": {
                    "approval_id": "appr-123456",
                    "expires_at": 1.0,
                    "payload": {
                        "description": "修正 readinessProbe 端口",
                        "risk": "low",
                        "execute_command": "kubectl patch deployment workload -n ns -p '{}'",
                        "rollback_advice": "恢复原端口",
                    },
                },
            }
        return {
            "job_id": job_id,
            "status": self.status,
            "result": {"reason": "Running/Ready 且稳定"},
        }

    async def approve(self, job_id, approval_id, approved, reviewer="", reason=""):
        if self.status != "awaiting_approval":
            # Like the backend: a decided approval is gone (HTTP 404).
            raise RuntimeError(
                'AIOps backend returned HTTP 404: {"detail":"审批请求不存在或已失效"}'
            )
        self.approvals.append((job_id, approval_id, approved, reviewer))
        self.status = "recovered" if approved else "rejected"
        return {"job_id": job_id, "status": self.status}


def _send(text, *, metadata=None, task_id=None, context_id=None, data=None):
    parts = [{"kind": "text", "text": text}]
    if data is not None:
        parts.append({"kind": "data", "data": data})
    message = {"kind": "message", "role": "user", "messageId": str(uuid4()), "parts": parts}
    if task_id:
        message["taskId"] = task_id
    if context_id:
        message["contextId"] = context_id
    params = {"message": message, "configuration": {"blocking": True}}
    if metadata:
        params["metadata"] = metadata
    return {"jsonrpc": "2.0", "id": str(uuid4()), "method": "message/send", "params": params}


def _settings():
    return AdapterSettings(
        backend_url="http://backend.test", public_url="http://a2a.test", agent_version="t"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reply",
    [
        {"data": {"approval_id": "appr-123456", "approved": True, "reviewer": "ops-bot"}},
        {"text": "批准 appr-123456"},
        # LLM hosts often send both forms of one decision; it must be submitted once.
        {
            "text": "批准 appr-123456",
            "data": {"approval_id": "appr-123456", "approved": True, "reviewer": "ops-bot"},
        },
    ],
)
async def test_repair_pauses_for_approval_and_resumes_in_the_same_task(reply):
    backend = RepairBackend()
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        first = (
            await client.post(
                "/", json=_send("诊断并修复 ns 的异常 Pod", metadata={"aiops_mode": "repair"})
            )
        ).json()["result"]
        assert first["status"]["state"] == "input-required"
        data = [p for p in first["status"]["message"]["parts"] if p["kind"] == "data"][0]["data"]
        assert data["batch_id"] == "batch-diag-1"
        assert data["approvals"][0]["approval_id"] == "appr-123456"
        assert data["approvals"][0]["execute_command"].startswith("kubectl patch deployment")
        call = backend.calls[0]
        assert call["mode"] == "repair" and call["repair_plan"] is True
        assert call["session_id"].startswith("a2a-")

        second = (
            await client.post(
                "/",
                json=_send(
                    reply.get("text", "审批"),
                    task_id=first["id"],
                    context_id=first["contextId"],
                    data=reply.get("data"),
                ),
            )
        ).json()["result"]
    assert second["status"]["state"] == "completed"
    assert [a[:3] for a in backend.approvals] == [("job-1", "appr-123456", True)]
    repair = [a for a in second["artifacts"] if a["name"] == "kubernetes-aiops-repair.md"][0]
    assert "recovered" in repair["parts"][0]["text"]


@pytest.mark.asyncio
async def test_same_context_reuses_one_backend_session():
    backend = RepairBackend()
    backend.status = "recovered"
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        first = (
            await client.post("/", json=_send("诊断", metadata={"aiops_mode": "repair"}))
        ).json()
        context_id = first["result"]["contextId"]
        await client.post(
            "/",
            json=_send("修复刚刚的问题", context_id=context_id, metadata={"aiops_mode": "repair"}),
        )
    assert backend.calls[0]["session_id"] == backend.calls[1]["session_id"]


@pytest.mark.asyncio
async def test_repair_without_backend_identity_is_rejected():
    backend = RepairBackend()
    backend.settings = SimpleNamespace(backend_api_token="")
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        result = (
            await client.post("/", json=_send("修复", metadata={"aiops_mode": "repair"}))
        ).json()
    assert result["result"]["status"]["state"] == "rejected"
    assert not backend.calls


@pytest.mark.asyncio
async def test_a_repair_request_without_metadata_still_pauses_for_approval():
    # Live 2026-10-26 (run d52a2280): an A2A host asked "帮我修复 …" without
    # aiops_mode; the backend waited 600 s for an approval the caller never saw.
    backend = RepairBackend()
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        first = (await client.post("/", json=_send("帮我修复 ns 的异常 Pod"))).json()["result"]
        assert first["status"]["state"] == "input-required"
        call = backend.calls[0]
        assert call["mode"] == "query" and call["repair_on_request"] is True
        assert call["repair_plan"] is False
        second = (
            await client.post(
                "/",
                json=_send("批准 appr-123456", task_id=first["id"], context_id=first["contextId"]),
            )
        ).json()["result"]
    assert second["status"]["state"] == "completed"
    assert [a[:3] for a in backend.approvals] == [("job-1", "appr-123456", True)]


@pytest.mark.asyncio
async def test_a_plain_question_completes_without_any_approval():
    backend = RepairBackend()
    backend.plans_a_batch = False  # a query or diagnosis: the backend starts no batch
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        result = (await client.post("/", json=_send("集群有什么问题"))).json()["result"]
    assert result["status"]["state"] == "completed"
    assert backend.calls[0]["repair_on_request"] is True and not backend.approvals


@pytest.mark.asyncio
async def test_a_just_answered_approval_is_not_asked_again():
    # Live 2026-10-27 (batch-e4ea959e): the snapshot right after an approval still listed
    # it as pending and the caller was asked to approve the same action twice.
    backend = RepairBackend()
    backend.stale_snapshot = True
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        first = (await client.post("/", json=_send("帮我修复 ns 的异常 Pod"))).json()["result"]
        second = (
            await client.post(
                "/",
                json=_send("批准 appr-123456", task_id=first["id"], context_id=first["contextId"]),
            )
        ).json()["result"]
    assert second["status"]["state"] == "completed"
    assert len(backend.approvals) == 1
