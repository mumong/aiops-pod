import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.skills.models import Layer
from app.core.workflow.graph import _make_evidence_router, _make_layer_router


def test_layer_router_sends_query_to_evidence():
    router = _make_layer_router(["layer", "evidence", "rca", "conclusion"])

    assert router({"layer": Layer.QUERY}) == "evidence"


def test_layer_router_sends_healthy_to_conclusion():
    router = _make_layer_router(["layer", "evidence", "rca", "conclusion"])

    assert router({"layer": Layer.HEALTHY}) == "conclusion"


def test_layer_router_sends_diagnostic_layers_to_next_node():
    router = _make_layer_router(["layer", "evidence", "rca", "conclusion"])

    assert router({"layer": Layer.L0}) == "evidence"
    assert router({"layer": Layer.L2}) == "evidence"


def test_evidence_router_routes_query_to_conclusion():
    router = _make_evidence_router(["layer", "evidence", "rca", "conclusion"])

    assert router({"layer": Layer.QUERY}) == "rca"
    assert router({"layer": Layer.L2}) == "rca"
