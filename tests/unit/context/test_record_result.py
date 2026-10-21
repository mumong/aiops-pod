"""Serving computed-result contract; no dependencies on the MCP sibling checkout."""

import copy
import json

import pytest

from app.core.context.observation import ObservationProcessor
from app.core.context.record_result import parse_record_result
from app.core.workflow.stream_contract import project_query_tool_event


@pytest.fixture
def packet():
    return {
        "contract_version": "evidence-records.v1",
        "status": "success",
        "coverage": "partial",
        "record_unit": "pod",
        "source_metadata": {
            "scope": {"namespace": None},
            "observed_at": "2026-10-09T00:00:00Z",
            "coverage": "partial",
            "next_continue_token": "next",
        },
        "input_rows": 24,
        "matched_rows": 24,
        "unknown_filter_rows": 0,
        "executed_query": {"record_type": "pod"},
        "result_type": "records",
        "columns": ["namespace", "pod", "uid", "ready", "value"],
        "rows": [
            {"namespace": "test", "pod": f"pod-{i}", "uid": str(i), "ready": False, "value": 0}
            for i in range(24)
        ],
    }


def test_lossless_observation_and_bounded_display(packet, tmp_path):
    raw = json.dumps(packet)
    obs = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=200).process(
        "record-contract", "query_collect", 1, "query_pod_lifecycle", raw
    )
    assert obs["semantic_success"] is True
    assert obs["summary"] == raw
    assert obs["processor"] == "evidence_records+lossless"
    from pathlib import Path

    assert Path(obs["raw_ref"]).read_text() == raw
    display = project_query_tool_event({"type": "tool_result", "result": raw, **obs})[
        "tool_display"
    ]
    assert display["records_omitted"] == 4
    assert len(display["records"]) == 20
    assert display["records"][0]["value"] == 0
    assert display["records"][0]["ready"] is False
    assert display["source_metadata"]["next_continue_token"] == "next"
    assert obs["summary"] == raw


def test_valid_groups(packet):
    packet.update(
        result_type="groups",
        groups=[{"node": "n1", "count": 14}, {"node": None, "count": 10}],
        executed_query={"group_by": "node"},
    )
    packet.pop("rows")
    packet.pop("columns")
    parsed, success = parse_record_result(packet)
    assert success is True
    assert parsed["groups"][1]["node"] is None


def test_empty_selection_and_unknown_are_not_failure(packet):
    packet.update(rows=[], matched_rows=0, unknown_filter_rows=12)
    parsed, success = parse_record_result(packet)
    assert success is True
    assert parsed["coverage"] == "partial"
    display = project_query_tool_event({"type": "tool_result", "result": json.dumps(packet)})[
        "tool_display"
    ]
    assert display["records"] == []
    assert display["unknown_filter_rows"] == 12


@pytest.mark.parametrize(
    "change",
    [
        {"matched_rows": True},
        {"matched_rows": 25},
        {"unknown_filter_rows": 1},
        {"columns": ["pod", "pod"]},
        {"rows": []},
        {"coverage": "present"},
        {"source_metadata": {}},
        {"record_unit": "arbitrary"},
        {"result_type": "other"},
    ],
)
def test_malformed_packets_are_not_successful_empty(packet, change):
    packet.update(change)
    parsed, success = parse_record_result(packet)
    assert success is False
    assert parsed["parse_status"] == "failed"


def test_group_counts_checked(packet):
    packet.update(
        result_type="groups",
        groups=[{"node": "n", "count": 2}],
        executed_query={"group_by": "node"},
    )
    assert parse_record_result(packet)[1] is False


def test_errors_preserve_execution_failure():
    raw = json.dumps(
        {
            "contract_version": "evidence-records.v1",
            "status": "error",
            "error": "result_too_large",
            "coverage": "unknown",
            "source_metadata": {},
        }
    )
    display = project_query_tool_event({"type": "tool_result", "result": raw})["tool_display"]
    assert display["semantic_success"] is False
    assert display["error"] == "result_too_large"


def test_unrelated_contracts_unchanged(packet):
    before = copy.deepcopy(packet)
    parse_record_result(packet)
    assert before == packet
    assert parse_record_result({"contract_version": "pod-lifecycle.v1", "pods": []}) is None
    assert parse_record_result('{"status":"success","data":{"result":[]}}') is None


def test_paged_records_keep_source_counts_and_require_consistent_continuation(packet):
    packet["rows"] = packet["rows"][:3]
    packet["source_metadata"].update(coverage="present", next_continue_token="lr1.token.3")
    packet["pagination"] = {
        "snapshot_id": "snapshot",
        "offset": 0,
        "returned_rows": 3,
        "total_rows": 24,
        "remaining_rows": 21,
        "next_continue_token": "lr1.token.3",
        "source_has_more": False,
    }
    parsed, success = parse_record_result(packet)
    assert success
    assert parsed["matched_rows"] == 24 and len(parsed["rows"]) == 3
    display = project_query_tool_event({"type": "tool_result", "result": json.dumps(packet)})[
        "tool_display"
    ]
    assert display["pagination"]["remaining_rows"] == 21
    for change in ({"remaining_rows": 0}, {"next_continue_token": None}, {"returned_rows": 24}):
        broken = copy.deepcopy(packet)
        broken["pagination"].update(change)
        assert parse_record_result(broken)[1] is False


def _grouped(packet, groups):
    packet.update(result_type="groups", groups=groups, executed_query={"group_by": "phase"})
    packet.pop("rows")
    packet.pop("columns")
    return packet


def test_groups_with_health_facts_are_valid(packet):
    # MCP adds counted health facts per group (run 97f67069325c471c).
    _grouped(
        packet,
        [
            {
                "phase": "Running",
                "count": 20,
                "not_ready": 2,
                "terminating": 1,
                "not_ready_examples": ["b/crash-1", "c/oom-1"],
                "restarted_in_window": 2,
                "waiting_reasons": {"CrashLoopBackOff": 2},
                "last_termination_reasons": {"OOMKilled": 1},
            },
            {"phase": "Pending", "count": 4, "not_ready": 0, "ready_unknown": 4},
        ],
    )
    parsed, success = parse_record_result(packet)
    assert success is True


@pytest.mark.parametrize(
    "extra",
    [
        {"unexpected": 1},  # unknown key still rejected
        {"not_ready": -1},  # counts are non-negative ints
        {"not_ready": 30},  # never more than the group
        {"not_ready_examples": "b/crash-1"},  # list of strings
        {"waiting_reasons": {"CrashLoopBackOff": "2"}},
    ],
)
def test_malformed_health_facts_are_rejected(packet, extra):
    _grouped(packet, [{"phase": "Running", "count": 24, **extra}])
    assert parse_record_result(packet)[1] is False
