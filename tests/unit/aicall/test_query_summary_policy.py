import json
from pathlib import Path

import pytest

from app.core.context.observation import ObservationProcessor


def process(tmp_path, tool, raw, node="query_collect"):
    def forbidden(*args):
        raise AssertionError("Targeted summaries must not rewrite numeric facts with an LLM")
    return ObservationProcessor(archive_root=str(tmp_path), summarizer=forbidden).process(
        run_id="policy", node_id=node, sequence=1, tool_name=tool,
        raw_content=raw, preserve_raw=True)


@pytest.mark.parametrize("tool", ["read_context_archive", "fetch_runbook", "custom_tool",
                                  "kubectl_get_by_kind_in_namespace"])
@pytest.mark.parametrize('node', ['query_collect', 'layer', 'evidence'])
def test_excluded_tools_remain_exact(tmp_path, tool, node):
    raw = "original\n" * 2000
    assert process(tmp_path, tool, raw, node)["summary"] == raw


@pytest.mark.parametrize("tool", sorted(ObservationProcessor.QUERY_SUMMARY_TOOLS))
def test_small_outputs_remain_exact(tmp_path, tool):
    assert process(tmp_path, tool, "error: missing pod")["summary"] == "error: missing pod"


def test_large_describe_is_archived_and_summarized(tmp_path):
    raw = "Name: demo\nNamespace: xnet\nReason: OOMKilled\n" + "noise\n" * 3000
    result = process(tmp_path, "kubectl_describe", raw)
    assert "query_targeted_summary" in result["processor"]
    assert "OOMKilled" in result["summary"]
    assert len(result["summary"]) < 4000
    assert Path(result["raw_ref"]).read_text() == raw
    assert "raw_ref" in result["summary"]
    for node in ("layer", "evidence"):
        assert "query_targeted_summary" in process(tmp_path, "kubectl_describe", raw, node)["processor"]


def test_catalog_has_coverage_and_multiple_families(tmp_path):
    raw = json.dumps({"status": "success", "data":
                      [f"apiserver_metric_{i}" for i in range(1000)] +
                      ["node_cpu_seconds_total", "kepler_node_package_joules_total"]})
    result = process(tmp_path, "get_metric_names", raw)
    assert "node_cpu_seconds_total" in result["summary"]
    assert "kepler_node_package_joules_total" in result["summary"]
    assert result["structured"]["omitted"] > 0
    assert len(result["summary"]) < 4000


def test_metric_series_keeps_exact_labels_and_values(tmp_path):
    series = [{"metric": {"__name__": "node_filesystem_avail_bytes", "instance": f"n{i}"},
               "value": [1234, "456789.25"]} for i in range(200)]
    raw = json.dumps({"status": "success", "data": {"resultType": "vector", "result": series}})
    result = process(tmp_path, "execute_prometheus_instant_query", raw)
    assert "node_filesystem_avail_bytes" in result["summary"]
    assert '"value":[1234,"456789.25"]' in result["summary"]
    assert "省略" in result["summary"]
    assert len(result["summary"]) < 4000


@pytest.mark.parametrize('node', ['query_collect', 'layer', 'evidence'])
def test_pod_metrics_preserve_runtime_identity_and_whole_time_series(tmp_path, node):
    series = [{'metric': {'__name__': 'container_memory_working_set_bytes',
                         'namespace': 'ns', 'pod': 'p', 'container': 'app', 'id': f'runtime-{i}'},
               'values': [[100, '12'], [110, '24']], 'sample_count': 2}
              for i in range(50)]
    raw = json.dumps({'ok': True, 'coverage': 'present', 'dimension': 'metrics',
                      'status': 'query_succeeded', 'source_system': 'prometheus',
                      'entity': {'namespace': 'ns', 'pod': 'p'}, 'purpose': 'memory',
                      'directness': 'direct', 'facts': [], 'samples': series,
                      'evidence_refs': [], 'truncated': False, 'limits': {},
                      'query': {'query_type': 'range'}, 'series': series})
    result = process(tmp_path, 'execute_pod_promql', raw, node)
    assert '"id":"runtime-0"' in result['summary']
    assert '"values":[[100,"12"],[110,"24"]]' in result['summary']
    assert '独立标签序列' in result['summary']
    assert '省略' in result['summary']
    assert 'raw_ref' in result['summary']
    assert Path(result['raw_ref']).read_text() == raw
