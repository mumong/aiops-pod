"""/repair/policy endpoints: readable rules, dry command checks, guarded mode switch."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import register_routes
from app.core.remediation.settings import RepairSettings


class _Service:
    workflow_config = {
        "remediation": {"enabled": True, "mode": "review", "approval_timeout_seconds": 600}
    }


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_REPAIR_RECORD_ROOT", str(tmp_path))
    monkeypatch.setattr("app.api.repair_routes.get_service", lambda: _Service())
    monkeypatch.setattr(
        "app.api.repair_routes.repair_settings", RepairSettings(path=tmp_path / "s.json")
    )
    app = FastAPI()
    register_routes(app)
    return TestClient(app)


def test_policy_is_readable_without_a_session(client):
    body = client.get("/repair/policy").json()
    assert body["mode"] == "review" and body["mode_source"] == "config"
    assert "delete" in body["rules"]["denied_operations"]
    assert body["runtime_switch"]["available"] is False  # no admin token configured


def test_check_endpoint_names_rules_and_never_executes(client):
    body = client.post(
        "/repair/policy/check",
        json={
            "commands": [
                "kubectl delete ns demo --force",
                "kubectl patch pod/x -n demo -p '{}'",
            ]
        },
    ).json()
    results = body["results"]
    assert results[0]["allowed"] is False and results[0]["rule"] == "denied_operations"
    assert results[1]["allowed"] is True and results[1]["operation"] == "patch"
    assert client.post("/repair/policy/check", json={"commands": []}).status_code == 422


def test_mode_switch_requires_admin_token(client, monkeypatch):
    payload = {"mode": "auto", "reason": "acceptance", "ttl_minutes": 15}
    assert client.put("/repair/policy/mode", json=payload).status_code == 403
    monkeypatch.setenv("AIOPS_ADMIN_TOKEN", "secret-token")
    assert (
        client.put(
            "/repair/policy/mode", json=payload, headers={"X-AIOps-Admin-Token": "wrong"}
        ).status_code
        == 403
    )
    ok = client.put(
        "/repair/policy/mode", json=payload, headers={"X-AIOps-Admin-Token": "secret-token"}
    )
    assert (
        ok.status_code == 200
        and ok.json()["mode"] == "auto"
        and ok.json()["mode_source"] == "runtime"
    )
    assert client.get("/repair/policy").json()["mode"] == "auto"
    audit = client.get("/repair/audit", headers={"X-AIOps-Admin-Token": "secret-token"}).json()
    assert audit["events"][0]["kind"] == "mode_changed"
    cleared = client.delete("/repair/policy/mode", headers={"X-AIOps-Admin-Token": "secret-token"})
    assert cleared.json()["mode"] == "review"
    assert client.get("/repair/audit").status_code in (401, 403)  # no token, no session
