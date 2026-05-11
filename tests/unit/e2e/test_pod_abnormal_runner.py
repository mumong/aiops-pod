from pathlib import Path

from test.pod_abnormal_e2e.run_pod_abnormal_cases import (
    Case,
    evaluate_response,
    extract_evidence_rate,
    extract_mttr_seconds,
    extract_runbook_ids,
    load_cases,
)


def test_extract_mttr_seconds_prefers_stats_block():
    text = "## 性能统计\n├─ 总耗时: 4.5m\n"
    assert extract_mttr_seconds(text, wall_clock=999) == 270


def test_extract_evidence_rate_from_collection_summary():
    rate, collected, planned, source = extract_evidence_rate(
        "collection_summary: 计划 7 项，实际采集 6 项，未采集 1 项，完整度 86%"
    )

    assert rate == 6 / 7
    assert collected == 6
    assert planned == 7
    assert source == "collection_summary"


def test_extract_runbook_ids_from_trace_lines():
    ids = extract_runbook_ids(
        """
        📋 诊断追踪
        - **核心 Runbook**: l3-imagepull-failed
        - **参考 Runbook**: pod-volume-mount-failed, l3-imagepull-failed
        """
    )

    assert "l3-imagepull-failed" in ids
    assert "pod-volume-mount-failed" in ids


def test_evaluate_response_scores_pod_abnormal_case():
    case = Case(
        id="oom",
        name="OOM",
        expected_pod_abnormal_type="OOMKilled",
        expected_layer="L2",
        expected_runbooks=["l2-oomkilled"],
        root_cause_keywords=["OOMKilled", "Exit Code: 137", "40Mi"],
        evidence_keywords=["Last State", "OOMKilled", "Exit Code: 137"],
    )
    text = """
    📤 → 下游数据: layer=Layer.L2
    根因: Pod memhog OOMKilled, Exit Code: 137, memory limit 40Mi.
    证据: Last State Terminated Reason OOMKilled Exit Code: 137
    collection_summary: 计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%
    📋 诊断追踪
    - **核心 Runbook**: l2-oomkilled
    ## 📊 性能统计
    ├─ 总耗时: 90s
    ├─ 工具调用: 8 次
    └─ LLM 调用: 4 次
    """

    result = evaluate_response(case, text, wall_clock=120, idx=1)

    assert result["success"] is True
    assert result["layer"] == "L2"
    assert result["root_cause_ok"] is True
    assert result["evidence_ok"] is True
    assert result["runbook_ok"] is True
    assert result["mttr_seconds"] == 90


def test_cases_yaml_loads_enabled_pod_abnormal_cases():
    _, cases = load_cases(Path("test/pod_abnormal_e2e/cases.yaml"))

    enabled = [case for case in cases if case.enabled]
    assert len(enabled) >= 10
    assert {case.expected_pod_abnormal_type for case in enabled} >= {
        "Evicted",
        "VolumeMountFailed",
        "PendingUnschedulable",
        "TerminatingStuck",
        "OOMKilled",
        "CrashLoopBackOffRuntime",
        "ImagePullFailed",
        "SandboxCreateFailed",
        "ConfigError",
        "NotReadyProbeFailed",
    }
