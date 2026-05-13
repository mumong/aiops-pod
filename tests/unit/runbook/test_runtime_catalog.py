import json
from pathlib import Path

import yaml


def test_runtime_catalog_only_exposes_pod_abnormal_mainline_runbooks():
    configmap = Path("deploy/configmap/runbooks.yaml")
    data = yaml.safe_load(configmap.read_text(encoding="utf-8"))
    catalog = json.loads(data["data"]["catalog.json"])

    runbook_ids = {entry["id"] for entry in catalog["catalog"]}

    assert runbook_ids == {
        "pod-evicted",
        "pod-volume-mount-failed",
        "pod-pending-unschedulable",
        "pod-node-lost-unknown",
        "pod-terminating-stuck",
        "pod-oomkilled",
        "pod-crashloop-runtime",
        "pod-imagepull-failed",
        "pod-sandbox-create-failed",
        "pod-config-error",
        "pod-notready-probe-failed",
    }


def test_runtime_configmap_only_contains_pod_abnormal_and_query_prometheus_runbooks():
    configmap = Path("deploy/configmap/runbooks.yaml")
    data = yaml.safe_load(configmap.read_text(encoding="utf-8"))

    allowed = {
        "catalog.json",
        "pod-evicted.md",
        "pod-volume-mount-failed.md",
        "pod-pending-unschedulable.md",
        "pod-node-lost-unknown.md",
        "pod-terminating-stuck.md",
        "pod-oomkilled.md",
        "pod-crashloop-runtime.md",
        "pod-imagepull-failed.md",
        "pod-sandbox-create-failed.md",
        "pod-config-error.md",
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
