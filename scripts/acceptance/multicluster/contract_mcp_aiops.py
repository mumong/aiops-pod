#!/usr/bin/env python3
"""Seam check: real MCP outputs must pass the AIOps observation contract.

Run e43e8298: MCP 8.0.4 returned ``query_succeeded`` + ``coverage=partial`` for
VictoriaLogs events. Its own unit test asserted exactly those fields, and AIOps
rejected every one as ``invalid_success_contract``; lanes re-issued the call
until the repeat limit. Each repo was green on its own.

This runs the tools inside the center's MCP Pod (real runtime path, every
cluster) and feeds each output through the AIOps ``ObservationProcessor`` of
this checkout. Any parse/contract failure fails the case.

    contract_mcp_aiops.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))  # robusta root: the AIOps processor under test

import mc_common as mc  # noqa: E402
from tools_direct import run_tools  # noqa: E402

REJECTED = ("parse_failed", "invalid_tool", "extract_failed")


def pods(cluster: str) -> tuple[tuple[str, str], tuple[str, str]]:
    """One Pod with recent Warning events and one without, on this cluster."""
    items = mc.kubectl_json(cluster, "get", "pods", "-A")["items"]

    def ready(p):
        return all(c.get("ready") for c in p.get("status", {}).get("containerStatuses") or [{}])

    unready = [p for p in items if not ready(p)]
    healthy = [p for p in items if ready(p) and p["metadata"]["namespace"] != "kube-system"]
    pick = unready[0] if unready else items[0]
    calm = healthy[0] if healthy else items[-1]
    return (
        (pick["metadata"]["namespace"], pick["metadata"]["name"]),
        (calm["metadata"]["namespace"], calm["metadata"]["name"]),
    )


def cases() -> list:
    out = []
    for label, kubeconfig in (
        ("center", "center"),
        ("edge-88", "edge-88"),
        ("edge-89", "edge-89"),
    ):
        (ns, pod), (calm_ns, calm) = pods(kubeconfig)
        base = {"cluster": label, "namespace": ns, "pod": pod, "purpose": "contract check"}
        out += [
            (f"{label}-logs-events", "obs", "query_pod_logs", {**base, "window_minutes": 120}),
            (
                f"{label}-logs-quiet",
                "obs",
                "query_pod_logs",
                {**base, "namespace": calm_ns, "pod": calm, "window_minutes": 5},
            ),
            (
                f"{label}-promql",
                "obs",
                "execute_pod_promql",
                {
                    **base,
                    "promql": f'kube_pod_status_ready{{namespace="{ns}",pod="{pod}"}}',
                    "query_type": "instant",
                },
            ),
            (f"{label}-tracing", "obs", "query_pod_tracing", base),
            (f"{label}-topology", "obs", "query_pod_topology", base),
            (
                f"{label}-lifecycle",
                "k8s",
                "query_pod_lifecycle",
                {"cluster": label, "namespace": ns},
            ),
        ]
    return out


def main() -> None:
    from app.core.context.observation import ObservationProcessor

    plan = cases()
    results = run_tools(plan)
    tools = {key: name for key, _, name, _ in plan}
    with tempfile.TemporaryDirectory(prefix="mc-contract-") as root:
        processor = ObservationProcessor(archive_root=root)
        for index, (key, name) in enumerate(tools.items(), 1):
            if key not in results:
                mc.check(f"C-{key}", False, f"no output: {str(results)[:200]}")
                continue
            raw = results[key]
            raw = (
                raw if isinstance(raw, str) else __import__("json").dumps(raw, ensure_ascii=False)
            )
            seen = processor.process("mc-contract", "evidence", index, name, raw)
            structured = seen.get("structured") or {}
            verdict = f"{seen.get('processor')} {structured.get('status', '')}"
            mc.check(
                f"C-{key}",
                not any(word in verdict for word in REJECTED),
                f"{verdict} {structured.get('contract_errors') or ''}".strip()[:200],
            )
    mc.finish()


if __name__ == "__main__":
    main()
