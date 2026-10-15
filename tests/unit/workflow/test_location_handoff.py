"""Identity survives compaction; bulk evidence and prose do not become protected."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from app.core.aicall import working_context
from app.core.context.handoff import handoff_from_messages, protected_handoff
from app.core.context.lifecycle_core import messages_without_core
from app.core.workflow.diagnosis_contract import LocationHandoff, scoped_handoff
from app.core.workflow.nodes.autonomous_parallel import plan_groups
from app.core.workflow.working_material import build_working_material


def handoff(count=4):
    return LocationHandoff(
        targets=[
            dict(
                target_id=f"t{i}",
                entity=dict(kind="Pod", namespace="ns", name=f"p{i}"),
                issue="observed failure",
                evidence_refs=[f"/raw/{i}"],
            )
            for i in range(count)
        ]
    ).model_dump()


@pytest.mark.parametrize("count", [0, 1, 4, 20])
def test_all_selected_entities_become_groups_without_model_reextraction(count):
    result = plan_groups(SimpleNamespace(), {"diagnosis_handoff": handoff(count)})
    assert len(result["autonomous_groups"]) == count


def test_bulk_lifecycle_is_summarizable_but_available_before_compaction(monkeypatch):
    record = {
        "contract_version": "pod-lifecycle.v1",
        "status": "success",
        "pods": [
            {"namespace": "ns", "name": f"healthy-{i}", "phase": "Running"} for i in range(72)
        ],
    }
    state = {
        "question": "diagnose",
        "diagnosis_handoff": handoff(),
        "thinking_events": [
            {
                "type": "tool_result",
                "tool_name": "query_pod_lifecycle",
                "result": record,
                "raw_ref": "/raw/all",
                "status": "success",
            }
        ],
    }
    material = build_working_material(state)
    assert material["observations"][0]["result"] == record
    assert "lifecycle_core" not in material["protected_handoff"]
    seen = []

    async def summarize(model, question, text, *args, **kwargs):
        seen.append(text)
        return "summary of evidence, original at /raw/all"

    monkeypatch.setattr(working_context, "summarize_history", summarize)
    monkeypatch.setattr(working_context, "partition_recent", lambda groups, window: (groups, []))
    for _ in range(3):
        material = asyncio.run(
            working_context.compact_working_material(None, material, window=54000)
        )
        assert material["protected_handoff"]["diagnosis_handoff"] == handoff()
        assert "lifecycle_core" not in material["protected_handoff"]
    assert "healthy-71" in seen[0]
    assert "healthy-71" not in json.dumps(material)
    assert "/raw/all" in json.dumps(material)


def test_agent_middleware_does_not_reprotect_new_lifecycle_tools():
    payload = build_working_material({"question": "q", "diagnosis_handoff": handoff()})
    messages = [
        {"role": "user", "content": json.dumps(payload)},
        {
            "role": "tool",
            "content": json.dumps(
                {
                    "contract_version": "pod-lifecycle.v1",
                    "status": "success",
                    "pods": [{"namespace": "ns", "name": "p"}],
                }
            ),
        },
    ]
    assert messages_without_core(messages) == messages
    protected = handoff_from_messages(messages)
    assert protected["diagnosis_handoff"] == handoff()
    assert "lifecycle_core" not in protected


def test_parallel_fanin_protects_identities_not_analysis_or_lifecycle():
    root = handoff()
    lanes = [
        {
            "group_id": f"g{i}",
            "status": "completed",
            "material": build_working_material(
                {
                    "question": "q",
                    "diagnosis_handoff": scoped_handoff(root, f"t{i}"),
                    "query_draft": "long RCA narrative " * 1000,
                }
            ),
        }
        for i in range(4)
    ]
    material = build_working_material(
        {"question": "q", "diagnosis_handoff": root, "autonomous_group_results": lanes}
    )
    protected = protected_handoff(material)
    assert len(protected["groups"]) == 4
    assert "long RCA narrative" not in json.dumps(protected)
    assert "lifecycle_core" not in protected
    assert len(json.dumps(protected)) < 6000


def test_quick_query_keeps_previous_lifecycle_policy():
    material = build_working_material(
        {
            "question": "q",
            "thinking_events": [
                {
                    "type": "tool_result",
                    "result": {
                        "contract_version": "pod-lifecycle.v1",
                        "status": "success",
                        "pods": [{"namespace": "ns", "name": "p"}],
                    },
                }
            ],
        }
    )
    assert "lifecycle_core" in material["protected_handoff"]
