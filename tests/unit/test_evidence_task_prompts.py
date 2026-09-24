"""Golden final model messages captured before evidence task extraction."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.schemas import EvidencePlanOutput


QUESTION = "中文问题 {literal}\n`quote`"


def _capture_plan(trailing):
    node = EvidenceCollectorNode()
    captured = {}

    def call(**kwargs):
        captured.update(kwargs)
        return None, "raw"

    node.ai_call = SimpleNamespace(call_structured=call)
    assert node._generate_structured_evidence_plan(
        "system {literal}" + trailing, QUESTION, "L1"
    ) == ([], "raw")
    assert captured["schema"] is EvidencePlanOutput
    assert captured["max_tokens"] == 2048
    return captured


def _capture_refinement(tool_name, refs):
    node = EvidenceCollectorNode()
    node.tools = [
        SimpleNamespace(name=name) for name in (tool_name, "kubectl_describe", "fetch_runbook")
    ]
    cases = [
        {
            "case_id": "case-中文",
            "detail": "{value}\n`text`",
            "recommended_refs_by_dimension": refs,
        },
        {"case_id": ""},
    ]
    node._build_post_case_refinement_payload = lambda events: {
        "cases": cases,
        "ignored": "old behavior",
    }
    captured = {}

    def call(question, system_prompt, **kwargs):
        captured.update(question=question, system_prompt=system_prompt, **kwargs)
        return "response", []

    node._call_llm = call
    assert node._run_post_case_evidence_refinement(
        question=QUESTION, thinking_events=[], tool_result_sequence_start=7
    ) == ("response", [])
    assert captured["skip_remediation_policy"] is True
    assert captured["tool_result_sequence_start"] == 7
    assert "kubectl_describe" in captured["blocked_tool_names"]
    assert tool_name not in captured["blocked_tool_names"]
    return captured


def _capture_reconciliation(matched):
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name=name) for name in ("fetch_runbook", "kubectl_describe")]
    node._format_completed_mandatory_summary = lambda events: "case 中文 {facts}\nline"
    node._format_post_case_detail_summary = lambda events: "detail {raw}\n`tail`"
    captured = {}

    def call(question, system_prompt, **kwargs):
        captured.update(question=question, system_prompt=system_prompt, **kwargs)
        return "response", []

    node._call_llm = call
    assert node._run_post_case_runbook_reconciliation(
        question=QUESTION,
        layer_analysis=json.dumps({"matched_runbooks": matched}),
        thinking_events=[],
        tool_result_sequence_start=9,
    ) == ("response", [])
    assert captured["skip_remediation_policy"] is True
    assert captured["tool_result_sequence_start"] == 9
    assert "kubectl_describe" in captured["blocked_tool_names"]
    assert "fetch_runbook" not in captured["blocked_tool_names"]
    return captured


CASES = {
    "plan_plain": lambda: _capture_plan(""),
    "plan_trailing": lambda: _capture_plan(" \n\t"),
    "refinement_refs": lambda: _capture_refinement(
        "get_aiops_case_evidence", {"logs": ["logs.中文"]}
    ),
    "refinement_fine_tool": lambda: _capture_refinement("query_aiops_logs", {}),
    "runbook_empty": lambda: _capture_reconciliation([]),
    "runbook_string": lambda: _capture_reconciliation("one.md"),
    "runbook_normalized": lambda: _capture_reconciliation(
        ["one.md", "one", "dir/two", "bad id", ""]
    ),
}
EXPECTED_DIGESTS = {
    "plan_plain": "b980f50d38238aba984d244bf7f6b0a13f229517fb2be9230e0afbb9c3d8a6c5",
    "plan_trailing": "b980f50d38238aba984d244bf7f6b0a13f229517fb2be9230e0afbb9c3d8a6c5",
    "refinement_refs": "a9612fe32c578ad223bf02b06fa48cad3e7573bc6aeb87fc3374c85aed402e8c",
    "refinement_fine_tool": "b4d7e0306b5382c66dc84fc804c16267b518fb3eb49167fcde97382369e94384",
    "runbook_empty": "2d0e4c971b3a477b1e7c5e831f033e9305b42f04d2325f30e3765f6d368f4ee0",
    "runbook_string": "63cf5fcfdffffecfd74a7d603f5db0e5c4c446aa04dadee323d6ad303718bcd6",
    "runbook_normalized": "d9cdde68b946b1a1b68b4306211b42a6a1556be5228ec78e1d30dbe72a864586",
}


def _message_digest(captured):
    return hashlib.sha256(
        json.dumps(
            [captured["system_prompt"], captured["question"]],
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


@pytest.mark.parametrize("case", CASES)
def test_final_evidence_message_bytes(case):
    assert _message_digest(CASES[case]()) == EXPECTED_DIGESTS[case]


@pytest.mark.parametrize("skip", ["budget", "no_case", "no_tool"])
def test_refinement_skip_conditions_do_not_call_model(skip):
    node = EvidenceCollectorNode()
    node.tools = []
    node._build_post_case_refinement_payload = lambda events: {
        "cases": [] if skip == "no_case" else [{"case_id": "case"}]
    }
    node._call_llm = lambda *args, **kwargs: pytest.fail("skip branch called model")
    events = [{"context_usage_ratio": 0.8}] if skip == "budget" else []
    assert node._run_post_case_evidence_refinement(
        question=QUESTION, thinking_events=events, tool_result_sequence_start=0
    ) == (None, [])


def test_reconciliation_without_case_summary_does_not_call_model():
    node = EvidenceCollectorNode()
    node._format_completed_mandatory_summary = lambda events: ""
    node._call_llm = lambda *args, **kwargs: pytest.fail("empty summary called model")
    assert node._run_post_case_runbook_reconciliation(
        question=QUESTION, layer_analysis="{}", thinking_events=[], tool_result_sequence_start=0
    ) == (None, [])
