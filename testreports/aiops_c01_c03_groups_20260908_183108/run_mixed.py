"""Two cluster-wide requests with six concurrent c01/c03 root-cause fixtures."""
import hashlib
import importlib.util
import time
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / "aiops_c01_variants_20260908_173631/run_c01.py"
spec = importlib.util.spec_from_file_location("c01_experiment_protocol", SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.OUT = OUT
MEMBERS = ["c01-cpu", "c01-memory", "c01-pvc", "c03-secret", "c03-key", "c03-hostpath"]
runner.STATE["planned_requests"] = 2
runner.STATE["current_group"] = "01-mixed"


if __name__ == "__main__":
    runner.checkpoint()
    try:
        for member in MEMBERS:
            ns = runner.CASES[member]["namespace"]
            existing = runner.command(["kubectl", "get", "namespace", ns,
                "--ignore-not-found=true", "-o", "name"], capture=True, timeout=20)
            if existing.strip():
                raise RuntimeError(f"namespace already exists: {ns}")
        rb = runner.kubectl_json(["-n", "aiops", "get", "configmap", "aiops-runbooks"])["data"]
        runner.save(OUT / "runbook-snapshot.json", rb)
        runner.STATE["runbook_sha256"] = {
            k: hashlib.sha256(v.encode()).hexdigest() for k, v in rb.items()}
        nodes = runner.kubectl_json(["get", "nodes"])
        runner.save(OUT / "node-capacity.json", [{"name": n["metadata"]["name"],
            "capacity": n["status"].get("capacity"),
            "allocatable": n["status"].get("allocatable")} for n in nodes["items"]])
        deployment = runner.kubectl_json(["-n", "aiops", "get", "deployment", "aiops-copilot"])
        runner.STATE["images"] = {c["name"]: c["image"]
            for c in deployment["spec"]["template"]["spec"]["containers"]}
        for member in MEMBERS:
            runner.ACTIVE.append(member)
            runner.deploy(runner.CASES[member])
        for member in MEMBERS:
            if not runner.validate_variant(runner.CASES[member], 240):
                raise RuntimeError(f"fault not established: {member}")
        time.sleep(20)
        for index in (1, 2):
            runner.request("01-mixed", index)
        runner.cleanup()
        runner.STATE["status"] = "completed"
    except BaseException as exc:
        runner.STATE.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        try:
            if runner.ACTIVE:
                runner.cleanup()
        finally:
            runner.STATE["finished_at"] = datetime.now().isoformat()
            runner.checkpoint()
