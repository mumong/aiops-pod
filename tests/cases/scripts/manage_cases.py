#!/usr/bin/env python3
"""Single-case lifecycle for the original fixtures and opt-in root-cause variants.

Only explicit catalog namespaces can be changed. Variant validation verifies the
injected cause, not the Agent's answer or observability backend completeness.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from verify_observability import evaluate_status_gate, resolve_workload_pods, run_kubectl_json

ROOT = Path(__file__).resolve().parents[1]


def catalog() -> dict[str, dict]:
    result = {}
    for path, variant in ((ROOT / "catalog.yaml", False), (ROOT / "variants/catalog.yaml", True)):
        for source in json.loads(path.read_text())["cases"]:
            case = dict(source, variant=variant)
            if case["id"] in result:
                raise ValueError(f"duplicate case: {case['id']}")
            expected = r"aiops-case-v\d{2}" if variant else r"aiops-case-\d{2}"
            if not re.fullmatch(expected, case["namespace"]):
                raise ValueError(f"unsafe namespace: {case['namespace']}")
            directory = (ROOT / case["directory"]).resolve()
            if not directory.is_relative_to(ROOT) or not (directory / "kustomization.yaml").is_file():
                raise ValueError(f"invalid fixture directory: {directory}")
            result[case["id"]] = case
    return result


def command(args: list[str], *, capture: bool = False, timeout: int = 300) -> str:
    completed = subprocess.run(args, check=True, text=True, capture_output=capture, timeout=timeout)
    return completed.stdout or ""


def variant_namespace(case: dict) -> dict:
    """Refuse to overwrite/delete an unrelated namespace with the same name."""
    raw = command(["kubectl", "get", "namespace", case["namespace"],
                   "--ignore-not-found=true", "-o", "json"], capture=True, timeout=20)
    existing = json.loads(raw) if raw.strip() else {}
    if existing and existing.get("metadata", {}).get("labels", {}).get("aiops.lab/fixture-suite") != "root-variants":
        raise ValueError(f"refusing unowned namespace {case['namespace']}")
    return existing


def deploy(case: dict) -> None:
    directory = str(ROOT / case["directory"])
    command(["kubectl", "kustomize", directory], capture=True, timeout=30)
    if case["variant"] and variant_namespace(case):
        raise ValueError(f"{case['namespace']} already exists; run make case-clean CASE={case['id']} before redeploying")
    print(f"Deploy {case['id']} into {case['namespace']}", flush=True)
    command(["kubectl", "apply", "-k", directory])
    if case["variant"] and case.get("trigger") == "delete-pod-after-ready":
        command(["kubectl", "-n", case["namespace"], "wait", "--for=condition=Ready",
                 f"pod/{case['workload_name']}", f"--timeout={case['timeout_seconds']}s"])
        command(["kubectl", "-n", case["namespace"], "delete", f"pod/{case['workload_name']}", "--wait=false"])
    print(f"Applied; verify the actual cause with: make case-validate CASE={case['id']}")


def clean(case: dict) -> None:
    if case["variant"] and not variant_namespace(case):
        return
    namespace = case["namespace"]
    cleanup = case.get("cleanup", {})
    if cleanup.get("release_finalizer"):
        raw = command(["kubectl", "-n", namespace, "get", cleanup["release_finalizer"],
                       "--ignore-not-found=true", "-o", "json"], capture=True, timeout=20)
        finalizers = (json.loads(raw) if raw.strip() else {}).get("metadata", {}).get("finalizers", [])
        if "aiops.lab/hold" in finalizers:
            path = f"/metadata/finalizers/{finalizers.index('aiops.lab/hold')}"
            patch = [{"op": "test", "path": path, "value": "aiops.lab/hold"}, {"op": "remove", "path": path}]
            command(["kubectl", "-n", namespace, "patch", cleanup["release_finalizer"],
                     "--type=json", "-p", json.dumps(patch)])
    if cleanup.get("shorten_grace"):
        if cleanup.get("release_file"):
            # Cooperative teardown only after grading, inside this owned fixture.
            raw = command(["kubectl", "-n", namespace, "get", "pod", case["workload_name"],
                           "--ignore-not-found=true", "-o", "json"], capture=True, timeout=20)
            pod = json.loads(raw) if raw.strip() else {}
            if pod and any("running" in c.get("state", {}) for c in pod.get("status", {}).get("containerStatuses", [])):
                if not pod.get("metadata", {}).get("deletionTimestamp"):
                    raise ValueError("refusing release before fixture deletion was triggered")
                marker = cleanup["release_file"]
                if marker != "/state/teardown-requested":
                    raise ValueError("unsupported teardown marker")
                try:
                    command(["kubectl", "-n", namespace, "exec", case["workload_name"], "-c", case["container"],
                             "--", "python3", "-c", "from pathlib import Path; Path('/state/teardown-requested').touch()"], timeout=20)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                    # The marker can stop PID 1 before exec returns. A nonzero
                    # result is not proof of failure (nor proof of success).
                    # Confirm the SAME Pod has ended; never swallow RBAC/network
                    # errors or act on a replacement object.
                    for attempt in range(10):
                        current_raw = command(["kubectl", "-n", namespace, "get", "pod", case["workload_name"],
                                               "--ignore-not-found=true", "-o", "json"], capture=True, timeout=20)
                        current = json.loads(current_raw) if current_raw.strip() else {}
                        if not current:
                            break
                        if current.get("metadata", {}).get("uid") != pod.get("metadata", {}).get("uid"):
                            raise RuntimeError("fixture Pod replaced during cleanup; refusing deletion") from exc
                        statuses = current.get("status", {}).get("containerStatuses", [])
                        if statuses and all("terminated" in c.get("state", {}) for c in statuses):
                            break
                        if attempt == 9:
                            raise exc
                        time.sleep(1)
                    print("Cleanup exec ended early; original fixture is terminated or absent", flush=True)
        # Shorten only this disposable fixture's grace period; never force-delete nodes.
        command(["kubectl", "-n", namespace, "delete", f"pod/{case['workload_name']}",
                 "--ignore-not-found=true", "--grace-period=1", "--wait=true", "--timeout=90s"], timeout=100)
    try:
        command(["kubectl", "delete", "namespace", namespace, "--ignore-not-found=true",
                 "--wait=true", "--timeout=180s"], timeout=200)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if not release_unstarted_fixture(case):
            raise
        command(["kubectl", "delete", "namespace", namespace, "--ignore-not-found=true",
                 "--wait=true", "--timeout=90s"], timeout=100)


def unstarted_deleting_fixture(case: dict, pod: dict) -> bool:
    """Narrow fallback for disposable Pending Pods stuck in mount teardown."""
    meta, spec, status = pod.get("metadata", {}), pod.get("spec", {}), pod.get("status", {})
    containers = status.get("containerStatuses", [])
    return bool(
        case.get("variant") and case.get("workload_kind") == "Pod"
        and meta.get("namespace") == case["namespace"] and meta.get("name") == case["workload_name"]
        and meta.get("uid") and meta.get("resourceVersion") and meta.get("deletionTimestamp")
        and not meta.get("finalizers") and status.get("phase") == "Pending"
        and not spec.get("initContainers") and not spec.get("ephemeralContainers")
        and containers and {c.get("name") for c in containers} == {c.get("name") for c in spec.get("containers", [])}
        and all(c.get("started") is False and c.get("restartCount") == 0
                and not c.get("containerID") and not c.get("lastState")
                and c.get("state", {}).get("waiting", {}).get("reason") == "ContainerCreating"
                for c in containers)
    )


def release_unstarted_fixture(case: dict) -> bool:
    if not case.get("variant") or not variant_namespace(case):
        return False
    raw = command(["kubectl", "-n", case["namespace"], "get", "pod", case["workload_name"],
                   "--ignore-not-found=true", "-o", "json"], capture=True, timeout=20)
    pod = json.loads(raw) if raw.strip() else {}
    if not unstarted_deleting_fixture(case, pod):
        return False
    metadata = pod["metadata"]
    body = {"apiVersion": "v1", "kind": "DeleteOptions", "gracePeriodSeconds": 0,
            "preconditions": {"uid": metadata["uid"], "resourceVersion": metadata["resourceVersion"]}}
    print(f"Cleanup fallback: deleting never-started fixture {case['namespace']}/{case['workload_name']} "
          f"uid={metadata['uid']} with UID/resourceVersion preconditions", flush=True)
    subprocess.run(["kubectl", "delete", "--raw",
                    f"/api/v1/namespaces/{case['namespace']}/pods/{case['workload_name']}", "-f", "-"],
                   input=json.dumps(body), text=True, check=True, capture_output=True, timeout=30)
    return True


def _field(value: dict, path: str):
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def check_variant(case: dict, pod: dict, events: list[dict], logs: str = "", *, marker_present: bool = False) -> tuple[bool, dict]:
    gate = case["status_gate"]
    uid = pod.get("metadata", {}).get("uid")
    events = [event for event in events if uid and event.get("involvedObject", {}).get("uid") == uid]
    # A current waiting.message can contain the same complete cause as an
    # expired Event. Limit this fallback to config errors, requiring all cause
    # patterns in ONE target-container message, not unrelated/old observations.
    patterns = gate.get("event_patterns_all", [])
    waiting_cause = (bool(patterns)
                     and gate.get("waiting_reasons") == ["CreateContainerConfigError"] and any(
        c.get("name") == case.get("container")
        and c.get("state", {}).get("waiting", {}).get("reason") == "CreateContainerConfigError"
        and all(re.search(p, c.get("state", {}).get("waiting", {}).get("message", ""), re.I)
                for p in patterns)
        for c in pod.get("status", {}).get("containerStatuses", [])
    ))
    effective_gate = {k: v for k, v in gate.items() if k != "event_reasons"} if waiting_cause else gate
    matched, facts = evaluate_status_gate(pod, events, effective_gate)
    checks = {"status": matched}
    patterns = gate.get("event_patterns_all", [])
    if patterns:
        # All cause patterns must occur in the SAME event for the current Pod UID.
        checks["cause_event"] = waiting_cause or any(
            (not gate.get("event_reasons") or event.get("reason") in gate["event_reasons"])
            and all(re.search(pattern, event.get("message", ""), re.I) for pattern in patterns)
            for event in events
        )
    if gate.get("log_patterns_all"):
        checks["cause_log"] = all(re.search(pattern, logs, re.I) for pattern in gate["log_patterns_all"])
    if gate.get("no_finalizers"):
        checks["no_finalizers"] = not pod.get("metadata", {}).get("finalizers")
    if gate.get("all_containers_running"):
        statuses = pod.get("status", {}).get("containerStatuses", [])
        checks["containers_running"] = bool(statuses) and all("running" in s.get("state", {}) for s in statuses)
    if gate.get("no_prestop"):
        checks["no_prestop"] = all(not c.get("lifecycle", {}).get("preStop") for c in pod.get("spec", {}).get("containers", []))
    for path, expected in gate.get("pod_fields", {}).items():
        checks[path] = _field(pod, path) == expected
    if gate.get("marker_file"):
        checks["hook_started"] = marker_present
    blockers = [e.get("message", "") for e in events
                if any(re.search(pattern, e.get("message", ""), re.I)
                       for pattern in gate.get("fail_fast_event_patterns", []))]
    return all(checks.values()), {"pod_uid": uid, "checks": checks, "status_facts": facts,
                                 "cause_source": "container_waiting_message" if waiting_cause else "configured_gate",
                                 "blocking_events": blockers}


def validate_variant(case: dict, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        try:
            identity, pod = resolve_workload_pods(case)[0]
            events = run_kubectl_json(["-n", identity.namespace, "get", "events", "--field-selector", f"involvedObject.uid={identity.uid}"]).get("items", [])
            gate = case["status_gate"]
            logs = ""
            if gate.get("log_patterns_all"):
                args = ["kubectl", "-n", identity.namespace, "logs", identity.name,
                        "-c", case["container"], "--tail=80", "--limit-bytes=16000"]
                if gate.get("minimum_restarts"):
                    args.append("--previous")
                logs = command(args, capture=True, timeout=20)
            marker_present = False
            if gate.get("marker_file"):
                # This checks a file created by the hook, not merely its configured presence.
                result = subprocess.run(["kubectl", "-n", identity.namespace, "exec", identity.name,
                                         "-c", case["container"], "--", "test", "-f", gate["marker_file"]],
                                        capture_output=True, timeout=20)
                marker_present = result.returncode == 0
            matched, detail = check_variant(case, pod, events, logs, marker_present=marker_present)
            print(json.dumps({"case": case["id"], "matched": matched, **detail}, ensure_ascii=False), flush=True)
            if matched:
                print("PASS: 注入的异常状态和具体原因已成立（不是 Agent 评分，也不是三维遥测验收）。")
                return True
            if detail.get("blocking_events"):
                print("BLOCKED: 环境前置条件失败，不是目标故障；保存事件后跳过该场景。", file=sys.stderr, flush=True)
                return False
        except (subprocess.SubprocessError, ValueError, IndexError, KeyError) as exc:
            print(f"Waiting for {case['id']}: {exc}", flush=True)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print("FAIL: 注入条件未成立；先排查环境，不要据此计算 Agent 错误率。", file=sys.stderr)
            return False
        time.sleep(min(5, remaining))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "deploy", "validate", "clean", "render", "namespace"])
    parser.add_argument("--case")
    parser.add_argument("--variants", action="store_true", help="list or explicitly clean the variant catalog only")
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args(argv)
    cases = catalog()
    if args.action == "list":
        for case in cases.values():
            if not args.variants or case["variant"]:
                print(f"{case['id']:<20} {case['namespace']:<19} {case.get('symptom', case['name']):<35} {case.get('fault_scenario', '')}")
        return 0
    if args.action == "clean" and args.variants and not args.case:
        for case in cases.values():
            if case["variant"]:
                clean(case)
        return 0
    if args.case not in cases:
        parser.error("--case must be an exact catalog ID; use make case-list")
    case = cases[args.case]
    if args.action == "namespace":
        print(case["namespace"])
    elif args.action == "render":
        command(["kubectl", "kustomize", str(ROOT / case["directory"])], timeout=30)
    elif args.action == "deploy":
        deploy(case)
    elif args.action == "clean":
        clean(case)
    elif case["variant"]:
        if args.timeout is not None and args.timeout < 1:
            parser.error("--timeout must be positive")
        return 0 if validate_variant(case, args.timeout or case["timeout_seconds"]) else 1
    else:
        # Preserve the original verifier's config.env and timeout behavior.
        os.execvp("bash", ["bash", str(ROOT / "scripts/validate.sh"), "--case", case["id"], "--wait"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
