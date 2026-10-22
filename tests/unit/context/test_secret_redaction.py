"""Secret values never reach the model (run ef5cbfed: base64 data + last-applied plaintext)."""

import json

import yaml

from app.core.context.secret_redaction import redact_secret_values

SECRET_YAML = """apiVersion: v1
data:
  available-key: YmVuaWdu
kind: Secret
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"Secret","stringData":{"available-key":"benign"}}
    owner: team-a
  name: workload-input
  namespace: aiops-case-04
type: Opaque
"""


def test_yaml_secret_keeps_keys_not_values_or_last_applied():
    out, found = redact_secret_values(SECRET_YAML)
    assert found and "YmVuaWdu" not in out and "benign" not in out
    doc = yaml.safe_load(out)
    assert doc["data"] == {"available-key": "<redacted: 8 bytes>"}
    assert doc["metadata"]["annotations"] == {"owner": "team-a"}
    assert doc["metadata"]["name"] == "workload-input"


def test_json_list_and_string_data_are_redacted():
    listing = {
        "kind": "List",
        "items": [
            {"kind": "Secret", "stringData": {"password": "hunter2"}, "metadata": {"name": "a"}},
            {"kind": "ConfigMap", "data": {"app.json": "{}"}, "metadata": {"name": "b"}},
        ],
    }
    out, found = redact_secret_values(json.dumps(listing))
    doc = json.loads(out)
    assert found and "hunter2" not in out
    assert doc["items"][0]["stringData"] == {"password": "<redacted: 7 bytes>"}
    assert doc["items"][1]["data"] == {"app.json": "{}"}  # ConfigMaps are not touched


def test_non_secret_output_is_returned_unchanged():
    for text in ("NAME READY\nweb 1/1", "kind: Deployment\nmetadata: {name: w}\n", ""):
        assert redact_secret_values(text) == (text, False)


def test_unparseable_secret_output_is_replaced_whole():
    out, found = redact_secret_values("kind: Secret\ndata: {a: [unclosed\n  password: hunter2")
    assert found and "hunter2" not in out and "整体脱敏" in out


def test_every_document_of_a_multi_document_output_is_redacted():
    two = SECRET_YAML + "---\n" + SECRET_YAML.replace("YmVuaWdu", "c2Vjb25k")
    out, found = redact_secret_values(two)
    assert found and "YmVuaWdu" not in out and "c2Vjb25k" not in out
