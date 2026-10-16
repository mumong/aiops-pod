"""Runtime review/auto switch: config baseline, TTL-bound override, persisted, audited."""

import json

import pytest

from app.core.remediation import audit
from app.core.remediation.settings import RepairSettings

CFG = {"enabled": True, "mode": "review", "approval_timeout_seconds": 600}


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_REPAIR_RECORD_ROOT", str(tmp_path))
    return RepairSettings(path=tmp_path / "settings.json")


def test_config_is_the_baseline(settings):
    eff = settings.effective(CFG)
    assert eff["mode"] == "review" and eff["mode_source"] == "config"
    assert eff["approval_timeout_seconds"] == 600 and eff["override"] is None
    assert settings.effective({"mode": "auto"})["mode"] == "auto"


def test_override_switches_mode_with_ttl_and_persists(settings, tmp_path, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.core.remediation.settings.time.time", lambda: now[0])
    eff = settings.set_override(
        mode="auto",
        reason="acceptance",
        ttl_minutes=10,
        changed_by="tester",
        config=CFG,
        approval_timeout_seconds=30,
    )
    assert eff["mode"] == "auto" and eff["mode_source"] == "runtime"
    assert eff["approval_timeout_seconds"] == 30
    assert eff["override"]["expires_at"] == 1000.0 + 600
    # Survives a restart (new instance reads the same file).
    again = RepairSettings(path=tmp_path / "settings.json")
    assert again.effective(CFG)["mode"] == "auto"
    now[0] = 1000.0 + 601
    assert (
        again.effective(CFG)["mode"] == "review"
        and again.effective(CFG)["mode_source"] == "config"
    )
    kinds = [e["kind"] for e in audit.read_audit()]
    assert kinds == ["mode_changed"]
    assert audit.read_audit()[0]["mode"] == "auto"


def test_override_validation_and_clear(settings):
    with pytest.raises(ValueError):
        settings.set_override(mode="yolo", reason="x", ttl_minutes=5, changed_by="t", config=CFG)
    with pytest.raises(ValueError):
        settings.set_override(mode="auto", reason="x", ttl_minutes=0, changed_by="t", config=CFG)
    with pytest.raises(ValueError):
        settings.set_override(
            mode="auto", reason="x", ttl_minutes=24 * 60 + 1, changed_by="t", config=CFG
        )
    settings.set_override(mode="auto", reason="x", ttl_minutes=5, changed_by="t", config=CFG)
    assert settings.clear_override(changed_by="t", config=CFG)["mode_source"] == "config"
    assert [e["mode"] for e in audit.read_audit(kind="mode_changed")] == ["review", "auto"]


def test_corrupt_settings_file_falls_back_to_config(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json")
    assert RepairSettings(path=path).effective(CFG)["mode_source"] == "config"
    json.loads(path.read_text()) if path.read_text().startswith('{"') else None
