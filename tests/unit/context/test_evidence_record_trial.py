"""Generic record engine gates and lifecycle adapter evidence fidelity."""

import copy

import pytest

from scripts.evidence_record_trial import lifecycle_rows, query_records, select_records


@pytest.fixture
def payload():
    return {
        "status": "success",
        "coverage": "partial",
        "next_continue_token": "next-page",
        "history_complete": False,
        "raw_ref": "frozen-source",
        "pods": [
            {
                "namespace": "test",
                "name": "recovered",
                "uid": "u1",
                "node": "node1",
                "phase": "Running",
                "containers": [
                    {
                        "name": "app",
                        "role": "app",
                        "ready": True,
                        "restart_count_total": 13,
                        "restart_count_in_window": None,
                        "termination_within_window": True,
                        "state": {"running": {}},
                        "last_state": {
                            "terminated": {
                                "reason": "OOMKilled",
                                "exitCode": 137,
                                "finishedAt": "2026-10-09T00:09:00Z",
                            }
                        },
                    },
                    {
                        "name": "init",
                        "role": "init",
                        "ready": False,
                        "restart_count_total": 0,
                        "last_state": {"terminated": {"reason": "Completed", "exitCode": 0}},
                    },
                ],
            },
            {
                "namespace": "test",
                "name": "unknown",
                "uid": "u2",
                "node": "node2",
                "phase": "Pending",
                "containers": [{"name": "new", "status_observed": False}],
            },
        ],
    }


def test_lifecycle_adapter_copies_values_without_diagnosis(payload):
    before = copy.deepcopy(payload)
    rows = lifecycle_rows(payload, "container")
    assert payload == before
    assert len(rows) == 3
    assert rows[0]["ready"] is True
    assert rows[0]["phase"] == "Running"
    assert rows[0]["last_termination_reason"] == "OOMKilled"
    assert rows[0]["last_exit_code"] == 137
    assert rows[0]["restart_count_total"] == 13
    assert rows[0]["restart_count_in_window"] is None
    assert rows[1]["last_exit_code"] == 0
    assert rows[2]["last_termination_reason"] is None


def test_matching_with_identity_and_unknowns(payload):
    args = {
        "record_type": "container",
        "fields": ["last_termination_reason"],
        "where": [{"field": "last_termination_reason", "op": "eq", "value": "OOMKilled"}],
    }
    packet = query_records(payload, args)
    assert packet["matched_rows"] == 1
    assert packet["unknown_filter_rows"] == 1
    assert packet["rows"] == [
        {
            "namespace": "test",
            "pod": "recovered",
            "uid": "u1",
            "container": "app",
            "role": "app",
            "last_termination_reason": "OOMKilled",
        }
    ]
    assert packet["source_metadata"]["coverage"] == "partial"
    assert packet["source_metadata"]["next_continue_token"] == "next-page"
    assert packet["source_metadata"]["raw_ref"] == "frozen-source"


def test_same_container_predicates(payload):
    packet = query_records(
        payload,
        {
            "record_type": "container",
            "where": [
                {"field": "last_termination_reason", "op": "eq", "value": "OOMKilled"},
                {"field": "ready", "op": "eq", "value": False},
            ],
        },
    )
    assert packet["matched_rows"] == 0
    assert packet["unknown_filter_rows"] == 1


@pytest.mark.parametrize(
    "record_type,expected",
    [
        ("pod", [{"node": "node1", "count": 1}, {"node": "node2", "count": 1}]),
        ("container", [{"node": "node1", "count": 2}, {"node": "node2", "count": 1}]),
    ],
)
def test_group_counts_have_explicit_unit(payload, record_type, expected):
    packet = query_records(payload, {"record_type": record_type, "group_by": "node"})
    assert packet["record_unit"] == record_type
    assert packet["groups"] == expected


def test_generic_non_kubernetes_records():
    rows = [{"id": i, "value": i % 2, "available": False} for i in range(200)]
    output = select_records(
        rows,
        known_fields=["id", "value", "available"],
        fields=["value"],
        where=[{"field": "id", "op": "gte", "value": 198}],
        identity_fields=["id"],
    )
    assert output["rows"] == [{"id": 198, "value": 0}, {"id": 199, "value": 1}]
    assert output["matched_rows"] == 2
    assert output["input_rows"] == 200


@pytest.mark.parametrize(
    "args",
    [
        {"record_type": "bogus"},
        {"fields": ["unknown"]},
        {"fields": []},
        {"record_type": "pod", "fields": ["ready"]},
        {"group_by": "containers"},
        {"pod": "recovered"},
        {"namespace": None},
        {"where": [{"field": "node", "op": "exec", "value": 1}]},
        {"match": "xor"},
        {"shell": "echo x"},
        {"where": [{"field": "node", "op": "gt", "value": 1}]},
    ],
)
def test_invalid_parameters_fail_explicitly(payload, args):
    assert query_records(payload, args)["status"] == "error"


def test_no_true_equals_one_or_unknown_equals_zero():
    rows = [{"value": True}, {"value": 1}, {"value": None}, {"value": 0}]
    result = select_records(
        rows,
        known_fields=["value"],
        fields=["value"],
        where=[{"field": "value", "op": "eq", "value": 1}],
    )
    assert result["rows"] == [{"value": 1}]
    assert result["unknown_filter_rows"] == 1


def test_empty_unknown_and_errors_are_different(payload):
    empty = copy.deepcopy(payload)
    empty["pods"] = []
    assert query_records(empty, {})["rows"] == []
    assert query_records(payload, {"namespace": "missing"})["matched_rows"] == 0
    payload["status"] = "error"
    assert query_records(payload, {})["status"] == "error"


def test_oversized_result_does_not_drop_late_row(payload):
    payload["pods"][-1]["name"] = "x" * 15000
    packet = query_records(payload, {})
    assert packet["error"] == "result_too_large"
    assert packet["matched_rows"] == 2
    assert "rows" not in packet


def test_boundary_fixture_recovery_and_unknown_are_not_cross_joined():
    from scripts.evidence_boundary_fixtures import make_fixture

    source = make_fixture("partial")
    query = {
        "record_type": "container",
        "where": [
            {"field": "last_termination_reason", "op": "eq", "value": "OOMKilled"},
            {"field": "ready", "op": "eq", "value": False},
        ],
    }
    result = query_records(source, query)
    assert result["matched_rows"] == 0
    assert result["unknown_filter_rows"] == 1
    assert result["source_metadata"]["next_continue_token"] == "synthetic-next-page"
    assert result["source_metadata"]["remaining_item_count"] == 17
    query["where"][1]["value"] = True
    result = query_records(source, query)
    assert result["matched_rows"] == 1
    assert result["rows"][0]["pod"] == "recovered"
    assert result["rows"][0]["container"] == "app"
    assert result["rows"][0]["restart_count_total"] == 7
    assert result["rows"][0]["restart_count_in_window"] is None


@pytest.mark.parametrize("variant,status", [("empty", "success"), ("error", "error")])
def test_boundary_fixture_empty_and_failed_are_distinct(variant, status):
    from scripts.evidence_boundary_fixtures import make_fixture

    result = query_records(make_fixture(variant), {"record_type": "pod", "group_by": "node"})
    assert result["status"] == status
    if variant == "empty":
        assert result["groups"] == []
        assert result["matched_rows"] == 0
    else:
        assert "matched_rows" not in result
