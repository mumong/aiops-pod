"""Counterexamples from the benchmark audit: incorrect answers must fail."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

DEMO = Path(__file__).resolve().parents[3] / "test/aiops_quality_e2e"
sys.path.insert(0, str(DEMO))
from evaluator import extract_root_claims, score_root_causes, score_runbooks
from run_quality_demo import (
    load_scenarios, exclusive_lock, atomic_write, scoring_manifest,
    rescore_existing_report, evaluation_warnings, build_console_report,
)


@pytest.mark.parametrize("case,body", [
    ("c01", "已确认根因：节点 CPU 不足导致 Pending。nodeSelector 配置正常，所有节点均匹配。"),
    ("c01", "已确认根因：节点 CPU 不足。已排除 aiops.lab/unavailable 标签不匹配。"),
    ("c05", "已确认根因：Multus 的 NetworkAttachmentDefinition 配置正常，实际原因是 IPAM 地址池耗尽。"),
    ("c08", "可能是 OOMKilled 导致 Exit Code 137，需进一步验证。"),
    ("c08", "已确认根因：可能 OOMKilled，内存限制为 64Mi。"),
    ("c08", "无法排除 OOMKilled，内存限制为 64Mi。"),
    ("c06", "已确认根因：应用进程以 Exit Code 20 非零退出，导致 CrashLoopBackOff。"),
    ("c06", "已确认根因：应用进程退出码 200，导致 CrashLoopBackOff。"),
    ("c08", "现有证据不足，根因确认失败。可能是 OOMKilled，容器限制为 64Mi。"),
    ("c08", "已确认根因：/work 代码异常。已排除：OOMKilled，尽管内存限制为 64Mi。"),
    ("c10", "已确认根因：Liveness Probe 配置的 /work 返回 HTTP 500，被 kubelet 重启。"),
    ("c10", "已确认根因：OOM Killer 因内存不足杀死容器，Liveness Probe 返回 HTTP 500。"),
    ("c07", "已确认根因：CONFIG_MISSING 导致 Exit Code 78 非零退出，实际根因是资源耗尽导致的 OOMKilled。"),
    ("c07", "已确认根因：CONFIG_MISSING 导致 Exit Code 78，非零退出由 OOMKilled 引发。"),
    ("c09", "已确认根因：Liveness Probe 返回 HTTP 503，导致容器重启。"),
    ("c09", "已确认根因：OOMKilled 导致 Readiness Probe 返回 HTTP 503。"),
    ("c09", "已确认根因：Readiness Probe 因 HTTP 404 失败。业务 /work 正常返回 200。"),
    ("c09", "已确认根因：Readiness Probe 返回 HTTP 5030。"),
    ("c09", "已确认根因：/work 业务返回 HTTP 503，但 Readiness Probe 正常。"),
    ("c09", "根因无法确认，可能 Readiness Probe 返回 503，仍需验证。"),
    ("c09", "已确认根因：Readiness Probe 配置为 /work，返回 HTTP 503。"),
])
def test_wrong_or_tentative_answers_fail(case, body):
    scenario = load_scenarios(DEMO / "demo_cases.yaml")[case]
    report = "## 🎯 根因分析 · g1\n### 根因结论\n" + body
    assert not score_root_causes(scenario.expected_root_causes, extract_root_claims(report)).passed


@pytest.mark.parametrize("case,body", [
    ("c01", "已确认根因：Pod 的 Node-Selector 与集群节点标签不匹配，导致调度失败。"),
    ("c05", "已确认根因：Multus 查找网络配置失败（NoNetworkFound），导致 FailedCreatePodSandBox。"),
    ("c08", "已确认根因：内存增长超过 64 MiB 限制，触发 OOMKiller 强制终止容器。"),
    ("c10", "已确认根因：Liveness Probe /health 返回 HTTP 500，kubelet 因此重启容器。容器内存限制为 96Mi，使用量为 16Mi。"),
    ("c10", "已确认根因：Liveness Probe /health 返回 HTTP 500 被 Kubelet 重启，而非内存不足（OOM）。日志中也无 Kernel OOM Killer 记录。"),
])
def test_equivalent_confirmed_mechanisms_pass(case, body):
    scenario = load_scenarios(DEMO / "demo_cases.yaml")[case]
    report = "## 🎯 根因分析 · g1\n### 根因结论\n" + body
    assert score_root_causes(scenario.expected_root_causes, extract_root_claims(report)).passed


def test_future_runbook_suggestion_is_not_a_reference():
    report = "📋 Runbook 参考\n\n- g1: pod-config-error\n\n后续建议调用 pod-oomkilled 排查。"
    assert not score_runbooks(["pod-oomkilled"], report).passed


def test_lock_blocks_other_process_and_is_released(tmp_path):
    path = tmp_path / "cluster.lock"
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
        "from run_quality_demo import exclusive_lock; "
        "lock=exclusive_lock(Path(sys.argv[2])); lock.__enter__(); lock.__exit__(None,None,None)"
    )
    command = [sys.executable, "-c", code, str(DEMO), str(path)]
    with exclusive_lock(path):
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode != 0
        assert "another quality task" in result.stderr
    assert subprocess.run(command, capture_output=True).returncode == 0


def test_failed_atomic_replace_preserves_previous_checkpoint(tmp_path, monkeypatch):
    path = tmp_path / "stats.json"
    path.write_text('{"valid": true}')
    def fail(*args):
        raise OSError("simulated interrupted publication")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        atomic_write(path, '{"valid": false}')
    assert json.loads(path.read_text()) == {"valid": True}
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("case,run_id,body,passed", [
    ("c01", "9f7d39bd9bda4834", "已确认的根因：Pod 的 nodeSelector 配置了 aiops.lab/unavailable=true，而集群中所有节点均不具备此标签。Pod 的资源请求极低，排除了资源竞争因素。因此，调度失败确认为标签选择器约束导致的节点匹配失败。", True),
    ("c01", "c9424703c85e4de2", "已确认的根因是 Pod 配置了集群中不存在的标签选择器 aiops.lab/unavailable=true。", True),
    ("c01", "94c16f53cd594862", "已确认的根因是 Pod 配置了不可满足的 nodeSelector（或节点亲和性）条件（具体为 aiops.lab/unavailable=true），而集群内所有节点均缺失该 Label。", True),
    ("c08", "1872f88399b8498d", "已确认根因为应用内存使用持续增长（最高观察至 46 MiB）逼近并可能突破 64Mi 的容器内存限制，触发内核 OOM Killer 终止进程，进而引发 Kubernetes 的 CrashLoopBackOff。", True),
    ("c11", "0564718e1afb497c", "已确认的根因：容器异常终止导致 Pod 进入僵死删除状态。\n\n未确认的环节与决定性事实缺失：诊断信息中指出可能存在 aiops.lab/hold finalizer 阻止删除，但当前事实中未直接包含该 finalizer 的元数据证据。", False),
])
def test_historical_conclusion_excerpts(case, run_id, body, passed):
    """Excerpts from 20260903_104420; IDs retain provenance, never influence scoring."""
    scenario = load_scenarios(DEMO / "demo_cases.yaml")[case]
    report = "## 🎯 根因分析 · g1\n### 根因结论\n" + body
    assert score_root_causes(scenario.expected_root_causes, extract_root_claims(report)).passed is passed, run_id


def test_custom_case_rules_are_in_manifest(tmp_path):
    rules = tmp_path / "custom.yaml"
    rules.write_text("rules: first")
    before = scoring_manifest(rules)
    rules.write_text("rules: second")
    assert scoring_manifest(rules) != before


def test_corrupt_rescore_is_isolated_and_explicitly_incomplete(tmp_path):
    scenarios = load_scenarios(DEMO / "demo_cases.yaml")
    run = {"success": True, "run_index": 1, "run_id": "broken", "elapsed_seconds": 1,
           "root_cause": {"passed": True}, "runbook": {"coverage": 1},
           "evidence": {"planned": 1, "collected": 1, "completeness": 1}}
    original = json.dumps({"scenarios": [{"id": "c04", "runs": [run]}]})
    (tmp_path / "stats.json").write_text(original)
    archive = tmp_path / "c04/run-01-broken"
    archive.mkdir(parents=True)
    (archive / "report.md").write_text("report")
    (archive / "events.json").write_text("{truncated")
    revision = rescore_existing_report(tmp_path, scenarios, [scenarios["c04"]])
    assert not revision["rescore_complete"]
    assert revision["rescore_missing_archives"]
    assert "待复核" in build_console_report(revision, tmp_path)
    assert (tmp_path / "stats.json").read_text() == original


def test_missing_evidence_is_reported_not_silently_averaged():
    stats = {"scenarios": [{"id": "c01", "runs": [
        {"success": True, "evidence": {"completeness": None}},
        {"success": True, "evidence": {"completeness": 1}},
    ]}]}
    assert "1/2" in evaluation_warnings(stats)[0]


@pytest.mark.parametrize("fixture", sorted(
    (Path(__file__).parent / "fixtures/quality_20260907").glob("*.md")
), ids=lambda p: p.stem)
def test_september_seventh_real_reports_match_primary_root(fixture):
    scenario = load_scenarios(DEMO / "demo_cases.yaml")[fixture.name[:3]]
    score = score_root_causes(scenario.expected_root_causes, extract_root_claims(fixture.read_text()))
    assert score.passed, score.matches
