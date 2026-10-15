"""Root variants must discriminate causes, targets and arithmetic denominators."""
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("test/aiops_quality_e2e").resolve()))
import run_quality_demo as q
from variant_suite import combine_scenarios, score_target_runbooks


def report(rows):
    return ("## 📊 异常概览与现象\n\n| 组 | 异常实体 | 异常状态 |\n|---|---|---|\n"
            + "\n".join(f"| g{i} | `{ns}/workload` | abnormal |" for i, (ns, _) in enumerate(rows, 1))
            + "\n\n" + "\n\n".join(f"## 🎯 根因分析 · g{i}\n\n### 根因结论\n\n已确认根因：{text}"
                                      for i, (_, text) in enumerate(rows, 1)))


GOOD = {
    "c01-cpu": "CPU request 100k 远超节点容量，导致无法调度。",
    "c01-memory": "内存请求 1Pi 远超节点容量。",
    "c01-pvc": "PVC unavailable-claim 不存在，阻止调度。",
    "c03-secret": "Secret unavailable-input 不存在，卷挂载失败。",
    "c03-key": "ConfigMap workload-input 的 unavailable-key 键缺失，导致卷挂载失败。",
    "c03-hostpath": "hostPath 指定目录不存在，导致挂载失败。",
    "c02-tag": "镜像 tag 不存在，manifest unknown。",
    "c06-command": "启动命令不存在，退出127。",
    "c06-file": "配置文件 /input/app.conf 不存在，退出1。",
    "c07-env": "必需环境变量 APP_REQUIRED_CONFIG 未设置，退出78。",
    "c04-configmap-key": "ConfigMap workload-input 中的 unavailable-key 键缺失，无法构造环境变量。",
    "c11-prestop": "preStop hook 长时间运行，阻塞删除。",
    "c11-grace": "进程忽略 SIGTERM，等待较长宽限期。",
    "c05-plugin": "NAD 存在，但 CNI 插件 aiops-unavailable 未安装，Sandbox 创建失败。",
    "c08-startup": "启动时一次性分配256Mi内存超过64Mi限制，导致OOMKilled。",
    "c09-port": "readiness 探针端口18081错配，应用未监听该端口，连接拒绝。",
    "c10-timeout": "liveness 存活探针超时，导致容器反复重启。",
}


@pytest.mark.parametrize("case_id,text", GOOD.items())
def test_variant_positive_and_inconclusive(case_id, text):
    s = q.load_scenarios(q.DEMO_CASES_PATH)[case_id]
    ns = s.expected_root_causes[0].namespace
    claims = q.extract_root_claims(report([(ns, text)]))
    assert q.score_root_causes(s.expected_root_causes, claims).passed
    assert not q.score_root_causes(s.expected_root_causes, [replace(claims[0], inconclusive=True)]).passed
    assert not q.score_root_causes(s.expected_root_causes, [replace(claims[0], namespaces=("wrong-ns",))]).passed


def test_suites_cover_every_base_and_preserve_baseline():
    s = q.load_scenarios(q.DEMO_CASES_PATH)
    assert len(q.select_scenarios(s, "all")) == 11
    assert len(q.select_scenarios(s, "variants")) == 17
    assert len(q.select_scenarios(s, "expanded")) == 28
    for base in q.select_scenarios(s, "all"):
        assert any(v.id.startswith(base.id + "-") for v in s.values())
    assert all(v.question == "我的集群有什么问题？" and v.expected_root_causes for v in s.values())
    assert len(q.default_output_dir(list(s.values())).name) < 160
    with pytest.raises(ValueError):
        q.select_scenarios(s, "c01-cpu,c01-cpu")


def test_swapped_same_symptom_causes_do_not_pass():
    s = q.load_scenarios(q.DEMO_CASES_PATH)
    combined = combine_scenarios([s["c03-secret"], s["c03-key"]], q.load_catalog(q.CATALOG_PATH))
    swapped = report([("aiops-case-v04", GOOD["c03-key"]), ("aiops-case-v05", GOOD["c03-secret"])])
    assert q.score_root_causes(combined.expected_root_causes, q.extract_root_claims(swapped)).matched_count == 0
    one = report([("aiops-case-v04", GOOD["c03-secret"])])
    diagnosis = q.DiagnosisResult("mock", one, {}, 60, (), "")
    result = q._score_run(combined, diagnosis, q.EvidenceScore(1, 2, .5, (), "test"))
    assert result["root_cause"]["accuracy"] == .5
    assert result["group_audit"]["missing_namespaces"] == ["aiops-case-v05"]


def test_runbook_cannot_be_borrowed_from_other_target():
    targets = (("aiops-case-v01", ("pod-pending-unschedulable",)),
               ("aiops-case-v05", ("pod-volume-mount-failed",)))
    text = report([("aiops-case-v01", "CPU 请求过高"), ("aiops-case-v05", "key 缺失")])
    text += "\n\n📋 Runbook 参考\n\n- **g1 aiops-case-v01/workload**: pod-pending-unschedulable, pod-volume-mount-failed\n"
    result = score_target_runbooks(targets, text, q.extract_root_claims(text))
    assert result["coverage"] == .5


@pytest.mark.parametrize("text,passed", [
    ("Volume input 引用了 ConfigMap 中不存在的 Key unavailable-key，导致挂载失败。", True),
    ("ConfigMap workload-input 对象不存在，导致无法取得 unavailable-key 键。", False),
    ("ConfigMap workload-input 存在，但 key unavailable-key 缺失。", True),
])
def test_missing_key_is_not_missing_configmap(text, passed):
    s = q.load_scenarios(q.DEMO_CASES_PATH)["c03-key"]
    claims = q.extract_root_claims(report([("aiops-case-v05", text)]))
    assert q.score_root_causes(s.expected_root_causes, claims).passed is passed


def test_duplicate_target_conclusions_require_review():
    s = q.load_scenarios(q.DEMO_CASES_PATH)["c03-key"]
    claims = q.extract_root_claims(report([("aiops-case-v05", GOOD["c03-key"]),
                                         ("aiops-case-v05", "ConfigMap 对象不存在")]))
    assert not q.score_root_causes(s.expected_root_causes, claims).passed


def test_per_run_percentage_mean_and_invalid_fixture_exclusion():
    def run(accuracy, ev):
        return {"success": True, "root_cause": {"accuracy": accuracy}, "runbook": {"coverage": accuracy},
                "evidence": {"completeness": ev}, "elapsed_seconds": 60}
    rows = [run(1, 1), run(.5, .5), dict(run(0, 0), fixture_valid=False)]
    result = q._aggregate_runs(rows)
    assert result["root_accuracy"] == result["runbook_coverage"] == result["evidence_completeness"] == .75
    assert result["successful"] == 3 and result["valid_samples"] == 2


@pytest.mark.parametrize("index,matched", [(1, 4), (2, 5)])
def test_historical_mixed_reports_agree_with_manual_review(index, matched):
    path = Path(f"testreports/aiops_c01_c03_groups_20260908_183108/01-mixed/run-{index:02d}/report.md")
    if not path.is_file():
        pytest.skip("optional local historical archive")
    s = q.load_scenarios(q.DEMO_CASES_PATH)
    mix = combine_scenarios([s[x] for x in ("c01-cpu", "c01-memory", "c01-pvc", "c03-secret", "c03-key", "c03-hostpath")], q.load_catalog(q.CATALOG_PATH))
    claims = q.extract_root_claims(path.read_text())
    assert q.score_root_causes(mix.expected_root_causes, claims).matched_count == matched
    assert score_target_runbooks(mix.runbook_targets, path.read_text(), claims)["coverage"] == (0 if index == 1 else 1)
