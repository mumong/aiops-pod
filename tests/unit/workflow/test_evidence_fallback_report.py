"""When RCA delivers nothing, the group's own tool-backed evidence is shown, not a placeholder."""

from app.core.workflow.case_result import evidence_fallback_report


def test_report_renders_evidence_facts_and_open_questions_without_inferring_a_cause():
    handoff = {
        "key_facts": [
            {
                "statement": "Pod 处于 Terminating，finalizer aiops.lab/hold 未释放",
                "observed_at": "2026-10-15T10:30:00Z",
                "evidence_refs": [
                    "/tmp/aiops/reports/context_archives/r-g4/tools/003-evidence-kubectl_get_yaml.raw.txt"
                ],
            },
            {"statement": "容器上次退出码 137", "evidence_refs": ["ref-2"]},
        ],
        "unresolved": ["finalizer 为何未自动释放"],
    }
    report = evidence_fallback_report(handoff, "容器已退出但对象仍在。")
    assert report.startswith("### 诊断结论")
    assert "不构成根因结论" in report and "根因是" not in report
    assert (
        "| Pod 处于 Terminating，finalizer aiops.lab/hold 未释放 | 2026-10-15T10:30:00Z |"
        in report
    )
    assert "`ref-2`" in report and "- finalizer 为何未自动释放" in report
    assert "### 取证分析\n容器已退出但对象仍在。" in report


def test_nothing_real_means_empty_report():
    assert evidence_fallback_report({"key_facts": [], "unresolved": ["x"]}, "") == ""
    assert evidence_fallback_report(None, "   ") == ""
