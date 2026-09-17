import json
import pytest

from langchain_core.tools import StructuredTool

from app.core.workflow.task_tools import scope_tool, promql_scope_error


@pytest.mark.parametrize("query", [
    'sum by(pod)(rate(container_cpu_usage_seconds_total{namespace="xnet",container!="POD"}[5m])) * 1000',
    'max_over_time(container_memory_working_set_bytes{namespace="xnet"}[1h:5m])',
    'sum(a{namespace="xnet"}) / sum(b{namespace="xnet"})',
    'a{namespace=~"^(xnet|team-a)$"}',
    'a{namespace="xnet"} or b{namespace="team-a"}',
    'node_memory_MemAvailable_bytes{instance="10.2.0.48:9100"}',
    'vector(1)',
])
def test_scoped_promql_keeps_complex_expressions(query):
    assert promql_scope_error(query, ["xnet", "team-a"]) is None


@pytest.mark.parametrize("query", [
    'sum(rate(container_cpu_usage_seconds_total[5m]))',
    'a{namespace="other"}',
    'a{namespace="xnet"} + b{namespace="other"}',
    'a{namespace=~"xnet|other"}',
    'a{namespace=~"xnet.*"}',
    'a{namespace!="other"}',
    'a{label="namespace=\\"xnet\\""}',
    'node_memory_MemAvailable_bytes',
    'sum(',
])
def test_unbounded_or_cross_namespace_selector_is_rejected(query):
    assert promql_scope_error(query, ["xnet", "team-a"])


def test_namespace_guard_rejects_wrong_or_missing_scope_without_calling_backend():
    calls = []

    def lookup(kind: str, namespace: str = "") -> str:
        """Read a resource."""
        calls.append((kind, namespace))
        return "observed"

    original = StructuredTool.from_function(lookup)
    guarded = scope_tool(original, ["xnet"])
    assert json.loads(guarded.invoke({"kind": "pod", "namespace": "other"}))["status"] == "tool_error"
    assert json.loads(guarded.invoke({"kind": "pod"}))["status"] == "tool_error"
    assert calls == []
    assert guarded.invoke({"kind": "pod", "namespace": "xnet"}) == "observed"
    assert guarded.invoke({"kind": "node"}) == "observed"
    assert original.invoke({"kind": "pod", "namespace": "other"}) == "observed"
