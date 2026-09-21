"""Replay the c01 experiment protocol for three FailedMount variants.

Only fixture resources and this output directory are changed. Production and
scoring code remain fixed throughout the eight baseline requests.
"""
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
runner.GROUPS = [
    ("01-secret", ["c03-secret"]),
    ("02-key", ["c03-key"]),
    ("03-hostpath", ["c03-hostpath"]),
    ("04-combined", ["c03-secret", "c03-key", "c03-hostpath"]),
]


if __name__ == "__main__":
    runner.checkpoint()
    try:
        # Abort before deployment if any requested fixture namespace exists.
        for member in ("c03-secret", "c03-key", "c03-hostpath"):
            ns = runner.CASES[member]["namespace"]
            existing = runner.command(["kubectl", "get", "namespace", ns,
                "--ignore-not-found=true", "-o", "name"], capture=True, timeout=20)
            if existing.strip():
                raise RuntimeError(f"namespace already exists: {ns}")
        nodes = runner.kubectl_json(["get", "nodes"])
        runner.save(OUT / "node-capacity.json", [{"name": n["metadata"]["name"],
            "capacity": n["status"].get("capacity"),
            "allocatable": n["status"].get("allocatable")} for n in nodes["items"]])
        rb = runner.kubectl_json(["-n", "aiops", "get", "configmap", "aiops-runbooks"])["data"]
        runner.save(OUT / "runbook-snapshot.json", rb)
        runner.STATE["runbook_sha256"] = {
            k: hashlib.sha256(v.encode()).hexdigest() for k, v in rb.items()}
        for group, members in runner.GROUPS:
            runner.STATE["current_group"] = group
            runner.checkpoint()
            for member in members:
                runner.ACTIVE.append(member)
                runner.deploy(runner.CASES[member])
            for member in members:
                if not runner.validate_variant(runner.CASES[member], 240):
                    raise RuntimeError(f"fault not established: {member}")
            time.sleep(20)
            for index in (1, 2):
                runner.request(group, index)
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
