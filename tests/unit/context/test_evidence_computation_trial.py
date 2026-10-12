"""Offline engine gates, not proof of model or end-to-end competence."""
import copy

import pytest

from scripts.evaluate_evidence_computation import compute, oracle, replay, schema


@pytest.fixture
def source():
    return {
        "status": "success", "coverage": "partial", "history_complete": False,
        "next_continue_token": "opaque-next", "remaining_item_count": 20,
        "scope": {"namespace": None}, "observed_at": "2026-10-09T00:10:00Z",
        "window": {"minutes": 10}, "limitations": ["Last termination is not full history"],
        "pods": [{"name": f"pod-{i}", "namespace": "test", "uid": f"uid-{i}",
                  "node": "node-a" if i < 70 else "node-b", "phase": "Running",
                  "containers": [{"name": "app", "ready": True, "restart_count_total": 0,
                                  "restart_count_in_window": None, "last_state": {}}]}
                 for i in range(101)],
    }


def test_late_record_not_lost_and_input_unchanged(source):
    source["pods"][-1]["containers"][0].update(
        restart_count_total=13,
        last_state={"terminated": {"reason": "OOMKilled", "exitCode": 137,
                                   "finishedAt": "2026-10-09T00:09:00Z"}})
    before = copy.deepcopy(source)
    result = compute(source, "pods[?containers[?last_state.terminated.reason == 'OOMKilled']]."
                     "{name:name,uid:uid,phase:phase,containers:containers}")
    assert source == before
    assert result["source_record_count"] == 101
    pod = result["result"][0]
    assert pod["name"] == "pod-100"
    assert pod["uid"] == "uid-100"
    assert pod["phase"] == "Running"
    assert pod["containers"][0]["ready"] is True
    assert pod["containers"][0]["restart_count_in_window"] is None
    assert oracle(source)["previous_oom"][0]["name"] == "pod-100"


def test_same_container_predicates_do_not_cross_join(source):
    source["pods"][0]["containers"] = [
        {"name": "app", "ready": True, "last_state": {"terminated": {"reason": "X"}}},
        {"name": "sidecar", "ready": False, "last_state": {"terminated": {"reason": "Y"}}},
    ]
    result = compute(source, "pods[?containers[?ready == `false` && last_state.terminated.reason == 'X']]")
    assert result["result"] == []
    result = compute(source, "pods[?containers[?ready == `false` && last_state.terminated.reason == 'Y']].name")
    assert result["result"] == ["pod-0"]


@pytest.mark.parametrize("expression, expected", [
    ("length(pods)", 101), ("length(pods[?node == 'node-a'])", 70),
    ("pods[-1].name", "pod-100"), ("pods[0].containers[0].ready", True),
    ("pods[0].containers[0].restart_count_total", 0),
    ("history_complete", False), ("pods[0].containers[0].restart_count_in_window", None),
    ("pods[?name == 'absent']", []), ("missing_field", None),
])
def test_values_preserved(source, expression, expected):
    packet = compute(source, expression)
    assert packet["status"] == "success"
    assert packet["result"] == expected
    assert type(packet["result"]) is type(expected)
    assert packet["source_metadata"]["coverage"] == "partial"
    assert packet["source_metadata"]["next_continue_token"] == "opaque-next"
    assert packet["source_metadata"]["remaining_item_count"] == 20


def test_sort_and_filter_before_output_limit(source):
    result = compute(source, "sort_by(pods, &name)[-1].{uid:uid,name:name}", max_bytes=1000)
    assert result["status"] == "success"
    assert result["result"] == {"name": "pod-99", "uid": "uid-99"}


@pytest.mark.parametrize("expression", ["[", "", "a" * 2049, None, 10,
                                        "read_file('/etc/passwd')", "system('echo test')"])
def test_invalid_or_nonexistent_function_is_error(source, expression):
    assert compute(source, expression)["status"] == "error"


def test_giant_result_not_silently_truncated(source):
    source["pods"][-1]["text"] = "x" * 15000
    result = compute(source, "pods[-1]")
    assert result["error"] == "result_too_large"
    assert "result" not in result
    assert compute(source, "pods[-1].name")["result"] == "pod-100"


def test_source_error_is_not_successful_empty_selection(source):
    source["status"] = "error"
    assert compute(source, "pods[?name == 'missing']")["error"] == "source_not_successful"
    assert replay(source, {}, "compute") == source


def test_raw_optional_selection_and_source_scope_preserved(source):
    assert replay(source, {}, "raw") == source | {"returned_count": 101}
    assert replay(source, {}, "compute") == replay(source, {}, "raw")
    result = replay(source, {"namespace": "test", "pod": "pod-100", "expression": "pods[].name"}, "compute")
    assert result["result"] == ["pod-100"]
    assert result["source_metadata"]["scope"] == {"namespace": None}
    assert result["source_record_count"] == 1


@pytest.mark.parametrize("arguments", [{"pod": "pod-1"}, {"namespace": None},
                                       {"exec": "echo hello"}])
def test_invalid_scope_or_argument_is_error(source, arguments):
    assert replay(source, arguments, "compute")["status"] == "error"


def test_raw_schema_does_not_offer_expression(source):
    assert "expression" not in schema("raw")["function"]["parameters"]["properties"]
    assert "expression" in schema("compute")["function"]["parameters"]["properties"]
    assert replay(source, {"expression": "pods"}, "raw")["status"] == "error"


def test_generic_json_no_pod_specific_selection_rule():
    payload = {"status": "success", "records": [{"id": "first", "value": 8},
                                                {"id": "last", "value": 0}]}
    packet = compute(payload, "records[?value == `0`].{id:id,value:value}")
    assert packet["result"] == [{"id": "last", "value": 0}]
    assert packet["source_record_count"] is None
