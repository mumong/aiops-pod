"""Exercise the real suite orchestrator without sending diagnosis requests."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path("tests/quality").resolve()))
import run_quality_demo as q
from variant_suite import fixture_manager


def setup_runner(monkeypatch, tmp_path, *, cleanup_fails=False):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_quality_demo.py",
            "--foreground",
            "--scenario",
            "c02-tag,c06-file",
            "-n",
            "1",
            "-c",
            "1",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        q.requests, "get", lambda *a, **k: SimpleNamespace(raise_for_status=lambda: None)
    )
    monkeypatch.setattr(
        q,
        "run_command",
        lambda *a, **k: SimpleNamespace(stdout="https://fixture-recovery-unit-test", returncode=0),
    )
    monkeypatch.setattr(q.time, "sleep", lambda seconds: None)
    calls = []
    cleanup = []

    def clean(catalog):
        cleanup.append(True)
        if cleanup_fails and len(cleanup) > 1:
            raise subprocess.CalledProcessError(
                1, ["kubectl", "delete", "namespace", "owned-fixture"]
            )

    monkeypatch.setattr(q, "cleanup_catalog_namespaces", clean)
    monkeypatch.setattr(q, "apply_scenario", lambda *a: None)
    pod = {
        "metadata": {"uid": "current", "name": "workload"},
        "status": {"message": "x509: certificate signed by unknown authority"},
    }
    monkeypatch.setattr(q, "_pod_for_case", lambda case: pod)
    monkeypatch.setattr(
        q,
        "_kubectl_json",
        lambda args: {
            "items": [
                {
                    "involvedObject": {"uid": "current"},
                    "message": "x509: certificate signed by unknown authority",
                }
            ]
        },
    )

    def gate(case):
        if case["id"] == "c02-tag":
            raise TimeoutError("specific cause gate did not pass")
        return pod

    monkeypatch.setattr(q, "wait_for_case_gate", gate)

    def postcheck(case, timeout):
        assert timeout == 60
        return True

    monkeypatch.setattr(fixture_manager(), "validate_variant", postcheck)

    def diagnose(**kwargs):
        calls.append(kwargs["scenario"].id)
        return {
            "run_index": kwargs["run_index"],
            "run_id": "unit-run",
            "success": True,
            "elapsed_seconds": 1,
            "root_cause": {"passed": True, "accuracy": 1},
            "runbook": {
                "coverage": 1,
                "expected": ["pod-crashloop-runtime"],
                "matched": ["pod-crashloop-runtime"],
                "passed": True,
            },
            "evidence": {"completeness": 1, "collected": 1, "planned": 1},
        }

    monkeypatch.setattr(q, "run_diagnosis_once", diagnose)
    return calls


def test_gate_failure_is_archived_and_next_case_runs(monkeypatch, tmp_path):
    calls = setup_runner(monkeypatch, tmp_path)
    assert q.main() == "completed_with_errors"
    assert calls == ["c06-file"]
    stats = json.loads((tmp_path / "stats.json").read_text())
    bad, good = stats["scenarios"]
    assert bad["runs"] == [] and bad["blocked_run_indexes"] == [1]
    assert bad["fixture_errors"][0]["category"] == "registry_tls_untrusted"
    archive = json.loads(Path(bad["fixture_errors"][0]["archive"]).read_text())
    assert archive["members"]["c02-tag"]["pod"]["metadata"]["uid"] == "current"
    assert good["status"] == "completed" and len(good["runs"]) == 1
    console = q.build_console_report(stats, tmp_path)
    assert "未完成全量有效验收" in console and "待复核" in console and "1/2" in console
    assert q._aggregate_scenario_metrics(stats["scenarios"])["root_accuracy"] == 1
    assert (
        q._aggregate_scenario_metrics(stats["scenarios"])["metric_samples"]["root_accuracy"] == 1
    )


def test_cleanup_failure_stops_before_next_case(monkeypatch, tmp_path):
    calls = setup_runner(monkeypatch, tmp_path, cleanup_fails=True)
    with pytest.raises(subprocess.CalledProcessError):
        q.main()
    assert calls == []
    stats = json.loads((tmp_path / "stats.json").read_text())
    assert stats["status"] == "failed" and stats["cleanup_error"]


def test_worker_publishes_partial_completion(monkeypatch, tmp_path):
    path = tmp_path / "runner.status.json"
    monkeypatch.setenv(q.PROTECTED_STATUS_ENV, str(path))
    monkeypatch.setattr(q, "main", lambda: "completed_with_errors")
    q._protected_worker_entrypoint()
    assert json.loads(path.read_text())["status"] == "completed_with_errors"


def test_runtime_resume_preserves_scores_and_snapshots(tmp_path):
    old = {"version": "v1", "sha256": {"run_quality_demo.py": "old", "evaluator.py": "same"}}
    new = {"version": "v1", "sha256": {"run_quality_demo.py": "new", "evaluator.py": "same"}}
    stats = {
        "scoring_manifest": old,
        "scenarios": [{"runs": [{"run_index": 1, "root_cause": {"accuracy": 0.5}}]}],
    }
    with pytest.raises(RuntimeError):
        q.accept_runtime_resume(stats, new, tmp_path, allowed=False)
    q.accept_runtime_resume(stats, new, tmp_path, allowed=True)
    audit = stats["runtime_resume_audit"][0]
    assert audit["preserved_runs"] == 1
    assert json.loads(Path(audit["snapshot"]).read_text())["scoring_manifest"] == old
    assert stats["scenarios"][0]["runs"][0]["root_cause"]["accuracy"] == 0.5


def test_actual_resume_skips_recorded_runs(monkeypatch, tmp_path):
    calls = setup_runner(monkeypatch, tmp_path)
    assert q.main() == "completed_with_errors"
    original = json.loads((tmp_path / "stats.json").read_text())["scenarios"][1]["runs"]
    monkeypatch.setattr(sys, "argv", sys.argv + ["--resume"])
    calls.clear()
    assert q.main() == "completed_with_errors"
    assert calls == []  # blocked setup retried, already scored scenario untouched
    resumed = json.loads((tmp_path / "stats.json").read_text())
    assert resumed["scenarios"][1]["runs"] == original


@pytest.mark.parametrize("field", ["evaluator.py", "cases_file", "variant_cases.yaml"])
def test_runtime_resume_rejects_grading_changes(tmp_path, field):
    old = {"version": "v1", "sha256": {field: "old"}}
    new = {"version": "v1", "sha256": {field: "new"}}
    with pytest.raises(RuntimeError):
        q.accept_runtime_resume({"scoring_manifest": old}, new, tmp_path, allowed=True)


def test_expired_events_refresh_once_without_weakening_gate(monkeypatch):
    scenario = SimpleNamespace(members=["c10"])
    catalog = {"c10": {"id": "c10"}}
    attempts, actions = [], []

    def gate(case):
        attempts.append(case)
        if len(attempts) == 1:
            raise TimeoutError("Unhealthy event absent")
        return {"metadata": {"uid": "new"}}

    monkeypatch.setattr(q, "wait_for_case_gate", gate)
    monkeypatch.setattr(fixture_manager(), "clean", lambda c: actions.append("clean"))
    monkeypatch.setattr(fixture_manager(), "deploy", lambda c: actions.append("deploy"))
    stats = {}
    assert (
        q.precheck_with_refresh(scenario, catalog, stats, 18, reuse_existing=False)["c10"][
            "metadata"
        ]["uid"]
        == "new"
    )
    assert actions == ["clean", "deploy"] and len(attempts) == 2
    assert stats["fixture_refreshes"][0]["run_index"] == 18
    monkeypatch.setattr(q, "wait_for_case_gate", lambda c: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        q.precheck_with_refresh(scenario, catalog, {}, 19, reuse_existing=False)
    assert actions == ["clean", "deploy", "clean", "deploy"]
    with pytest.raises(TimeoutError):
        q.precheck_with_refresh(scenario, catalog, {}, 19, reuse_existing=True)
    assert len(actions) == 4
