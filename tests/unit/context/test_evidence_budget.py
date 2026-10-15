"""Serial accumulation, parallel atomicity and rollback of generic budgets."""
import asyncio
import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages

from app.core.aicall.builtin_tools import LegacyReadContextArchiveTool, ReadContextArchiveTool
from app.core.aicall.working_context import (
    WorkingContextMiddleware,
    compact_message,
    message_groups,
    source_receipts,
)
from app.core.context.budget import estimate_tokens
from app.core.context.evidence_policy import EvidencePolicy
from app.core.context.evidence_view import (
    build_evidence_view,
    compact_json,
    decode_json,
    encode_json,
)


class Client:
    def _guard_agent_model_request(self, request, **kwargs):
        return request, {"context_window": 54000}

    def _serialize_agent_message(self, message):
        return message.model_dump()


class Summary:
    def __init__(self):
        self.calls = []

    async def ainvoke(self, messages, **kwargs):
        self.calls.append(messages)
        return AIMessage(content="用户任务、已收集的证据及未解决的问题。")


def exchange(index, parallel=1):
    calls = [{"id": f"{index}-{j}", "name": "unknown_future_tool", "args": {"index": index}}
             for j in range(parallel)]
    return [AIMessage(content="", tool_calls=calls), *[
        ToolMessage(content=(f"exact-{index}-{j}:" + "abc " * 2500), tool_call_id=c["id"])
        for j, c in enumerate(calls)]]


def middleware(tmp_path, monkeypatch, node="query_collect", summary=None):
    monkeypatch.setenv("AIOPS_EVIDENCE_VIEW_MODE", "compact")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    summary = summary or Summary()
    events = []
    mw = WorkingContextMiddleware(Client(), None, summary, [], "system", "原始任务", "budget", node,
                                  lambda **e: events.append(e))
    return mw, summary, events


@pytest.mark.parametrize("node", ["query_collect", "layer", "evidence", "evidence-g1"])
def test_serial_growth_has_headroom_not_compaction_every_call(tmp_path, monkeypatch, node):
    mw, model, events = middleware(tmp_path, monkeypatch, node)
    state = [HumanMessage(content="原始任务")]
    compact_at = []
    for index in range(25):
        state = add_messages(state, exchange(index))
        update = asyncio.run(mw.abefore_model({"messages": state}, None))
        if update:
            state = add_messages(state, update["messages"])
            compact_at.append(index)
            assert mw.tool_history_tokens(state) <= 8000
            assert state[0].content == "原始任务"
            # The most recent complete exchange stays exact.
            assert state[-1].content == exchange(index)[-1].content
        assert mw.tool_history_tokens(state) <= 24000
    assert len(compact_at) >= 2
    assert compact_at[0] >= 5
    assert all(b - a >= 4 for a, b in zip(compact_at, compact_at[1:], strict=False))
    assert len(model.calls) == len(compact_at)
    assert any("累计工具证据" in e.get("content", "") for e in events)


def test_parallel_batch_never_orphans_calls_and_lanes_are_independent(tmp_path, monkeypatch):
    first, _, _ = middleware(tmp_path, monkeypatch, "evidence-g1")
    second, second_model, _ = middleware(tmp_path, monkeypatch, "evidence-g2")
    large = [HumanMessage(content="q"), *exchange(1, 10)]
    small = [HumanMessage(content="q"), *exchange(2)]

    async def run():
        return await asyncio.gather(first.abefore_model({"messages": large}, None),
                                    second.abefore_model({"messages": small}, None))

    a, b = asyncio.run(run())
    assert a and b is None and not second_model.calls
    assert len(message_groups(add_messages(large, a["messages"]))) == 2
    assert "exact-2-0" in small[-1].content


def test_failed_summary_does_not_mutate_history(tmp_path, monkeypatch):
    class Failed(Summary):
        async def ainvoke(self, *a, **kw):
            raise RuntimeError("provider unavailable")
    mw, _, _ = middleware(tmp_path, monkeypatch, summary=Failed())
    state = [HumanMessage(content="q"), *exchange(1, 10)]
    before = [m.model_dump() for m in state]
    with pytest.raises(RuntimeError, match="provider unavailable"):
        asyncio.run(mw.abefore_model({"messages": state}, None))
    assert [m.model_dump() for m in state] == before


def test_legacy_does_not_add_cumulative_trigger(tmp_path, monkeypatch):
    mw, model, _ = middleware(tmp_path, monkeypatch)
    mw.evidence_policy = EvidencePolicy()
    assert asyncio.run(mw.abefore_model({"messages": [HumanMessage(content="q"), *exchange(1, 12)]}, None)) is None
    assert not model.calls


def test_node_handoff_counts_inherited_evidence(tmp_path, monkeypatch):
    mw, model, _ = middleware(tmp_path, monkeypatch)
    inherited = {"question": "原始任务", "observations": [{"result": "evidence " * 10000}]}
    state = [HumanMessage(content=json.dumps(inherited)), *exchange(0)]
    update = asyncio.run(mw.abefore_model({"messages": state}, None))
    assert update and model.calls
    replaced = add_messages(state, update["messages"])
    assert replaced[-1].content == state[-1].content
    assert asyncio.run(mw.abefore_model({"messages": replaced}, None)) is None


def test_read_is_bounded_and_legacy_remains_raw(tmp_path):
    path = tmp_path / "large.txt"
    raw = "中文🙂" * 12000
    path.write_text(raw)
    reader = ReadContextArchiveTool(allowed_roots=[str(tmp_path)])
    bounded = reader._run(str(path), length=40000, view="raw")
    assert estimate_tokens(bounded) <= 4096
    assert "next_offset=" in bounded
    old = LegacyReadContextArchiveTool(allowed_roots=[str(tmp_path)])._run(str(path), length=40000)
    assert old.startswith("<context_archive>") and len(old) > len(bounded)
    assert json.loads(reader._run(str(path), view="compact"))["contract_version"] == "evidence-view.v1"


def test_invalid_archive_selection_reports_failure_not_empty_success(tmp_path):
    from app.core.context.observation import ObservationProcessor
    path = tmp_path / "data.json"
    path.write_text('{"items":[]}')
    raw = ReadContextArchiveTool(allowed_roots=[str(tmp_path)])._run(str(path), json_pointer="/missing")
    assert raw.startswith("Error:") and "invalid_pointer" in raw
    result = ObservationProcessor(archive_root=str(tmp_path), evidence_view_mode="compact").process(
        "run", "evidence", 1, "read_context_archive", raw, preserve_raw=True)
    assert result["semantic_success"] is False


def test_table_encoding_preserves_units_false_null_identity_and_multiplicity():
    rows = [{"long_identity_column": f"a-{i}", "timestamp_utc": i,
             "measurement_units": "bytes", "observed_value": v}
            for i, v in enumerate([False, 0, None, "0", 1.0] * 50)]
    data = {"rows": rows, "columns": ["literal"], "a/~": rows}
    encoded = encode_json(data)
    assert encoded["encoding"] == "record-tables.v1"
    assert compact_json(decode_json(encoded)) == compact_json(data)
    assert len(compact_json(encoded)) < len(compact_json(data)) * 0.6


def test_complete_subtree_is_not_whole_response_coverage():
    view = build_evidence_view('{"a":[1,2],"b":[3]}', "/archive/file", json_pointer="/a")
    assert view["view_complete"] and view["integrity"] == "lossless_selected_subtree"
    assert decode_json(view["data"]) == [1, 2]


def test_source_refs_survive_compaction_and_node_handoff(tmp_path, monkeypatch):
    mw, model, _ = middleware(tmp_path, monkeypatch)
    state = [HumanMessage(content="q"), *exchange(1, 10)]
    for index, message in enumerate(state[2:]):
        message.additional_kwargs = {"aiops_raw_ref": f"/archive/tool-{index}.raw.txt",
                                     "aiops_semantic_success": index != 2}
    assert "aiops_raw_ref" not in str(compact_message(state[2]))
    assert compact_message(state[2], include_refs=True)["provenance"]["aiops_raw_ref"] == "/archive/tool-0.raw.txt"
    update = asyncio.run(mw.abefore_model({"messages": state}, None))
    replaced = add_messages(state, update["messages"])
    catalog = next(tmp_path.glob("budget/compactions/*.sources.json"))
    records = json.loads(catalog.read_text())
    assert len(records) == 10 and records[2]["semantic_success"] is False
    assert records[0]["tool_args"] == {"index": 1}
    assert str(catalog) in replaced[1].content
    payload = {"question": "q", "observations": records,
               "recent_interactions": [compact_message(m, include_refs=True) for m in state[1:]]}
    assert len(source_receipts([HumanMessage(content=json.dumps(payload))])) == 10


@pytest.mark.parametrize("values", [(4096, 6000, 8000), (256, 24000, 8000), (9000, 24000, 8000)])
def test_invalid_configuration_fails_explicitly(monkeypatch, values):
    monkeypatch.setenv("AIOPS_EVIDENCE_VIEW_MODE", "compact")
    for key, value in zip(("RESULT", "HISTORY", "RECENT"), values, strict=False):
        monkeypatch.setenv(f"AIOPS_EVIDENCE_{key}_TOKENS", str(value))
    with pytest.raises(ValueError, match="Evidence budgets"):
        EvidencePolicy.from_env()
