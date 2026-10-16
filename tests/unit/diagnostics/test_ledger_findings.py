"""Ledger + findings reproduce today's live failure modes from events alone."""

import json

from app.core.aicall.guards import AgentGuards
from app.core.aicall.output_budget import OutputBudget
from app.core.diagnostics.findings import classify_ledger
from app.core.diagnostics.ledger import build_call_ledger, guard_of
from app.core.diagnostics.report import build_run_report, render_markdown


def _events(rounds, extra=()):
    out = []
    t = 1000.0
    for i, (ms, out_tokens, calls) in enumerate(rounds, 1):
        out.append(
            {
                "type": "ai_usage",
                "iteration": i,
                "model_duration_ms": ms,
                "usage": {"input_tokens": 9000 + i * 300, "output_tokens": out_tokens},
                "timestamp": t,
            }
        )
        for _ in range(calls):
            t += 0.1
            out.append({"type": "tool_start", "tool": "x", "timestamp": t})
        t += 1
    out.extend(extra)
    return out


def _tool(name, guard=None, status="success", raw=100, summ=100):
    return {
        "tool_name": name,
        "tool_args": {"q": name},
        "status": status,
        "guard": guard,
        "raw_chars": raw,
        "summary_chars": summ,
        "semantic_success": status == "success",
        "raw_ref": "/a.raw.txt",
    }


def test_guard_of_maps_tool_message_flags():
    assert guard_of({"aiops_repeat_page": 2}) == "repeat_page"
    assert guard_of({"aiops_repeat_notice": True}) == "repeat_notice"
    assert guard_of({"aiops_turn_cap": True}) == "turn_cap"
    assert guard_of({}) is None


def test_tool_call_burst_and_budget_exhaustion_are_found():
    # Live 5a1ea8d104b642a1: one message issued 250 tool calls, 6000 output tokens.
    events = _events([(5000, 200, 3), (100000, 6000, 250)])
    tools = [_tool("get_metric_names")] * 16 + [_tool("get_metric_names", guard="turn_cap")] * 234
    ledger = build_call_ledger(
        run_id="r",
        node_id="query_collect",
        events=events,
        tool_calls=tools,
        duration_ms=148000,
        incomplete_reason="repeat_limit",
    )
    assert ledger["rounds"][1]["tool_calls"] == 250 and ledger["counts"]["turn_capped"] == 234
    codes = {f["code"] for f in classify_ledger(ledger, AgentGuards(16, 3, 3000), OutputBudget())}
    assert {
        "tool_call_burst",
        "output_budget_exhausted_round",
        "long_model_round",
        "repeat_limit_stop",
    } <= codes


def test_repeats_pages_repairs_and_voluntary_stop():
    events = _events(
        [(3000, 150, 2), (2000, 120, 1)],
        extra=[
            {"type": "tool_call_args_repaired", "count": 1, "timestamp": 1},
            {"type": "execution_incomplete", "reason": "no_structured_output", "timestamp": 2},
            {
                "type": "structured_finalization",
                "status": "success",
                "reason": "no_structured_output",
                "timestamp": 3,
            },
        ],
    )
    tools = [
        _tool("a", raw=23000, summ=3000),
        _tool("a", guard="repeat_page"),
        _tool("a", guard="repeat_notice"),
    ]
    ledger = build_call_ledger(
        run_id="r",
        node_id="query_collect",
        events=events,
        tool_calls=tools,
        duration_ms=30000,
        incomplete_reason="no_structured_output",
        structured_delivered=True,
    )
    codes = {f["code"] for f in classify_ledger(ledger)}
    assert {
        "identical_call_repeats",
        "malformed_tool_args_repaired",
        "structured_finalization",
        "large_tool_output_bounded",
    } <= codes
    assert "tool_call_burst" not in codes


def test_report_aggregates_main_and_lane_ledgers(tmp_path):
    root = tmp_path
    for run, node in (("r1", "layer"), ("r1-g1", "evidence"), ("r1-g1", "rca")):
        d = root / run / "ledger"
        d.mkdir(parents=True, exist_ok=True)
        ledger = build_call_ledger(
            run_id=run,
            node_id=node,
            events=_events([(1000, 50, 1)]),
            tool_calls=[_tool("t")],
            duration_ms=1500,
        )
        (d / f"{node}.json").write_text(json.dumps(ledger), encoding="utf-8")
    (root / "r1" / "parallel").mkdir()
    (root / "r1" / "parallel" / "results.json").write_text(
        json.dumps(
            [
                {
                    "group_id": "g1",
                    "status": "completed",
                    "case_result": {
                        "outcome": "abnormal",
                        "certainty": "confirmed",
                        "summary": "env typo",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    report = build_run_report(
        "r1",
        root=str(root),
        final_state={
            "request_route": "full_diagnosis",
            "request_contract": {"task": "diagnose", "scope": "pod"},
            "diagnosis_handoff": {
                "coverage": "complete",
                "targets": [
                    {
                        "target_id": "t1",
                        "status": "investigate",
                        "entity": {"kind": "Pod", "namespace": "ns", "name": "p"},
                    }
                ],
            },
        },
        node_durations_ms={"layer": 1500, "parallel_evidence": 4000},
        elapsed_seconds=6.2,
        outcome="success",
    )
    assert [c["node"] for c in report["calls"]] == ["layer", "evidence", "rca"]
    assert (
        report["lanes"][0]["outcome"] == "abnormal"
        and report["targets"][0]["entity"] == "Pod/ns/p"
    )
    md = render_markdown(report)
    assert "# Run r1" in md and "| g1 | completed | abnormal |" in md and "## 发现" in md
