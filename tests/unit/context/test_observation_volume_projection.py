"""Regression contracts for source-preserving Kubernetes diagnostic summaries."""

import json
from pathlib import Path

import pytest
import yaml

from app.core.context.observation import ObservationProcessor


@pytest.mark.parametrize("source,spec,legacy_name", [
    ("secret", {"secretName": "missing-secret", "optional": False,
                "items": [{"key": "token", "path": "token.txt"}]}, "missing-secret"),
    ("configMap", {"name": "existing-config", "optional": False,
                   "items": [{"key": "missing-key", "path": "app.conf"}]}, "existing-config"),
    ("persistentVolumeClaim", {"claimName": "missing-claim", "readOnly": True}, "missing-claim"),
    ("hostPath", {"path": "/var/lib/missing-input", "type": "Directory"}, None),
])
def test_pod_volume_projection_preserves_source_fields(source, spec, legacy_name):
    doc = {"kind": "Pod", "metadata": {"name": "workload", "namespace": "sample"},
           "spec": {"volumes": [{"name": "input", source: spec}],
                    "containers": [{"name": "app", "volumeMounts": [
                        {"name": "input", "mountPath": "/input", "readOnly": True}]}]}}
    structured, summary, _ = ObservationProcessor()._extract_yaml(yaml.safe_dump(doc))
    volume = structured["volumes"][0]
    assert volume["source_details"][source] == spec
    if legacy_name is not None:
        assert volume[source] == legacy_name
    assert structured["containers"][0]["volumeMounts"] == doc["spec"]["containers"][0]["volumeMounts"]
    rendered_volume = json.loads(summary.split("\nvolumes:\n- ", 1)[1])
    assert rendered_volume["source_details"][source] == spec
    assert '"mountPath": "/input"' in summary


def test_volume_projection_does_not_invent_optional_or_type():
    raw = yaml.safe_dump({"kind": "Pod", "spec": {"volumes": [
        {"name": "input", "secret": {"secretName": "referenced-secret"}},
        {"name": "local", "hostPath": {"path": "/data/input"}},
    ]}})
    structured, _, _ = ObservationProcessor()._extract_yaml(raw)
    assert "optional" not in structured["volumes"][0]["source_details"]["secret"]
    assert "type" not in structured["volumes"][1]["source_details"]["hostPath"]


def test_configmap_projection_preserves_key_inventory_without_values():
    raw = yaml.safe_dump({"apiVersion": "v1", "kind": "ConfigMap",
        "metadata": {"name": "input", "namespace": "sample", "uid": "uid-one",
                     "resourceVersion": "123"},
        "data": {"available-key": "PRIVATE_CONFIG_VALUE"},
        "binaryData": {"binary-key": "PRIVATE_BINARY_VALUE"}})
    structured, summary, _ = ObservationProcessor()._extract_yaml(raw)
    assert structured["data_keys"] == ["available-key"]
    assert structured["binary_data_keys"] == ["binary-key"]
    assert structured["uid"] == "uid-one"
    assert structured["resourceVersion"] == "123"
    assert "available-key" in summary and "binary-key" in summary
    assert "PRIVATE_CONFIG_VALUE" not in json.dumps(structured) + summary
    assert "PRIVATE_BINARY_VALUE" not in json.dumps(structured) + summary


def test_yaml_diagnostic_not_found_is_not_a_failed_invocation():
    raw = yaml.safe_dump({"kind": "Pod", "metadata": {"name": "workload"},
        "status": {"phase": "Pending", "conditions": [{"type": "Ready", "status": "False",
            "message": 'secret "input" not found'}]}})
    structured, summary, _ = ObservationProcessor()._extract_yaml(raw)
    assert structured["status"] == "yaml_summarized"
    assert 'secret "input" not found' in summary


def test_actual_failed_yaml_is_still_failed():
    structured, _, _ = ObservationProcessor()._extract_yaml(
        'Command failed (exit 1):\nkubectl get pod missing -o yaml\n'
        'Error from server (NotFound): pods "missing" not found')
    assert structured["status"] == "command_failed"


def test_describe_keeps_equal_values_in_distinct_field_scopes():
    raw = """Name: workload
Namespace: sample
Status: Pending
Containers:
  app:
    Image: example/app
    Limits:
      cpu: 100k
      memory: 1Pi
    Requests:
      cpu: 100k
      memory: 1Pi
  sidecar:
    Image: example/app
    Limits:
      cpu: 100k
      memory: 1Pi
    Requests:
      cpu: 100k
      memory: 1Pi
Volumes:
  first:
    Type: Secret (a volume populated by a Secret)
    SecretName: first-secret
    Optional: false
  second:
    Type: Secret (a volume populated by a Secret)
    SecretName: second-secret
    Optional: false
Events:
  Type Reason Age From Message
  Warning FailedMount 1s kubelet secret "first-secret" not found
"""
    sections = ObservationProcessor._extract_describe_pod_sections(raw)
    summary = "\n".join(sections["summary_lines"])
    assert summary.count("cpu: 100k") == 4
    assert summary.count("memory: 1Pi") == 4
    assert summary.count("Limits:") == 2 and summary.count("Requests:") == 2
    assert summary.count("Type: Secret") == 2
    assert summary.count("Optional: false") == 2
    assert "second:\n    Type: Secret" in summary


def test_pod_yaml_summary_preserves_resource_groups_without_converting_units():
    resources = {"requests": {"cpu": "100k", "memory": "1Pi"},
                 "limits": {"cpu": "100k", "memory": "1Pi"}}
    raw = yaml.safe_dump({"kind": "Pod", "spec": {"containers": [
        {"name": "app", "resources": resources}]}})
    structured, summary, _ = ObservationProcessor()._extract_yaml(raw)
    assert structured["containers"][0]["resources"] == resources
    assert json.dumps(structured["containers"][0]["resources"], ensure_ascii=False) in summary


def test_volume_details_reach_archived_structured_and_agent_summary(tmp_path):
    raw = yaml.safe_dump({"apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": "workload", "namespace": "sample"},
        "spec": {"volumes": [{"name": "input", "hostPath": {
            "path": "/var/lib/missing-input", "type": "Directory"}}]}})
    processed = ObservationProcessor(archive_root=str(tmp_path)).process(
        run_id="volume-projection", node_id="evidence", sequence=1,
        tool_name="kubectl_get_yaml", raw_content=raw)
    archived = json.loads(Path(processed["structured_ref"]).read_text())
    assert archived["volumes"][0]["source_details"]["hostPath"] == {
        "path": "/var/lib/missing-input", "type": "Directory"}
    assert Path(processed["raw_ref"]).read_text() == raw
    assert Path(processed["summary_ref"]).read_text() == processed["summary"]
    assert "/var/lib/missing-input" in processed["summary"]
