"""Repair planning starts from the write target's current spec, not from a fresh investigation.

Live batch of run f8e56239b1b74313: four planners took 2.0-3.8 min each, 7-15 model
rounds, mostly re-reading the same YAML in 3000-char pages and listing every
Deployment in the cluster. The controller chain walk already fetches the Pod and the
root controller; their compact facts (and the keys, never the values, of the Secrets
and ConfigMaps the template references) now go to the planner as material.
"""

import json

from app.core.remediation.ownership import resolve_controller_chain
from app.core.remediation.write_facts import (
    config_refs,
    pod_state,
    referenced_configs,
    spec_digest,
)

CONTAINER = {
    "name": "app",
    "image": "python:3",
    "command": ["python3", "/opt/aiops/server.py"],
    "env": [
        {"name": "MODE", "value": "normal"},
        {
            "name": "TOKEN",
            "valueFrom": {"secretKeyRef": {"name": "workload-input", "key": "token"}},
        },
    ],
    "envFrom": [{"configMapRef": {"name": "workload-env"}}],
    "ports": [{"containerPort": 8080, "name": "http"}],
    "readinessProbe": {"httpGet": {"path": "/ready", "port": 8081}},
    "resources": {"limits": {"memory": "96Mi"}},
    "volumeMounts": [{"name": "code", "mountPath": "/opt/aiops"}],
}
DEPLOYMENT = {
    "kind": "Deployment",
    "metadata": {"name": "workload", "namespace": "ns", "generation": 3, "managedFields": [{}]},
    "spec": {
        "replicas": 1,
        "template": {
            "metadata": {"labels": {"app": "workload"}},
            "spec": {
                "containers": [CONTAINER],
                "volumes": [{"name": "code", "configMap": {"name": "workload-code"}}],
            },
        },
    },
    "status": {"observedGeneration": 3, "readyReplicas": 0},
}


def test_spec_digest_keeps_what_a_patch_needs_and_drops_noise():
    digest = spec_digest(DEPLOYMENT)
    assert digest["kind"] == "Deployment" and digest["name"] == "workload"
    assert digest["template_path"] == "spec.template.spec"
    app = digest["containers"][0]
    assert app["readinessProbe"]["httpGet"]["port"] == 8081
    assert app["env"][1] == {
        "name": "TOKEN",
        "valueFrom": {"secretKeyRef": {"name": "workload-input", "key": "token"}},
    }
    assert digest["volumes"] == [{"name": "code", "configMap": {"name": "workload-code"}}]
    assert digest["replicas"] == 1 and digest["ready_replicas"] == 0
    assert "managedFields" not in json.dumps(digest)


def test_bare_pod_digest_and_state_show_the_deletion():
    pod = {
        "kind": "Pod",
        "metadata": {
            "name": "workload",
            "namespace": "ns",
            "deletionTimestamp": "2026-10-20T01:29:53Z",
            "finalizers": ["aiops.lab/hold"],
        },
        "spec": {"containers": [CONTAINER], "terminationGracePeriodSeconds": 10},
        "status": {
            "phase": "Running",
            "containerStatuses": [
                {
                    "name": "app",
                    "ready": False,
                    "restartCount": 0,
                    "state": {"terminated": {"reason": "Error", "exitCode": 137}},
                }
            ],
        },
    }
    assert spec_digest(pod)["template_path"] == "spec"
    state = pod_state(pod)
    assert state["deletion_timestamp"] == "2026-10-20T01:29:53Z"
    assert state["finalizers"] == ["aiops.lab/hold"]
    assert state["containers"][0]["state"]["terminated"]["exitCode"] == 137


def test_referenced_configs_cover_env_envfrom_and_volumes():
    refs = referenced_configs(spec_digest(DEPLOYMENT))
    assert refs == [
        ("ConfigMap", "workload-code"),
        ("ConfigMap", "workload-env"),
        ("Secret", "workload-input"),
    ]


def test_config_refs_list_keys_only_and_report_missing_objects():
    calls = []

    def runner(command):
        calls.append(command)
        if "secret/workload-input" in command:
            return "password\nuser"
        raise RuntimeError('Error from server (NotFound): configmaps "x" not found')

    refs = config_refs("ns", [("Secret", "workload-input"), ("ConfigMap", "x")], runner)
    assert refs[0] == {
        "kind": "Secret",
        "name": "workload-input",
        "exists": True,
        "keys": ["password", "user"],
    }
    assert refs[1]["exists"] is False and "NotFound" in refs[1]["error"]
    # Values never leave kubectl: the template prints key names only.
    assert all("go-template" in c and ".data" in c for c in calls)


def test_chain_carries_pod_state_and_write_target():
    pod = {
        "kind": "Pod",
        "metadata": {
            "name": "p",
            "uid": "u",
            "ownerReferences": [{"kind": "Deployment", "name": "workload", "controller": True}],
        },
        "spec": {"containers": [CONTAINER]},
        "status": {"phase": "Running"},
    }

    def runner(command):
        return json.dumps(pod if "pod/p" in command else DEPLOYMENT)

    chain = resolve_controller_chain("ns", "p", runner)
    data = chain.to_dict()
    assert data["write_target"]["kind"] == "Deployment"
    assert data["write_target"]["containers"][0]["name"] == "app"
    assert data["pod_state"]["phase"] == "Running"
