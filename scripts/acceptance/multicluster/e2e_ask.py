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
LEGACY = {"base": None}  # --phase a5: the existing single-cluster env (default kubeconfig)
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
        before = log_snapshot()
        data = urllib.parse.urlencode(
            {"q": question, "session_id": self.id, "stream": "true", "format": "sse"}
        ).encode()
        req = urllib.request.Request(f"{LEGACY['base'] or BASE}/ask", data=data, method="POST")
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
        return summarize(question, events, started, before)


def _logs(args: list) -> list:
    out = subprocess.run(
        ["kubectl", *args, "--since=2h"], capture_output=True, text=True, timeout=60, check=False
    )
    return out.stdout.splitlines()


def _mcp_log_args() -> list:
    target = [] if LEGACY["base"] else ["--kubeconfig", mc.kubeconfig("center")]
    return [*target, "-n", "mcp", "logs", "deploy/mcp-server-manager"]


def _runner_log_args(edge: str) -> list:
    return ["--kubeconfig", mc.kubeconfig(edge), "-n", "aiops", "logs", "deploy/aiops-edge-runner"]


def log_snapshot() -> dict:
    """Log lines before a question; new lines afterwards belong to it (immune to node clock skew)."""
    snap = {"mcp": set(_logs(_mcp_log_args()))}
    if not LEGACY["base"]:
        for edge in ("edge-88", "edge-89"):
            snap[edge] = set(_logs(_runner_log_args(edge)))
    return snap


def summarize(question: str, events: list, started: float, before: dict) -> dict:
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
    calls = mcp_calls(before)
    return {
        "question": question,
        "run_id": run_id,
        "route": route,
        "contract": contract or {},
        "answer": answer,
        "tool_calls": calls,
        "runner_hits": {e: runner_hits(e, before) for e in ("edge-88", "edge-89")},
        "seconds": round(time.time() - started),
    }


def mcp_calls(before: dict) -> list:
    new = [line for line in _logs(_mcp_log_args()) if line not in before["mcp"]]
    calls = []
    for match in TOOL_CALL.finditer("\n".join(new)):
        try:
            args = json.loads(match.group(2))
        except json.JSONDecodeError:
            args = {"_raw": match.group(2)[:200]}
        calls.append({"tool": match.group(1), "cluster": args.get("cluster"), "args": args})
    return calls


def runner_hits(edge: str, before: dict) -> int:
    if LEGACY["base"]:
        return 0
    return sum(
        "AUDIT " in line for line in _logs(_runner_log_args(edge)) if line not in before[edge]
    )


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


def phase_a5() -> None:
    """A5 + P2-2 on the existing single-cluster env: behaviour unchanged."""
    LEGACY["base"] = "http://10.2.0.48:30800"
    r = Session().ask("有哪些 Pod 异常")
    record(r)
    mc.check(
        "P2-2-no-cluster-question",
        r["route"] in ("focused", "full_diagnosis")
        and "cluster_mode" not in r["contract"]
        and r["tool_calls"],
        f"run={r['run_id']} route={r['route']} calls={len(r['tool_calls'])} {r['seconds']}s",
    )
    mc.check(
        "A5-no-cluster-argument",
        all(c["cluster"] is None for c in r["tool_calls"]),
        str({c["tool"] for c in r["tool_calls"] if c["cluster"]}),
    )
    r = Session().ask("深度诊断 aiops-case-06 命名空间的 Pod 为什么异常")
    record(r)
    text = r["answer"]
    mc.check(
        "A5-deep-diagnosis-c06",
        r["route"] == "full_diagnosis" and ("CrashLoop" in text or "退出" in text),
        f"run={r['run_id']} {r['seconds']}s {text[:140]!r}",
    )
    mc.check("A5-no-cluster-argument-deep", all(c["cluster"] is None for c in r["tool_calls"]))


QUALITY_CASES = {
    # case: (namespace, correct-cause test on the answer)
    "c06": (
        "aiops-case-06",
        lambda t: ("APP_CONF" in t or "环境变量" in t)
        and ("CONFIG" in t or "拼写" in t or "名称" in t),
    ),
    "c09": ("aiops-case-09", lambda t: "8081" in t or ("端口" in t and "8080" in t)),
}
FABRICATION = re.compile(r"(链路|trace|Tempo|DeepFlow|Elasticsearch|span)", re.I)


def phase_quality(rounds: int = 3) -> None:
    """T047 / acceptance §5: same cases, new env (13.x + victoria) vs existing env (12.0.69 + legacy)."""
    rows = []
    for env, base, prefix in (
        ("new", None, "edge-88 上 "),
        ("legacy", "http://10.2.0.48:30800", ""),
    ):
        LEGACY["base"] = base
        for case, (namespace, correct) in QUALITY_CASES.items():
            for i in range(rounds):
                r = Session().ask(f"深度诊断 {prefix}{namespace} 命名空间的 Pod 为什么异常")
                r.update(env=env, case=case, round=i + 1)
                record(r)
                text = r["answer"]
                rows.append(
                    {
                        "env": env,
                        "case": case,
                        "round": i + 1,
                        "run": r["run_id"],
                        "seconds": r["seconds"],
                        "correct": bool(correct(text)),
                        "fabrication_flag": bool(env == "new" and FABRICATION.search(text)),
                        "tool_calls": len(r["tool_calls"]),
                    }
                )
                print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    LEGACY["base"] = None
    for env in ("new", "legacy"):
        for case in QUALITY_CASES:
            sel = [r for r in rows if r["env"] == env and r["case"] == case]
            print(
                f"SUMMARY {env} {case}: correct {sum(r['correct'] for r in sel)}/{len(sel)}, "
                f"avg {sum(r['seconds'] for r in sel) // max(1, len(sel))}s, "
                f"avg tools {sum(r['tool_calls'] for r in sel) // max(1, len(sel))}, "
                f"fabrication flags {sum(r['fabrication_flag'] for r in sel)}"
            )
    flags = [r for r in rows if r["fabrication_flag"]]
    mc.check("Q-no-fabrication-flags", not flags, f"review runs: {[r['run'] for r in flags]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["p2", "a5", "quality"], required=True)
    args = parser.parse_args()
    {"p2": phase_p2, "a5": phase_a5, "quality": phase_quality}[args.phase]()
    mc.finish()


if __name__ == "__main__":
    main()
