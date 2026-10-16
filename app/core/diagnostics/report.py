"""Run report: everything needed to understand one run, written next to its archive."""

from __future__ import annotations

import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional

from app.core.context.archive import get_archive_root
from app.core.diagnostics.findings import classify

logger = logging.getLogger(__name__)


def _load(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def load_ledgers(root: str, run_id: str) -> List[Dict[str, Any]]:
    paths = sorted(glob.glob(os.path.join(root, run_id, "ledger", "*.json")))
    for lane in sorted(glob.glob(os.path.join(root, f"{run_id}-g*"))):
        paths.extend(sorted(glob.glob(os.path.join(lane, "ledger", "*.json"))))
    return [ledger for ledger in (_load(p) for p in paths) if ledger]


def _lane_outcomes(root: str, run_id: str) -> List[Dict[str, Any]]:
    try:
        with open(os.path.join(root, run_id, "parallel", "results.json"), encoding="utf-8") as f:
            results = json.load(f)
    except (OSError, ValueError):
        results = []
    items = results.get("results") if isinstance(results, dict) else results
    out = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            case = item.get("case_result") or {}
            out.append(
                {
                    "group_id": item.get("group_id"),
                    "status": item.get("status"),
                    "outcome": case.get("outcome"),
                    "certainty": case.get("certainty"),
                    "summary": (case.get("summary") or "")[:160],
                }
            )
    return out


def build_run_report(
    run_id: str,
    *,
    root: Optional[str] = None,
    final_state: Optional[Dict[str, Any]] = None,
    node_durations_ms: Optional[Dict[str, float]] = None,
    elapsed_seconds: Optional[float] = None,
    outcome: Optional[str] = None,
) -> Dict[str, Any]:
    root = root or get_archive_root()
    ledgers = load_ledgers(root, run_id)
    state = final_state or {}
    router = _load(os.path.join(root, run_id, "node_outputs", "request_router.output.json")) or {}
    snap = router.get("snapshot") or {}
    contract = state.get("request_contract") or snap.get("request_contract") or {}
    handoff = state.get("diagnosis_handoff") or {}
    answer = state.get("query_answer") or {}
    report = {
        "contract_version": "run-report.v1",
        "run_id": run_id,
        "route": state.get("request_route") or snap.get("request_route"),
        "task": contract.get("task"),
        "scope": contract.get("scope"),
        "outcome": outcome,
        "elapsed_seconds": round(elapsed_seconds, 1) if elapsed_seconds is not None else None,
        "node_durations_s": {k: round(v / 1000, 1) for k, v in (node_durations_ms or {}).items()},
        "targets": [
            {
                "id": t.get("target_id"),
                "status": t.get("status"),
                "entity": f"{(t.get('entity') or {}).get('kind')}/{(t.get('entity') or {}).get('namespace')}/{(t.get('entity') or {}).get('name')}",
            }
            for t in handoff.get("targets") or []
        ],
        "coverage": handoff.get("coverage"),
        "lanes": _lane_outcomes(root, run_id),
        "answer": {"status": answer.get("status"), "missing": answer.get("missing")}
        if answer
        else None,
        "calls": [
            {
                "run_id": l["run_id"],
                "node": l["node"],
                "duration_s": round(l["duration_ms"] / 1000, 1),
                "model_s": round(l["model_ms"] / 1000, 1),
                "rounds": len(l["rounds"]),
                "tools": l["counts"],
                "tools_by_name": l["tools_by_name"],
                "incomplete_reason": l["incomplete_reason"],
            }
            for l in ledgers
        ],
        "findings": classify(ledgers),
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# Run {report['run_id']}",
        f"route={report.get('route')} task={report.get('task')} scope={report.get('scope')} outcome={report.get('outcome')} elapsed={report.get('elapsed_seconds')}s",
        "",
    ]
    if report.get("node_durations_s"):
        lines += ["## 节点耗时", "| 节点 | 秒 |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in report["node_durations_s"].items()]
        lines.append("")
    if report.get("targets"):
        lines += [
            "## 定位目标",
            *[f"- {t['entity']} [{t['status']}] {t['id']}" for t in report["targets"]],
            f"coverage={report.get('coverage')}",
            "",
        ]
    if report.get("lanes"):
        lines += [
            "## Lane 结果",
            "| lane | status | outcome | certainty | summary |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {l['group_id']} | {l['status']} | {l.get('outcome')} | {l.get('certainty')} | {l.get('summary')} |"
            for l in report["lanes"]
        ]
        lines.append("")
    lines += [
        "## 模型调用",
        "| call | 秒 | 模型秒 | 轮 | 工具 | 执行 | 重复 | 分页 | 截断 | 错误 | 结束原因 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in report.get("calls") or []:
        t = c["tools"]
        lines.append(
            f"| {c['run_id'][-5:]}/{c['node']} | {c['duration_s']} | {c['model_s']} | {c['rounds']} | {t.get('tool_calls')} | {t.get('executed')} | {t.get('repeat_notices')} | {t.get('repeat_pages')} | {t.get('turn_capped')} | {t.get('tool_errors')} | {c.get('incomplete_reason') or ''} |"
        )
    lines.append("")
    lines += ["## 发现（工程异常类型）"]
    if not report.get("findings"):
        lines.append("- 无")
    for f in report.get("findings") or []:
        lines.append(
            f"- **{f['severity']}** `{f['code']}` @ {f['where']} — {f['evidence']}（{f['hint']}）"
        )
    if report.get("answer"):
        lines += [
            "",
            f"answer.status={report['answer'].get('status')} missing={report['answer'].get('missing')}",
        ]
    return "\n".join(lines) + "\n"


def write_run_report(run_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Build, archive and log the report; never raises into the workflow."""
    try:
        from app.core.context.archive import ContextArchive

        report = build_run_report(run_id, **kwargs)
        archive = ContextArchive(run_id=run_id)
        archive.write_json("run_report.json", report)
        archive.write_text("run_report.md", render_markdown(report))
        codes = (
            ",".join(f"{f['code']}" for f in report["findings"] if f["severity"] != "info")
            or "none"
        )
        calls = report.get("calls") or []
        logger.info(
            "[run_summary] run=%s route=%s outcome=%s elapsed=%ss calls=%d rounds=%d tools=%d repeats=%d capped=%d findings=%s",
            run_id,
            report.get("route"),
            report.get("outcome"),
            report.get("elapsed_seconds"),
            len(calls),
            sum(c["rounds"] for c in calls),
            sum(c["tools"].get("tool_calls", 0) for c in calls),
            sum(
                c["tools"].get("repeat_notices", 0) + c["tools"].get("repeat_pages", 0)
                for c in calls
            ),
            sum(c["tools"].get("turn_capped", 0) for c in calls),
            codes,
        )
        for f in report["findings"]:
            if f["severity"] in {"warning", "error"}:
                logger.warning(
                    "[run_finding] run=%s code=%s where=%s %s",
                    run_id,
                    f["code"],
                    f["where"],
                    f["evidence"],
                )
        return report
    except Exception as exc:  # diagnostics must never break a run
        logger.warning("[run_summary] report failed for run=%s: %s", run_id, exc)
        return None
