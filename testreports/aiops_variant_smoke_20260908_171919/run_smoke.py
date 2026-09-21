"""Two real cluster-wide diagnoses; manual review only, no scorer tuning."""
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
from run_quality_demo import diagnose, evidence_archive_from_kubectl

QUESTION = "我的集群有什么问题？"
URL = "http://10.2.0.48:30800"
CASES = catalog()
CREATED = []
STATE = {"status": "running", "started_at": datetime.now().isoformat(),
         "question": QUESTION, "url": URL, "timeout_seconds": 1200,
         "request_attempts": 1, "runs": []}


def save(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def checkpoint():
    save(OUT / "runner.json", STATE)


def snapshot(directory, name, members):
    results = {}
    for member in members:
        ns = CASES[member]["namespace"]
        results[member] = {
            "namespace": ns,
            "pods": json.loads(command(["kubectl", "-n", ns, "get", "pods", "-o", "json"], capture=True, timeout=20)),
            "events": json.loads(command(["kubectl", "-n", ns, "get", "events", "-o", "json"], capture=True, timeout=20)),
        }
    save(directory / name, results)


def run(name, additions):
    for member in additions:
        CREATED.append(member)  # Include any partially applied fixture in final cleanup.
        deploy(CASES[member])
    for member in CREATED:
        if not validate_variant(CASES[member], 240):
            raise RuntimeError(f"fault not established: {member}; no Agent request sent")
    print("Allow telemetry 20 seconds to catch up", flush=True)
    time.sleep(20)
    directory = OUT / name
    directory.mkdir()
    snapshot(directory, "before.json", CREATED)
    row = {"name": name, "members": list(CREATED), "status": "requesting"}
    STATE["runs"].append(row)
    checkpoint()
    result = diagnose(URL, QUESTION, 1200, live_mode="compact", live_path=directory / "live.log",
                      raw_path=directory / "raw.sse", live_prefix=f"[{name}] ")
    (directory / "report.md").write_text(result.answer, encoding="utf-8")
    save(directory / "events.json", result.events)
    save(directory / "metrics.json", result.metrics)
    row.update(status="completed", run_id=result.run_id, elapsed_seconds=result.elapsed_seconds)
    checkpoint()
    score, records = evidence_archive_from_kubectl(result.run_id, namespace="aiops",
        target="deployment/aiops-copilot", container="aiops-copilot",
        archive_root="/tmp/aiops/reports/context_archives")
    save(directory / "evidence.archive.json", {"plan_audit": asdict(score), "records": records})
    snapshot(directory, "after.json", CREATED)
    print(f"RUN COMPLETED {name} {result.run_id} {result.elapsed_seconds:.1f}s", flush=True)


if __name__ == "__main__":
    checkpoint()
    try:
        run("01-pending-two-causes", ["c01-cpu", "c01-memory"])
        run("02-pending-and-mount-four-causes", ["c03-secret", "c03-key"])
        STATE["status"] = "completed"
    except BaseException as exc:
        STATE.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        STATE["cleanup_errors"] = []
        for member in reversed(CREATED):
            try:
                clean(CASES[member])
            except Exception as exc:
                STATE["cleanup_errors"].append({"case": member, "error": str(exc)})
        STATE["finished_at"] = datetime.now().isoformat()
        checkpoint()
