from copy import deepcopy
import json
import pytest
from app.core.remediation.group_context import diagnosis_groups, scoped_diagnosis
from app.core.remediation.records import RecordUnavailable


def fixture():
    return {"run_id": "d1", "payload": {"report": "ALL_GROUPS_BODY", "request_contract": {"scope": "cluster"},
        "groups": [{"group_id": f"g{i}", "analysis": f"CAUSE_{i}",
                    "target": {"entities": [{"kind": "Pod", "namespace": "ns", "name": f"p{i}"}]},
                    "evidence": [{"result_excerpt": f"EVIDENCE_{i}", "raw_ref": f"/raw/{i}"}]}
                   for i in (1, 2, 3)],
        "shared_evidence": {"evidence": [{"tool_name": "fetch_runbook", "raw_ref": "/book",
                                         "result_excerpt": "SHARED_FULL_BODY"}]}}}


def test_scoped_group_keeps_evidence_not_other_groups_or_shared_full_text():
    original = fixture()
    before = deepcopy(original)
    result = scoped_diagnosis(original, "g2")
    body = json.dumps(result)
    assert "EVIDENCE_2" in body and "CAUSE_2" in body and "/book" in body
    assert all(value not in body for value in ("EVIDENCE_1", "EVIDENCE_3", "ALL_GROUPS_BODY", "SHARED_FULL_BODY"))
    assert result["payload"]["request_contract"]["pod_names"] == ["p2"]
    assert original == before


def test_group_identity_and_single_legacy_diagnosis():
    assert len(diagnosis_groups(fixture())) == 3
    with pytest.raises(RecordUnavailable):
        scoped_diagnosis(fixture(), "missing")
    source = {"run_id": "old", "payload": {"report": "single diagnostic report"}}
    assert diagnosis_groups(source) == [{"group_id": "single", "target": None}]
    assert scoped_diagnosis(source, "single") == source
    source = fixture()
    source["payload"]["groups"].append(source["payload"]["groups"][0])
    with pytest.raises(RecordUnavailable):
        diagnosis_groups(source)
