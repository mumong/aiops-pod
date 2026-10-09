"""Paginated source facts must reach the model without lossy re-summary."""
import json

from app.core.context.observation import ObservationProcessor
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisStageNode
from app.core.workflow.nodes.query_answer import QueryCollectNode


def test_lifecycle_preserves_large_page_and_recent_termination(tmp_path):
    data = {"contract_version": "pod-lifecycle.v1", "status": "success", "coverage": "partial",
            "next_continue_token": "opaque", "pods": [
                {"name": f"p{i}", "uid": f"uid{i}", "phase": "Running", "containers": [
                    {"ready": True, "last_state": {"terminated": {"reason": "OOMKilled"}},
                     "termination_within_window": True, "restart_count_in_window": None}
                ]} for i in range(50)]}
    raw = json.dumps(data)
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000,
                                     summarizer=lambda *a: "should never replace facts")
    result = processor.process(run_id="lifecycle", node_id="layer", sequence=1,
                               tool_name="query_pod_lifecycle", raw_content=raw)
    assert result["summary"] == raw
    assert result["structured"]["pods"] == data["pods"]
    assert result["structured"]["next_continue_token"] == "opaque"
    assert result["semantic_success"] is True
    assert "query_pod_lifecycle" in DiagnosisStageNode.READ_TOOLS
    assert "query_pod_lifecycle" in QueryCollectNode.READ_TOOLS


def test_lifecycle_errors_are_not_successful_empty_data(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path))
    for raw in ['{"status":"error","coverage":"unknown","error":"Forbidden"}', 'not json']:
        result = processor.process(run_id="bad", node_id="layer", sequence=1,
                                   tool_name="query_pod_lifecycle", raw_content=raw)
        assert result["semantic_success"] is False
        assert result["summary"] == raw
