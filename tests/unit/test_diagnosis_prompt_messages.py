"""Golden method/model inputs captured before diagnosis-template extraction."""

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.skills.models import Layer
from app.core.workflow.nodes import root_cause_analyzer as rca_module
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.schemas import RCACompactOutput, RCAOutput


QUESTION = '问题 {unchanged}\n`Pod` "中文"'
EVIDENCE = '证据 {"key": "value"}\n原始错误'


class CapturedModelCall(BaseException):
    """Escape exception-recovery code at the model boundary, without a call."""


def _capture_rca(mode, schema):
    node = RootCauseAnalyzerNode()
    node.ai_call = object()
    node._get_rca_prompt = lambda: "system layer={layer}\nevidence={evidence_summary}"
    node._model_rca_schema = lambda: schema
    captured = {}

    def call(**kwargs):
        captured.update(kwargs)
        raise CapturedModelCall

    node._call_structured_agent = call
    with pytest.raises(CapturedModelCall):
        getattr(node, f"_analyze_with_llm_{mode}")(QUESTION, Layer.L2, EVIDENCE)
    assert captured["schema"] is schema
    assert captured["use_tools"] is False
    assert captured["allow_text_fallback"] is True
    return [captured["system_prompt"], captured["question"]]


def _repair_context():
    return RootCauseAnalyzerNode._build_rca_repair_context(
        {
            "authoritative_entity_ids": ["Pod/ns/pod"],
            "selection_manifest": {
                "eligible_support_fact_ids": ["f1"],
                "required_context_fact_ids": ["f2"],
            },
            "selected_facts": [
                {"fact_id": "f1", "value": EVIDENCE},
                {"fact_id": "f2", "value": "context"},
                {"fact_id": "ignored"},
            ],
        },
        {
            "phenomenon": QUESTION,
            "root_cause": "unknown",
            "claim_validation": {"reasons": ["missing"], "invalid_fact_ids": ["bad"]},
        },
    )


def _rca_context(ledger):
    node = RootCauseAnalyzerNode()
    node._is_rca_fact_ledger_context_enabled = lambda **kwargs: ledger
    node._extract_tool_data_for_rca = lambda *args, **kwargs: "tool data"
    with patch.object(
        rca_module,
        "extract_fact_ledgers_from_evidence_analysis",
        return_value=[{}] if ledger else [],
    ):
        return node._build_rca_context(
            {"layer_handoff": {}, "layer_analysis": "{}", "evidence_analysis": "{}"}
        )


def _quality_context():
    node = RootCauseAnalyzerNode()
    node._is_rca_fact_ledger_context_enabled = lambda **kwargs: True
    result = node._extract_tool_data_for_rca(
        json.dumps(
            {
                "source_coverage": {"metrics": "present"},
                "unresolved_questions": [QUESTION],
            },
            ensure_ascii=False,
        )
    )
    assert "不能替代 diagnostic_sufficiency" in result
    return result


def _conclusion_node():
    node = ConclusionFormatterNode()
    node._get_conclusion_prompt = lambda: "report system {literal}"
    node._archive_node_input = lambda value: None
    node._estimate_tokens = lambda text: len(text)
    node._resolve_context_token_budget = lambda **kwargs: 100000
    return node


def _capture_report(tool_data, constrained=False):
    node = _conclusion_node()
    node._build_evidence_summary = lambda value: value
    node._build_rca_summary = lambda value: value
    if constrained:
        node._resolve_context_token_budget = lambda **kwargs: 400
    captured = {}

    def call(**kwargs):
        captured.update(kwargs)
        return "report"

    node.ai_call = SimpleNamespace(call_simple=call)
    node._generate_with_llm(
        question=QUESTION,
        layer_analysis="layer " * (250 if constrained else 1),
        evidence_analysis=EVIDENCE * (100 if constrained else 1),
        rca_analysis="rca",
        tool_data_text=tool_data,
        layer=Layer.L2,
    )
    return [captured["system_prompt"], captured["question"]]


def _capture_query(has_data):
    node = _conclusion_node()
    captured = {}

    def call(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(markdown_report="query report"), None, []

    node._call_structured_agent = call
    node._generate_query_with_llm(
        question=QUESTION,
        tool_data_text=EVIDENCE if has_data else "",
        query_result={"rows": [{"text": EVIDENCE}]} if has_data else None,
        max_tokens=200,
    )
    assert captured["use_tools"] is False
    assert captured["use_native_structured"] is False
    return [captured["system_prompt"], captured["question"]]


def _capture_group(group_id):
    node = _conclusion_node()
    node._build_multi_group_report_context = lambda question, groups, **kwargs: {
        "question": question,
        "groups": groups,
        **kwargs,
    }
    node._normalize_group_report_fragment = lambda content, **kwargs: content
    node._render_multi_group_overview = lambda question, groups: "overview"
    node._conclusion_lane_concurrency = lambda count: 1
    captured = {}

    def call(**kwargs):
        captured.update(kwargs)
        return "fragment"

    node.ai_call = SimpleNamespace(call_simple=call)
    groups = [{"group_id": group_id, "fact": EVIDENCE}]
    node._generate_multi_group_report_with_agent(
        question=QUESTION, group_results=groups, conclusion_max_tokens=None
    )
    return [captured["system_prompt"], captured["question"]]


CASES = {
    "compact_contract": lambda: RootCauseAnalyzerNode._rca_schema_contract(RCACompactOutput),
    "full_contract": lambda: RootCauseAnalyzerNode._rca_schema_contract(RCAOutput),
    "rca_user": lambda: RootCauseAnalyzerNode._build_rca_user_message(QUESTION, EVIDENCE),
    "rca_user_empty": lambda: RootCauseAnalyzerNode._build_rca_user_message("", ""),
    "lite_compact": lambda: _capture_rca("lite", RCACompactOutput),
    "lite_full": lambda: _capture_rca("lite", RCAOutput),
    "full_compact": lambda: _capture_rca("full", RCACompactOutput),
    "full_full": lambda: _capture_rca("full", RCAOutput),
    "repair_context": _repair_context,
    "ledger_context": lambda: _rca_context(True),
    "narrative_context": lambda: _rca_context(False),
    "quality_context": _quality_context,
    "report": lambda: _capture_report(EVIDENCE),
    "report_empty_tools": lambda: _capture_report(""),
    "report_constrained": lambda: _capture_report(EVIDENCE * 400, constrained=True),
    "query": lambda: _capture_query(True),
    "query_empty": lambda: _capture_query(False),
    "group": lambda: _capture_group("g{literal}"),
    "group_fallback_id": lambda: _capture_group(""),
}
EXPECTED_DIGESTS = {
    "compact_contract": "fa5629189f799ca51a8804692b2234ebb1c370d6fb43874238ead591e7ab9208",
    "full_contract": "88eeedc1981c0d2e50c75bf0c122cde19fbf3c61915bd4c01688953732c4c1c9",
    "rca_user": "e8f647330d46e0ebfa3a4e102c7df19016ec1d6528fcebaa163425eca0878399",
    "rca_user_empty": "365056a3ced611d0afd30b61f06eaedc720f197819e3d776526bf24d013f8389",
    "lite_compact": "05837afce6b2b8b817e5477769c9f300d6b2af67ce43e617f4d7c026aca9ae2d",
    "lite_full": "3188444e56625c8ed4a5230831a2343cdbbb6cf6948b5f612289358937a4c16f",
    "full_compact": "ecdca0bf79685713e27f2d55ed46f3709113f72250885403af74cf4566087ba5",
    "full_full": "f5c4e07130d40e3c31d7338f398426d15d40c121545482add371aa4a034caea0",
    "repair_context": "3b8f2278f661b1f65ddb9fdb205477c8bbf780a0cb6494e18488bd5706e3e57a",
    "ledger_context": "6d544d5c80a571e0b29c704fe73e83b6c5f9cf2c0765d1dde09b7e28d288d8ef",
    "narrative_context": "61ad54a12752fd99900550c1e87144fd147cfc83273cb816e759d728429afe7d",
    "quality_context": "57ef1280e708b650a7d3298b682b4cc6205ddd6920eb7e5e96670f0b55ca826c",
    "report": "a1184d22a977dd0b23e97ecaaf58ccf22059449f76449449ca93050e967c95d9",
    "report_empty_tools": "8bec8c715df3d006e8c8cf8b80b13af880507f2354ea98b5e59a2eb7beb95ea9",
    "report_constrained": "a45922d10e116b373a792b1adcaa3f2640e4c4eafcc87af9d71675ecc3d61276",
    "query": "dadf21bd217f91ae52bb74a538e08b6ae85eaea70f43cdb3e7d221ea05472b09",
    "query_empty": "e016f96d7ee6e3e3bc0958c98a5d04e2c575b8a8d12b1c6b618b169889d4df1e",
    "group": "1317650fd605d805c76fe601ba05cba80d846d496fdb0b2b4933b51d9da9c0b3",
    "group_fallback_id": "24d3bf5b9885e4700e3d08abab1ca5d38e5e2ce9a32f15aaada5d7ef88a45de5",
}


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


@pytest.mark.parametrize("case", CASES)
def test_diagnosis_message_bytes(case):
    assert _digest(CASES[case]()) == EXPECTED_DIGESTS[case]


def test_group_report_fact_encoding_contract():
    context = ConclusionFormatterNode._build_multi_group_report_context(QUESTION, [])
    assert context["fact_encoding"] == {
        "authority": "canonical normalized facts",
        "aggregation": (
            "repeated logs and equivalent L7 flows may be structurally grouped; "
            "counts, time ranges, numeric ranges, trace_ids and fact_ids remain explicit"
        ),
        "trend_rule": (
            "metric trend is valid only when trend_evaluable=true and sample_count>=2"
        ),
    }
