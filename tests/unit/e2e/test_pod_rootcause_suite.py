import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path("test/pod_rootcause_e2e").resolve()))

from test.pod_rootcause_e2e import run_rootcause_suite as suite
from test.pod_rootcause_e2e.run_rootcause_cases import Case


def _case(case_id: str, group: str = "terminating") -> Case:
    return Case(
        id=case_id,
        group=group,
        name=case_id,
        manifest="manifests/terminating/finalizer-stuck.yaml",
    )


def _suite_case(case_id: str, index_group: str = "terminating") -> suite.SuiteCase:
    case = _case(case_id, index_group)
    return suite.SuiteCase(
        case=case,
        manifest=Path(f"/tmp/{case_id}.yaml"),
        cleanup_manifest=Path(f"/tmp/{case_id}.yaml"),
        trigger=[],
        cleanup=[],
    )


def test_cleanup_namespace_patches_labeled_pods_by_name(monkeypatch):
    commands = []

    def fake_list_resource_names(namespace, resource, label, dry_run=False):
        assert namespace == "aiops-e2e"
        assert resource == "pod"
        if label == "rootcause-e2e=true":
            return ["pod/rc-terminating-finalizer"]
        return []

    def fake_run_command(command, **kwargs):
        commands.append(command)
        return None

    monkeypatch.setattr(suite, "list_resource_names", fake_list_resource_names)
    monkeypatch.setattr(suite, "run_command", fake_run_command)

    suite.cleanup_namespace("aiops-e2e")

    assert ["kubectl", "-n", "aiops-e2e", "patch", "pod/rc-terminating-finalizer", "-p", '{"metadata":{"finalizers":null}}', "--type=merge"] in commands
    assert not any(command[:5] == ["kubectl", "-n", "aiops-e2e", "patch", "pod"] and "-l" in command for command in commands)


def test_sandbox_runtimeclass_manifest_is_admitted_before_kubelet_failure():
    docs = [
        doc
        for doc in yaml.safe_load_all(Path("test/pod_rootcause_e2e/manifests/sandbox/runtimeclass-invalid.yaml").read_text(encoding="utf-8"))
        if doc
    ]
    runtime_class = next((doc for doc in docs if doc.get("kind") == "RuntimeClass"), None)
    pod = next((doc for doc in docs if doc.get("kind") == "Pod"), None)

    assert runtime_class is not None
    assert pod is not None
    assert pod["spec"]["runtimeClassName"] == runtime_class["metadata"]["name"]
    assert runtime_class["handler"] == "rc-definitely-missing-runtime-handler"


def test_terminating_long_running_cases_survive_fifty_request_suite():
    prestop = yaml.safe_load(Path("test/pod_rootcause_e2e/manifests/terminating/prestop-stuck.yaml").read_text(encoding="utf-8"))
    long_grace = yaml.safe_load(Path("test/pod_rootcause_e2e/manifests/terminating/long-grace-period.yaml").read_text(encoding="utf-8"))

    assert prestop["spec"]["terminationGracePeriodSeconds"] >= 21600
    assert "sleep 21600" in str(prestop["spec"]["containers"][0]["lifecycle"]["preStop"]["exec"]["command"])
    assert long_grace["spec"]["terminationGracePeriodSeconds"] >= 21600
    assert "sleep 21600" in str(long_grace["spec"]["containers"][0]["command"])


def test_write_suite_summary_aggregates_completed_and_failed_cases(tmp_path):
    completed = _suite_case("terminating-finalizer-stuck")
    failed = _suite_case("sandbox-runtimeclass-invalid", "sandbox")
    completed_dir = tmp_path / "terminating" / "01-terminating-finalizer-stuck"
    completed_dir.mkdir(parents=True)
    (completed_dir / "stats.json").write_text(
        json.dumps(
            {
                "total_runs": 2,
                "success": 2,
                "failed": 0,
                "cases": {
                    "terminating-finalizer-stuck": {
                        "group": "terminating",
                        "root_cause_accuracy": 100.0,
                        "runbook_coverage": 50.0,
                        "evidence_completeness": 75.0,
                        "avg_mttr_seconds": 120.0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    args = argparse.Namespace(
        repeat=2,
        concurrency=1,
        url="http://127.0.0.1:30800",
        question="只检查 aiops-e2e",
    )

    suite.write_suite_summary(
        tmp_path,
        [completed, failed],
        args,
        started=0,
        outcomes={"terminating-finalizer-stuck": {"status": "completed"}, "sandbox-runtimeclass-invalid": {"status": "failed", "error": "apply failed"}},
    )

    summary_md = (tmp_path / "suite_summary.md").read_text(encoding="utf-8")
    suite_stats = json.loads((tmp_path / "suite_stats.json").read_text(encoding="utf-8"))

    assert "完成 Case: 1/2" in summary_md
    assert "| terminating-finalizer-stuck | terminating | completed | 2 | 100.0% | 50.0% | 75.0% | 2.0m |" in summary_md
    assert "| sandbox-runtimeclass-invalid | sandbox | failed | 0 | N/A | N/A | N/A | N/A | apply failed |" in summary_md
    assert "| TOTAL | 1 | 2 | 100.0% | 50.0% | 75.0% | 2.0m |" in summary_md
    assert suite_stats["completed_cases"] == 1
    assert suite_stats["failed_cases"] == 1
