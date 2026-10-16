"""Deterministic engineering findings over run ledgers.

Codes describe the agent run's behaviour (what to look at first after a run);
they never classify the cluster fault. Thresholds come from the same guards and
budgets the runtime uses, so a finding means "a guard fired or nearly fired".
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from app.core.aicall.guards import AgentGuards
from app.core.aicall.output_budget import OutputBudget

LONG_ROUND_SECONDS = 60


def _finding(code: str, severity: str, where: str, evidence: str, hint: str) -> Dict[str, str]:
    return {"code": code, "severity": severity, "where": where, "evidence": evidence, "hint": hint}


def classify_ledger(
    ledger: Dict[str, Any],
    guards: AgentGuards | None = None,
    budget: OutputBudget | None = None,
) -> List[Dict[str, str]]:
    guards = guards or AgentGuards.from_config()
    budget = budget or OutputBudget.from_config()
    where = f"{ledger.get('run_id')}/{ledger.get('node')}"
    counts = ledger.get("counts") or {}
    out: List[Dict[str, str]] = []

    cap = guards.max_tool_calls_per_turn
    burst = max((r.get("tool_calls") or 0 for r in ledger.get("rounds") or []), default=0)
    if cap and burst > cap:
        out.append(
            _finding(
                "tool_call_burst",
                "warning",
                where,
                f"one model message issued {burst} tool calls (cap {cap}); {counts.get('turn_capped', 0)} not executed",
                "model degenerate repetition; the per-turn cap contained it, generation time was still spent",
            )
        )
    if counts.get("repeat_notices"):
        out.append(
            _finding(
                "identical_call_repeats",
                "info",
                where,
                f"{counts['repeat_notices']} identical calls answered by notice, {counts.get('repeat_pages', 0)} by raw pages",
                "model re-issued calls it already had; see tools[].guard",
            )
        )
    reasons = set(ledger.get("guards", {}).get("incomplete") or [])
    reason = ledger.get("incomplete_reason") or ""
    if reason == "repeat_limit" or any("重复" in str(r) and "上限" in str(r) for r in reasons):
        out.append(
            _finding(
                "repeat_limit_stop",
                "warning",
                where,
                "stage stopped by max_identical_calls",
                "deterministic stop; answer delivered from existing material",
            )
        )
    if reason == "idle_round":
        out.append(
            _finding(
                "idle_round_stop",
                "info",
                where,
                "a whole round repeated already answered calls; loop ended, delivered from material",
                "model signalled completion while emitting stale tool calls (see requests/ trace)",
            )
        )
    if ledger.get("guards", {}).get("args_repaired"):
        out.append(
            _finding(
                "malformed_tool_args_repaired",
                "warning",
                where,
                f"{ledger['guards']['args_repaired']} assistant message(s) had non-JSON tool arguments",
                "streamed tool-call deltas merged; repaired before resend (would have been HTTP 400)",
            )
        )
    if reason == "step_limit" or "step_limit" in reasons:
        out.append(
            _finding(
                "step_limit",
                "warning",
                where,
                "recursion limit reached",
                "raise workflow.max_steps or inspect why rounds were unproductive",
            )
        )
    if reason == "agent_timeout":
        out.append(
            _finding(
                "agent_timeout",
                "error",
                where,
                "agent wall-clock limit reached",
                "model service slow or stalled",
            )
        )
    if reason == "agent_error" or any("模型服务请求失败" in str(r) for r in reasons):
        out.append(
            _finding(
                "provider_error",
                "error",
                where,
                "; ".join(str(r) for r in reasons if "模型服务" in str(r)) or "agent error",
                "check gateway / vLLM logs for this time window",
            )
        )
    if any("停滞" in str(r) for r in reasons):
        out.append(
            _finding(
                "model_stalled",
                "error",
                where,
                "no bytes from the model stream within the idle limit",
                "model service issue (see llm-stall-evidence)",
            )
        )
    fin = ledger.get("guards", {}).get("finalization") or {}
    if fin:
        status = fin.get("status") or ("success" if fin.get("ok") else "failed")
        code = "structured_finalization" if status == "success" else "empty_structured_delivery"
        out.append(
            _finding(
                code,
                "info" if status == "success" else "error",
                where,
                f"finalization reason={fin.get('reason')} status={status}",
                "the stage ended without a structured result; delivered from material"
                if status == "success"
                else "no structured result even after retry",
            )
        )
    elif ledger.get("structured_delivered") is False and reason:
        out.append(
            _finding(
                "empty_structured_delivery",
                "error",
                where,
                f"no structured result (reason={reason})",
                "see cases/invalid-output.txt",
            )
        )
    if counts.get("tool_errors"):
        out.append(
            _finding(
                "tool_failures",
                "info",
                where,
                f"{counts['tool_errors']} tool results were errors",
                "tool contract or arguments; see tools[].status",
            )
        )
    if counts.get("bounded_outputs"):
        out.append(
            _finding(
                "large_tool_output_bounded",
                "info",
                where,
                f"{counts['bounded_outputs']} results bounded for the model (raw archived)",
                "read-back available via raw_ref",
            )
        )
    if ledger.get("guards", {}).get("compactions"):
        out.append(
            _finding(
                "context_compacted",
                "info",
                where,
                f"{ledger['guards']['compactions']} compaction(s)",
                "history replaced by working summary",
            )
        )
    for r in ledger.get("rounds") or []:
        if (r.get("model_ms") or 0) >= LONG_ROUND_SECONDS * 1000:
            out.append(
                _finding(
                    "long_model_round",
                    "warning",
                    where,
                    f"round {r.get('iteration')} took {round((r.get('model_ms') or 0) / 1000)}s, output_tokens={r.get('output_tokens')}",
                    "reasoning-heavy or runaway generation; compare output_tokens with llm.output_tokens.agent",
                )
            )
        if (r.get("output_tokens") or 0) >= int(budget.agent * 0.95):
            out.append(
                _finding(
                    "output_budget_exhausted_round",
                    "warning",
                    where,
                    f"round {r.get('iteration')} produced {r.get('output_tokens')} tokens (reserve {budget.agent})",
                    "model hit max_tokens: text/tool-call burst or long reasoning",
                )
            )
    return out


def classify(ledgers: Iterable[Dict[str, Any]], **kwargs) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for ledger in ledgers:
        out.extend(classify_ledger(ledger, **kwargs))
    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(out, key=lambda f: order.get(f["severity"], 9))
