import pytest

from app.core.workflow.report_presentation import (
    build_dimension_presentations,
    keep_grounded_narrative,
    render_human_report,
)
from app.core.workflow.schemas import FactLedger, FactRecord


ENTITY_ID = "k8s.pod:demo/example:uid-1"


def fact(
    *,
    fact_id: str,
    dimension: str,
    fact_type: str,
    source_system: str,
    attribute: str,
    value,
    evidence_refs=None,
    directness: str = "direct",
    confidence: str = "high",
) -> FactRecord:
    return FactRecord.model_validate({
        "fact_id": fact_id,
        "entity_id": ENTITY_ID,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "example",
        "dimension": dimension,
        "fact_type": fact_type,
        "attribute": attribute,
        "value": value,
        "source_system": source_system,
        "directness": directness,
        "confidence": confidence,
        "strength": "strong",
        "evidence_refs": (
            evidence_refs
            if evidence_refs is not None
            else ([] if fact_type == "coverage" else [f"ref-{fact_id}"])
        ),
    })


def ledger(records) -> FactLedger:
    return FactLedger.model_validate({
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "case-display",
        "scope_entity_ids": [ENTITY_ID],
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    })


def test_real_signal_wins_over_empty_provider_coverage():
    rows = build_dimension_presentations([ledger([
        fact(
            fact_id="fact-cover001",
            dimension="logging",
            fact_type="coverage",
            source_system="elasticsearch",
            attribute="logging.coverage",
            value={"coverage": "empty"},
        ),
        fact(
            fact_id="fact-log00001",
            dimension="logging",
            fact_type="log",
            source_system="kubernetes",
            attribute="container.previous_log",
            value={"message": "required configuration is missing"},
        ),
    ])])

    row = rows["logging"]

    assert row.state == "partial"
    assert row.sources == ("kubernetes",)
    assert "required configuration is missing" in row.signals[0]
    assert "未获取到" not in row.render_markdown()


def test_deepflow_is_visible_when_tempo_is_empty():
    rows = build_dimension_presentations([ledger([
        fact(
            fact_id="fact-flow0001",
            dimension="tracing",
            fact_type="flow",
            source_system="deepflow",
            attribute="l7_flow",
            value={
                "request_type": "GET",
                "request_resource": "/healthz",
                "response_code": 200,
                "duration_us": "26577",
            },
        ),
        fact(
            fact_id="fact-cover002",
            dimension="tracing",
            fact_type="coverage",
            source_system="tempo",
            attribute="tracing.coverage",
            value={"coverage": "empty"},
        ),
    ])])

    row = rows["tracing"]

    assert row.state == "partial"
    assert row.sources == ("deepflow",)
    assert "**GET /healthz**" in row.signals[0]
    assert "**200**" in row.signals[0]
    assert "未获取到" not in row.render_markdown()


def test_previous_container_log_observation_populates_logging():
    observations = [{
        "tool": "kubectl_previous_logs",
        "semantic_success": True,
        "structured": {
            "status": "logs_summarized",
            "selected_lines": ["allocated 2 MiB; total=62 MiB"],
        },
        "raw_ref": "context-archive:run/tools/previous.raw.txt",
    }]

    row = build_dimension_presentations([], observations)["logging"]

    assert row.state == "present"
    assert row.sources == ("kubectl_previous_logs",)
    assert "**allocated 2 MiB; total=62 MiB**" in row.signals[0]


@pytest.mark.parametrize(
    "observed_state",
    ["OOMKilled", "CreateContainerConfigError", "ErrImagePull"],
)
def test_fault_values_share_one_generic_report_path(observed_state):
    state_fact = fact(
        fact_id="fact-state001",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": observed_state},
    )

    report = render_human_report(
        model_content="",
        ledgers=[ledger([state_fact])],
        validated_claim={
            "diagnostic_status": "diagnosed",
            "confidence": 0.9,
            "claim_validation": {
                "valid": True,
                "valid_supporting_fact_ids": [state_fact.fact_id],
                "valid_contradicting_fact_ids": [],
            },
            "hypotheses": [{
                "entity_id": ENTITY_ID,
                "supporting_fact_ids": [state_fact.fact_id],
                "contradicting_fact_ids": [],
            }],
        },
        dimensions=build_dimension_presentations([ledger([state_fact])]),
    )

    assert "## 诊断概览" in report
    assert "## 现象描述" in report
    assert "## 关键证据" in report
    assert "## 证据关联与因果链" in report
    assert "## 根因结论" in report
    assert f"**{observed_state}**" in report


def test_grounded_paragraph_is_kept_and_hidden_refs_removed():
    state_record = fact(
        fact_id="fact-state002",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "ErrImagePull"},
    )

    result = keep_grounded_narrative(
        "容器状态为 **ErrImagePull**。 <!-- facts:fact-state002 -->",
        records={state_record.fact_id: state_record},
        allowed_fact_ids={state_record.fact_id},
    )

    assert "ErrImagePull" in result
    assert "fact-state002" not in result
    assert "<!--" not in result


def test_narrative_with_unsupported_exact_value_is_rejected():
    metric_record = fact(
        fact_id="fact-metric01",
        dimension="metrics",
        fact_type="measurement",
        source_system="prometheus",
        attribute="container_memory_working_set_bytes",
        value="65953792",
    )

    result = keep_grounded_narrative(
        "内存峰值为 **999Mi**。 <!-- facts:fact-metric01 -->",
        records={metric_record.fact_id: metric_record},
        allowed_fact_ids={metric_record.fact_id},
    )

    assert result == ""


def test_narrative_with_unknown_fact_reference_is_rejected():
    state_record = fact(
        fact_id="fact-state003",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "Running"},
    )

    result = keep_grounded_narrative(
        "状态已确认。 <!-- facts:fact-unknown -->",
        records={state_record.fact_id: state_record},
        allowed_fact_ids={state_record.fact_id},
    )

    assert result == ""


def test_human_report_keeps_grounded_ai_explanation_and_drops_invention():
    state_record = fact(
        fact_id="fact-state004",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "ErrImagePull"},
    )
    current_ledger = ledger([state_record])
    claim = {
        "diagnostic_status": "diagnosed",
        "confidence": 0.9,
        "claim_validation": {
            "valid": True,
            "valid_supporting_fact_ids": [state_record.fact_id],
            "valid_contradicting_fact_ids": [],
        },
    }
    model_content = """## 现象描述
镜像状态为 **ErrImagePull**，这解释了容器尚未启动。 <!-- facts:fact-state004 -->

## 根因结论
镜像下载耗时 **999s**。 <!-- facts:fact-state004 -->
"""

    report = render_human_report(
        model_content=model_content,
        ledgers=[current_ledger],
        validated_claim=claim,
        dimensions=build_dimension_presentations([current_ledger]),
    )

    assert "这解释了容器尚未启动" in report
    assert "999s" not in report
    assert "fact-state004" not in report
    assert "<!--" not in report
