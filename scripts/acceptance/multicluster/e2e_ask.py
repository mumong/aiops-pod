#!/usr/bin/env python3
"""L3 end-to-end acceptance through the center's /ask (spec SC-001).

Scope assertions do not trust what the model *said*: they use what the MCP
servers actually received (``[TOOL_CALL]`` lines, the arguments after AIOps
bound the cluster) and which edge runners logged requests during the run.

    e2e_ask.py --phase p2
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mc_common as mc  # noqa: E402

BASE = f"http://{mc.CENTER_HOST}:30800"
EDGE88 = "vc-942nkkozc8o5fyb9q3bznb1ws"
EDGE89 = "vc-dluw0jousipr6h5co2bwpyqk2"
CENTER = "vc-xnet-management"
TOOL_CALL = re.compile(r"\[TOOL_CALL\] (\S+) \| args=(\{.*\})")


class Session:
    def __init__(self) -> None:
        self.id = "mce2e" + uuid.uuid4().hex[:16]
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    def ask(self, question: str, timeout: int = 900) -> dict:
        started = time.time()
        data = urllib.parse.urlencode(
            {"q": question, "session_id": self.id, "stream": "true", "format": "sse"}
        ).encode()
        req = urllib.request.Request(f"{BASE}/ask", data=data, method="POST")
        events = []
        event = None
        with self.opener.open(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").rstrip("\n")
                if line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    try:
                        events.append((event, json.loads(line[5:])))
                    except json.JSONDecodeError:
                        pass
        return summarize(question, events, started)


def summarize(question: str, events: list, started: float) -> dict:
    contract, route, answer, run_id = None, None, "", ""
    for name, data in events:
        snap = data.get("state_snapshot") or {}
        if data.get("node") == "request_router" and snap.get("request_contract"):
            contract = snap["request_contract"]
            route = snap.get("request_route")
        if name == "final":
            answer = data.get("answer") or data.get("query_answer") or data.get("conclusion") or ""
            run_id = data.get("run_id") or run_id
        run_id = run_id or data.get("run_id") or ""
    calls = mcp_calls(started)
    return {
        "question": question,
        "run_id": run_id,
        "route": route,
        "contract": contract or {},
        "answer": answer,
        "tool_calls": calls,
        "runner_hits": {e: runner_hits(e, started) for e in ("edge-88", "edge-89")},
        "seconds": round(time.time() - started),
    }


def mcp_calls(since: float) -> list:
    seconds = int(time.time() - since) + 5
    out = subprocess.run(
        [
            "kubectl",
            "--kubeconfig",
            mc.kubeconfig("center"),
            "-n",
            "mcp",
            "logs",
            "deploy/mcp-server-manager",
            f"--since={seconds}s",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    ).stdout
    calls = []
    for match in TOOL_CALL.finditer(out):
        try:
            args = json.loads(match.group(2))
        except json.JSONDecodeError:
            args = {"_raw": match.group(2)[:200]}
        calls.append({"tool": match.group(1), "cluster": args.get("cluster"), "args": args})
    return calls


def runner_hits(edge: str, since: float) -> int:
    seconds = int(time.time() - since) + 5
    out = subprocess.run(
        [
            "kubectl",
            "--kubeconfig",
            mc.kubeconfig(edge),
            "-n",
            "aiops",
            "logs",
            "deploy/aiops-edge-runner",
            f"--since={seconds}s",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    ).stdout
    return out.count("AUDIT ")


def record(result: dict) -> None:
    path = Path(__file__).resolve().parent / "results"
    path.mkdir(exist_ok=True)
    with open(path / "e2e.jsonl", "a") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")


def clusters_of(result: dict) -> set:
    return {c["cluster"] for c in result["tool_calls"] if c["tool"] != "list_clusters"}


def phase_p2() -> None:
    # A8a / A8b: unscoped question is clarified; the answer and the follow-up stay on edge-89.
    s = Session()
    r = s.ask("有哪些 Pod 异常")
    record(r)
    mc.check(
        "A8a-clarify-without-tools",
        r["route"] == "clarify"
        and not r["tool_calls"]
        and "全部集群" in (r["contract"].get("clarification") or ""),
        f"run={r['run_id']}",
    )
    r = s.ask("edge-89")
    record(r)
    mc.check(
        "A8b-answer-scoped",
        r["contract"].get("clusters") == [EDGE89]
        and r["tool_calls"]
        and clusters_of(r) == {EDGE89}
        and r["runner_hits"]["edge-88"] == 0,
        f"run={r['run_id']} clusters={clusters_of(r)} hits={r['runner_hits']}",
    )
    r = s.ask("那它的事件呢")
    record(r)
    mc.check(
        "A8b-follow-up-keeps-cluster",
        r["route"] != "clarify"
        and r["contract"].get("clusters") == [EDGE89]
        and clusters_of(r) <= {EDGE89},
        f"run={r['run_id']} route={r['route']} clusters={clusters_of(r)}",
    )

    # A8c: the three scope kinds.
    for question, expected, mode in (
        ("中心集群的 vmagent 正常吗", [CENTER], "single"),
        ("edge-88 和 edge-89 各有几个 Pod", [EDGE88, EDGE89], "multiple"),
    ):
        r = Session().ask(question)
        record(r)
        mc.check(
            f"A8c-{mode}-{len(expected)}",
            r["contract"].get("clusters") == expected and clusters_of(r) <= set(expected),
            f"run={r['run_id']} got={r['contract'].get('clusters')}",
        )

    # A7: unknown cluster.
    r = Session().ask("edge-99 上有什么问题")
    record(r)
    mc.check(
        "A7-unknown-cluster",
        r["route"] == "clarify"
        and not r["tool_calls"]
        and "edge-99" in (r["contract"].get("clarification") or ""),
        f"run={r['run_id']}",
    )

    # A6: same namespace/name on the other cluster must not leak in.
    r = Session().ask("edge-88 上 aiops-case-06 命名空间的 Pod 为什么异常")
    record(r)
    mc.check(
        "A6-no-cross-cluster",
        clusters_of(r) == {EDGE88} and r["runner_hits"]["edge-89"] == 0,
        f"run={r['run_id']} clusters={clusters_of(r)} hits={r['runner_hits']} {r['seconds']}s",
    )

    # P2-1: deep diagnosis on one edge cluster.
    r = Session().ask("深度诊断 edge-88 上 aiops-case-08 命名空间的 Pod")
    record(r)
    text = r["answer"]
    mc.check(
        "P2-1-deep-diagnosis-scoped",
        r["route"] == "full_diagnosis"
        and clusters_of(r) == {EDGE88}
        and r["runner_hits"]["edge-89"] == 0,
        f"run={r['run_id']} route={r['route']} calls={len(r['tool_calls'])} {r['seconds']}s",
    )
    mc.check(
        "P2-1-oom-identified",
        "OOM" in text.upper() or "内存" in text,
        text[:160].replace("\n", " "),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["p2"], required=True)
    args = parser.parse_args()
    {"p2": phase_p2}[args.phase]()
    mc.finish()


if __name__ == "__main__":
    main()
