import json
from pathlib import Path

import pytest

from app.core.context.observation import ObservationProcessor


def process(tmp_path, tool, raw, node="query_collect"):
    def forbidden(*args):
        raise AssertionError("Targeted summaries must not rewrite numeric facts with an LLM")

    return ObservationProcessor(archive_root=str(tmp_path), summarizer=forbidden).process(
        run_id="policy",
        node_id=node,
        sequence=1,
        tool_name=tool,
        raw_content=raw,
        preserve_raw=True,
    )


@pytest.mark.parametrize("tool", ["read_context_archive", "fetch_runbook", "custom_tool"])
@pytest.mark.parametrize("node", ["query_collect", "layer", "evidence"])
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
        assert (
            "query_targeted_summary"
            in process(tmp_path, "kubectl_describe", raw, node)["processor"]
        )


@pytest.mark.parametrize("node", ["query_collect", "layer", "evidence", "rca"])
@pytest.mark.parametrize(
    "tool,dimension",
    [
        ("query_pod_logs", "logging"),
        ("query_pod_tracing", "tracing"),
        ("query_pod_topology", "topology"),
    ],
)
def test_heavy_observability_uses_projection_in_raw_first_runtime(tmp_path, node, tool, dimension):
    from tests.unit.context.test_observability_projection import _payload, _record

    records = [
        _record(
            f"fact-{i}",
            dimension,
            {
                "message": "request completed",
                "http_status": 200,
                "response_code": 200,
                "request_resource": "/health",
            },
        )
        for i in range(100)
    ]
    payload = _payload(dimension, records)
    payload.pop("fact_ledger")
    payload["samples"] = records
    raw = json.dumps(payload)
    result = process(tmp_path, tool, raw, node)
    assert "query_targeted_summary" in result["processor"]
    assert "raw_passthrough" not in result["processor"]
    assert len(result["summary"]) < 4000
    assert Path(result["raw_ref"]).read_text() == raw
    assert result["structured"]["agent_projection"]
    assert result["structured"]["retrieval"]["raw_ref"] == result["raw_ref"]
    assert "uid-1" in result["summary"]
    assert "read_context_archive" in result["summary"]


@pytest.mark.parametrize("tool", sorted(ObservationProcessor.LOG_TOOLS))
def test_large_kubectl_logs_use_existing_summary(tmp_path, tool):
    raw = "INFO heartbeat\n" * 1500 + "ERROR OOMKilled memory limit 64Mi\n"
    result = process(tmp_path, tool, raw)
    assert "OOMKilled" in result["summary"]
    assert "64Mi" in result["summary"]
    assert len(result["summary"]) < 4000
    assert Path(result["raw_ref"]).read_text() == raw


def test_log_duplicates_do_not_hide_recovery_or_distinct_status(tmp_path):
    raw = "ERROR /ready status=503\n" * 1000 + "INFO /ready status=200 recovered\n"
    result = process(tmp_path, "kubectl_logs", raw)
    assert "status=503" in result["summary"]
    assert "status=200 recovered" in result["summary"]
    assert result["structured"]["omitted_line_count"] == 999


def test_oversized_log_line_is_not_reported_as_empty(tmp_path):
    result = process(tmp_path, "kubectl_logs", "x" * 10000)
    assert "日志非空" in result["summary"]
    assert "日志为空；" not in result["summary"]


def test_late_error_and_recovery_survive_distinct_noise(tmp_path):
    raw = "\n".join(f"INFO unrelated record {i}" for i in range(2000))
    raw += "\nERROR OOMKilled limit=64Mi\nINFO recovered status=200\n"
    result = process(tmp_path, "kubectl_logs", raw)
    assert "OOMKilled limit=64Mi" in result["summary"]
    assert "recovered status=200" in result["summary"]


def test_memory_growth_endpoints_survive_noise(tmp_path):
    raw = "\n".join(f'{{"allocated_mib": {i}}}' for i in range(2, 50, 2))
    raw += "\n" + "\n".join(f"INFO unrelated record {i}" for i in range(500))
    result = process(tmp_path, "kubectl_logs", raw)
    assert '"allocated_mib": 2' in result["summary"]
    assert '"allocated_mib": 48' in result["summary"]


def test_new_node_cannot_bypass_heavy_tool_policy(tmp_path):
    raw = "INFO heartbeat\n" * 1000
    assert (
        "query_targeted_summary"
        in process(tmp_path, "kubectl_logs", raw, "new_agent")["processor"]
    )


@pytest.mark.parametrize("tool", ["kubernetes_jq_query", "get_label_values"])
def test_json_summary_preserves_whole_records_and_archive(tmp_path, tool):
    data = [{"pod": f"pod-{i}", "value": "123456.789"} for i in range(500)]
    raw = json.dumps({"status": "success", "data": data})
    result = process(tmp_path, tool, raw)
    assert result["structured"]["data"]["data"] == data
    assert result["structured"]["omitted_count"] > 0
    for line in result["summary"].splitlines():
        if line.startswith("{"):
            assert json.loads(line)["value"] == "123456.789"
    assert Path(result["raw_ref"]).read_text() == raw


def test_large_namespace_inventory_is_not_health_filtered(tmp_path):
    raw = "NAME READY STATUS RESTARTS AGE\n" + "\n".join(
        f"healthy-{i} 1/1 Running 0 1d" for i in range(500)
    )
    result = process(tmp_path, "kubectl_get_by_kind_in_namespace", raw)
    assert "healthy-0" in result["summary"]
    assert result["structured"]["omitted_rows"] > 0
    assert "未展示不代表不存在" in result["summary"]


def test_table_padding_does_not_consume_evidence_budget(tmp_path):
    raw = "NAME" + " " * 4000 + "STATUS\n" + "demo" + " " * 4000 + "Running\n"
    result = process(tmp_path, "kubectl_get_by_kind_in_namespace", raw)
    assert "demo  Running" in result["summary"]
    assert result["structured"]["omitted_rows"] == 0
    assert Path(result["raw_ref"]).read_text() == raw


def test_catalog_has_coverage_and_multiple_families(tmp_path):
    raw = json.dumps(
        {
            "status": "success",
            "data": [f"apiserver_metric_{i}" for i in range(1000)]
            + ["node_cpu_seconds_total", "kepler_node_package_joules_total"],
        }
    )
    result = process(tmp_path, "get_metric_names", raw)
    assert "node_cpu_seconds_total" in result["summary"]
    assert "kepler_node_package_joules_total" in result["summary"]
    assert result["structured"]["omitted"] > 0
    assert len(result["summary"]) < 4000


def test_metric_series_keeps_exact_labels_and_values(tmp_path):
    series = [
        {
            "metric": {"__name__": "node_filesystem_avail_bytes", "instance": f"n{i}"},
            "value": [1234, "456789.25"],
        }
        for i in range(200)
    ]
    raw = json.dumps({"status": "success", "data": {"resultType": "vector", "result": series}})
    result = process(tmp_path, "execute_prometheus_instant_query", raw)
    assert "node_filesystem_avail_bytes" in result["summary"]
    assert '"value":[1234,"456789.25"]' in result["summary"]
    assert "省略" in result["summary"]
    assert len(result["summary"]) < 4000


@pytest.mark.parametrize("node", ["query_collect", "layer", "evidence"])
def test_pod_metrics_preserve_runtime_identity_and_whole_time_series(tmp_path, node):
    series = [
        {
            "metric": {
                "__name__": "container_memory_working_set_bytes",
                "namespace": "ns",
                "pod": "p",
                "container": "app",
                "id": f"runtime-{i}",
            },
            "values": [[100, "12"], [110, "24"]],
            "sample_count": 2,
        }
        for i in range(50)
    ]
    raw = json.dumps(
        {
            "ok": True,
            "coverage": "present",
            "dimension": "metrics",
            "status": "query_succeeded",
            "source_system": "prometheus",
            "entity": {"namespace": "ns", "pod": "p"},
            "purpose": "memory",
            "directness": "direct",
            "facts": [],
            "samples": series,
            "evidence_refs": [],
            "truncated": False,
            "limits": {},
            "query": {"query_type": "range"},
            "series": series,
        }
    )
    result = process(tmp_path, "execute_pod_promql", raw, node)
    assert '"id":"runtime-0"' in result["summary"]
    assert '"values":[[100,"12"],[110,"24"]]' in result["summary"]
    assert "独立标签序列" in result["summary"]
    assert "省略" in result["summary"]
    assert "raw_ref" in result["summary"]
    assert Path(result["raw_ref"]).read_text() == raw
