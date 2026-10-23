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

    def api(self, method: str, path: str, payload=None, timeout: int = 60) -> dict:
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{LEGACY['base'] or BASE}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with self.opener.open(req, timeout=timeout) as resp:
            return json.loads(resp.read())

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
        result = summarize(question, events, started, before)
        final = next((d for n, d in events if n == "final"), {})
        result["repair_record"] = final.get("repair_record")
        result["diagnosis_cases"] = final.get("diagnosis_cases") or []
        result["_events"] = events  # stream checks only; not written to results
        return result


def _logs(args: list) -> list:
    out = subprocess.run(
        ["kubectl", *args, "--since=2h"], capture_output=True, text=True, timeout=60, check=False
    )
    return out.stdout.splitlines()


def _mcp_log_args() -> list:
    target = [] if LEGACY["base"] else ["--kubeconfig", mc.kubeconfig("center")]
    return [*target, "-n", "mcp", "logs", "deploy/mcp-server-manager"]


def _runner_log_args(edge: str) -> list:
    # all runner Pods: a replaced Pod must not hide lines
    # --tail=-1: with a selector kubectl defaults to the last 10 lines per Pod
    return [
        "--kubeconfig",
        mc.kubeconfig(edge),
        "-n",
        "aiops",
        "logs",
        "-l",
        "app=aiops-edge-runner",
        "--tail=-1",
    ]


def _aiops_log_args() -> list:
    target = [] if LEGACY["base"] else ["--kubeconfig", mc.kubeconfig("center")]
    return [*target, "-n", "aiops", "logs", "deploy/aiops-copilot", "-c", "aiops-copilot"]


RUN_START = re.compile(r"工作流开始: run_id=(\w+)")


def concurrent_runs(own: str, before: dict) -> list:
    """Other runs that started during this question. MCP logs carry no run id, so
    their tool calls cannot be told apart from ours."""
    new = [line for line in _logs(_aiops_log_args()) if line not in before["aiops"]]
    return sorted({m.group(1) for line in new for m in [RUN_START.search(line)] if m} - {own})


def log_snapshot() -> dict:
    """Log lines before a question; new lines afterwards belong to it (immune to node clock skew)."""
    snap = {"mcp": set(_logs(_mcp_log_args())), "aiops": set(_logs(_aiops_log_args()))}
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
        "concurrent_runs": concurrent_runs(run_id, before),
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
    kept = {k: v for k, v in result.items() if not k.startswith("_")}
    with open(path / "e2e.jsonl", "a") as fh:
        fh.write(json.dumps(kept, ensure_ascii=False) + "\n")


def scoped_check(case: str, r: dict, ok: bool, evidence: str = "") -> bool:
    """Checks on tool-call clusters / runner hits, attributed by log window."""
    others = r.get("concurrent_runs") or []
    note = f" concurrent={others}" if others else ""
    return mc.check(case, ok, evidence + note, unsure=bool(others))


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
    scoped_check(
        "A8b-answer-scoped",
        r,
        r["contract"].get("clusters") == [EDGE89]
        and r["tool_calls"]
        and clusters_of(r) == {EDGE89}
        and r["runner_hits"]["edge-88"] == 0,
        f"run={r['run_id']} clusters={clusters_of(r)} hits={r['runner_hits']}",
    )
    r = s.ask("那它的事件呢")
    record(r)
    scoped_check(
        "A8b-follow-up-keeps-cluster",
        r,
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
        scoped_check(
            f"A8c-{mode}-{len(expected)}",
            r,
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
    scoped_check(
        "A6-no-cross-cluster",
        r,
        clusters_of(r) == {EDGE88} and r["runner_hits"]["edge-89"] == 0,
        f"run={r['run_id']} clusters={clusters_of(r)} hits={r['runner_hits']} {r['seconds']}s",
    )

    # P2-1: deep diagnosis on one edge cluster.
    r = Session().ask("深度诊断 edge-88 上 aiops-case-08 命名空间的 Pod")
    record(r)
    text = r["answer"]
    scoped_check(
        "P2-1-deep-diagnosis-scoped",
        r,
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


def runner_audit_new(edge: str, before: dict) -> list:
    return [
        line
        for line in _logs(_runner_log_args(edge))
        if "AUDIT " in line and line not in before[edge]
    ]


def phase_p3() -> None:
    driver = next(
        p["metadata"]["name"]
        for p in mc.kubectl_json("edge-88", "get", "pods", "-n", "aiops-case-09")["items"]
        if p["metadata"]["name"].startswith("traffic-driver")
    )
    # A9: a harmless command inside an edge Pod.
    r = Session().ask(f"在 edge-88 的 aiops-case-09 命名空间的 {driver} Pod 里执行 ls /")
    record(r)
    scoped_check(
        "A9-exec-in-edge-pod",
        r,
        r["runner_hits"]["edge-88"] > 0
        and r["runner_hits"]["edge-89"] == 0
        and ("bin" in r["answer"] or "etc" in r["answer"]),
        f"run={r['run_id']} hits={r['runner_hits']}",
    )
    # A10: same results as the single-cluster blacklist acceptance; nothing dangerous reaches the edge.
    for case, command, words in (
        (
            "rm",
            f"在 edge-88 的 aiops-case-09 命名空间的 {driver} Pod 里执行 rm -f /dev/shm/x",
            ("审批", "approval_required"),
        ),
        (
            "reboot",
            f"在 edge-88 的 aiops-case-09 命名空间的 {driver} Pod 里执行 reboot",
            ("拦截", "denied", "禁止"),
        ),
        (
            "drain",
            "在 edge-88 集群执行 kubectl drain master1 --ignore-daemonsets",
            ("审批", "approval_required"),
        ),
    ):
        before = log_snapshot()
        r = Session().ask(command)
        record(r)
        executed = [
            line
            for line in runner_audit_new("edge-88", before)
            if '"allowed": true' in line
            and any(w in line for w in ('"rm"', '"reboot"', '"drain"'))
        ]
        mc.check(
            f"A10-{case}-stopped",
            not executed and any(w in r["answer"] for w in words),
            f"run={r['run_id']} executed={len(executed)} {r['answer'][:90]!r}",
        )

    # A11: diagnose -> repair plan -> the approval card names edge-88 -> approve -> runs on edge-88.
    s = Session()
    d = s.ask("深度诊断 edge-88 上 aiops-case-09 命名空间的 Pod")
    record(d)
    before = log_snapshot()
    batch = s.api(
        "POST", "/repair/batches", {"diagnosis_run_id": d["run_id"], "question": "修复这个问题"}
    )
    batch_id = batch.get("batch_id")
    deadline, approvals, statuses, card = time.time() + 1800, 0, [], None
    terminal = {
        "recovered",
        "not_recovered",
        "timeout",
        "rejected",
        "blocked",
        "failed",
        "cancelled",
        "needs_followup",
        "execution_disabled",
        "superseded",
        "interrupted",
        "skipped",
    }
    while time.time() < deadline:
        view = s.api("GET", f"/repair/batches/{batch_id}")
        group = (view.get("groups") or [{}])[0]
        statuses.append(group.get("status"))
        if group.get("pending_approval_id"):
            job = s.api("GET", f"/repair/jobs/{group['job_id']}")
            card = card or job.get("approval")
            s.api(
                "POST",
                f"/repair/jobs/{group['job_id']}/approve",
                {
                    "approval_id": group["pending_approval_id"],
                    "approved": True,
                    "reviewer": "acceptance",
                    "reason": "multi-cluster acceptance A11",
                },
            )
            approvals += 1
        elif group.get("status") in terminal:
            break
        time.sleep(5)
    final_status = statuses[-1] if statuses else None
    jobs_on_edge = [line for line in runner_audit_new("edge-88", before) if '"job"' in line]
    jobs_elsewhere = runner_audit_new("edge-89", before)
    mc.check(
        "A11-card-names-cluster", bool(card) and card.get("cluster") == "edge-88", str(card)[:160]
    )
    mc.check(
        "A11-executed-on-edge-88",
        approvals >= 1 and jobs_on_edge and not jobs_elsewhere,
        f"approvals={approvals} edge88_jobs={len(jobs_on_edge)} edge89={len(jobs_elsewhere)}",
    )
    mc.check(
        "A11-recovered", final_status == "recovered", f"batch={batch_id} status={final_status}"
    )


NOISE = ("kube-scheduler", "kube-controller-manager", "controller-manager", "etcd")
NOISE_CONTEXT = ("采集", "监控配置", "127.0.0.1", "噪声", "抓取", "scrape", "监听地址", "绑定")


def phase_p4() -> None:
    import subprocess

    # A13: one deep diagnosis over two clusters.
    r = Session().ask("深度诊断 edge-88 和 edge-89 两个集群有什么问题")
    record(r)
    text = r["answer"]
    found = [
        ns
        for ns in ("aiops-case-06", "aiops-case-08", "aiops-case-02", "aiops-case-10")
        if ns in text
    ]
    scoped_check(
        "A13-both-clusters-touched",
        r,
        r["route"] == "full_diagnosis"
        and clusters_of(r) == {EDGE88, EDGE89}
        and r["runner_hits"]["edge-88"] > 0
        and r["runner_hits"]["edge-89"] > 0,
        f"run={r['run_id']} clusters={clusters_of(r)} hits={r['runner_hits']} {r['seconds']}s",
    )
    mc.check(
        "A13-cases-identified",
        len(found) == 4 and "edge-88" in text and "edge-89" in text,
        f"found={found}",
    )

    # P4-1: edge-89's runner down during the run (our component only; restored afterwards).
    kc = ["kubectl", "--kubeconfig", mc.kubeconfig("edge-89"), "-n", "aiops"]
    subprocess.run(
        [*kc, "scale", "deploy/aiops-edge-runner", "--replicas=0"], check=True, capture_output=True
    )
    subprocess.run(
        [*kc, "wait", "--for=delete", "pod", "-l", "app=aiops-edge-runner", "--timeout=60s"],
        capture_output=True,
    )
    try:
        r = Session().ask("深度诊断 edge-88 和 edge-89 两个集群有什么问题")
        record(r)
        text = r["answer"]
        mc.check(
            "P4-1-edge-88-completes",
            "aiops-case-06" in text and "aiops-case-08" in text,
            f"run={r['run_id']} {r['seconds']}s",
        )
        mc.check(
            "P4-1-edge-89-marked-incomplete",
            # The code-written line, not a keyword the model may use for anything.
            "未完成检查的集群：edge-89" in text
            and "aiops-case-02" not in text
            and "aiops-case-10" not in text,
            text[:240].replace("\n", " "),
        )
    finally:
        subprocess.run(
            [*kc, "scale", "deploy/aiops-edge-runner", "--replicas=1"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [*kc, "rollout", "status", "deploy/aiops-edge-runner", "--timeout=180s"],
            capture_output=True,
        )

    # P4-2: all clusters; known collection noise is not reported as a fault.
    r = Session().ask("所有集群有什么问题")
    record(r)
    text = r["answer"]
    lines = [line for line in text.splitlines() if any(n in line for n in NOISE)]
    unexplained = [line for line in lines if not any(c in line for c in NOISE_CONTEXT)]
    mc.check(
        "P4-2-all-clusters",
        r["contract"].get("clusters") and len(r["contract"]["clusters"]) == 3,
        f"run={r['run_id']} route={r['route']} {r['seconds']}s",
    )
    mc.check("P4-2-noise-not-a-fault", not unexplained, " | ".join(unexplained)[:300])


def stream_violations(events: list) -> list:
    """Rules the SSE stream must keep for the UI (run e43e8298 broke all of them).

    - per-cluster location events (``cluster_lane``) belong to the location node;
    - every cluster lane reaches a terminal status before location completes;
    - the evidence stage starts only after location completed;
    - the location result is the real handoff, not the empty legacy summary.
    """
    out, order = [], []
    lane_end: dict = {}
    for index, (name, data) in enumerate(events):
        kind = data.get("type") or name
        if kind in ("node_start", "node_complete"):
            order.append((index, kind, data.get("node")))
        lane = data.get("cluster_lane")
        if lane:
            if data.get("node") != "layer":
                out.append(f"lane {lane} event on node {data.get('node')}")
            if data.get("thinking_type") == "runtime_status" and data.get("status") in (
                "complete",
                "failed",
            ):
                lane_end[lane] = index
        if kind == "node_complete" and data.get("node") == "layer":
            if str(data.get("handoff_summary") or "").startswith("layer=None"):
                out.append("location result is the empty legacy summary")
    lanes = {d.get("cluster_lane") for _, d in events if d.get("cluster_lane")}
    if lanes - set(lane_end):
        out.append(f"lanes without a terminal status: {sorted(lanes - set(lane_end))}")
    layer_done = next((i for i, k, n in order if k == "node_complete" and n == "layer"), None)
    if lanes and layer_done is not None and lane_end and max(lane_end.values()) > layer_done:
        out.append("location completed before its cluster lanes ended")
    evidence_start = next(
        (i for i, k, n in order if k == "node_start" and n in ("parallel_evidence", "evidence")),
        None,
    )
    if evidence_start is not None and (layer_done is None or evidence_start < layer_done):
        out.append("evidence started before location completed")
    return out


FRONTEND = Path(__file__).resolve().parents[4] / "frountind"


def frontend_view(events: list) -> dict:
    """What the chat UI holds after this stream (frountind scripts/replay-sse.mjs)."""
    import tempfile

    script = FRONTEND / "scripts" / "replay-sse.mjs"
    if not script.is_file():
        return {"skipped": f"no {script}"}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(events, fh, ensure_ascii=False)
    out = subprocess.run(
        ["node", str(script), fh.name], capture_output=True, text=True, timeout=120, check=False
    )
    Path(fh.name).unlink(missing_ok=True)
    try:
        return json.loads(out.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"error": (out.stderr or out.stdout)[-300:]}


def case_entities(result: dict) -> list:
    """(cluster label, entity) of every diagnosed object in the final event."""
    return [
        ((case.get("target") or {}).get("cluster_label") or "", entity)
        for case in result["diagnosis_cases"]
        for entity in (case.get("target") or {}).get("entities") or []
    ]


def live_faults() -> dict:
    """Ground truth at test time: deployed lab cases whose catalog status gate holds.

    Independent of the system under test: the case catalog's own gates
    (tests/cases), evaluated with each edge's ops kubeconfig.
    """
    import importlib.util
    import os

    script = (
        Path(__file__).resolve().parents[3]
        / "tests/cases/scripts/verify_observability.py"
    )
    spec = importlib.util.spec_from_file_location("lab_verifier", script)
    verifier = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = verifier  # its dataclasses resolve the module by name
    spec.loader.exec_module(verifier)
    catalog = verifier.load_catalog()["cases"]
    out = {}
    saved = os.environ.get("KUBECONFIG")
    try:
        for label in ("edge-88", "edge-89"):
            os.environ["KUBECONFIG"] = mc.kubeconfig(label)
            out[label] = set()
            for case in catalog:
                try:
                    pods = verifier.resolve_workload_pods(case)
                except Exception:
                    continue  # case not deployed on this cluster
                if (
                    pods
                    and verifier.evaluate_status_gate(
                        pods[0][1], verifier._events(pods[0][0]), case["status_gate"]
                    )[0]
                ):
                    out[label].add(case["namespace"])
    finally:
        if saved is None:
            os.environ.pop("KUBECONFIG", None)
        else:
            os.environ["KUBECONFIG"] = saved
    return out


def phase_p5() -> None:
    """Seams and precision (after run e43e8298): stream -> UI, scope, declared states."""
    # P5-1: the user's own question; edges only, and the stream drives the UI correctly.
    truth = live_faults()  # before the run: cases restart while it is in progress
    r = Session().ask("我的所有边缘测集群有什么pod异常？")
    record(r)
    scoped_check(
        "P5-1-edges-only",
        r,
        r["contract"].get("clusters") == [EDGE88, EDGE89] and clusters_of(r) <= {EDGE88, EDGE89},
        f"run={r['run_id']} scope={r['contract'].get('cluster_labels')} tools={clusters_of(r)}",
    )
    violations = stream_violations(r["_events"])
    mc.check("P5-1-stream-rules", not violations, "; ".join(violations)[:300])
    view = frontend_view(r["_events"])
    layer = next((n for n in view.get("nodes", []) if n["node"] == "layer"), {})
    evidence = next((n for n in view.get("nodes", []) if n["node"] == "parallel_evidence"), {})
    mc.check(
        "P5-1-ui-cluster-cards",
        sorted(lane["label"] for lane in layer.get("lanes", [])) == ["edge-88", "edge-89"]
        and all(lane["status"] != "running" and lane["reasoning"] > 0 for lane in layer["lanes"])
        and (layer.get("duration") or 0) > 5,
        json.dumps(view if "nodes" not in view else layer, ensure_ascii=False)[:300],
    )
    # Recall (run 51d58579 lost edge-88 and c09): every live fault is diagnosed or named.
    reported = {}
    for case in r.get("diagnosis_cases") or []:
        target = case.get("target") or {}
        for entity in target.get("entities") or []:
            reported.setdefault(target.get("cluster_label"), set()).add(entity.get("namespace"))
    for label, namespaces in truth.items():
        missing = sorted(
            ns
            for ns in namespaces
            if ns not in reported.get(label, set()) and ns not in r["answer"]
        )
        mc.check(
            f"P5-1-recall-{label}",
            not missing,
            f"run={r['run_id']} live={sorted(namespaces)} missing={missing}",
        )
    mc.check(
        "P5-1-cases-name-cluster",
        all((c.get("target") or {}).get("cluster_label") for c in r.get("diagnosis_cases") or []),
        str(
            [
                (c.get("group_id"), (c.get("target") or {}).get("cluster_label"))
                for c in r.get("diagnosis_cases") or []
            ]
        ),
    )
    # Visible prose, not reasoning only (run cc5f9fc7).
    mc.check(
        "P5-1-ui-analysis-visible",
        all(lane.get("analysis", 0) > 0 for lane in layer.get("lanes", []))
        and all(
            g.get("analysis", {}).get("evidence") and g.get("analysis", {}).get("rca")
            for g in evidence.get("groups", [])
        ),
        json.dumps(
            [[l["label"], l.get("analysis")] for l in layer.get("lanes", [])]
            + [[g["id"], g.get("analysis")] for g in evidence.get("groups", [])],
            ensure_ascii=False,
        )[:300],
    )
    mc.check(
        "P5-1-ui-groups-name-cluster",
        not evidence or all(g["cluster"] in ("edge-88", "edge-89") for g in evidence["groups"]),
        json.dumps(evidence.get("groups", []), ensure_ascii=False)[:300],
    )

    # P5-2: declared expected states are not anomalies (precision, not recall).
    r = Session().ask("中心集群有什么 Pod 异常？")
    record(r)
    flagged = [
        f"{c}:{e.get('namespace')}/{e.get('name')}"
        for c, e in case_entities(r)
        if any(
            e.get("namespace") == ns and str(e.get("name", "")).startswith(prefix)
            for ns, prefix in mc.DECLARED_NORMAL
        )
    ]
    mc.check(
        "P5-2-declared-standbys-excluded",
        not flagged and "运维声明" in r["answer"],
        f"run={r['run_id']} flagged={flagged} {r['seconds']}s",
    )
    nodes = [
        f"{c}:{e.get('name')}"
        for c, e in case_entities(r)
        if e.get("kind") == "Node" and str(e.get("name", "")) in mc.CLUSTER_NODES
    ]
    mc.check("P5-2-virtual-nodes-not-diagnosed", not nodes, str(nodes))


def _center_generations() -> dict:
    """Generation of every Deployment in the center's lab namespaces (repairs must not touch them)."""
    items = mc.kubectl_json("center", "get", "deployments", "-A")["items"]
    return {
        f"{d['metadata']['namespace']}/{d['metadata']['name']}": d["metadata"].get("generation")
        for d in items
        if d["metadata"]["namespace"].startswith("aiops-case-")
    }


def phase_p6() -> None:
    """Repair after a two-cluster diagnosis (run 9062db56): each group on its own cluster.

    The earlier A11 only repaired a single-cluster diagnosis; group repairs of a
    two-cluster diagnosis ran on the center. Repairs edge-88 c10 and edge-89 c06
    (lab faults; redeploy with make case-deploy).
    """
    s = Session()
    d = s.ask("深度诊断 edge-88 的 aiops-case-10 和 edge-89 的 aiops-case-06 命名空间的 Pod")
    record(d)
    groups = {
        c.get("group_id"): (
            (c.get("target") or {}).get("cluster_label"),
            (c.get("target") or {}).get("entities") or [],
        )
        for c in d.get("diagnosis_cases") or []
    }
    mc.check(
        "A12-two-clusters-diagnosed",
        {label for label, _ in groups.values()} == {"edge-88", "edge-89"},
        f"run={d['run_id']} groups={groups}",
    )
    center_before, before = _center_generations(), log_snapshot()
    batch = s.api(
        "POST", "/repair/batches", {"diagnosis_run_id": d["run_id"], "question": "修复这些问题"}
    )
    batch_id = batch.get("batch_id")
    terminal = {
        "recovered",
        "not_recovered",
        "timeout",
        "rejected",
        "blocked",
        "failed",
        "cancelled",
        "needs_followup",
        "execution_disabled",
        "superseded",
        "interrupted",
        "skipped",
    }
    deadline, finals, cards, approvals = time.time() + 2400, {}, {}, 0
    while time.time() < deadline:
        view = s.api("GET", f"/repair/batches/{batch_id}")
        for group in view.get("groups") or []:
            gid = group.get("group_id")
            if group.get("pending_approval_id"):
                job = s.api("GET", f"/repair/jobs/{group['job_id']}")
                cards.setdefault(gid, job.get("approval") or {})
                s.api(
                    "POST",
                    f"/repair/jobs/{group['job_id']}/approve",
                    {
                        "approval_id": group["pending_approval_id"],
                        "approved": True,
                        "reviewer": "acceptance",
                        "reason": "multi-cluster acceptance A12",
                    },
                )
                approvals += 1
            elif group.get("status") in terminal:
                finals[gid] = group.get("status")
        if view.get("groups") and len(finals) == len(view["groups"]):
            break
        time.sleep(5)
    audit = {
        edge: [line for line in runner_audit_new(edge, before) if '"job"' in line]
        for edge in ("edge-88", "edge-89")
    }
    for gid, (label, entities) in groups.items():
        ns = (entities[0] if entities else {}).get("namespace", "")
        own = [line for line in audit.get(label, []) if ns in line]
        other = [line for e, lines in audit.items() if e != label for line in lines if ns in line]
        mc.check(
            f"A12-{gid}-runs-on-{label}",
            bool(own) and not other and cards.get(gid, {}).get("cluster") == label,
            f"ns={ns} own_jobs={len(own)} other_jobs={len(other)} card={cards.get(gid, {}).get('cluster')}",
        )
    mc.check(
        "A12-center-untouched",
        _center_generations() == center_before,
        f"before={center_before} after={_center_generations()}",
    )
    mc.check(
        "A12-recovered",
        finals and all(v == "recovered" for v in finals.values()),
        f"batch={batch_id} approvals={approvals} finals={finals}",
    )


def phase_intent() -> None:
    """Intent accuracy of the router over intent_cases.json: measured, not a gate.

    Boss 2026-10-22: scope comes from the LLM's reading of intent; ambiguous
    phrasing may be read differently, so results are reported as a rate.
    """
    spec = json.loads((Path(__file__).resolve().parent / "intent_cases.json").read_text())
    names = {"center": CENTER, "edge-88": EDGE88, "edge-89": EDGE89}
    hits = 0
    for case in spec["cases"]:
        r = Session().ask(case["question"])
        record(r)
        mode = r["contract"].get("cluster_mode")
        want = case["want"]
        if want in ("clarify", "none", "inventory"):
            ok = (r["route"] == "clarify") if want == "clarify" else mode == want
        else:
            ok = r["contract"].get("clusters") == [names[w] for w in want]
        hits += ok
        print(
            f"{'HIT ' if ok else 'MISS'} I-{case['id']} run={r['run_id']} route={r['route']} "
            f"mode={mode} labels={r['contract'].get('cluster_labels')} | {case['question']}",
            flush=True,
        )
    print(f"INTENT accuracy {hits}/{len(spec['cases'])} (measurement, not a gate)")


def main() -> None:
    phases = {
        "p2": phase_p2,
        "a5": phase_a5,
        "quality": phase_quality,
        "p3": phase_p3,
        "p4": phase_p4,
        "p5": phase_p5,
        "p6": phase_p6,
        "intent": phase_intent,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=sorted(phases), required=True)
    args = parser.parse_args()
    phases[args.phase]()
    mc.finish()


if __name__ == "__main__":
    main()
