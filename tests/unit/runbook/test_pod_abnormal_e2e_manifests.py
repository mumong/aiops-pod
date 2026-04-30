from pathlib import Path

import yaml


ROOT = Path("test/e2e/manifests")

EXPECTED_CASES = {
    "Evicted": {
        "manifest": "l0-logfill-enospc.yaml",
        "runbook": "l0-volume-limit.md",
        "status": "Evicted",
    },
    "VolumeMountFailed": {
        "manifest": "pod-volume-mount-failed.yaml",
        "runbook": "pod-volume-mount-failed.md",
        "status": "Pending|ContainerCreating",
    },
    "PendingUnschedulable": {
        "manifest": "l1-taint-node.yaml",
        "runbook": "l1-taint-node.md",
        "status": "Pending",
    },
    "NodeLostOrUnknown": {
        "manifest": "pod-node-lost-unknown.yaml",
        "runbook": "pod-node-lost-unknown.md",
        "status": "Unknown",
    },
    "TerminatingStuck": {
        "manifest": "pod-terminating-stuck.yaml",
        "runbook": "pod-terminating-stuck.md",
        "status": "Terminating",
    },
    "OOMKilled": {
        "manifest": "l2-oomkilled.yaml",
        "runbook": "l2-oomkilled.md",
        "status": "CrashLoopBackOff|Error",
    },
    "CrashLoopBackOffRuntime": {
        "manifest": "pod-crashloop-runtime.yaml",
        "runbook": "pod-crashloop-runtime.md",
        "status": "CrashLoopBackOff",
    },
    "ImagePullFailed": {
        "manifest": "l3-imagepull-fail-victim.yaml",
        "runbook": "l3-imagepull-failed.md",
        "status": "ImagePullBackOff|ErrImagePull",
    },
    "SandboxCreateFailed": {
        "manifest": "pod-sandbox-create-failed.yaml",
        "runbook": "pod-sandbox-create-failed.md",
        "status": "ContainerCreating|Pending",
    },
    "ConfigError": {
        "manifest": "l4-config-bootstrap-fail.yaml",
        "runbook": "l4-config-bootstrap-fail.md",
        "status": "CrashLoopBackOff|CreateContainerConfigError|CreateContainerError",
    },
    "NotReadyProbeFailed": {
        "manifest": "pod-notready-probe-failed.yaml",
        "runbook": "pod-notready-probe-failed.md",
        "status": "Running",
    },
}


def _load_primary_object(path: Path) -> dict:
    docs = [doc for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")) if doc]
    assert docs, f"{path} must contain at least one Kubernetes object"
    return docs[0]


def _pod_metadata(obj: dict) -> dict:
    if obj.get("kind") == "Deployment":
        return obj["spec"]["template"].setdefault("metadata", {})
    return obj.setdefault("metadata", {})


def test_each_pod_abnormal_runbook_has_a_dedicated_e2e_manifest():
    for pod_type, expected in EXPECTED_CASES.items():
        path = ROOT / expected["manifest"]
        assert path.exists(), f"{pod_type} missing manifest {path}"


def test_pod_abnormal_e2e_manifests_declare_expected_state_contract():
    for pod_type, expected in EXPECTED_CASES.items():
        path = ROOT / expected["manifest"]
        obj = _load_primary_object(path)
        metadata = _pod_metadata(obj)
        labels = metadata.get("labels") or {}
        annotations = metadata.get("annotations") or {}

        assert labels.get("pod_abnormal_type") == pod_type, path
        assert labels.get("e2e-test") == "true", path
        assert annotations.get("aiops.e2e/runbook") == expected["runbook"], path
        assert annotations.get("aiops.e2e/expected-status") == expected["status"], path
        assert annotations.get("aiops.e2e/expected-evidence"), path


def test_deployment_e2e_manifest_selectors_match_pod_template_labels():
    for expected in EXPECTED_CASES.values():
        path = ROOT / expected["manifest"]
        obj = _load_primary_object(path)
        if obj.get("kind") != "Deployment":
            continue

        selector = obj["spec"]["selector"]["matchLabels"]
        template_labels = obj["spec"]["template"]["metadata"]["labels"]

        for key, value in selector.items():
            assert template_labels.get(key) == value, path


def test_e2e_scripts_reference_every_pod_abnormal_manifest():
    run_all = Path("test/e2e/run_all.sh").read_text(encoding="utf-8")
    validate = Path("test/e2e/validate.sh").read_text(encoding="utf-8")

    for pod_type, expected in EXPECTED_CASES.items():
        assert expected["manifest"] in run_all, f"{pod_type} is not deployed by run_all.sh"
        assert pod_type in validate, f"{pod_type} is not shown by validate.sh"
