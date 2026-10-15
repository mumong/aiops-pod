from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.core.workflow.case_result import DiagnosisCaseOutput, bind_case_result, case_index


def output():
    return {
        "outcome": "abnormal",
        "summary": "存在待处理的异常",
        "cause": "配置与启动要求不一致",
        "certainty": "supported",
        "key_facts": [{"statement": "启动日志报告缺少配置", "evidence_refs": ["/archive/log"]}],
        "unresolved": ["未验证恢复"],
        "runbook_refs": [],
        "report": "本组完整报告",
    }


def bound(data=None):
    return bind_case_result(
        data or output(),
        group_id="g1",
        target={
            "target_id": "t1",
            "entities": [{"kind": "Pod", "namespace": "ns", "name": "p", "uid": "uid1"}],
        },
        result_ref="/archive/cases/g1.json",
    )


def test_overview_does_not_receive_full_report_or_key_evidence_bodies():
    data = output()
    data["report"] = "very long report " * 20000
    result = bound(data)
    index = case_index(result)
    assert "report" not in index and "key_facts" not in index and "cause" not in index
    assert index["target_id"] == "t1" and index["entities"][0]["uid"] == "uid1"
    assert result["report"] == data["report"]
    assert result["key_facts"][0]["evidence_refs"] == ["/archive/log"]


def test_report_paragraphs_fix_escaped_prose_without_decoding_original_evidence():
    data = output()
    data["report"] = (
        "### 诊断结论"
        + r"\n\n"
        + "结论"
        + r"\n\n"
        + "### 关键证据\n\n"
        + "`literal\\n\\nvalue`\n\n"
        + "```text\nerror\\n\\nsource\n```\n\n"
        + r"C:\new\node is a path"
    )
    report = bound(data)["report"]
    assert report.startswith("### 诊断结论\n\n结论\n\n### 关键证据")
    assert "`literal\\n\\nvalue`" in report
    assert "```text\nerror\\n\\nsource\n```" in report
    assert r"C:\new\node" in report


def test_rca_report_contract_requires_real_evidence_without_extra_collection():
    from app.core.prompts import DEEP_RCA_PROMPT

    for heading in ("诊断结论", "异常现象", "关键证据", "原因分析", "待核实与采集边界"):
        assert "### " + heading in DEEP_RCA_PROMPT
    assert "真实工具结果" in DEEP_RCA_PROMPT
    assert "不强制追加查询" in DEEP_RCA_PROMPT
    assert "不暴露 Secret 值" in DEEP_RCA_PROMPT


def test_model_cannot_change_identity_or_inject_repair_command():
    for field in ("target", "group_id", "commands", "execution_status"):
        with pytest.raises(ValidationError):
            DiagnosisCaseOutput.model_validate({**output(), field: "unexpected"})


def test_overlong_core_is_rejected_not_silently_truncated():
    data = output()
    data["summary"] = "x" * 321
    with pytest.raises(ValidationError):
        bound(data)
    data = output()
    data["key_facts"] *= 9
    with pytest.raises(ValidationError):
        bound(data)


def test_index_isolation_does_not_mutate_result():
    result = bound()
    before = deepcopy(result)
    index = case_index(result)
    index["entities"][0]["uid"] = "different"
    assert result == before


def test_failed_case_remains_in_inventory_without_manufacturing_diagnosis():
    index = case_index(
        {"group_id": "g2", "execution_status": "failed", "target": {"target_id": "t2"}}
    )
    assert index["group_id"] == "g2"
    assert index["execution_status"] == "failed"
    assert index["outcome"] == "inconclusive"


@pytest.mark.parametrize("count", [1, 4, 10, 100])
def test_index_growth_independent_of_tool_history_and_report_length(count):
    import json

    result = bound()
    indexes = []
    for number in range(count):
        item = {
            **result,
            "group_id": f"g{number}",
            "report": "large" * 10000,
            "tool_history": "large" * 10000,
        }
        indexes.append(case_index(item))
    assert len(indexes) == count
    assert len(json.dumps(indexes, ensure_ascii=False)) < count * 600
