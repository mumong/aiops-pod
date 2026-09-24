"""Characterize full layer/parallel handoffs before extracting instructions."""

import hashlib
import json

import pytest

from app.core.skills.models import Layer
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode as LayerNode
from app.core.workflow.nodes.parallel_evidence import ParallelEvidenceNode as ParallelNode


def outputs():
    result = {}
    layer = LayerNode()
    layer._get_layer_prompt = lambda: "原提示 {literal}\n"
    result["layer_retry"] = layer._get_query_retry_prompt()
    for explicit in (False, True):
        layer._extract_explicit_pod_targets = lambda *args: [("demo", "api")] if explicit else []
        result[f"layer_handoff:{explicit}"] = layer._build_layer_handoff(
            "当前问题 {literal}", {}, Layer.L1, [Layer.L1], [],
        )
    for family in ("", " CrashLoopBackOff "):
        result[f"scenario:{family}"] = layer._default_scenarios_for_abnormal_type(family)
    for name, events in (
        ("empty", []),
        ("mixed", [{"type": "thinking", "result": "omit"}, {
            "type": "tool_result", "tool_name": "kubectl", "status": "error",
            "tool_args": {"q": "中文 {x}\n"}, "result": "失败",
            "structured": {"present": False}, "raw_ref": "archive://原文",
        }]),
    ):
        result[f"baseline:{name}"] = layer._append_explicit_pod_baseline_handoff(
            "问题 {literal}\n\t", events,
        )
    parallel = object.__new__(ParallelNode)
    for name, state, group in (
        ("empty", {}, {}),
        ("fallback", {"question": "当前 {q}"}, {
            "entities": [{"namespace": "ns", "name": "pod"}],
            "status_keywords": ["", "Pending"],
        }),
        ("original", {"original_question": "原问题 {x}\n", "question": "子任务"}, {
            "entities": [{"namespace": "中文", "name": f"pod-{i}"} for i in range(5)],
            "status_keywords": ["Pending", "Terminating"],
            "matched_runbooks": ["book-1"],
        }),
    ):
        scoped = parallel._build_group_state(
            question="unused", state=state, handoff={}, group=group, gid="g1",
        )
        result[f"group:{name}"] = scoped
        result[f"retry:{name}"] = parallel._build_retry_group_state(
            scoped_state=scoped,
            group_state={"thinking_events": [
                {"type": "thinking", "text": "omit"},
                {"type": "tool_result", "result": "事实 {raw}"},
            ], "evidence_analysis": "现有证据"},
            result={"entity_evidence_snapshot": {
                "fact_index": {"valid": {"text": "真实"}, "invalid": None},
                "selection_manifest": {"rca_input_fact_ids": ["missing", "valid", "invalid"]},
            }},
            rca_update={"rca_analysis": '{"summary":"旧结果"}'},
            feedback={"failure_codes": ["missing_evidence"]},
        )
    return result


EXPECTED = {
    'layer_retry': 'c17ac3a7575a12d334d68bc050df0ec73fc422fedbb897b521f573c7c6e44893',
    'layer_handoff:False': '383c8ada7ef36eaec401bcb9897cde7f81e02540ce347425fde4522a8254124e',
    'layer_handoff:True': 'ea6339309903c9600142842a518cabbaffde3273be81e3b6d0ac23ddb1e3983d',
    'scenario:': '6ade360b274544dae862dad5b4d2065453480160c9351b91b842567af87aa45e',
    'scenario: CrashLoopBackOff ': 'eaca957a668b4ad5bd958f7ee191dd19ea29d93d32cd65c3e539c4252bc99caf',
    'baseline:empty': '6055ef2934e6854b57bf7f621365107fcacb8e14f4da7d412047a943c7f101cb',
    'baseline:mixed': 'f8eee33cdb7f0af95945bbc536cc77d0c2fc56fe20787e1c133bad197f335fef',
    'group:empty': 'd89a0cd2af47e6288e8253a7767906e2fa41a6380cef5159a440e90815062ea0',
    'retry:empty': '7a10a6f3d4243ff53d1f5aeabdf90d51f96e7eacdf7ef332eab0da34cfdb31b2',
    'group:fallback': '02f5410f06c05118d4a636cec52d57b425e1a2ee27dd86b6161f031613c19e6e',
    'retry:fallback': 'da1f70691dccda099def333f22df3ad4a6ee6ddbbf44d296d6e158384a32ed29',
    'group:original': '5f6b92507aeeeb56d24e911311f4c35654b6d2b66326bf04b61c092151ad7fb9',
    'retry:original': '67487fcd30c43cecf939c10d931bc1838344962d99e26851360f34fdcaef3bc9',
}


@pytest.mark.parametrize("name", list(outputs()))
def test_complete_handoff_characterization(name):
    value = outputs()[name]
    encoded = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    assert hashlib.sha256(encoded.encode("utf-8")).hexdigest() == EXPECTED[name]


def test_extraction_instructions_preserve_original_text():
    from app.core.prompts import (
        LAYER_EXTRACT_INSTRUCTION,
        LAYER_QUERY_RETRY_EXTRACT_INSTRUCTION,
    )

    assert LAYER_EXTRACT_INSTRUCTION == "基于 layer 阶段工具结果和分析文本生成 Pydantic LayerOutput"
    assert LAYER_QUERY_RETRY_EXTRACT_INSTRUCTION == "基于 QUERY direct 严格重试后的工具结果生成 Pydantic LayerOutput"


def test_handoff_instruction_arrays_are_request_local():
    first = outputs()["layer_handoff:False"]
    first["must_verify"].append("request-local")
    first["do_not_change"].clear()
    fresh = outputs()["layer_handoff:False"]
    assert "request-local" not in fresh["must_verify"]
    assert len(fresh["do_not_change"]) == 3
