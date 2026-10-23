"""Multi-cluster scope questions: input-required, then the reply continues the same task."""

import httpx
import pytest

pytest.importorskip(
    "a2a",
    reason="A2A tests run in the isolated requirements.a2a-dev.txt environment",
)

from a2a_adapter.app import create_app
from a2a_adapter.backend import BackendEvent
from tests.a2a.test_repair_skill import RepairBackend, _send, _settings

QUESTION = "请说明要查看哪个集群：edge-88、edge-89，或所有边缘集群？"


class ScopeBackend:
    """Asks for the cluster until the request names one, like the multi-cluster router."""

    def __init__(self, final_key="request_route"):
        self.calls, self.final_key = [], final_key

    async def health(self):
        return {"status": "healthy"}

    async def stream(self, question, *, mode, cancel_event, **_):
        self.calls.append({"question": question, "mode": mode})
        yield BackendEvent("run_start", {"run_id": f"run-{len(self.calls)}"})
        if "edge-88" not in question:
            clarify = (
                {"request_route": "clarify"}
                if self.final_key == "request_route"
                else {"query_answer": {"status": "clarify"}}
            )
            yield BackendEvent("final", {"answer": QUESTION, **clarify})
            return
        yield BackendEvent("final", {"answer": "# edge-88\n\n2 个 Pod 异常"})


@pytest.mark.asyncio
@pytest.mark.parametrize("final_key", ["request_route", "query_answer"])
async def test_scope_question_pauses_and_reply_completes_the_original_request(final_key):
    backend = ScopeBackend(final_key)
    app = create_app(_settings(), backend_client=backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        first = (
            await client.post(
                "/", json=_send("有哪些异常 Pod", metadata={"aiops_mode": "diagnosis"})
            )
        ).json()["result"]
        assert first["status"]["state"] == "input-required"
        assert first["status"]["message"]["parts"][0]["text"] == QUESTION
        assert not first.get("artifacts")

        second = (
            await client.post(
                "/", json=_send("edge-88", task_id=first["id"], context_id=first["contextId"])
            )
        ).json()["result"]
    assert second["status"]["state"] == "completed"
    assert second["artifacts"][0]["parts"][0]["text"].startswith("# edge-88")
    assert backend.calls[1] == {
        "question": "有哪些异常 Pod\n（补充说明：edge-88）",
        "mode": "diagnosis",
    }


class ClusterRepairBackend(RepairBackend):
    async def job(self, job_id):
        job = await super().job(job_id)
        if job.get("approval"):
            job["approval"]["payload"]["cluster"] = "edge-89"
        return job


@pytest.mark.asyncio
async def test_approval_request_names_the_cluster_of_each_action():
    app = create_app(_settings(), backend_client=ClusterRepairBackend())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://a2a.test"
    ) as client:
        first = (
            await client.post("/", json=_send("修复异常 Pod", metadata={"aiops_mode": "repair"}))
        ).json()["result"]
    parts = first["status"]["message"]["parts"]
    assert "集群 edge-89" in parts[0]["text"]
    assert parts[1]["data"]["approvals"][0]["cluster"] == "edge-89"
