import json
from pathlib import Path

import yaml


def test_runtime_catalog_only_exposes_pod_abnormal_mainline_runbooks():
    configmap = Path("deploy/configmap/runbooks.yaml")
    data = yaml.safe_load(configmap.read_text(encoding="utf-8"))
    catalog = json.loads(data["data"]["catalog.json"])

    runbook_ids = {entry["id"] for entry in catalog["catalog"]}

    assert runbook_ids == {
        "l0-volume-limit",
        "pod-volume-mount-failed",
        "l1-taint-node",
        "pod-node-lost-unknown",
        "pod-terminating-stuck",
        "l2-oomkilled",
        "pod-crashloop-runtime",
        "l3-imagepull-failed",
        "pod-sandbox-create-failed",
        "l4-config-bootstrap-fail",
        "pod-notready-probe-failed",
    }


def test_runtime_configmap_only_contains_pod_abnormal_and_query_prometheus_runbooks():
    configmap = Path("deploy/configmap/runbooks.yaml")
    data = yaml.safe_load(configmap.read_text(encoding="utf-8"))

    allowed = {
        "catalog.json",
        "l0-volume-limit.md",
        "pod-volume-mount-failed.md",
        "l1-taint-node.md",
        "pod-node-lost-unknown.md",
        "pod-terminating-stuck.md",
        "l2-oomkilled.md",
        "pod-crashloop-runtime.md",
        "l3-imagepull-failed.md",
        "pod-sandbox-create-failed.md",
        "l4-config-bootstrap-fail.md",
        "pod-notready-probe-failed.md",
        "private-k8s-query-promql-reference.md",
    }

    assert set(data["data"]) == allowed
    assert "private-k8s-health-reference.md" not in data["data"]
    assert "query-reference.md" not in data["data"]
    assert "l4-dependency-503.md" not in data["data"]


def test_runtime_runbooks_do_not_expose_legacy_operation_layer_language():
    configmap = Path("deploy/configmap/runbooks.yaml")
    text = configmap.read_text(encoding="utf-8")

    forbidden_phrases = [
        "Pod异常/L",
        "服务网络层",
        "应用层",
        "基础设施层",
        "工作负载层",
        "集群与节点层",
        "derived_layer",
    ]

    for phrase in forbidden_phrases:
        assert phrase not in text
