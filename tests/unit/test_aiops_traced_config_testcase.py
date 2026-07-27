from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "testcases" / "aiops-traced-config-crashloop.yaml"
OOM_MANIFEST = ROOT / "testcases" / "aiops-traced-oom.yaml"
SCRIPT = ROOT / "scripts" / "aiops-traced-config-crashloop.sh"


def _documents() -> list[dict]:
    return [
        document
        for document in yaml.safe_load_all(MANIFEST.read_text(encoding="utf-8"))
        if isinstance(document, dict)
    ]


def _documents_from(path: Path) -> list[dict]:
    return [
        document
        for document in yaml.safe_load_all(path.read_text(encoding="utf-8"))
        if isinstance(document, dict)
    ]


def test_manifest_defines_common_crashloop_observability_environment():
    documents = _documents()
    resources = {
        (document.get("kind"), document.get("metadata", {}).get("name"))
        for document in documents
    }

    assert ("Namespace", "aiops-traced-config") in resources
    assert ("ConfigMap", "traced-config-app") in resources
    assert ("Service", "trace-config-api") in resources
    assert ("Deployment", "trace-config-api") in resources
    assert ("Deployment", "trace-config-driver") in resources


def test_business_application_emits_correlated_error_evidence_and_exits_non_oom():
    config_map = next(
        document
        for document in _documents()
        if document.get("kind") == "ConfigMap"
        and document.get("metadata", {}).get("name") == "traced-config-app"
    )
    server = config_map["data"]["server.py"]
    driver = config_map["data"]["driver.py"]

    assert "PAYMENT_GATEWAY_TOKEN" in server
    assert '"config_missing"' in server
    assert '"trace_id"' in server
    assert '"span_id"' in server
    assert '"http.response.status_code"' in server
    assert "OTLP_ENDPOINT" in server
    assert "os._exit(78)" in server
    assert "traceparent" in driver
    assert "HTTPError" in driver


def test_otlp_boolean_attributes_are_encoded_before_integer_attributes():
    config_map = next(
        document
        for document in _documents()
        if document.get("kind") == "ConfigMap"
        and document.get("metadata", {}).get("name") == "traced-config-app"
    )
    server = config_map["data"]["server.py"]

    assert server.index("isinstance(value, bool)") < server.index("isinstance(value, int)")


def test_traced_testcases_export_otlp_to_current_monitor_stack():
    expected = "http://lgtm.monitor.svc:4318/v1/traces"

    for manifest in (MANIFEST, OOM_MANIFEST):
        documents = _documents_from(manifest)
        config_map = next(
            document
            for document in documents
            if document.get("kind") == "ConfigMap"
        )
        deployment = next(
            document
            for document in documents
            if document.get("kind") == "Deployment"
            and document.get("metadata", {}).get("name", "").endswith("-api")
        )
        env = {
            item["name"]: item.get("value")
            for item in deployment["spec"]["template"]["spec"]["containers"][0]["env"]
        }

        assert expected in config_map["data"]["server.py"]
        assert env["OTLP_ENDPOINT"] == expected


def test_script_exposes_full_lifecycle_and_verifies_crashloop_signals():
    script = SCRIPT.read_text(encoding="utf-8")

    for action in ("apply", "status", "logs", "verify", "cleanup"):
        assert f"{action})" in script
    assert 'reason}" == "Error"' in script
    assert 'exit_code}" == "78"' in script
    assert "CrashLoopBackOff" in script
    assert "config_missing" in script
    assert "PAYMENT_GATEWAY_TOKEN" in script


def test_oom_application_span_is_exported_before_dangerous_allocation():
    config_map = next(
        document
        for document in _documents_from(OOM_MANIFEST)
        if document.get("kind") == "ConfigMap"
        and document.get("metadata", {}).get("name") == "traced-oom-app"
    )
    server = config_map["data"]["server.py"]
    handler = server[server.index("def do_GET"):]

    export_call = handler.index("export_span(")
    allocation = handler.index(
        "chunks.append(bytearray(mib * 1024 * 1024))"
    )

    assert export_call < allocation
    assert "export_span(trace_id, span_id, parent_span_id" in handler
    assert '"parentSpanId": parent_span_id' in server
    assert '"url.path": path' in handler[:allocation]
    assert '"aiops.allocated_mib.before": before_mib' in handler[:allocation]
    assert '"aiops.alloc_mib": mib' in handler[:allocation]
    assert '"k8s.pod.name": POD_NAME' in handler[:allocation]
    assert '"aiops.allocation.phase": "pre_allocation_attempt"' in handler[:allocation]
    assert "OOMKilled" not in server
    assert "resource.memory.oomkilled" not in server
