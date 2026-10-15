"""Evidence lanes present real observability tools first; nothing is hidden by the order."""

from types import SimpleNamespace

from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode, DiagnosisStageNode


def _tools(*names):
    return [SimpleNamespace(name=n) for n in names]


def test_evidence_lane_orders_observability_tools_first_and_keeps_the_rest_stable():
    node = DiagnosisEvidenceNode()
    ordered = node.order_tools(
        _tools(
            "kubectl_describe",
            "query_pod_logs",
            "fetch_runbook",
            "execute_pod_promql",
            "kubectl_events",
            "query_pod_topology",
        )
    )
    assert [t.name for t in ordered] == [
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_topology",
        "kubectl_describe",
        "fetch_runbook",
        "kubectl_events",
    ]


def test_layer_stage_keeps_service_order():
    node = DiagnosisStageNode()
    names = ["kubectl_describe", "query_pod_lifecycle", "fetch_runbook"]
    assert [t.name for t in node.order_tools(_tools(*names))] == names
