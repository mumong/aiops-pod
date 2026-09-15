"""Offline rendering and counterexamples; never applies resources to a cluster."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("variant_case_manager", ROOT / "scripts/manage_cases.py")
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)
CASES = {key: value for key, value in manager.catalog().items() if value["variant"]}


@pytest.mark.parametrize("case_id", list(CASES))
def test_variant_renders_one_isolated_bounded_pod(case_id):
    case = CASES[case_id]
    output = subprocess.run(["kubectl", "kustomize", str(ROOT / case["directory"])],
                            check=True, text=True, capture_output=True).stdout
    docs = list(yaml.safe_load_all(output))
    allowed = {"Namespace", "Pod", "ConfigMap"}
    if case_id == "c05-plugin":
        allowed.add("NetworkAttachmentDefinition")
    assert {d["kind"] for d in docs} <= allowed
    pods = [d for d in docs if d["kind"] == "Pod"]
    assert len(pods) == 1
    pod = pods[0]
    assert pod["metadata"]["namespace"] == case["namespace"]
    assert pod["metadata"]["name"] == "workload"
    assert case_id not in json.dumps(pod["metadata"])
    assert "finalizers" not in pod["metadata"]
    assert not pod["spec"]["automountServiceAccountToken"]
    assert not pod["spec"].get("hostNetwork")
    assert not pod["spec"].get("hostPID")
    assert pod["spec"]["securityContext"]["runAsNonRoot"]
    app = pod["spec"]["containers"][0]
    assert app["resources"]["limits"]["cpu"]
    assert app["resources"]["limits"]["memory"]
    assert not app["securityContext"]["allowPrivilegeEscalation"]
    assert app["securityContext"]["readOnlyRootFilesystem"]
    for doc in docs:
        if doc["kind"] == "Namespace":
            assert doc["metadata"]["name"] == case["namespace"]
        else:
            assert doc["metadata"]["namespace"] == case["namespace"]
    if case_id == "c03-hostpath":
        assert pod["spec"]["volumes"][0]["hostPath"]["type"] == "Directory"
        assert app["volumeMounts"][0]["readOnly"]
    else:
        assert "hostPath:" not in output


def pod(phase="Pending", waiting=None, exit_code=None, deleting=False):
    container = {"state": {"waiting": {"reason": waiting}} if waiting else {"running": {}},
                 "restartCount": 1 if exit_code else 0}
    if exit_code:
        container["lastState"] = {"terminated": {"exitCode": exit_code}}
    return {"metadata": {"uid": "current", **({"deletionTimestamp": "2026-09-08T12:00:00Z"} if deleting else {})},
            "spec": {"containers": [{}]},
            "status": {"phase": phase, "containerStatuses": [container]}}


def event(message, reason="FailedScheduling", uid="current"):
    return {"involvedObject": {"uid": uid}, "reason": reason, "message": message}


def test_config_error_current_message_survives_event_expiry():
    sample = pod(waiting="CreateContainerConfigError")
    container = sample["status"]["containerStatuses"][0]
    container["name"] = "app"
    message = "couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input"
    container["state"]["waiting"]["message"] = message
    ok, detail = manager.check_variant(CASES["c04-configmap-key"], sample, [])
    assert ok and detail["cause_source"] == "container_waiting_message"
    for wrong in ("", "couldn't find key unavailable-key in Secret workload-input", "configmap workload-input exists"):
        container["state"]["waiting"]["message"] = wrong
        assert not manager.check_variant(CASES["c04-configmap-key"], sample, [])[0]
    container["state"]["waiting"]["message"] = message
    container["name"] = "another-container"
    assert not manager.check_variant(CASES["c04-configmap-key"], sample, [])[0]


@pytest.mark.parametrize("outcome", ["absent", "terminated", "running", "replaced"])
def test_teardown_exec_race_requires_confirmed_terminal_state(monkeypatch, outcome):
    initial = pod("Running", deleting=True)
    initial["metadata"]["uid"] = "old"
    current = json.loads(json.dumps(initial))
    if outcome == "terminated":
        current["status"]["containerStatuses"][0]["state"] = {"terminated": {"exitCode": 0}}
    if outcome == "replaced":
        current["metadata"]["uid"] = "new"
    calls, reads = [], []
    def command(args, **kwargs):
        calls.append(args)
        if "exec" in args:
            raise subprocess.CalledProcessError(137, args)
        if "get" in args:
            reads.append(True)
            if len(reads) == 1:
                return json.dumps(initial)
            return "" if outcome == "absent" else json.dumps(current)
        return ""
    monkeypatch.setattr(manager, "command", command)
    monkeypatch.setattr(manager, "variant_namespace", lambda c: {"owned": True})
    monkeypatch.setattr(manager.time, "sleep", lambda _: None)
    if outcome in {"running", "replaced"}:
        with pytest.raises((subprocess.CalledProcessError, RuntimeError)):
            manager.clean(CASES["c11-prestop"])
        assert not any("delete" in args for args in calls)
    else:
        manager.clean(CASES["c11-prestop"])
        assert any("delete" in args and "namespace" in args for args in calls)


@pytest.mark.parametrize("case_id,correct,wrong", [
    ("c01-cpu", "0/3 nodes are available: 3 Insufficient cpu", "0/3 nodes are available: 3 Insufficient memory"),
    ("c01-memory", "0/3 nodes are available: 3 Insufficient memory", "0/3 nodes didn't match Pod's node affinity/selector"),
    ("c01-pvc", 'persistentvolumeclaim "unavailable-claim" not found', "Insufficient cpu"),
])
def test_same_pending_state_requires_the_specific_cause(case_id, correct, wrong):
    case = CASES[case_id]
    assert manager.check_variant(case, pod(), [event(correct)])[0]
    assert not manager.check_variant(case, pod(), [event(wrong)])[0]
    assert not manager.check_variant(case, pod(), [event(correct, uid="old-pod")])[0]


def test_cause_patterns_cannot_be_assembled_from_unrelated_events():
    case = CASES["c01-pvc"]
    assert not manager.check_variant(case, pod(), [event('persistentvolumeclaim "unavailable-claim" bound'),
                                                  event('something else not found')])[0]


@pytest.mark.parametrize("case_id,message", [
    ("c03-secret", 'MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found'),
    ("c03-key", 'MountVolume.SetUp failed for volume "input" : references non-existent config key: unavailable-key'),
    ("c03-hostpath", 'MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/unavailable is not a directory'),
])
def test_mount_cause_messages(case_id, message):
    sample = pod()
    sample["spec"]["volumes"] = [{"configMap": {"name": "workload-input", "items": [{"key": "unavailable-key"}]}}]
    assert manager.check_variant(CASES[case_id], sample, [event(message, "FailedMount")])[0]
    assert not manager.check_variant(CASES[case_id], sample, [event("attach timeout", "FailedMount")])[0]


def test_image_tag_is_not_confused_with_dns_or_auth_failures():
    case = CASES["c02-tag"]
    sample = pod(waiting="ImagePullBackOff")
    for text in ("manifest unknown", "xnet.registry.io:8443/observability/python:aiops-fixture-unavailable-20260908: not found",
                 "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found"):
        assert manager.check_variant(case, sample, [event(text, "Failed")])[0]
    for text in ("lookup xnet.registry.io: no such host", "401 unauthorized", "secret not found", "x509: certificate expired",
                 "pause:another-tag: not found", "failed to pull pause:aiops-fixture-unavailable-20260908: 403 Forbidden"):
        assert not manager.check_variant(case, sample, [event(text, "Failed")])[0]


@pytest.mark.parametrize("case_id,code,logs", [
    ("c06-command", 127, "sh: exec: /opt/app/unavailable-command: not found"),
    ("c06-file", 1, "FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'"),
    ("c07-env", 78, "APP_REQUIRED_CONFIG environment variable is missing"),
])
def test_crashloop_requires_both_exit_code_and_actual_log(case_id, code, logs):
    case = CASES[case_id]
    sample = pod("Running", "CrashLoopBackOff", code)
    assert manager.check_variant(case, sample, [], logs)[0]
    assert not manager.check_variant(case, sample, [], "unrelated runtime error")[0]
    assert not manager.check_variant(case, pod("Running", "CrashLoopBackOff", 2), [], logs)[0]


def test_configmap_env_missing_key_is_not_secret_missing_key():
    case = CASES["c04-configmap-key"]
    sample = pod(waiting="CreateContainerConfigError")
    assert manager.check_variant(case, sample, [event("couldn't find key unavailable-key in ConfigMap ns/workload-input", "Failed")])[0]
    assert not manager.check_variant(case, sample, [event("couldn't find key unavailable-key in Secret ns/workload-input", "Failed")])[0]


def test_termination_is_not_inferred_from_yaml_alone():
    sample = pod("Running", deleting=True)
    case = CASES["c11-prestop"]
    assert not manager.check_variant(case, sample, [], marker_present=False)[0]
    assert manager.check_variant(case, sample, [], marker_present=True)[0]
    sample["metadata"]["finalizers"] = ["aiops.lab/hold"]
    assert not manager.check_variant(case, sample, [], marker_present=True)[0]
    sample = pod("Running", deleting=True)
    sample["spec"]["terminationGracePeriodSeconds"] = 3900
    case = CASES["c11-grace"]
    assert not manager.check_variant(case, sample, [], "application started")[0]
    assert manager.check_variant(case, sample, [], "SIGTERM received; waiting")[0]
    sample["spec"]["containers"][0]["lifecycle"] = {"preStop": {"exec": {"command": ["sleep", "1"]}}}
    assert not manager.check_variant(case, sample, [], "SIGTERM received; waiting")[0]


def test_baseline_catalog_and_safe_bundle_are_not_expanded():
    baseline = json.loads((ROOT / "catalog.yaml").read_text())["cases"]
    assert [c["id"] for c in baseline] == [f"c{i:02d}" for i in range(1, 12)]
    assert len(CASES) == 17
    assert len({c["namespace"] for c in CASES.values()}) == 17
    assert "variants" not in (ROOT / "safe/kustomization.yaml").read_text()


def test_plugin_variant_requires_plugin_failure_not_missing_nad():
    case = CASES["c05-plugin"]
    assert manager.check_variant(case, pod(), [event('failed to find plugin "aiops-unavailable" in path', 'FailedCreatePodSandBox')])[0]
    assert not manager.check_variant(case, pod(), [event('networkattachmentdefinition secondary-net not found', 'FailedCreatePodSandBox')])[0]


def test_startup_oom_requires_oom_reason_and_allocation_log():
    sample = pod("Running", "CrashLoopBackOff", 137)
    sample["status"]["containerStatuses"][0]["lastState"]["terminated"]["reason"] = "OOMKilled"
    assert manager.check_variant(CASES["c08-startup"], sample, [], 'startup allocation 256Mi')[0]
    assert not manager.check_variant(CASES["c08-startup"], sample, [], 'business request /work')[0]
    sample["status"]["containerStatuses"][0]["lastState"]["terminated"]["reason"] = "Error"
    assert not manager.check_variant(CASES["c08-startup"], sample, [], 'startup allocation 256Mi')[0]


def test_probe_variants_require_correct_probe_and_failure_mechanism():
    sample = pod("Running")
    sample["spec"]["containers"][0]["readinessProbe"] = {"httpGet": {"port": 18081}}
    assert manager.check_variant(CASES["c09-port"], sample, [event('Readiness probe failed: dial tcp 10.0.0.1:18081: connection refused', 'Unhealthy')], 'listening on 18080')[0]
    assert not manager.check_variant(CASES["c09-port"], sample, [event('Readiness probe failed: HTTP 503', 'Unhealthy')], 'listening on 18080')[0]
    sample["status"]["containerStatuses"][0]["restartCount"] = 1
    sample["spec"]["containers"][0]["livenessProbe"] = {"timeoutSeconds": 1}
    assert manager.check_variant(CASES["c10-timeout"], sample, [event('Liveness probe failed: context deadline exceeded', 'Unhealthy')], 'listening on 18080')[0]
    assert not manager.check_variant(CASES["c10-timeout"], sample, [event('Readiness probe failed: context deadline exceeded', 'Unhealthy')], 'listening on 18080')[0]


def teardown_pod():
    sample = pod("Pending", "ContainerCreating", deleting=True)
    sample["metadata"].update(namespace="aiops-case-v05", name="workload", resourceVersion="123")
    sample["spec"]["containers"] = [{"name": "app"}]
    sample["status"]["containerStatuses"][0].update(name="app", started=False)
    return sample


@pytest.mark.parametrize("change", ["started", "containerID", "restartCount", "lastState", "unknown"])
def test_cleanup_fallback_rejects_possible_runtime_containers(change):
    case = CASES["c03-key"]
    sample = teardown_pod()
    assert manager.unstarted_deleting_fixture(case, sample)
    status = sample["status"]["containerStatuses"][0]
    status.update({"started": True} if change == "started" else
                  {"containerID": "containerd://live"} if change == "containerID" else
                  {"restartCount": 1} if change == "restartCount" else
                  {"lastState": {"terminated": {"exitCode": 0}}} if change == "lastState" else
                  {"started": None})
    assert not manager.unstarted_deleting_fixture(case, sample)


def test_cleanup_fallback_is_uid_and_version_conditioned(monkeypatch):
    sample = teardown_pod()
    monkeypatch.setattr(manager, "variant_namespace", lambda case: {"metadata": {"name": case["namespace"]}})
    monkeypatch.setattr(manager, "command", lambda *args, **kwargs: json.dumps(sample))
    calls = []
    monkeypatch.setattr(manager.subprocess, "run", lambda args, **kwargs: calls.append((args, kwargs)))
    assert manager.release_unstarted_fixture(CASES["c03-key"])
    args, kwargs = calls[0]
    assert "/api/v1/namespaces/aiops-case-v05/pods/workload" in args
    body = json.loads(kwargs["input"])
    assert body["preconditions"] == {"uid": "current", "resourceVersion": "123"}
    assert body["gracePeriodSeconds"] == 0


def test_cleanup_fallback_rejects_finalizers_and_other_namespaces():
    sample = teardown_pod()
    sample["metadata"]["finalizers"] = ["some-controller/hold"]
    assert not manager.unstarted_deleting_fixture(CASES["c03-key"], sample)
    sample["metadata"].pop("finalizers")
    sample["metadata"]["namespace"] = "production"
    assert not manager.unstarted_deleting_fixture(CASES["c03-key"], sample)


def test_cleanup_refuses_unowned_namespace_without_deleting():
    calls = []
    def fake(args, **kwargs):
        calls.append(args)
        return json.dumps({"metadata": {"labels": {}}})
    with patch.object(manager, "command", side_effect=fake):
        with pytest.raises(ValueError, match="unowned"):
            manager.clean(CASES["c11-prestop"])
    assert len(calls) == 1 and "get" in calls[0]


def test_termination_cleanup_is_exact_and_shortens_grace():
    calls = []
    def fake(args, **kwargs):
        calls.append(args)
        return json.dumps({"metadata": {"labels": {"aiops.lab/fixture-suite": "root-variants"}}})
    case = CASES["c11-grace"]
    with patch.object(manager, "command", side_effect=fake):
        manager.clean(case)
    assert calls[2] == ["kubectl", "-n", case["namespace"], "delete", "pod/workload", "--ignore-not-found=true", "--grace-period=1", "--wait=true", "--timeout=90s"]
    assert calls[3][0:4] == ["kubectl", "delete", "namespace", case["namespace"]]
    assert not any("--force" in c or "--all" in c for c in calls)


def test_cooperative_cleanup_releases_hook_before_wait(monkeypatch):
    calls = []
    sample = {"metadata": {"deletionTimestamp": "now", "labels": {"aiops.lab/fixture-suite": "root-variants"}},
              "status": {"containerStatuses": [{"state": {"running": {}}}]}}
    def command(args, **kwargs):
        calls.append(args)
        return json.dumps(sample)
    monkeypatch.setattr(manager, "command", command)
    manager.clean(CASES["c11-prestop"])
    release = next(i for i, args in enumerate(calls) if "exec" in args)
    delete = next(i for i, args in enumerate(calls) if "delete" in args)
    assert release < delete
    assert "/state/teardown-requested" in calls[release][-1]
    assert "aiops-case-v12" in calls[release]


@pytest.mark.parametrize("case_id", ["c11-prestop", "c11-grace"])
def test_cooperative_teardown_also_releases_main_process(case_id):
    patch = json.loads((ROOT / CASES[case_id]["directory"] / "patch.yaml").read_text())
    app = patch["spec"]["containers"][0]
    assert "/state/teardown-requested" in app["command"][-1]
    compile(app["command"][-1], case_id, "exec")
    if case_id == "c11-prestop":
        hook = app["lifecycle"]["preStop"]["exec"]["command"][-1]
        assert "/state/teardown-requested" in hook
        compile(hook, "preStop", "exec")


def test_tag_tls_blocker_is_current_uid_only():
    case = CASES["c02-tag"]
    sample = pod(waiting="ImagePullBackOff")
    msg = "failed to verify certificate: x509: certificate signed by unknown authority"
    ok, detail = manager.check_variant(case, sample, [event(msg, "Failed")])
    assert not ok and detail["blocking_events"] == [msg]
    assert not manager.check_variant(case, sample, [event(msg, "Failed", uid="old")])[1]["blocking_events"]


def test_deploy_refuses_existing_variant_before_apply():
    calls = []
    def fake(args, **kwargs):
        calls.append(args)
        return "" if "kustomize" in args else json.dumps({"metadata": {"labels": {"aiops.lab/fixture-suite": "root-variants"}}})
    with patch.object(manager, "command", side_effect=fake):
        with pytest.raises(ValueError, match="already exists"):
            manager.deploy(CASES["c01-cpu"])
    assert not any("apply" in c for c in calls)


def test_deploy_triggers_termination_only_after_ready():
    calls = []
    with patch.object(manager, "command", side_effect=lambda args, **kwargs: calls.append(args) or ""):
        manager.deploy(CASES["c11-prestop"])
    assert [c[1] if c[1] != "-n" else c[3] for c in calls] == ["kustomize", "get", "apply", "wait", "delete"]


def test_make_list_and_render_are_offline():
    repo = ROOT.parents[1]
    result = subprocess.run(["make", "case-list-variants"], cwd=repo, text=True, capture_output=True, check=True)
    assert "c01-cpu" in result.stdout
    result = subprocess.run(["make", "case-render", "CASE=c01-cpu"], cwd=repo, text=True, capture_output=True, check=True)
    workload = next(d for d in yaml.safe_load_all(result.stdout) if d["kind"] == "Pod")
    assert str(workload["spec"]["containers"][0]["resources"]["requests"]["cpu"]) == "100000"
