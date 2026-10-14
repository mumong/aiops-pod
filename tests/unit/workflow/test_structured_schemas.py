import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.workflow.schemas import (
    FactLedger,
    FactRecord,
)
from app.core.context.observation import ObservationProcessor


def test_prometheus_http_error_is_semantic_failure():
    processor = ObservationProcessor()

    observation = processor.process(
        run_id="test-prometheus-error",
        node_id="layer",
        sequence=1,
        tool_name="execute_prometheus_instant_query",
        raw_content='{"error": "400 Client Error: Bad Request for url: http://prometheus/api/v1/query?query=bad"}',
    )

    assert observation["semantic_success"] is False
    assert observation["structured"]["status"] == "prometheus_error"
    assert "400 Client Error" in observation["summary"]


def test_prometheus_api_error_preserves_parse_error_and_query():
    processor = ObservationProcessor()

    observation = processor.process(
        run_id="test-prometheus-api-error",
        node_id="layer",
        sequence=1,
        tool_name="execute_prometheus_instant_query",
        raw_content=(
            '{"status":"error","errorType":"bad_data",'
            '"error":"invalid parameter \\"query\\": 1:49: parse error: unexpected character inside braces: \'/\'",'
            '"query":"1 - (node_filesystem_avail_bytes{mountpoint=\\"/\\" / node_filesystem_size_bytes{mountpoint=\\"/\\"})",'
            '"url":"http://prometheus/api/v1/query"}'
        ),
    )

    assert observation["semantic_success"] is False
    assert observation["structured"]["status"] == "prometheus_error"
    assert observation["structured"]["error_type"] == "bad_data"
    assert "unexpected character inside braces" in observation["structured"]["error"]
    assert "node_filesystem_avail_bytes" in observation["structured"]["query"]
    assert "Prometheus errorType: bad_data" in observation["summary"]
    assert "unexpected character inside braces" in observation["summary"]
    assert "PromQL:" in observation["summary"]


def test_prometheus_empty_vector_is_successful_with_empty_coverage():
    processor = ObservationProcessor()

    observation = processor.process(
        run_id="test-prometheus-empty",
        node_id="layer",
        sequence=1,
        tool_name="execute_prometheus_instant_query",
        raw_content='{"status":"success","data":{"resultType":"vector","result":[]}}',
    )

    assert observation["semantic_success"] is True
    assert observation["structured"]["coverage"] == "empty"
    assert observation["structured"]["status"] == "prometheus_empty"
    assert observation["structured"]["result_count"] == 0
    assert "结果为空" in observation["summary"]


def test_fact_schemas_accept_generic_evidence_contract():
    entity_id = "k8s.pod:demo/api:uid-a"
    record = FactRecord.model_validate({
        "fact_id": "fact-000000000001",
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "logging",
        "fact_type": "log",
        "attribute": "log.message",
        "value": {"message": "request returned status 503"},
        "source_system": "elasticsearch",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["logs:target"],
    })
    ledger = FactLedger.model_validate({
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "case-facts",
        "scope_entity_ids": [entity_id],
        "records": [record.model_dump()],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    })
    assert ledger.records[0].fact_id == record.fact_id

