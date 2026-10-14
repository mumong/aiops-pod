import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.prompts import get_workflow_prompt


def test_query_prometheus_runbook_declares_query_and_pod_diagnosis_tool_boundary():
    configmap = yaml.safe_load(
        Path("deploy/configmap/runbooks.yaml").read_text(encoding="utf-8")
    )
    query_runbook = configmap["data"]["private-k8s-query-promql-reference.md"]

    assert "/query" in query_runbook
    assert "/ask" in query_runbook
    assert "execute_prometheus_instant_query" in query_runbook
    assert "execute_prometheus_range_query" in query_runbook
    assert "execute_pod_promql" in query_runbook


def test_deployed_workflow_disables_layer_early_stop_by_default():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    layer_early_stop = app_config["workflow"]["layer"]["early_stop"]
    assert layer_early_stop["enabled"] is False
    assert layer_early_stop["explicit_pod_enabled"] is True


def test_deployed_workflow_disables_rca_validation():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    assert app_config["workflow"]["rca_validation"]["enabled"] is False
    assert (
        app_config["workflow"]["rca_context"]["fact_ledger_enabled"]
        is False
    )
    assert (
        app_config["workflow"]["rca_context"]
        ["include_evidence_llm_analysis"]
        is True
    )
    assert app_config["workflow"]["rca_structured_output"]["schema"] == "compact"
    assert (
        app_config["workflow"]["evidence"]
        ["observability_first_round_gate"]["retry_failed_once"]
        is True
    )
    assert (
        app_config["workflow"]["evidence"]
        ["pre_react_observability_baseline"]["enabled"]
        is True
    )


def test_oom_and_liveness_runbooks_contain_scoped_query_shape_examples():
    configmap = yaml.safe_load(
        Path("deploy/configmap/runbooks.yaml").read_text(encoding="utf-8")
    )
    oom = configmap["data"]["pod-oomkilled.md"]
    crashloop = configmap["data"]["pod-crashloop-runtime.md"]
    terminating = configmap["data"]["pod-terminating-stuck.md"]

    for runbook in (oom, crashloop):
        assert '"tool":"execute_pod_promql"' in runbook
        assert '"query_type":"range"' in runbook
        assert '"tool":"query_pod_logs"' in runbook
        assert '"tool":"query_pod_tracing"' in runbook
        assert '"purpose":' in runbook
    assert "container_memory_working_set_bytes" in oom
    assert "kube_pod_container_resource_limits" in oom
    assert "kube_pod_container_status_last_terminated_reason" in oom
    assert '"trace_id":"<trace_id>"' in oom
    assert '"request_resource":"<probe-path>"' in crashloop
    assert "不同 endpoint" in crashloop
    assert "8100 专项查询参考（非强制）" in terminating
    assert "kube_pod_deletion_timestamp" in terminating
    assert '"tool":"query_pod_topology"' in terminating


def test_deployed_config_enables_autonomous_observability_and_disables_compatibility_servers():
    configmap = yaml.safe_load(
        Path("deploy/configmap/config.yaml").read_text(encoding="utf-8")
    )
    app_config = yaml.safe_load(configmap["data"]["config.yaml"])

    autonomous = app_config["mcp_servers"]["aiops-observability-query"]
    assert autonomous["enabled"] is True
    assert autonomous["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8100/sse"
    assert autonomous["config"]["mode"] == "sse"

    prometheus = app_config["mcp_servers"]["prometheus_tool"]
    assert prometheus["enabled"] is True
    assert (
        prometheus["config"]["url"]
        == "http://mcp-server-manager.mcp.svc.cluster.local:8095/sse"
    )
    assert prometheus["config"]["mode"] == "sse"
    assert "/query" in prometheus["description"]
    assert "/ask" in prometheus["description"]
    assert "execute_pod_promql" in prometheus["description"]

    coarse = app_config["mcp_servers"]["aiops-case-coarse"]
    assert coarse["enabled"] is False
    assert coarse["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8089/sse"
    assert coarse["config"]["mode"] == "sse"

    fine = app_config["mcp_servers"]["aiops-observability-fine"]
    assert fine["enabled"] is False
    assert fine["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8090/sse"
    assert fine["config"]["mode"] == "sse"
    assert app_config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert (
        app_config["workflow"]["evidence"]["observability_first_round_gate"]["enabled"]
        is True
    )


def test_workflow_prompts_do_not_contain_json_output_templates():
    prompt_names = [
        "tool_observation_summarizer",
    ]
    forbidden = [
        "```json",
        "只输出 JSON",
        "输出 JSON",
        "纯 JSON",
        "最终 JSON",
        "evidence_plan JSON",
        "JSON 模板",
        "手写 JSON",
        "手写结构化示例",
    ]
    for name in prompt_names:
        prompt = get_workflow_prompt(name)
        assert prompt
        for phrase in forbidden:
            assert phrase not in prompt


def test_deployment_enables_autonomous_evidence_context_stop():
    manifest_path = Path(__file__).resolve().parents[3] / "deploy" / "configmap" / "config.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(manifest["data"]["config.yaml"])

    assert config["workflow"]["evidence"]["observability_mode"] == "autonomous"
    assert config["workflow"]["evidence"]["early_stop"]["enabled"] is True






