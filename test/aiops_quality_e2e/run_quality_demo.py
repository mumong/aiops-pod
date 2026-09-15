#!/usr/bin/env python3
"""Run a small, isolated quality benchmark against the current AIOps API.

The demo focuses on two externally verifiable metrics:

* root-cause accuracy, scored against hidden deterministic signatures;
* evidence completeness, scored from Evidence Plan items actually collected.

It deliberately does not modify the diagnosis service or send ground truth to
the model.  One scenario may deploy one or more catalog members and declare one
or more expected root causes.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tempfile
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import requests
import yaml


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CATALOG_PATH = REPO_ROOT / "test/pod-anomaly-cases/catalog.yaml"
DEMO_CASES_PATH = HERE / "demo_cases.yaml"
CASE_ROOT = REPO_ROOT / "test/pod-anomaly-cases"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluator import (  # noqa: E402
    EvidenceExpectation,
    EvidenceLaneScore,
    EvidenceScore,
    RootCauseExpectation,
    evidence_from_final_metrics,
    evidence_lane_from_payload,
    extract_root_claims,
    score_runbooks,
    score_evidence_lanes,
    score_evidence_contract,
    score_root_causes,
)


SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
ARCHIVE_START = "__AIOPS_EVIDENCE_FILE__ "
ARCHIVE_END = "__AIOPS_EVIDENCE_END__"
QUALITY_THRESHOLDS = {
    "mttr_seconds": 900.0,
    "root_cause_accuracy": 0.7,
    "runbook_coverage": 0.7,
    "evidence_completeness": 0.7,
}
SCORING_VERSION = "2026-09-10.1"
PROTECTED_WORKER_ENV = "AIOPS_QUALITY_PROTECTED_WORKER"
PROTECTED_STATUS_ENV = "AIOPS_QUALITY_RUNNER_STATUS"
RUNNER_LOG_NAME = "runner.log"
RUNNER_STATUS_NAME = "runner.status.json"


def scoring_manifest(cases_file: Optional[Path] = None) -> dict[str, Any]:
    paths = [Path(__file__), HERE / "evaluator.py", HERE / "variant_suite.py", HERE / "variant_cases.yaml"]
    fixture_paths = [CASE_ROOT / "catalog.yaml", CASE_ROOT / "variants/catalog.yaml",
                     *sorted((CASE_ROOT / "variants").rglob("*.yaml")),
                     *sorted((CASE_ROOT / "cases").rglob("*.yaml")),
                     *sorted((CASE_ROOT / "scripts").glob("*.py"))]
    return {"version": SCORING_VERSION, "sha256": {
        **{p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        **{str(p.relative_to(REPO_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture_paths},
        "cases_file": hashlib.sha256((cases_file or HERE / "demo_cases.yaml").read_bytes()).hexdigest(),
    }}


def atomic_write(path: Path, text: str) -> None:
    """Readers see the previous complete file or the next complete file."""
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def accept_runtime_resume(stats: dict[str, Any], manifest: dict[str, Any],
                          output_dir: Path, *, allowed: bool) -> None:
    """Explicit, audited lifecycle-only migration; never bypass grading changes."""
    previous = stats.get("scoring_manifest") or {}
    if previous == manifest:
        return
    old_hashes = previous.get("sha256") or {}
    new_hashes = manifest.get("sha256") or {}
    changed = {k for k in old_hashes.keys() | new_hashes.keys()
               if old_hashes.get(k) != new_hashes.get(k)}
    lifecycle_files = {"run_quality_demo.py", "test/pod-anomaly-cases/scripts/manage_cases.py"}
    if (not allowed or not old_hashes or previous.get("version") != manifest.get("version")
            or old_hashes.keys() != new_hashes.keys() or not changed <= lifecycle_files):
        raise RuntimeError("checkpoint rules differ; only reviewed lifecycle-only changes may use --resume-runtime-update; scoring/fixture changes require a separate run")
    snapshot = output_dir / f"stats-before-runtime-resume-{time.time_ns()}.json"
    atomic_write(snapshot, json.dumps(stats, ensure_ascii=False, indent=2))
    stats.setdefault("runtime_resume_audit", []).append({
        "timestamp": datetime.now().isoformat(), "previous_manifest": previous,
        "current_manifest": manifest, "changed_files": sorted(changed),
        "snapshot": str(snapshot), "preserved_runs": sum(len(c.get("runs") or []) for c in stats.get("scenarios") or []),
        "scope": "explicitly reviewed lifecycle-only update; archived scores unchanged",
    })
    stats["scoring_manifest"] = manifest


def precheck_with_refresh(scenario, catalog, scenario_stats, run_index, *, reuse_existing):
    """Renew only disposable isolated fixtures when historical Events age out.

    Do not accept a weaker gate or refresh during a diagnosis. Fresh deployment
    must pass the original gate; only one refresh is allowed per run.
    """
    try:
        return {m: wait_for_case_gate(catalog[m]) for m in scenario.members}
    except TimeoutError as exc:
        if reuse_existing or len(scenario.members) != 1 or scenario.members[0] not in {"c02", "c10"}:
            raise
        member = scenario.members[0]
        from variant_suite import fixture_manager
        scenario_stats.setdefault("fixture_refreshes", []).append({
            "run_index": run_index, "timestamp": datetime.now().isoformat(),
            "reason": str(exc), "action": "redeploy_then_recheck_original_gate",
        })
        print(f"Refreshing {member} before run {run_index}: {exc}", flush=True)
        fixture_manager().clean(catalog[member])
        fixture_manager().deploy(catalog[member])
        return {member: wait_for_case_gate(catalog[member])}


@contextmanager
def exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"another quality task holds {path}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def assert_report_idle(output_dir: Path) -> None:
    status_path = output_dir / RUNNER_STATUS_NAME
    if not status_path.exists():
        return
    status = json.loads(status_path.read_text(encoding="utf-8"))
    pid = int(status.get("pid") or 0)
    if pid and pid != os.getpid() and status.get("status") == "running":
        try:
            command = Path(f"/proc/{pid}/cmdline").read_bytes()
        except FileNotFoundError:
            return
        if b"run_quality_demo.py" in command:
            raise RuntimeError(f"report is being written by worker {pid}; wait for completion")


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    anomaly_type: str
    fault_scenario: str
    members: tuple[str, ...]
    question: str
    settle_after_gate_seconds: int
    expected_root_causes: tuple[RootCauseExpectation, ...]
    expected_runbooks: tuple[str, ...]
    expected_evidence: tuple[EvidenceExpectation, ...]
    runbook_targets: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class DiagnosisResult:
    run_id: str
    answer: str
    metrics: Mapping[str, Any]
    elapsed_seconds: float
    events: tuple[Mapping[str, Any], ...]
    raw_sse: str


def _load_data(path: Path) -> Mapping[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError(f"expected mapping in {path}")
    return data


def load_catalog(path: Path) -> dict[str, Mapping[str, Any]]:
    if path.resolve() == CATALOG_PATH.resolve():
        from variant_suite import fixture_manager
        return fixture_manager().catalog()
    data = _load_data(path)
    cases = data.get("cases") or []
    result = {str(item["id"]): item for item in cases if isinstance(item, Mapping)}
    if len(result) != len(cases):
        raise ValueError(f"duplicate or invalid case IDs in {path}")
    return result


def load_scenarios(path: Path) -> dict[str, Scenario]:
    data = _load_data(path)
    defaults = data.get("defaults") or {}
    result: dict[str, Scenario] = {}
    for raw in data.get("scenarios") or []:
        scenario_id = str(raw.get("id") or "").strip()
        if not scenario_id or scenario_id in result:
            raise ValueError(f"invalid or duplicate scenario ID: {scenario_id!r}")
        expected = tuple(
            RootCauseExpectation.from_mapping(item, fallback_id=f"root-{index}")
            for index, item in enumerate(raw.get("expected_root_causes") or [], start=1)
        )
        if not expected:
            raise ValueError(f"scenario {scenario_id} has no expected_root_causes")
        expected_evidence = tuple(
            EvidenceExpectation.from_mapping(item, fallback_id=f"evidence-{index}")
            for index, item in enumerate(raw.get("expected_evidence") or [], start=1)
        )
        if not expected_evidence:
            raise ValueError(f"scenario {scenario_id} has no expected_evidence contract")
        evidence_ids = [item.id for item in expected_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError(f"scenario {scenario_id} has duplicate expected_evidence IDs")
        allowed_dimensions = {"kubernetes", "metrics", "logging", "tracing", "topology"}
        invalid_dimensions = sorted({
            dimension
            for item in expected_evidence
            for dimension in item.dimensions
            if dimension not in allowed_dimensions
        })
        if invalid_dimensions:
            raise ValueError(
                f"scenario {scenario_id} has invalid evidence dimensions: {invalid_dimensions}"
            )
        result[scenario_id] = Scenario(
            id=scenario_id,
            name=str(raw.get("name") or scenario_id),
            anomaly_type=str(raw.get("anomaly_type") or "Unknown"),
            fault_scenario=str(raw.get("fault_scenario") or raw.get("name") or scenario_id),
            members=tuple(str(item) for item in (raw.get("members") or [])),
            question=str(raw.get("question") or defaults.get("question") or "我的集群有什么问题？"),
            settle_after_gate_seconds=int(
                raw.get("settle_after_gate_seconds")
                or defaults.get("settle_after_gate_seconds")
                or 0
            ),
            expected_root_causes=expected,
            expected_runbooks=tuple(str(item) for item in (raw.get("expected_runbooks") or [])),
            expected_evidence=expected_evidence,
        )
    if path.resolve() == DEMO_CASES_PATH.resolve():
        from variant_suite import extend_scenarios
        return extend_scenarios(result)
    return result


def select_scenarios(
    scenarios: Mapping[str, Scenario], selector: str
) -> list[Scenario]:
    """Resolve comma-separated IDs or the isolated c01-c11 overnight suite."""

    requested = [item.strip() for item in str(selector or "").split(",") if item.strip()]
    if not requested:
        raise ValueError("no scenarios selected")
    if len(requested) != len(set(requested)):
        raise ValueError("duplicate scenario IDs")
    if "expanded" in requested or "variants" in requested:
        if len(requested) != 1:
            raise ValueError("suite selectors cannot be combined with explicit IDs")
        return [s for key, s in scenarios.items()
                if re.fullmatch(r"c\d{2}(?:-[a-z0-9-]+)?", key)
                and (requested[0] == "expanded" or not re.fullmatch(r"c\d{2}", key))]
    if "all" in requested:
        if len(requested) != 1:
            raise ValueError("'all' cannot be combined with explicit scenario IDs")
        selected = [
            scenario for scenario_id, scenario in scenarios.items()
            if re.fullmatch(r"c\d{2}", scenario_id)
        ]
        if not selected:
            raise ValueError("no cNN scenarios found")
        return selected
    missing = [item for item in requested if item not in scenarios]
    if missing:
        raise ValueError(f"unknown scenarios: {', '.join(missing)}")
    return [scenarios[item] for item in requested]


def default_output_dir(
    selected: Sequence[Scenario], *, timestamp: Optional[str] = None
) -> Path:
    """Build a unique report directory when --output-dir is omitted."""

    scenario_ids = [scenario.id for scenario in selected]
    full_suite = [f"c{index:02d}" for index in range(1, 12)]
    label = "all" if scenario_ids == full_suite else "-".join(scenario_ids)
    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-") or "custom"
    if len(safe_label) > 100:
        safe_label = "expanded-" + hashlib.sha256(label.encode()).hexdigest()[:12]
    suffix = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "testreports" / f"aiops_quality_{safe_label}_{suffix}"


def _has_output_dir_argument(argv: Sequence[str]) -> bool:
    return any(
        item == "--output-dir" or item.startswith("--output-dir=")
        for item in argv
    )


def protected_worker_command(argv: Sequence[str], output_dir: Path) -> list[str]:
    """Rebuild this invocation as a detached worker with a stable checkpoint path."""

    forwarded = list(argv)
    if not _has_output_dir_argument(forwarded):
        forwarded.extend(["--output-dir", str(output_dir)])
    return [sys.executable, str(Path(__file__).resolve()), *forwarded]


def _write_runner_status(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically publish detached-worker state for later SSH sessions."""

    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _follow_protected_worker(process: subprocess.Popen[Any], log_path: Path, offset: int) -> int:
    """Mirror the worker log while attached; the worker survives this process."""

    with log_path.open("r", encoding="utf-8", errors="replace") as reader:
        reader.seek(offset)
        while True:
            line = reader.readline()
            if line:
                print(line, end="", flush=True)
                continue
            return_code = process.poll()
            if return_code is not None:
                remainder = reader.read()
                if remainder:
                    print(remainder, end="", flush=True)
                return int(return_code)
            time.sleep(0.2)


def launch_protected_worker(output_dir: Path, argv: Sequence[str]) -> int:
    """Start the benchmark outside the terminal session and follow its log."""

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / RUNNER_LOG_NAME
    status_path = output_dir / RUNNER_STATUS_NAME
    offset = log_path.stat().st_size if log_path.exists() else 0
    command = protected_worker_command(argv, output_dir)
    worker_env = os.environ.copy()
    worker_env[PROTECTED_WORKER_ENV] = "1"
    worker_env[PROTECTED_STATUS_ENV] = str(status_path)
    with log_path.open("a", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            env=worker_env,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    print(
        f"Protected worker started: pid={process.pid}\n"
        f"Report directory: {output_dir}\n"
        f"Live log: {log_path}\n"
        "SSH disconnect will not stop the worker; this terminal is following its log.",
        flush=True,
    )
    try:
        return _follow_protected_worker(process, log_path, offset)
    except KeyboardInterrupt:
        print(
            f"\nLog following stopped; protected worker pid={process.pid} is still running.\n"
            f"Resume viewing with: tail -f {log_path}",
            file=sys.stderr,
            flush=True,
        )
        return 130
    except BrokenPipeError:
        # The SSH/terminal output disappeared.  The detached worker writes only
        # to runner.log and remains in its own session.
        return 0


def _protected_worker_entrypoint() -> None:
    """Run the real benchmark and publish completion independently of the launcher."""

    status_value = os.environ.get(PROTECTED_STATUS_ENV, "").strip()
    status_path = Path(status_value) if status_value else None
    started_at = datetime.now().isoformat()
    if status_path is not None:
        _write_runner_status(
            status_path,
            {
                "status": "running",
                "pid": os.getpid(),
                "started_at": started_at,
            },
        )
    try:
        outcome = main()
    except BaseException as exc:
        if status_path is not None:
            exit_code = exc.code if isinstance(exc, SystemExit) else 1
            _write_runner_status(
                status_path,
                {
                    "status": "failed",
                    "pid": os.getpid(),
                    "started_at": started_at,
                    "completed_at": datetime.now().isoformat(),
                    "exit_code": int(exit_code) if isinstance(exit_code, int) else 1,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        raise
    else:
        if status_path is not None:
            _write_runner_status(
                status_path,
                {
                    "status": outcome or "completed",
                    "pid": os.getpid(),
                    "started_at": started_at,
                    "completed_at": datetime.now().isoformat(),
                    "exit_code": 0,
                },
            )


def run_command(
    command: Sequence[str],
    *,
    check: bool = True,
    capture: bool = False,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(command), flush=True)
    result = subprocess.run(
        list(command),
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=capture,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        if capture and result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
    return result


def _kubectl_json(args: Sequence[str]) -> Mapping[str, Any]:
    result = run_command(["kubectl", *args], capture=True)
    data = json.loads(result.stdout or "{}")
    return data if isinstance(data, Mapping) else {}


def cleanup_catalog_namespaces(catalog: Mapping[str, Mapping[str, Any]]) -> None:
    """Delete only exact namespaces declared by the safe anomaly catalog."""

    from variant_suite import fixture_manager
    for case in catalog.values():
        if case.get("variant"):
            fixture_manager().clean(case)
    catalog = {key: case for key, case in catalog.items() if not case.get("variant")}
    namespaces = sorted({str(case.get("namespace") or "") for case in catalog.values()} - {""})
    for case in catalog.values():
        cleanup = case.get("cleanup") or {}
        release = str(cleanup.get("release_finalizer") or "").strip()
        namespace = str(case.get("namespace") or "").strip()
        if release and namespace:
            run_command(
                [
                    "kubectl", "-n", namespace, "patch", release,
                    "--type=json", "-p", '[{"op":"remove","path":"/metadata/finalizers"}]',
                ],
                check=False,
                capture=True,
            )
    if namespaces:
        run_command(
            [
                "kubectl", "delete", "namespace", *namespaces,
                "--ignore-not-found=true", "--wait=true", "--timeout=240s",
            ],
            timeout=300,
        )


def apply_scenario(scenario: Scenario, catalog: Mapping[str, Mapping[str, Any]]) -> None:
    for member_id in scenario.members:
        case = catalog[member_id]
        if case.get("variant"):
            from variant_suite import fixture_manager
            fixture_manager().deploy(case)
            continue
        directory = CASE_ROOT / str(case["directory"])
        run_command(["kubectl", "apply", "-k", str(directory)])

    for member_id in scenario.members:
        case = catalog[member_id]
        if case.get("variant") or case.get("trigger") != "delete-pod-after-ready":
            continue
        namespace = str(case["namespace"])
        workload = str(case["workload_name"])
        run_command(
            [
                "kubectl", "-n", namespace, "wait", "--for=condition=Ready",
                f"pod/{workload}", f"--timeout={int(case.get('timeout_seconds') or 180)}s",
            ]
        )
        run_command(["kubectl", "-n", namespace, "delete", f"pod/{workload}", "--wait=false"])


def _pod_for_case(case: Mapping[str, Any]) -> Mapping[str, Any]:
    namespace = str(case["namespace"])
    if str(case.get("workload_kind") or "").lower() == "pod":
        return _kubectl_json(["-n", namespace, "get", "pod", str(case["workload_name"]), "-o", "json"])
    data = _kubectl_json(
        [
            "-n", namespace, "get", "pods", "-l", "app.kubernetes.io/name=workload",
            "-o", "json",
        ]
    )
    items = [item for item in (data.get("items") or []) if isinstance(item, Mapping)]
    if not items:
        raise RuntimeError(f"no workload Pod found in {namespace}")
    return max(items, key=lambda item: str((item.get("metadata") or {}).get("creationTimestamp") or ""))


def _event_reasons(namespace: str, uid: str) -> set[str]:
    if not uid:
        return set()
    data = _kubectl_json(
        [
            "-n", namespace, "get", "events", "--field-selector", f"involvedObject.uid={uid}",
            "-o", "json",
        ]
    )
    return {str(item.get("reason") or "") for item in (data.get("items") or []) if isinstance(item, Mapping)}


def gate_matches(case: Mapping[str, Any], pod: Mapping[str, Any]) -> tuple[bool, list[str]]:
    gate = case.get("status_gate") or {}
    metadata = pod.get("metadata") or {}
    status = pod.get("status") or {}
    statuses = [item for item in (status.get("containerStatuses") or []) if isinstance(item, Mapping)]
    reasons: list[str] = []

    phases = [str(item) for item in (gate.get("phase") or [])]
    if phases and str(status.get("phase") or "") not in phases:
        reasons.append(f"phase={status.get('phase')} expected={phases}")

    waiting = {
        str(((item.get("state") or {}).get("waiting") or {}).get("reason") or "")
        for item in statuses
    }
    expected_waiting = set(str(item) for item in (gate.get("waiting_reasons") or []))
    if expected_waiting and not (waiting & expected_waiting):
        reasons.append(f"waiting={sorted(waiting)} expected={sorted(expected_waiting)}")

    terminated_states: list[Mapping[str, Any]] = []
    for item in statuses:
        for key in ("state", "lastState"):
            terminated = ((item.get(key) or {}).get("terminated") or {})
            if terminated:
                terminated_states.append(terminated)
    terminated_reasons = {str(item.get("reason") or "") for item in terminated_states}
    expected_terminated = set(str(item) for item in (gate.get("terminated_reasons") or []))
    if expected_terminated and not (terminated_reasons & expected_terminated):
        reasons.append(
            f"terminated_reasons={sorted(terminated_reasons)} expected={sorted(expected_terminated)}"
        )

    exit_codes = {int(item.get("exitCode")) for item in terminated_states if item.get("exitCode") is not None}
    expected_exit_codes = set(int(item) for item in (gate.get("terminated_exit_codes") or []))
    if expected_exit_codes and not (exit_codes & expected_exit_codes):
        reasons.append(f"exit_codes={sorted(exit_codes)} expected={sorted(expected_exit_codes)}")

    minimum_restarts = int(gate.get("minimum_restarts") or 0)
    restarts = sum(int(item.get("restartCount") or 0) for item in statuses)
    if restarts < minimum_restarts:
        reasons.append(f"restarts={restarts} expected>={minimum_restarts}")

    if "ready" in gate:
        ready_condition = next(
            (item for item in (status.get("conditions") or []) if item.get("type") == "Ready"),
            {},
        )
        ready = str(ready_condition.get("status") or "").lower() == "true"
        if ready is not bool(gate.get("ready")):
            reasons.append(f"ready={ready} expected={bool(gate.get('ready'))}")

    if gate.get("deletion_timestamp") and not metadata.get("deletionTimestamp"):
        reasons.append("deletionTimestamp missing")

    expected_finalizers = set(str(item) for item in (gate.get("finalizers") or []))
    finalizers = set(str(item) for item in (metadata.get("finalizers") or []))
    if expected_finalizers and not expected_finalizers.issubset(finalizers):
        reasons.append(f"finalizers={sorted(finalizers)} expected={sorted(expected_finalizers)}")

    expected_events = set(str(item) for item in (gate.get("event_reasons") or []))
    if expected_events:
        events = _event_reasons(str(case["namespace"]), str(metadata.get("uid") or ""))
        if not (events & expected_events):
            reasons.append(f"event_reasons={sorted(events)} expected={sorted(expected_events)}")

    return not reasons, reasons


def wait_for_case_gate(case: Mapping[str, Any]) -> Mapping[str, Any]:
    timeout_seconds = int(case.get("timeout_seconds") or 240)
    if case.get("variant"):
        from variant_suite import fixture_manager
        if not fixture_manager().validate_variant(case, timeout_seconds):
            raise TimeoutError(f"case {case['id']} specific cause gate did not pass")
        return _pod_for_case(case)
    deadline = time.monotonic() + timeout_seconds
    last_reason = "Pod not created"
    while time.monotonic() < deadline:
        try:
            pod = _pod_for_case(case)
            matched, reasons = gate_matches(case, pod)
            if matched:
                metadata = pod.get("metadata") or {}
                print(
                    f"Gate ready: {case['id']} {case['namespace']}/{metadata.get('name')}",
                    flush=True,
                )
                return pod
            last_reason = "; ".join(reasons)
        except Exception as exc:
            last_reason = str(exc)
        print(f"Waiting for {case['id']} gate: {last_reason}", flush=True)
        time.sleep(5)
    raise TimeoutError(f"case {case['id']} gate timed out: {last_reason}")


def record_fixture_failure(scenario, catalog, scenario_dir, scenario_stats, exc, *, phase):
    """Capture current UID's source events before cleanup, without changing scores."""
    record = {"phase": phase, "error": f"{type(exc).__name__}: {exc}",
              "timestamp": datetime.now().isoformat(), "members": {}}
    for member in scenario.members:
        case = catalog[member]
        detail = {"namespace": case["namespace"], "expected_gate": case.get("status_gate", {})}
        try:
            pod = _pod_for_case(case)
            detail["pod"] = pod
            uid = pod.get("metadata", {}).get("uid")
            if uid:
                detail["events"] = _kubectl_json([
                    "-n", case["namespace"], "get", "events", "--field-selector", f"involvedObject.uid={uid}", "-o", "json"])
        except Exception as archive_error:
            detail["archive_error"] = str(archive_error)
        record["members"][member] = detail
    source = json.dumps(record["members"], ensure_ascii=False).lower()
    record["category"] = ("registry_tls_untrusted" if "x509:" in source else
                          "registry_auth" if "unauthorized" in source else "fixture_gate_unmet")
    errors = scenario_stats.setdefault("fixture_errors", [])
    path = scenario_dir / f"fixture-failure-{phase}-{time.time_ns()}.json"
    atomic_write(path, json.dumps(record, ensure_ascii=False, indent=2))
    errors.append({"phase": phase, "category": record["category"], "error": record["error"], "archive": str(path)})
    scenario_stats["status"] = "blocked"
    print(f"BLOCKED {scenario.id}: {record['category']}; archived {path}. No Agent failure score assigned.", flush=True)


def quality_incomplete(stats):
    runs = [run for case in stats.get("scenarios", []) for run in case.get("runs", [])]
    return (stats.get("rescore_complete") is False or stats.get("status") in {"failed", "completed_with_errors"}
            or any(case.get("status") == "blocked" for case in stats.get("scenarios", []))
            or any(run.get("fixture_valid") is False or not run.get("success") for run in runs)
            or (stats.get("planned_runs") is not None and len(runs) < stats["planned_runs"]))


def _decode_line(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _live_event_lines(event: Mapping[str, Any], *, mode: str) -> list[str]:
    if mode == "off":
        return []
    event_type = str(event.get("type") or "message")
    if event_type == "run_start":
        return [f"[run] run_id={event.get('run_id')}"]
    if event_type == "node_start":
        return [f"[node:start] {event.get('node')} / {event.get('node_name')}"]
    if event_type == "node_complete":
        duration = float(event.get("duration_seconds") or 0.0)
        return [f"[node:done] {event.get('node')} / {event.get('node_name')} ({duration:.1f}s)"]
    if event_type == "thinking":
        thinking_type = str(event.get("thinking_type") or "")
        tool_name = str(event.get("tool_name") or "")
        if thinking_type == "tool_start":
            return [f"[tool:start] {tool_name}"]
        if thinking_type == "tool_result":
            preview = re.sub(r"\s+", " ", str(event.get("result_preview") or "")).strip()
            if len(preview) > 700:
                preview = preview[:697] + "..."
            return [f"[tool:done] {tool_name} status={event.get('status') or '-'} {preview}".rstrip()]
        if thinking_type == "ai_message":
            content = str(event.get("content") or "").strip()
            return [f"[agent:{event.get('node')}] {content}"] if content else []
        if mode == "full" and thinking_type == "ai_token":
            return [str(event.get("content") or "")]
        return []
    if event_type == "heartbeat":
        return [f"[heartbeat] {event.get('node') or '-'}"]
    if event_type == "error":
        return [f"[error] {event.get('error') or event.get('message') or event}"]
    if event_type == "final":
        answer = str(event.get("answer") or "")
        return [
            f"[final] run_id={event.get('run_id')} status={event.get('status') or '-'}",
            "=" * 72,
            "最终诊断报告",
            "=" * 72,
            answer,
        ]
    if event_type == "run_end":
        return [f"[run:end] run_id={event.get('run_id')} status={event.get('status') or '-'}"]
    return []


def _sse_events(
    lines: Iterable[Any],
    *,
    live_mode: str = "off",
    live_file: Optional[Any] = None,
    raw_file: Optional[Any] = None,
    live_prefix: str = "",
) -> tuple[list[Mapping[str, Any]], str]:
    events: list[Mapping[str, Any]] = []
    raw_lines: list[str] = []
    event_name = "message"
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event_name, data_lines
        if not data_lines:
            event_name = "message"
            return
        raw = "\n".join(data_lines)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        if not isinstance(payload, Mapping):
            payload = {"value": payload}
        event = {"type": event_name, **payload}
        events.append(event)
        for rendered in _live_event_lines(event, mode=live_mode):
            displayed = f"{live_prefix}{rendered}" if live_prefix else rendered
            if live_mode == "full" and event.get("thinking_type") == "ai_token":
                print(displayed, end="", flush=True)
                if live_file:
                    live_file.write(rendered)
            else:
                print(displayed, flush=True)
                if live_file:
                    live_file.write(rendered + "\n")
            if live_file:
                live_file.flush()
        event_name = "message"
        data_lines = []

    for raw_line in lines:
        line = _decode_line(raw_line)
        raw_lines.append(line)
        if raw_file:
            raw_file.write(line + "\n")
            raw_file.flush()
        if not line:
            flush()
        elif line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].lstrip())
    flush()
    return events, "\n".join(raw_lines) + "\n"


def diagnose(
    base_url: str,
    question: str,
    timeout_seconds: int,
    *,
    live_mode: str = "compact",
    live_path: Optional[Path] = None,
    raw_path: Optional[Path] = None,
    live_prefix: str = "",
) -> DiagnosisResult:
    started = time.monotonic()
    response = requests.get(
        f"{base_url.rstrip('/')}/ask",
        params={"q": question, "stream": "true", "format": "sse"},
        stream=True,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    live_handle = live_path.open("w", encoding="utf-8") if live_path else None
    raw_handle = raw_path.open("w", encoding="utf-8") if raw_path else None
    try:
        def deadline_lines() -> Iterable[Any]:
            for line in response.iter_lines(decode_unicode=True):
                if time.monotonic() - started > timeout_seconds:
                    response.close()
                    raise TimeoutError(
                        f"diagnosis exceeded wall-clock limit of {timeout_seconds}s"
                    )
                yield line

        events, raw_sse = _sse_events(
            deadline_lines(),
            live_mode=live_mode,
            live_file=live_handle,
            raw_file=raw_handle,
            live_prefix=live_prefix,
        )
    finally:
        if live_handle:
            live_handle.close()
        if raw_handle:
            raw_handle.close()
    final = next((event for event in reversed(events) if event.get("type") == "final"), None)
    if not final:
        errors = [str(event.get("error") or event.get("raw") or "") for event in events if event.get("type") == "error"]
        raise RuntimeError("diagnosis produced no final event" + (f": {'; '.join(errors)}" if errors else ""))
    run_id = str(final.get("run_id") or "")
    if not SAFE_ID.fullmatch(run_id):
        raise RuntimeError(f"invalid run_id from service: {run_id!r}")
    return DiagnosisResult(
        run_id=run_id,
        answer=str(final.get("answer") or ""),
        metrics=final.get("metrics") if isinstance(final.get("metrics"), Mapping) else {},
        elapsed_seconds=float(final.get("elapsed_seconds") or (time.monotonic() - started)),
        events=tuple(events),
        raw_sse=raw_sse,
    )


def _partial_run_id(raw_path: Path) -> str:
    """Recover a server run ID from an incomplete SSE archive when possible."""

    try:
        text = raw_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    matches = re.findall(r'"run_id"\s*:\s*"([A-Za-z0-9_.-]+)"', text)
    return matches[0] if matches else ""


def _parse_archive_records(stdout: str) -> list[tuple[str, Mapping[str, Any]]]:
    pattern = re.compile(
        rf"(?ms)^{re.escape(ARCHIVE_START)}(?P<path>[^\n]+)\n(?P<body>.*?)\n^{re.escape(ARCHIVE_END)}$"
    )
    records: list[tuple[str, Mapping[str, Any]]] = []
    for match in pattern.finditer(stdout or ""):
        path = match.group("path").strip()
        try:
            payload = json.loads(match.group("body"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            records.append((path, payload))
    lane_records = [item for item in records if re.search(r"-g[^/]+/node_outputs/evidence\.full\.json$", item[0])]
    return lane_records or records


def _parse_archive_stdout(stdout: str) -> list[EvidenceLaneScore]:
    selected = _parse_archive_records(stdout)
    return [
        evidence_lane_from_payload(
            payload,
            source=path,
            lane=Path(path).parent.parent.name,
        )
        for path, payload in selected
    ]


def evidence_archive_from_kubectl(
    run_id: str,
    *,
    namespace: str,
    target: str,
    container: str,
    archive_root: str,
) -> tuple[EvidenceScore, list[tuple[str, Mapping[str, Any]]]]:
    """Read Evidence lane payloads once and retain both plan audit and facts."""

    if not SAFE_ID.fullmatch(run_id):
        error = f"unsafe run_id: {run_id!r}"
        return score_evidence_lanes([], source="missing", error=error), []
    shell_script = (
        'for d in "$1/$2" "$1/$2"-g*; do '
        'f="$d/node_outputs/evidence.full.json"; '
        '[ -f "$f" ] || continue; '
        f'printf "{ARCHIVE_START}%s\\n" "$f"; '
        'cat "$f"; printf "\\n' + ARCHIVE_END + '\\n"; '
        'done'
    )
    command = [
        "kubectl", "-n", namespace, "exec", target,
        "-c", container, "--", "sh", "-c", shell_script, "sh", archive_root, run_id,
    ]
    try:
        result = run_command(command, check=False, capture=True, timeout=60)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return score_evidence_lanes([], source="missing", error=str(exc)), []
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "kubectl archive read failed").strip()
        return score_evidence_lanes([], source="missing", error=error), []
    records = _parse_archive_records(result.stdout)
    lanes = [
        evidence_lane_from_payload(payload, source=path, lane=Path(path).parent.parent.name)
        for path, payload in records
    ]
    score = score_evidence_lanes(
        lanes,
        source="kubectl_archive" if lanes else "missing",
        error="" if lanes else "no Evidence lane archives found",
    )
    return score, records


def evidence_from_kubectl_archive(
    run_id: str,
    *,
    namespace: str,
    target: str,
    container: str,
    archive_root: str,
) -> EvidenceScore:
    score, _ = evidence_archive_from_kubectl(
        run_id,
        namespace=namespace,
        target=target,
        container=container,
        archive_root=archive_root,
    )
    return score


def _runbook_observations(
    events: Sequence[Mapping[str, Any]], metrics: Mapping[str, Any]
) -> list[str]:
    observations: list[str] = []
    for event in events:
        if event.get("type") == "node_complete":
            observations.append(
                json.dumps(event.get("state_snapshot") or {}, ensure_ascii=False, default=str)
            )
    observations.append(
        json.dumps(metrics.get("runbook_coverage") or {}, ensure_ascii=False, default=str)
    )
    return observations


def _score_run(
    scenario: Scenario,
    diagnosis: DiagnosisResult,
    evidence: EvidenceScore,
    plan_evidence: Optional[EvidenceScore] = None,
    evidence_contract_audit: Optional[EvidenceScore] = None,
) -> dict[str, Any]:
    claims = extract_root_claims(diagnosis.answer)
    root_score = score_root_causes(scenario.expected_root_causes, claims)
    runbook_observations = _runbook_observations(diagnosis.events, diagnosis.metrics)
    runbook_score = score_runbooks(
        scenario.expected_runbooks,
        diagnosis.answer,
        observations=runbook_observations,
    )
    root_data = asdict(root_score)
    root_data["accuracy"] = (root_score.matched_count / root_score.expected_count
                             if len(scenario.members) > 1 else float(root_score.passed))
    runbook_data = asdict(runbook_score)
    if scenario.runbook_targets:
        from variant_suite import score_target_runbooks
        runbook_data = score_target_runbooks(scenario.runbook_targets, diagnosis.answer, claims)
    expected_targets = sorted({root.namespace for root in scenario.expected_root_causes if root.namespace})
    observed_targets = [ns for claim in claims for ns in claim.namespaces]
    return {
        "scoring_version": SCORING_VERSION,
        "success": True,
        "run_id": diagnosis.run_id,
        "elapsed_seconds": diagnosis.elapsed_seconds,
        "root_cause": root_data,
        "root_claims": [asdict(item) for item in claims],
        "group_audit": {
            "expected_namespaces": expected_targets,
            "observed_namespaces": sorted(set(observed_targets)),
            "missing_namespaces": sorted(set(expected_targets) - set(observed_targets)),
            "unexpected_namespaces": sorted(set(observed_targets) - set(expected_targets)) if expected_targets else [],
            "duplicate_namespaces": sorted({ns for ns in observed_targets if observed_targets.count(ns) > 1}),
            "ambiguous_claim_groups": [c.group for c in claims if len(c.namespaces) != 1] if expected_targets else [],
            "source": "final_report_overview_and_root_sections",
        },
        "runbook": runbook_data,
        "evidence": asdict(evidence),
        "evidence_plan_audit": asdict(plan_evidence) if plan_evidence is not None else None,
        "evidence_contract_audit": (
            asdict(evidence_contract_audit)
            if evidence_contract_audit is not None
            else None
        ),
    }


def run_diagnosis_once(
    *,
    run_index: int,
    repeat: int,
    scenario: Scenario,
    scenario_dir: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    prefix = f"[# {run_index:02d}/{repeat}] "
    print(f"{prefix}Diagnosis start", flush=True)
    pending_dir = scenario_dir / f"run-{run_index:02d}-pending"
    if pending_dir.exists():
        shutil.rmtree(pending_dir)
    pending_dir.mkdir(parents=True)
    run_started = time.monotonic()
    request_attempts = max(1, int(getattr(args, "request_attempts", 1) or 1))
    retry_backoff = max(
        0.0,
        float(getattr(args, "retry_backoff_seconds", 0.0) or 0.0),
    )
    attempt_failures: list[dict[str, Any]] = []
    diagnosis: Optional[DiagnosisResult] = None
    successful_attempt_dir: Optional[Path] = None
    for attempt in range(1, request_attempts + 1):
        attempt_dir = pending_dir / f"attempt-{attempt:02d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        attempt_prefix = (
            prefix
            if request_attempts == 1
            else f"{prefix}[attempt {attempt}/{request_attempts}] "
        )
        attempt_started = time.monotonic()
        try:
            diagnosis = diagnose(
                args.url,
                scenario.question,
                args.timeout,
                live_mode=args.live_mode,
                live_path=attempt_dir / "live.log",
                raw_path=attempt_dir / "raw.sse",
                live_prefix=attempt_prefix,
            )
            successful_attempt_dir = attempt_dir
            break
        except Exception as exc:
            attempt_elapsed = time.monotonic() - attempt_started
            partial_run_id = _partial_run_id(attempt_dir / "raw.sse")
            failure = {
                "attempt": attempt,
                "run_id": partial_run_id,
                "elapsed_seconds": round(attempt_elapsed, 3),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            attempt_failures.append(failure)
            (attempt_dir / "error.txt").write_text(str(exc), encoding="utf-8")
            if attempt >= request_attempts:
                break
            delay = retry_backoff * attempt
            print(
                f"{attempt_prefix}REQUEST_RETRY run_id={partial_run_id or '-'} "
                f"elapsed={attempt_elapsed:.1f}s backoff={delay:.1f}s error={exc}",
                flush=True,
            )
            if delay:
                time.sleep(delay)

    if diagnosis is None or successful_attempt_dir is None:
        elapsed = time.monotonic() - run_started
        last_failure = attempt_failures[-1] if attempt_failures else {}
        failed = {
            "run_index": run_index,
            "success": False,
            "run_id": str(last_failure.get("run_id") or ""),
            "elapsed_seconds": elapsed,
            "error": str(last_failure.get("error") or "diagnosis request failed"),
            "request_attempt_count": len(attempt_failures),
            "request_attempt_failures": attempt_failures,
        }
        (pending_dir / "score.json").write_text(
            json.dumps(failed, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            f"{prefix}REQUEST_FAIL attempts={len(attempt_failures)} "
            f"elapsed={elapsed:.1f}s error={failed['error']}",
            flush=True,
        )
        return failed

    run_dir = scenario_dir / f"run-{run_index:02d}-{diagnosis.run_id}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    pending_dir.rename(run_dir)
    # Keep the historical top-level files for manual review, while retaining
    # every request attempt below attempt-NN for timeout/retry auditing.
    shutil.copyfile(
        run_dir / successful_attempt_dir.name / "live.log",
        run_dir / "live.log",
    )
    shutil.copyfile(
        run_dir / successful_attempt_dir.name / "raw.sse",
        run_dir / "raw.sse",
    )
    (run_dir / "report.md").write_text(diagnosis.answer, encoding="utf-8")
    (run_dir / "events.json").write_text(
        json.dumps(diagnosis.events, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    plan_evidence, evidence_payloads = evidence_archive_from_kubectl(
        diagnosis.run_id,
        namespace=args.aiops_namespace,
        target=args.aiops_target,
        container=args.aiops_container,
        archive_root=args.archive_root,
    )
    (run_dir / "evidence.archive.json").write_text(
        json.dumps(
            [{"source": path, "payload": payload} for path, payload in evidence_payloads],
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    if plan_evidence.planned == 0:
        fallback = evidence_from_final_metrics(diagnosis.metrics)
        if fallback.planned:
            plan_evidence = fallback
    evidence_contract_audit = score_evidence_contract(
        scenario.expected_evidence,
        evidence_payloads,
        source="kubectl_archive_fixed_contract" if evidence_payloads else "missing",
        error="" if evidence_payloads else plan_evidence.error,
    )
    evidence = plan_evidence
    scored = _score_run(
        scenario,
        diagnosis,
        evidence,
        plan_evidence=plan_evidence,
        evidence_contract_audit=evidence_contract_audit,
    )
    scored["run_index"] = run_index
    scored["logical_elapsed_seconds"] = round(time.monotonic() - run_started, 3)
    scored["retry_elapsed_seconds"] = round(sum(
        float(item["elapsed_seconds"]) for item in attempt_failures
    ) + sum(retry_backoff * i for i in range(1, len(attempt_failures) + 1)), 3)
    scored["request_attempt_count"] = len(attempt_failures) + 1
    scored["request_attempt_failures"] = attempt_failures
    (run_dir / "score.json").write_text(
        json.dumps(scored, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(
        f"{prefix}Result run_id={diagnosis.run_id} "
        f"root={'PASS' if scored['root_cause']['passed'] else 'FAIL'} "
        f"runbook={'PASS' if scored['runbook']['passed'] else 'FAIL'} "
        f"evidence={evidence.collected}/{evidence.planned} "
        f"mttr={diagnosis.elapsed_seconds:.1f}s",
        flush=True,
    )
    return scored


def _fmt_rate(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def _fmt_duration(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    seconds = float(value)
    return f"{seconds:.1f}s" if seconds < 60 else f"{seconds / 60:.1f}m"


def _aggregate_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    requests_ok = [run for run in runs if run.get("success")]
    successful = [run for run in requests_ok if run.get("fixture_valid") is not False]
    root_correct = sum(
        1 for run in successful if (run.get("root_cause") or {}).get("passed")
    )
    runbook_matched = sum(
        len((run.get("runbook") or {}).get("matched") or []) for run in successful
    )
    runbook_expected = sum(
        len((run.get("runbook") or {}).get("expected") or []) for run in successful
    )
    evidence_collected = sum(
        int((run.get("evidence") or {}).get("collected") or 0) for run in successful
    )
    evidence_planned = sum(
        int((run.get("evidence") or {}).get("planned") or 0) for run in successful
    )
    evidence_values = [
        float((run.get("evidence") or {}).get("completeness"))
        for run in successful
        if (run.get("evidence") or {}).get("completeness") is not None
    ]
    runbook_values = []
    for run in successful:
        runbook = run.get("runbook") or {}
        coverage = runbook.get("coverage")
        if coverage is not None:
            runbook_values.append(float(coverage))
            continue
        expected = len(runbook.get("expected") or [])
        if expected:
            runbook_values.append(len(runbook.get("matched") or []) / expected)
    mttr_values = [float(run.get("elapsed_seconds") or 0.0) for run in successful]
    return {
        "runs": len(runs),
        "successful": len(requests_ok),
        "failed": len(runs) - len(requests_ok),
        "valid_samples": len(successful),
        "invalid_fixture_samples": len(requests_ok) - len(successful),
        "root_correct": root_correct,
        "root_accuracy": (sum(_root_accuracy(run.get("root_cause") or {}) for run in successful)
                          / len(successful) if successful else None),
        "runbook_matched": runbook_matched,
        "runbook_expected": runbook_expected,
        "runbook_coverage": (
            sum(runbook_values) / len(runbook_values) if runbook_values else None
        ),
        "evidence_collected": evidence_collected,
        "evidence_planned": evidence_planned,
        "evidence_samples": len(evidence_values),
        "evidence_completeness": (
            sum(evidence_values) / len(evidence_values) if evidence_values else None
        ),
        "avg_mttr_seconds": (
            sum(mttr_values) / len(mttr_values) if mttr_values else None
        ),
    }


def _root_accuracy(root: Mapping[str, Any]) -> float:
    return float(root.get("accuracy", float(bool(root.get("passed")))))


def _aggregate_scenario_metrics(
    scenarios: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Average independently calculated Case metrics with equal Case weight."""

    aggregates = [
        _aggregate_runs(
            [run for run in scenario.get("runs") or [] if isinstance(run, Mapping)]
        )
        for scenario in scenarios
    ]

    def mean_of(metric: str) -> Optional[float]:
        values = [
            float(aggregate[metric])
            for aggregate in aggregates
            if aggregate.get(metric) is not None
        ]
        return sum(values) / len(values) if values else None

    return {
        "scenario_count": len(aggregates),
        "metric_samples": {key: sum(a.get(key) is not None for a in aggregates)
                           for key in ("root_accuracy", "runbook_coverage", "evidence_completeness", "avg_mttr_seconds")},
        "root_accuracy": mean_of("root_accuracy"),
        "runbook_coverage": mean_of("runbook_coverage"),
        "evidence_completeness": mean_of("evidence_completeness"),
        "avg_mttr_seconds": mean_of("avg_mttr_seconds"),
    }


def evaluation_warnings(stats: Mapping[str, Any]) -> list[str]:
    warnings = []
    if quality_incomplete(stats):
        warnings.append("未完成全量有效验收：以下仅为已获得有效样本的统计，不代表整套测试通过。")
    if stats.get("rescore_complete") is False:
        warnings.append("重评分不完整：包含旧评分或缺失/损坏归档；以下数值仅供审查，不能作为新版完整验收结果。")
    for scenario in stats.get("scenarios") or []:
        if scenario.get("status") == "blocked":
            error = (scenario.get("fixture_errors") or [{}])[-1]
            warnings.append(f"{scenario['id']} 场景阻塞：{error.get('category', '')}；详见 {error.get('archive', '')}。")
        aggregate = _aggregate_runs(scenario.get("runs") or [])
        if aggregate["invalid_fixture_samples"]:
            warnings.append(f"{scenario['id']} 有 {aggregate['invalid_fixture_samples']} 次注入失效，原评分仅供审计，已排除质量均值。")
        if not aggregate["successful"]:
            warnings.append(f"{scenario['id']} 无成功样本，未进入质量均值。")
        elif aggregate["evidence_samples"] != aggregate["successful"]:
            warnings.append(
                f"{scenario['id']} 证据完整度有效样本 {aggregate['evidence_samples']}/{aggregate['successful']}；"
                "缺失值未计入均值，不代表采集完成。"
            )
    return warnings


def build_console_report(stats: Mapping[str, Any], output_dir: Path) -> str:
    """Build the final anomaly-oriented blind-test overview."""

    scenario_rows = [item for item in stats.get("scenarios") or [] if isinstance(item, Mapping)]
    all_runs = [
        run
        for scenario in scenario_rows
        for run in (scenario.get("runs") or [])
        if isinstance(run, Mapping)
    ]
    total = _aggregate_runs(all_runs)
    quality = _aggregate_scenario_metrics(scenario_rows)
    total_elapsed = float(stats.get("total_elapsed_seconds") or 0.0)
    lines = [
        "",
        "=" * 72,
        "AIOps 异常 Case E2E 质量报告（盲测模式）",
        "=" * 72,
        (
            f"场景数: {len(scenario_rows)} | 总运行: {total['runs']} | "
            f"成功: {total['successful']} | 失败: {total['failed']}"
        ),
        f"总耗时: {total_elapsed:.0f}s ({total_elapsed / 60:.1f}m)",
        f"任务状态: {stats.get('status', '未记录')} | 已记录请求: {total['runs']}/{stats.get('planned_runs', total['runs'])}",
        *[f"⚠ {warning}" for warning in evaluation_warnings(stats)],
        "",
        "─" * 72,
        "异常 Case 范围",
        "─" * 72,
        "| Case | 异常类型 | 本次具体故障场景 | 期望 Runbook |",
        "|---|---|---|---|",
    ]
    for scenario in scenario_rows:
        expected = ", ".join(scenario.get("expected_runbooks") or []) or "N/A"
        lines.append(
            f"| {scenario.get('id')} | {scenario.get('anomaly_type') or 'Unknown'} | "
            f"{scenario.get('fault_scenario') or scenario.get('name')} | {expected} |"
        )

    lines.extend([
        "",
        "─" * 72,
        "运行明细",
        "─" * 72,
        "| Case / 异常类型 | # | 请求 | 根因准确率 | Runbook | 证据完整度 | MTTR | Run ID |",
        "|---|---:|---|---|---|---|---:|---|",
    ])
    for scenario in scenario_rows:
        label = f"{scenario.get('id')} {scenario.get('anomaly_type') or 'Unknown'}"
        runs = sorted(
            (run for run in scenario.get("runs") or [] if isinstance(run, Mapping)),
            key=lambda item: int(item.get("run_index") or 0),
        )
        for run in runs:
            run_index = int(run.get("run_index") or 0)
            if not run.get("success"):
                lines.append(
                    f"| {label} | {run_index} | ❌ | N/A | N/A | N/A | "
                    f"{_fmt_duration(float(run.get('elapsed_seconds') or 0.0))} | - |"
                )
                continue
            root = run.get("root_cause") or {}
            runbook = run.get("runbook") or {}
            evidence = run.get("evidence") or {}
            root_text = _fmt_rate(_root_accuracy(root))
            runbook_text = (
                f"{'✅' if runbook.get('passed') else '❌'} "
                f"{len(runbook.get('matched') or [])}/{len(runbook.get('expected') or [])}"
            )
            evidence_text = (
                f"{_fmt_rate(evidence.get('completeness'))} "
                f"({int(evidence.get('collected') or 0)}/{int(evidence.get('planned') or 0)})"
            )
            lines.append(
                f"| {label} | {run_index} | ✅ | {root_text} | {runbook_text} | "
                f"{evidence_text} | {_fmt_duration(run.get('elapsed_seconds'))} | "
                f"{run.get('run_id') or '-'} |"
            )

    lines.extend([
        "",
        "─" * 72,
        "场景汇总",
        "─" * 72,
        "| Case | 异常类型 | 根因准确率 | Runbook 覆盖率 | 平均 MTTR | 证据完整度 | 成功运行 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for scenario in scenario_rows:
        runs = [run for run in scenario.get("runs") or [] if isinstance(run, Mapping)]
        aggregate = _aggregate_runs(runs)
        lines.append(
            f"| {scenario.get('id')} | {scenario.get('anomaly_type') or 'Unknown'} | "
            f"{_fmt_rate(aggregate['root_accuracy'])} | "
            f"{_fmt_rate(aggregate['runbook_coverage'])} | "
            f"{_fmt_duration(aggregate['avg_mttr_seconds'])} | "
            f"{_fmt_rate(aggregate['evidence_completeness'])} | "
            f"{aggregate['successful']}/{aggregate['runs']} |"
        )

    def status(value: Optional[float], threshold: float, *, less_than: bool = False) -> str:
        if quality_incomplete(stats):
            return "待复核"
        if value is None:
            return "N/A"
        passed = value < threshold if less_than else value >= threshold
        return "✅" if passed else "❌"

    thresholds = QUALITY_THRESHOLDS
    lines.extend([
        "",
        "=" * 60,
        "质量指标汇总",
        "=" * 60,
        "| 指标 | 阈值 | 实际 | 状态 |",
        "|---|---:|---:|---:|",
        (
            f"| MTTR | < {thresholds['mttr_seconds'] / 60:.0f}m | "
            f"{_fmt_duration(quality['avg_mttr_seconds'])} | "
            f"{status(quality['avg_mttr_seconds'], thresholds['mttr_seconds'], less_than=True)} |"
        ),
        (
            f"| 根因准确率 | >= {thresholds['root_cause_accuracy']:.0%} | "
            f"{_fmt_rate(quality['root_accuracy'])} | "
            f"{status(quality['root_accuracy'], thresholds['root_cause_accuracy'])} |"
        ),
        (
            f"| Runbook 覆盖率 | >= {thresholds['runbook_coverage']:.0%} | "
            f"{_fmt_rate(quality['runbook_coverage'])} | "
            f"{status(quality['runbook_coverage'], thresholds['runbook_coverage'])} |"
        ),
        (
            f"| 证据完整度 | >= {thresholds['evidence_completeness']:.0%} | "
            f"{_fmt_rate(quality['evidence_completeness'])} | "
            f"{status(quality['evidence_completeness'], thresholds['evidence_completeness'])} |"
        ),
        "",
        (
            "总体口径: 每个 Case 先独立计算四项指标，再对各 Case 指标做算术平均；"
            "各 Case 权重相同。单次证据完整度按 Evidence Plan 计划项与实际成功采集项计算，"
            "请求失败不进入对应 Case 的指标分母。"
        ),
        f"📁 报告目录: {output_dir.resolve()}/",
    ])
    lines.extend(f"⚠ {warning}" for warning in evaluation_warnings(stats))
    return "\n".join(lines)


def build_summary(stats: Mapping[str, Any]) -> str:
    lines = [
        "# 当前 AIOps 质量 Demo",
        "",
        *[f"> ⚠ {warning}\n" for warning in evaluation_warnings(stats)],
        "| 场景 | 运行 | 状态 | 根因准确率 | Runbook | 证据完整度 | MTTR | Run ID |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    all_runs: list[Mapping[str, Any]] = []
    for scenario in stats.get("scenarios") or []:
        for index, run in enumerate(scenario.get("runs") or [], start=1):
            if not run.get("success"):
                lines.append(
                    f"| {scenario['id']} | {index} | ❌ 请求失败 | - | - | - | "
                    f"{float(run.get('elapsed_seconds') or 0):.1f}s | - |"
                )
                all_runs.append(run)
                continue
            root = run["root_cause"]
            evidence = run["evidence"]
            runbook = run["runbook"]
            lines.append(
                f"| {scenario['id']} | {index} | ✅ | "
                f"{_fmt_rate(_root_accuracy(root))} | "
                f"{_fmt_rate(runbook['coverage'])} | "
                f"{_fmt_rate(evidence['completeness'])} ({evidence['collected']}/{evidence['planned']}) | "
                f"{float(run.get('elapsed_seconds') or 0):.1f}s | {run.get('run_id') or '-'} |"
            )
            all_runs.append(run)

    successful = [run for run in all_runs if run.get("success")]
    scenario_rows = [
        scenario
        for scenario in stats.get("scenarios") or []
        if isinstance(scenario, Mapping)
    ]
    quality = _aggregate_scenario_metrics(scenario_rows)
    samples = quality["metric_samples"]
    lines.extend([
        "",
        "## 四项质量指标汇总",
        "",
        f"- MTTR：{_fmt_duration(quality['avg_mttr_seconds'])}（{samples['avg_mttr_seconds']} 个 Case 独立计算后算术平均）",
        f"- 根因准确率：{_fmt_rate(quality['root_accuracy'])}（{samples['root_accuracy']} 个 Case 准确率算术平均）",
        f"- Runbook 覆盖率：{_fmt_rate(quality['runbook_coverage'])}（{samples['runbook_coverage']} 个 Case 覆盖率算术平均）",
        f"- 证据完整度：{_fmt_rate(quality['evidence_completeness'])}（{samples['evidence_completeness']} 个 Case 完整度算术平均）",
        "- 总体口径：每个 Case 先独立计算指标，再对各 Case 指标做算术平均，各 Case 权重相同。单次证据完整度按 Evidence Plan 的 `plan_collected / plan_total` 计算；Case 内对成功运行做算术平均。固定 Case 证据合同仅保留在 `evidence_contract_audit` 中供审计。",
        f"- 请求成功率：{_fmt_rate(len(successful) / len(all_runs) if all_runs else None)}（{len(successful)}/{len(all_runs)}，不混入上述四项指标分母）",
        "",
    ])
    return "\n".join(lines)


def _md_cell(value: Any) -> str:
    return str(value if value is not None else "-").replace("|", "\\|").replace("\n", " ")


def _readme_metrics(aggregate: Mapping[str, Any], *, incomplete: bool = False) -> list[str]:
    """Render existing scores only; this presentation layer never re-scores."""
    rows = [
        ("根因准确率", "root_accuracy", QUALITY_THRESHOLDS["root_cause_accuracy"], False),
        ("Runbook 覆盖率", "runbook_coverage", QUALITY_THRESHOLDS["runbook_coverage"], False),
        ("平均 MTTR", "avg_mttr_seconds", QUALITY_THRESHOLDS["mttr_seconds"], True),
        ("证据完整度", "evidence_completeness", QUALITY_THRESHOLDS["evidence_completeness"], False),
    ]
    lines = ["| 指标 | 实际 | 阈值 | 状态 |", "|---|---:|---:|---|"]
    for label, key, threshold, duration in rows:
        value = aggregate.get(key)
        formatted = _fmt_duration(value) if duration else _fmt_rate(value)
        limit = f"< {threshold / 60:g}m" if duration else f">= {threshold:.0%}"
        status = "N/A" if value is None else (
            "✅" if (value < threshold if duration else value >= threshold) else "❌"
        )
        if incomplete:
            status = "待复核"
        lines.append(f"| {label} | {formatted} | {limit} | {status} |")
    return lines


def build_case_readme(
    scenario: Mapping[str, Any], stats: Mapping[str, Any], output_dir: Path,
) -> str:
    cid = str(scenario["id"])
    runs = sorted(scenario.get("runs") or [], key=lambda r: int(r.get("run_index") or 0))
    aggregate = _aggregate_runs(runs)
    source_dir = Path(stats.get("source_report_dir") or output_dir)
    case_dir = output_dir / cid
    lines = [
        f"# {_md_cell(cid)} · {_md_cell(scenario.get('anomaly_type') or 'Unknown')}", "",
        "[返回总体报告](../readme.md)", "",
        f"具体故障：{_md_cell(scenario.get('fault_scenario') or scenario.get('name'))}", "",
        f"场景状态：{_md_cell(scenario.get('status') or '未记录')}。", "",
        *[f"> 故障验收记录：{_md_cell(error.get('category'))}；归档 `{_md_cell(error.get('archive'))}`。\n"
          for error in scenario.get("fixture_errors", [])],
        f"期望 Runbook：{_md_cell(', '.join(scenario.get('expected_runbooks') or []) or 'N/A')}", "",
        f"成功运行：{aggregate['successful']}/{aggregate['runs']}；"
        f"证据完整度有效样本：{aggregate['evidence_samples']}/{aggregate['successful']}。", "",
        "## 四项质量指标", "",
        *_readme_metrics(aggregate, incomplete=stats.get("rescore_complete") is False or
                         scenario.get("status") == "blocked" or aggregate["invalid_fixture_samples"] > 0), "",
        "## 每次运行", "",
        "以下是原脚本评分，不等于人工裁决；根因 0% 不自动代表 Agent 实际误诊。", "",
        "| # | 请求 | 根因准确率 | Runbook 覆盖率 | 证据完整度 | MTTR | 原始报告 / Run ID |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for run in runs:
        index = int(run.get("run_index") or 0)
        rid = str(run.get("run_id") or "")
        report = source_dir / cid / f"run-{index:02d}-{rid}" / "report.md"
        report_label = _md_cell(rid or "-")
        if rid and report.is_file():
            target = Path(os.path.relpath(report, case_dir)).as_posix()
            report_label = f"[{report_label}](<{target}>)"
        if not run.get("success"):
            lines.append(f"| {index} | ❌ | N/A | N/A | N/A | {_fmt_duration(run.get('elapsed_seconds'))} | {report_label} |")
            continue
        root = run.get("root_cause") or {}
        rb = run.get("runbook") or {}
        evidence = run.get("evidence") or {}
        ev = _fmt_rate(evidence.get("completeness"))
        if evidence.get("completeness") is not None:
            ev += f" ({evidence.get('collected', 0)}/{evidence.get('planned', 0)})"
        lines.append(
            f"| {index} | ✅ | {_fmt_rate(_root_accuracy(root))} | "
            f"{_fmt_rate(rb.get('coverage'))} | {ev} | {_fmt_duration(run.get('elapsed_seconds'))} | {report_label} |"
        )
    lines.extend(["", "## 统计说明", "",
        "Case 内对成功运行的单次指标求算术平均。证据单次先按各 lane 的完成项/计划项计算，"
        "再对每次完整度求平均；N/A 不进入均值。请求失败单列，不作为质量分数。",
        "Runbook 覆盖不等于选用精确率；证据完整度是 Agent Plan 完成率，不是独立的事实充分性核验。", ""])
    return "\n".join(lines)


def build_readme(stats: Mapping[str, Any], output_dir: Path) -> str:
    scenarios = stats.get("scenarios") or []
    runs = [run for scenario in scenarios for run in scenario.get("runs") or []]
    total = _aggregate_runs(runs)
    lines = [
        "# AIOps 异常 Case 质量报告", "",
        f"任务状态：{_md_cell(stats.get('status') or '未记录')}；评分版本：{_md_cell(stats.get('scoring_version') or '未记录')}。", "",
        f"场景数：{len(scenarios)}；已记录运行：{total['runs']} / 计划 {stats.get('planned_runs', '未记录')}；"
        f"成功：{total['successful']}；失败：{total['failed']}。", "",
        "以下保留脚本原始评分，不据此宣称已完成人工审查。", "",
        "## 场景汇总", "",
        "| Case | 异常类型 | 根因准确率 | Runbook 覆盖率 | 平均 MTTR | 证据完整度 | 成功运行 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for scenario in scenarios:
        a = _aggregate_runs(scenario.get("runs") or [])
        cid = str(scenario["id"])
        lines.append(
            f"| [{_md_cell(cid)}]({cid}/readme.md) | {_md_cell(scenario.get('anomaly_type') or 'Unknown')} | "
            f"{_fmt_rate(a['root_accuracy'])} | {_fmt_rate(a['runbook_coverage'])} | "
            f"{_fmt_duration(a['avg_mttr_seconds'])} | {_fmt_rate(a['evidence_completeness'])} | "
            f"{a['successful']}/{a['runs']} |"
        )
    lines.extend(["", "## 总体质量指标", "",
        *_readme_metrics(_aggregate_scenario_metrics(scenarios), incomplete=quality_incomplete(stats)), "",
        "先在每个 Case 内按运行求算术平均，再对有有效值的 Case 等权平均；不把各 Case 的数量合并作分母。",
        "单项通过不代表每个 Case 都通过，请同时查看上表和各 Case 明细。", ""])
    for warning in evaluation_warnings(stats):
        lines.extend([f"> ⚠ {warning}", ""])
    if (output_dir / "manual_review.md").is_file():
        lines.extend(["## 独立人工审查", "", "[查看逐份人工审查与评分差异](manual_review.md)。人工意见不覆盖上述原始分数。", ""])
    return "\n".join(lines)


def write_readme_reports(output_dir: Path, stats: Mapping[str, Any]) -> None:
    """Publish Markdown views without modifying source scores or reports."""
    scenarios = stats.get("scenarios") or []
    for scenario in scenarios:
        cid = str(scenario.get("id") or "")
        if not SAFE_ID.fullmatch(cid) or cid in {".", ".."}:
            raise ValueError(f"unsafe scenario id for report: {cid!r}")
    for scenario in scenarios:
        case_dir = output_dir / str(scenario["id"])
        case_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(case_dir / "readme.md", build_case_readme(scenario, stats, output_dir))
    atomic_write(output_dir / "readme.md", build_readme(stats, output_dir))


def write_checkpoint(output_dir: Path, stats: Mapping[str, Any]) -> None:
    """Persist aggregate state after every run for long benchmark jobs."""

    atomic_write(output_dir / "stats.json", json.dumps(stats, ensure_ascii=False, indent=2, default=str))
    atomic_write(output_dir / "summary.md", build_summary(stats))
    atomic_write(output_dir / "overview.txt", build_console_report(stats, output_dir) + "\n")
    write_readme_reports(output_dir, stats)


def rescore_existing_report(
    output_dir: Path,
    scenarios: Mapping[str, Scenario],
    selected: Sequence[Scenario],
    *, cases_file: Optional[Path] = None,
) -> dict[str, Any]:
    """Publish an independent scoring revision; preserve the source scores."""
    with exclusive_lock(output_dir / ".quality.lock"):
        assert_report_idle(output_dir)
        return _rescore_existing_report(output_dir, scenarios, selected, cases_file=cases_file)


def _rescore_existing_report(
    output_dir: Path, scenarios: Mapping[str, Scenario], selected: Sequence[Scenario],
    *, cases_file: Optional[Path] = None,
) -> dict[str, Any]:

    checkpoint_path = output_dir / "stats.json"
    if not checkpoint_path.is_file():
        raise SystemExit(f"missing checkpoint: {checkpoint_path}")
    stats = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if not isinstance(stats, dict):
        raise SystemExit(f"invalid checkpoint: {checkpoint_path}")
    source_dir = output_dir
    output_dir = source_dir / "rescores" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir.mkdir(parents=True, exist_ok=False)

    selected_ids = {scenario.id for scenario in selected}
    manifest = scoring_manifest(cases_file)
    rescored = 0
    missing: list[str] = []
    for scenario_stats in stats.get("scenarios") or []:
        scenario_id = str(scenario_stats.get("id") or "")
        if scenario_id not in selected_ids:
            continue
        scenario = scenarios.get(scenario_id)
        if scenario is None:
            continue
        for run in scenario_stats.get("runs") or []:
            if not run.get("success"):
                continue
            run_index = int(run.get("run_index") or 0)
            run_id = str(run.get("run_id") or "")
            run_dir = source_dir / scenario_id / f"run-{run_index:02d}-{run_id}"
            report_path = run_dir / "report.md"
            events_path = run_dir / "events.json"
            score_path = run_dir / "score.json"
            if not report_path.is_file() or not events_path.is_file():
                missing.append(str(run_dir))
                run["rescore_error"] = "missing report/events archive; original score retained"
                continue

            try:
                report = report_path.read_text(encoding="utf-8")
                events = json.loads(events_path.read_text(encoding="utf-8"))
                if not isinstance(events, list):
                    raise ValueError("events archive must be a list")
                existing_score = json.loads(score_path.read_text(encoding="utf-8")) if score_path.is_file() else {}
                if not isinstance(existing_score, dict):
                    raise ValueError("score archive must be an object")
            except (OSError, ValueError) as exc:
                missing.append(str(run_dir))
                run["rescore_error"] = f"invalid archive; original score retained: {exc}"
                continue
            metrics: Mapping[str, Any] = {}
            for event in events:
                if isinstance(event, Mapping) and event.get("type") == "final":
                    candidate = event.get("metrics") or {}
                    if isinstance(candidate, Mapping):
                        metrics = candidate

            revision = _score_run(
                scenario,
                DiagnosisResult(run_id, report, metrics, float(run.get("elapsed_seconds") or 0),
                                tuple(item for item in events if isinstance(item, Mapping)), ""),
                EvidenceScore(0, 0, None, (), "not_rescored"),
            )
            for key in ("scoring_version", "root_cause", "root_claims", "runbook", "group_audit"):
                run[key] = revision[key]
            run.pop("rescore_error", None)
            run["rescore_revision"] = output_dir.name
            existing_score.update(run)
            revision_dir = output_dir / scenario_id / run_dir.name
            revision_dir.mkdir(parents=True)
            existing_score["source_report"] = str(report_path.resolve())
            atomic_write(revision_dir / "score.json", json.dumps(existing_score, ensure_ascii=False, indent=2, default=str))
            rescored += 1

    stats["scoring_version"] = SCORING_VERSION
    stats["scoring_manifest"] = manifest
    stats["rescore_scope"] = "root_cause_and_runbook_only; evidence retained from source"
    stats["rescore_expectations"] = {
        scenario.id: {"root_causes": [asdict(item) for item in scenario.expected_root_causes],
                      "runbooks": list(scenario.expected_runbooks)}
        for scenario in selected
    }
    stats["source_report_dir"] = str(source_dir.resolve())
    stats["revision_dir"] = str(output_dir.resolve())
    stats["rescore_complete"] = not missing and all(
        run.get("rescore_revision") == output_dir.name
        for scenario in stats.get("scenarios", []) for run in scenario.get("runs", [])
        if run.get("success")
    )
    stats["rescored_at"] = datetime.now().isoformat()
    stats["rescore_missing_archives"] = missing
    write_checkpoint(output_dir, stats)
    print(
        f"Rescored {rescored} successful runs with scoring version {SCORING_VERSION}; "
        f"missing archives={len(missing)}",
        flush=True,
    )
    print(build_console_report(stats, output_dir), flush=True)
    return stats


def main() -> Optional[str]:
    with ExitStack() as stack:
        return _main(stack)


def _main(stack: ExitStack) -> Optional[str]:
    session_started = time.monotonic()
    parser = argparse.ArgumentParser(description="Current AIOps root-cause/evidence quality demo")
    parser.add_argument(
        "--scenario", default="c04",
        help="all=11 baselines; variants=17 variants; expanded=28 isolated scenarios; or comma-separated IDs",
    )
    parser.add_argument("--combine", action="store_true", help="deploy selected scenarios together and score each target separately")
    parser.add_argument("--repeat", "-n", type=int, default=1)
    parser.add_argument("--concurrency", "-c", type=int, default=1)
    parser.add_argument("--url", default="http://10.2.0.48:30800")
    parser.add_argument("--timeout", type=int, default=1200, help="diagnosis request timeout seconds")
    parser.add_argument(
        "--request-attempts",
        type=int,
        default=2,
        help="bounded attempts per logical run; every failed attempt is archived",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=30.0,
        help="linear backoff before retrying a failed diagnosis request",
    )
    parser.add_argument("--catalog", default=str(CATALOG_PATH))
    parser.add_argument("--cases-file", default=str(DEMO_CASES_PATH))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="disable detached-worker protection and bind the benchmark to this terminal",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="resume missing run indexes from an existing output-dir checkpoint",
    )
    parser.add_argument("--resume-runtime-update", action="store_true",
                        help="with --resume: explicitly accept reviewed lifecycle-only script changes, preserving an audit snapshot")
    parser.add_argument(
        "--rescore-existing",
        action="store_true",
        help="re-score archived reports in --output-dir without calling or deploying AIOps",
    )
    parser.add_argument("--reuse-existing", action="store_true", help="do not clean/apply anomaly cases")
    parser.add_argument("--keep-last", action="store_true", help="leave the final scenario deployed")
    parser.add_argument("--aiops-namespace", default="aiops")
    parser.add_argument("--aiops-target", default="deployment/aiops-copilot")
    parser.add_argument("--aiops-container", default="aiops-copilot")
    parser.add_argument("--archive-root", default="/tmp/aiops/reports/context_archives")
    parser.add_argument(
        "--live-mode", choices=("off", "compact", "full"), default="compact",
        help="stream human-readable progress; full also prints token-level model output",
    )
    args = parser.parse_args()

    if args.resume_runtime_update and not args.resume:
        parser.error("--resume-runtime-update requires --resume")

    if args.repeat < 1:
        raise SystemExit("--repeat must be >= 1")
    if args.concurrency < 1:
        raise SystemExit("--concurrency must be >= 1")
    if args.request_attempts < 1:
        raise SystemExit("--request-attempts must be >= 1")
    if args.retry_backoff_seconds < 0:
        raise SystemExit("--retry-backoff-seconds must be >= 0")
    if args.timeout < 900:
        print(
            "Warning: --timeout below 900s is shorter than the combined "
            "Layer/Evidence service budget and may create false request failures.",
            file=sys.stderr,
            flush=True,
        )
    catalog = load_catalog(Path(args.catalog))
    scenarios = load_scenarios(Path(args.cases_file))
    manifest = scoring_manifest(Path(args.cases_file))
    try:
        selected = select_scenarios(scenarios, args.scenario)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    for scenario in selected:
        unknown_members = [item for item in scenario.members if item not in catalog]
        if unknown_members:
            raise SystemExit(f"scenario {scenario.id} has unknown members: {unknown_members}")
    if args.combine:
        from variant_suite import combine_scenarios
        combined = combine_scenarios(selected, catalog)
        selected = [combined]
        scenarios[combined.id] = combined
    timed_members = {member for s in selected for member in s.members
                     if (catalog[member].get("cleanup") or {}).get("shorten_grace")}
    if timed_members and args.concurrency != 1:
        raise SystemExit("preStop/grace fixtures require -c 1 because they are renewed between runs")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else default_output_dir(selected, timestamp=timestamp)
    )
    if args.rescore_existing:
        if not args.output_dir:
            raise SystemExit("--rescore-existing requires --output-dir")
        rescore_existing_report(output_dir, scenarios, selected, cases_file=Path(args.cases_file))
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.foreground and os.environ.get(PROTECTED_WORKER_ENV) != "1":
        raise SystemExit(launch_protected_worker(output_dir, sys.argv[1:]))

    stack.enter_context(exclusive_lock(output_dir / ".quality.lock"))
    assert_report_idle(output_dir)
    # Lock by Kubernetes API server, independent of output directory or AIOps URL.
    cluster = run_command([
        "kubectl", "config", "view", "--minify", "-o", "jsonpath={.clusters[0].cluster.server}"
    ], capture=True, timeout=15).stdout.strip()
    if not cluster:
        raise RuntimeError("cannot determine cluster identity for test isolation")
    key = hashlib.sha256(cluster.encode()).hexdigest()[:24]
    stack.enter_context(exclusive_lock(Path(tempfile.gettempdir()) / f"aiops-quality-cluster-{key}.lock"))
    if (output_dir / "stats.json").exists() and not args.resume:
        raise RuntimeError("output directory already contains results; use --resume or a new directory")
    requests.get(f"{args.url.rstrip('/')}/health", timeout=10).raise_for_status()
    checkpoint_path = output_dir / "stats.json"
    if args.resume and checkpoint_path.exists():
        loaded = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise SystemExit(f"invalid checkpoint: {checkpoint_path}")
        stats: dict[str, Any] = loaded
        if stats.get("selected_scenarios") != [s.id for s in selected] or stats.get("repeat") != args.repeat:
            raise RuntimeError("resume must preserve the original selected scenarios and repeat count")
        accept_runtime_resume(stats, manifest, output_dir, allowed=args.resume_runtime_update)
        stats["resumed_at"] = datetime.now().isoformat()
        stats["concurrency"] = args.concurrency
        stats.setdefault("resume_sessions", []).append({
            "timestamp": stats["resumed_at"],
            "previous_terminal_state": {k: stats[k] for k in
                ("status", "error", "cleanup_error", "finished_at", "completed_at") if k in stats},
        })
        for key in ("error", "cleanup_error", "finished_at", "completed_at"):
            stats.pop(key, None)
    else:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "url": args.url,
            "concurrency": args.concurrency,
            "scoring_version": SCORING_VERSION,
            "scoring_manifest": manifest,
            "scenarios": [],
        }
    stats["selected_scenarios"] = [scenario.id for scenario in selected]
    stats["repeat"] = args.repeat
    stats["planned_runs"] = len(selected) * args.repeat
    selected_by_id = {scenario.id: scenario for scenario in selected}
    for existing in stats.get("scenarios") or []:
        scenario = selected_by_id.get(str(existing.get("id") or ""))
        if scenario is None:
            continue
        existing["name"] = scenario.name
        existing["anomaly_type"] = scenario.anomaly_type
        existing["fault_scenario"] = scenario.fault_scenario
        existing["expected_runbooks"] = list(scenario.expected_runbooks)
        existing["expected_evidence"] = [asdict(item) for item in scenario.expected_evidence]
    elapsed_before_session = float(stats.get("total_elapsed_seconds") or 0.0)

    def checkpoint() -> None:
        stats["total_elapsed_seconds"] = round(
            elapsed_before_session + (time.monotonic() - session_started), 3
        )
        write_checkpoint(output_dir, stats)

    environment_active = False

    stats["status"] = "running"
    try:
        for scenario_index, scenario in enumerate(selected, start=1):
            print(f"\n[{scenario_index}/{len(selected)}] {scenario.id}: {scenario.name}", flush=True)
            existing_stats = next(
                (item for item in stats.get("scenarios") or [] if item.get("id") == scenario.id),
                None,
            )
            existing_indexes = {
                int(item.get("run_index") or 0)
                for item in (existing_stats or {}).get("runs") or []
            }
            if args.resume and all(
                run_index in existing_indexes for run_index in range(1, args.repeat + 1)
            ):
                print(
                    f"Checkpoint: completed={len(existing_indexes)} pending=0 "
                    f"total={args.repeat}; skipping deployment",
                    flush=True,
                )
                continue
            scenario_dir = output_dir / scenario.id
            scenario_dir.mkdir(parents=True, exist_ok=True)
            scenario_stats = next(
                (item for item in stats.get("scenarios") or [] if item.get("id") == scenario.id),
                None,
            )
            if scenario_stats is None:
                scenario_stats = {
                    "id": scenario.id,
                    "name": scenario.name,
                    "anomaly_type": scenario.anomaly_type,
                    "fault_scenario": scenario.fault_scenario,
                    "members": list(scenario.members),
                    "expected_root_causes": [asdict(item) for item in scenario.expected_root_causes],
                    "expected_runbooks": list(scenario.expected_runbooks),
                    "expected_evidence": [asdict(item) for item in scenario.expected_evidence],
                    "runbook_targets": scenario.runbook_targets,
                    "runs": [],
                }
                stats.setdefault("scenarios", []).append(scenario_stats)
            completed_indexes = {
                int(item.get("run_index") or 0) for item in scenario_stats.get("runs") or []
            }
            pending_indexes = [
                run_index for run_index in range(1, args.repeat + 1)
                if run_index not in completed_indexes
            ]
            scenario_stats["status"] = "preparing"
            checkpoint()
            # Cleanup errors remain fatal: do not contaminate the next scenario.
            if not args.reuse_existing:
                cleanup_catalog_namespaces(catalog)
                environment_active = True
            try:
                if not args.reuse_existing:
                    apply_scenario(scenario, catalog)
                for member in scenario.members:
                    wait_for_case_gate(catalog[member])
            except (TimeoutError, subprocess.SubprocessError) as exc:
                record_fixture_failure(scenario, catalog, scenario_dir, scenario_stats, exc, phase="setup")
                scenario_stats["blocked_run_indexes"] = pending_indexes
                checkpoint()
                if not args.reuse_existing:
                    cleanup_catalog_namespaces(catalog)
                    environment_active = False
                continue
            scenario_stats.pop("blocked_run_indexes", None)
            scenario_stats["status"] = "running"
            if scenario.settle_after_gate_seconds:
                print(f"Telemetry settle: {scenario.settle_after_gate_seconds}s", flush=True)
                time.sleep(scenario.settle_after_gate_seconds)
            print(
                f"Checkpoint: completed={len(completed_indexes)} "
                f"pending={len(pending_indexes)} total={args.repeat}",
                flush=True,
            )
            checkpoint()
            def checked_run(run_index):
                # A long run must not silently outlive a preStop/grace fixture.
                if run_index > 1 and not args.reuse_existing:
                    from variant_suite import fixture_manager
                    for member in scenario.members:
                        if member in timed_members:
                            fixture_manager().clean(catalog[member])
                            fixture_manager().deploy(catalog[member])
                before = precheck_with_refresh(scenario, catalog, scenario_stats, run_index,
                                               reuse_existing=args.reuse_existing)
                atomic_write(scenario_dir / f"fixture-run-{run_index:02d}-before.json",
                             json.dumps(before, ensure_ascii=False, indent=2))
                scored = run_diagnosis_once(
                    run_index=run_index, repeat=args.repeat, scenario=scenario,
                    scenario_dir=scenario_dir, args=args,
                )
                scored["runtime_revision"] = hashlib.sha256(
                    json.dumps(manifest, sort_keys=True).encode()).hexdigest()
                try:
                    after = {m: _pod_for_case(catalog[m]) for m in scenario.members}
                    atomic_write(scenario_dir / f"fixture-run-{run_index:02d}-after.json",
                                 json.dumps(after, ensure_ascii=False, indent=2))
                    for member in scenario.members:
                        if before[member].get("metadata", {}).get("uid") != after[member].get("metadata", {}).get("uid"):
                            raise RuntimeError(f"{member} Pod UID changed during diagnosis")
                        if catalog[member].get("variant"):
                            from variant_suite import fixture_manager
                            if not fixture_manager().validate_variant(catalog[member], 60):
                                raise RuntimeError(f"{member} cause gate no longer holds")
                    scored["fixture_valid"] = True
                except Exception as exc:
                    scored["fixture_valid"] = False
                    scored["fixture_error"] = str(exc)
                    record_fixture_failure(scenario, catalog, scenario_dir, scenario_stats, exc,
                                           phase=f"run-{run_index:02d}-postcheck")
                    # Keep the response/score for audit but exclude invalid injections.
                score_path = scenario_dir / f"run-{run_index:02d}-{scored.get('run_id')}" / "score.json"
                if score_path.is_file():
                    atomic_write(score_path, json.dumps(scored, ensure_ascii=False, indent=2))
                return scored
            if args.concurrency == 1:
                for run_index in pending_indexes:
                    try:
                        scored = checked_run(run_index)
                    except TimeoutError as exc:
                        record_fixture_failure(scenario, catalog, scenario_dir, scenario_stats, exc,
                                               phase=f"run-{run_index:02d}-precheck")
                        completed = {r["run_index"] for r in scenario_stats["runs"]}
                        scenario_stats["blocked_run_indexes"] = [i for i in pending_indexes if i not in completed]
                        checkpoint()
                        break
                    scenario_stats["runs"].append(scored)
                    checkpoint()
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                    futures = {
                        pool.submit(
                            checked_run, run_index,
                        ): run_index
                        for run_index in pending_indexes
                    }
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            scored = future.result()
                        except TimeoutError as exc:
                            record_fixture_failure(scenario, catalog, scenario_dir, scenario_stats, exc,
                                                   phase=f"run-{futures[future]:02d}-precheck")
                            scenario_stats.setdefault("blocked_run_indexes", []).append(futures[future])
                            checkpoint()
                            continue
                        scenario_stats["runs"].append(scored)
                        scenario_stats["runs"].sort(key=lambda item: int(item.get("run_index") or 0))
                        checkpoint()
            if not args.reuse_existing and not (args.keep_last and scenario_index == len(selected)):
                cleanup_catalog_namespaces(catalog)
                environment_active = False
            if scenario_stats["status"] != "blocked":
                scenario_stats["status"] = "completed"
            checkpoint()
        # A finished traversal with blocked/invalid samples is not a full pass.
        stats["status"] = "completed_with_errors" if quality_incomplete(stats) else "completed"
    except BaseException as exc:
        stats["status"] = "failed"
        stats["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if environment_active and not args.reuse_existing and not args.keep_last:
            try:
                cleanup_catalog_namespaces(catalog)
            except Exception as exc:
                print(f"Final cleanup failed: {exc}", file=sys.stderr)
                stats["cleanup_error"] = str(exc)
                stats["status"] = "failed"
        stats["finished_at"] = datetime.now().isoformat()
        if stats["status"] in {"completed", "completed_with_errors"}:
            stats["completed_at"] = stats["finished_at"]
        checkpoint()
        print(build_console_report(stats, output_dir), flush=True)
    return stats["status"]


if __name__ == "__main__":
    if os.environ.get(PROTECTED_WORKER_ENV) == "1":
        _protected_worker_entrypoint()
    else:
        main()
