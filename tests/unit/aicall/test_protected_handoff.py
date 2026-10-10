import asyncio
import copy
import json

from app.core.context.handoff import (
    protected_handoff, handoff_from_messages, shared_runbook_projection,
    project_shared_messages,
)
from app.core.workflow.working_material import build_working_material


def material():
    return {"question": "检查异常", "parallel_results": [
        {"group_id": f"g{i}", "target": {"entities": [{"namespace": "ns", "name": f"p{i}"}]},
         "status": "partial" if i == 2 else "completed", "run_id": f"run-g{i}",
         "material": {"observations": [{"tool_name": "arbitrary_tool", "raw_ref": f"/raw/{i}",
             "status": "success", "result": "long body " * 1000}],
             "evidence_receipts": [{"raw_ref": f"/raw/{i}", "coverage": "empty", "group_id": f"g{i}"}],
             "execution_incomplete": ["timeout"] if i == 2 else []}}
        for i in range(3)]}


def test_repeated_compaction_keeps_identity_even_when_model_omits_everything(monkeypatch):
    from app.core.aicall import working_context as wc
    async def lossy(*args, **kwargs):
        return "模型只返回简短摘要，没有对象或证据引用"
    monkeypatch.setattr(wc, "summarize_history", lossy)
    original = material()
    snapshot = copy.deepcopy(original)
    expected = protected_handoff(original)
    compact = asyncio.run(wc.compact_working_material(None, original, window=16000))
    again = asyncio.run(wc.compact_working_material(None, compact, window=16000))
    assert compact["protected_handoff"] == again["protected_handoff"] == expected
    assert original == snapshot
    assert "long body" not in json.dumps(expected)
    assert expected["groups"][2]["execution_incomplete"] == ["timeout"]
    assert len(expected["groups"]) == 3


def test_message_contract_survives_replacement_and_node_handoff():
    expected = protected_handoff(material())
    messages = [{"type": "human", "content": json.dumps(material())}]
    assert handoff_from_messages(messages) == expected
    replacement = [{"type": "human", "content": json.dumps({"protected_handoff": expected})}]
    assert handoff_from_messages(replacement) == expected
    built = build_working_material({"question": "q", "thinking_events": [
        {"type": "context_compacted", "protected_handoff": expected, "working_summary": "s"}]})
    assert built["protected_handoff"] == expected


def test_shared_runbook_does_not_hide_new_read_error_or_unarchived_body():
    obs = {"tool_name": "fetch_runbook", "raw_ref": "/old", "tool_args": {"runbook_id": "generic"},
           "status": "success", "result": "FULL " * 5000}
    projected = shared_runbook_projection(obs, {"/old"})
    assert projected["result"]["shared_reference"] == "/old"
    assert len(json.dumps(projected)) < len(json.dumps(obs)) / 10
    assert obs["result"].startswith("FULL")
    for change in ({"raw_ref": "/new"}, {"raw_ref": None}, {"status": "error"},
                   {"semantic_success": False}, {"tool_name": "other"}):
        item = {**obs, **change}
        assert shared_runbook_projection(item, {"/old"}) == item


def test_shared_message_projection_keeps_call_linkage():
    messages = [{"type": "ai", "tool_calls": [{"id": "c", "name": "fetch_runbook"}]},
                {"type": "tool", "name": "fetch_runbook", "tool_call_id": "c", "content": "FULL",
                 "additional_kwargs": {"aiops_raw_ref": "/old"}}]
    projected = project_shared_messages(messages, {"/old"})
    assert projected[0] == messages[0]
    assert projected[1]["tool_call_id"] == "c"
    assert "/old" in projected[1]["content"]
    assert messages[1]["content"] == "FULL"
