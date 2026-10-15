#!/usr/bin/env python3
"""Per-run agent stability metrics from context archives (stdlib only).

Compares models on the things that decide delivery: model rounds per node, tool
calls, repeated identical tool results, location handoff delivery and parallel
fan-out. Reads /tmp/aiops/reports/context_archives/<run_id>/ inside the pod:

    kubectl -n aiops exec -i <pod> -c aiops-copilot -- python - <run_id> [<run_id> ...] \\
        < scripts/run_quality_report.py

Pass --root <dir> to read archives copied elsewhere.
"""
import collections
import glob
import hashlib
import json
import os
import sys

DEFAULT_ROOT = "/tmp/aiops/reports/context_archives"


def _load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _node_tools(run_dir):
    """{node: [(tool, sha1(raw)), ...]} in call order."""
    calls = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(run_dir, "tools", "*.raw.txt"))):
        name = os.path.basename(path)[: -len(".raw.txt")]
        try:
            _, node, tool = name.split("-", 2)
        except ValueError:
            continue
        with open(path, "rb") as handle:
            calls[node].append((tool, hashlib.sha1(handle.read()).hexdigest()))
    return calls


def report(run_id, root):
    run_dir = os.path.join(root, run_id)
    if not os.path.isdir(run_dir):
        return {"run_id": run_id, "error": "archive not found"}
    nodes = {}
    for node, calls in _node_tools(run_dir).items():
        seen = collections.Counter(calls)
        nodes[node] = {
            "model_rounds": len(glob.glob(os.path.join(run_dir, "budget", f"{node}_agent_guard_*.json"))),
            "tool_calls": len(calls),
            "repeated_identical_results": sum(count - 1 for count in seen.values() if count > 1),
        }
    plan = (_load(os.path.join(run_dir, "parallel", "plan.json")) or {}).get("input", {})
    handoff = ((plan.get("protected_handoff") or {}).get("diagnosis_handoff")) or {}
    results = _load(os.path.join(run_dir, "parallel", "results.json"))
    items = results if isinstance(results, list) else ((results or {}).get("results") or [])
    router = _load(os.path.join(run_dir, "node_outputs", "request_router.output.json")) or {}
    route = (router.get("snapshot") or router.get("output") or router).get("request_route")
    return {
        "run_id": run_id,
        "route": route,
        "nodes": nodes,
        "location_targets": len(handoff.get("targets") or []),
        "location_coverage": handoff.get("coverage"),
        "location_note": (handoff.get("coverage_note") or "")[:80],
        "parallel_groups": [
            {"group_id": g.get("group_id"), "status": g.get("status")} for g in items if isinstance(g, dict)
        ],
    }


def main(argv):
    root = DEFAULT_ROOT
    if "--root" in argv:
        index = argv.index("--root")
        root = argv[index + 1]
        argv = argv[:index] + argv[index + 2:]
    if not argv:
        sys.exit(__doc__)
    for run_id in argv:
        print(json.dumps(report(run_id, root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
