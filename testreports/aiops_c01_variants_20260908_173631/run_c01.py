"""Eight cluster-wide requests: three isolated Pending causes, then all three.

Reuse existing fixture gates, SSE client, archive retrieval and cleanup. This is
an execution record for manual review, not a change to production or scoring.
"""
import hashlib
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "test/pod-anomaly-cases/scripts"))
sys.path.insert(0, str(ROOT / "test/aiops_quality_e2e"))
from manage_cases import catalog, deploy, clean, validate_variant, command
from run_quality_demo import diagnose, evidence_archive_from_kubectl, atomic_write

QUESTION = "我的集群有什么问题？"
URL = "http://10.2.0.48:30800"
CASES = catalog()
ACTIVE = []
GROUPS = [("01-cpu", ["c01-cpu"]), ("02-memory", ["c01-memory"]),
          ("03-pvc", ["c01-pvc"]), ("04-combined", ["c01-cpu", "c01-memory", "c01-pvc"])]
STATE = {"status": "running", "started_at": datetime.now().isoformat(),
         "question": QUESTION, "url": URL, "timeout_seconds": 1200,
         "request_attempts": 1, "planned_requests": 8, "runs": [], "cleanup_errors": []}


def save(path, payload):
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))


def checkpoint():
    save(OUT / "runner.json", STATE)


def kubectl_json(args):
    return json.loads(command(["kubectl", *args, "-o", "json"], capture=True, timeout=25))


def snapshot(directory, name):
    results = {}
    for member in ACTIVE:
        ns = CASES[member]["namespace"]
        results[member] = {"namespace": ns,
            "pods": kubectl_json(["-n", ns, "get", "pods"]),
            "events": kubectl_json(["-n", ns, "get", "events"])}
    save(directory / name, results)


def cleanup():
    errors = []
    for member in reversed(ACTIVE):
        try:
            clean(CASES[member])
        except Exception as exc:
            errors.append({"case": member, "error": str(exc)})
    STATE["cleanup_errors"].extend(errors)
    if errors:
        checkpoint()
        raise RuntimeError("cleanup incomplete; stopping to avoid cross-scenario contamination")
    ACTIVE.clear()


def request(group, index):
    directory = OUT / group / f"run-{index:02d}"
    directory.mkdir(parents=True)
    for member in ACTIVE:
        if not validate_variant(CASES[member], 240):
            raise RuntimeError(f"fault not established: {member}; no Agent request sent")
    snapshot(directory, "before.json")
    row = {"group": group, "index": index, "members": list(ACTIVE), "status": "requesting"}
    STATE["runs"].append(row)
    checkpoint()
    try:
        result = diagnose(URL, QUESTION, 1200, live_mode="compact", live_path=directory / "live.log",
                          raw_path=directory / "raw.sse", live_prefix=f"[{group}/{index}] ")
        (directory / "report.md").write_text(result.answer, encoding="utf-8")
        save(directory / "events.json", result.events)
        save(directory / "metrics.json", result.metrics)
        row.update(status="completed", run_id=result.run_id, elapsed_seconds=result.elapsed_seconds)
        checkpoint()
        score, records = evidence_archive_from_kubectl(result.run_id, namespace="aiops",
            target="deployment/aiops-copilot", container="aiops-copilot",
            archive_root="/tmp/aiops/reports/context_archives")
        save(directory / "evidence.archive.json", {"plan_audit": asdict(score), "records": records})
        snapshot(directory, "after.json")
        print(f"RUN COMPLETED {group}/{index} {result.run_id} {result.elapsed_seconds:.1f}s", flush=True)
    except BaseException as exc:
        row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        checkpoint()
        raise


if __name__ == "__main__":
    checkpoint()
    try:
        nodes = kubectl_json(["get", "nodes"])
        save(OUT / "node-capacity.json", [{"name": n["metadata"]["name"],
            "capacity": n["status"].get("capacity"), "allocatable": n["status"].get("allocatable")}
            for n in nodes["items"]])
        rb = kubectl_json(["-n", "aiops", "get", "configmap", "aiops-runbooks"])["data"]
        save(OUT / "runbook-snapshot.json", rb)
        STATE["runbook_sha256"] = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in rb.items()}
        for group, members in GROUPS:
            STATE["current_group"] = group
            checkpoint()
            for member in members:
                ACTIVE.append(member)
                deploy(CASES[member])
            for member in members:
                if not validate_variant(CASES[member], 240):
                    raise RuntimeError(f"fault not established: {member}")
            time.sleep(20)
            for index in (1, 2):
                request(group, index)
            cleanup()
        STATE["status"] = "completed"
    except BaseException as exc:
        STATE.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        try:
            if ACTIVE:
                cleanup()
        finally:
            STATE["finished_at"] = datetime.now().isoformat()
            checkpoint()
