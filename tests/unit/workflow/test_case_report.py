import json
from types import SimpleNamespace

import pytest

from app.core.remediation.group_context import scoped_diagnosis
from app.core.remediation.records import diagnosis_payload
from app.core.workflow.case_report import conclude_cases, diagnosis_cases, pack_indexes


def state(count=4):
    groups, results = [], []
    for i in range(count):
        group = {
            "group_id": f"g{i}",
            "target_id": f"t{i}",
            "entities": [{"kind": "Pod", "namespace": "ns", "name": f"pod{i}", "uid": f"uid{i}"}],
        }
        case = {
            "group_id": group["group_id"],
            "target": group,
            "summary": f"异常{i}",
            "report": f"完整报告{i}",
            "execution_status": "completed",
            "outcome": "abnormal",
            "certainty": "supported",
            "key_facts": [{"statement": f"实际错误{i}", "evidence_refs": [f"/raw/{i}"]}],
            "unresolved": ["尚未恢复"],
            "runbook_refs": ["manual"],
            "result_ref": f"/case/{i}",
        }
        groups.append(group)
        results.append(
            {
                "group_id": group["group_id"],
                "status": "completed",
                "case_result": case,
                "material": {"observations": ["huge-body" * 10000]},
            }
        )
    return {
        "question": "检查Pod",
        "autonomous_groups": groups,
        "autonomous_group_results": results,
    }


def node(fail=False):
    calls = []

    def call(text, prompt, **kwargs):
        calls.append(json.loads(text))
        assert "huge-body" not in text and "完整报告" not in text
        assert kwargs["force_no_tools"]
        if fail:
            raise ValueError("working_context_compaction_required")
        return SimpleNamespace(result='{"overview":"存在已识别的异常，详见各组。"}'), []

    return SimpleNamespace(
        _call_llm=call, _archive_node_input=lambda _: None, _archive_node_output=lambda _: None
    ), calls


@pytest.mark.parametrize("count", [1, 4, 10, 100])
def test_all_reports_preserved_without_full_material_in_model(count):
    n, calls = node()
    result = conclude_cases(n, state(count))
    assert len(result["diagnosis_cases"]) == count
    for i in range(count):
        assert f"完整报告{i}" in result["conclusion"]
    assert result["diagnosis_overview"]["completed"] == count
    assert not result["diagnosis_overview"]["failed"]
    assert calls


def test_hundred_large_indexes_batch_without_rewriting_or_omitting_reports():
    from app.core.context.budget import count_tokens

    data = state(100)
    for row in data["autonomous_group_results"]:
        row["case_result"]["summary"] = "证据尚有缺口，不能判断已恢复。" * 19
    n, calls = node()
    result = conclude_cases(n, data)
    assert not result["diagnosis_overview"]["failed"]
    leaves = [item for call in calls if call["level"] == 0 for item in call["results"]]
    assert [i["group_id"] for i in leaves] == [f"g{i}" for i in range(100)]
    assert len(calls) > 1
    assert all(
        count_tokens(json.dumps(call["results"], ensure_ascii=False))["tokens"] <= 12000
        for call in calls
    )
    assert len(result["diagnosis_cases"]) == 100


def test_overview_failure_does_not_erase_reports_or_leak_internal_error_as_answer():
    n, _ = node(fail=True)
    result = conclude_cases(n, state())
    assert result["diagnosis_overview"]["failed"]
    assert "working_context_compaction_required" not in result["conclusion"]
    assert len(result["diagnosis_cases"]) == 4
    assert "完整报告3" in result["conclusion"]


def test_missing_worker_remains_partial_not_silently_omitted():
    data = state()
    data["autonomous_group_results"].pop()
    cases = diagnosis_cases(data)
    assert len(cases) == 4
    assert cases[-1]["group_id"] == "g3"
    assert cases[-1]["execution_status"] == "partial"


def test_repair_receives_only_selected_case_with_facts_unknowns_and_runbooks():
    n, _ = node()
    data = state()
    result = conclude_cases(n, data)
    record = {"run_id": "run", "payload": diagnosis_payload({**data, **result})}
    scoped = scoped_diagnosis(record, "g2")["payload"]
    assert scoped["report"] == "完整报告2"
    assert scoped["diagnosis_result"]["key_facts"][0]["evidence_refs"] == ["/raw/2"]
    assert scoped["diagnosis_result"]["unresolved"] == ["尚未恢复"]
    assert scoped["diagnosis_result"]["runbook_refs"] == ["manual"]
    assert "完整报告1" not in json.dumps(scoped, ensure_ascii=False)
    assert "huge-body" not in json.dumps(scoped)
    assert json.dumps(scoped, ensure_ascii=False).count("完整报告2") == 1


def test_batching_preserves_all_indexes_and_rejects_oversized_atom():
    items = [{"group_id": str(i), "summary": "内容" * 50} for i in range(100)]
    batches = pack_indexes(items, 500)
    assert len(batches) > 1
    assert [item for batch in batches for item in batch] == items
    with pytest.raises(ValueError):
        pack_indexes([{"summary": "a" * 20000}], 500)
