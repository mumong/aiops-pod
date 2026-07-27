#!/usr/bin/env python3
"""Replay archived RCA inputs through the current context budget logic.

This script is intentionally offline: it reads existing ContextArchive files,
rebuilds the RCA evidence context, and invokes only the local hard-budget
preparation step. It never calls an LLM provider and never modifies the source
archive.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.aicall.client import AICall
from app.core.context.budget import count_tokens
from app.core.prompts import get_workflow_prompt
from app.core.skills.models import EvidenceItem, EvidenceLevel
from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
from app.core.workflow.schemas import RCAOutput


DEFAULT_ARCHIVE_ROOT = Path("/tmp/model-comparison-20260722/archives")
DEFAULT_RUN_IDS = (
    "b1b19448b1724fc2",
    "d67a5d552e154dae",
    "ac9eac1ae0764a27",
)
FACT_ID_PATTERN = re.compile(r"\bfact-[0-9a-f]{12}\b")
EVIDENCE_REF_PATTERN = re.compile(
    r"\b(?:metric|log|deepflow|tempo)-[A-Za-z0-9_.:-]+\b"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _evidence_items(values: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        try:
            level = EvidenceLevel(str(value.get("level") or "important"))
        except ValueError:
            level = EvidenceLevel.IMPORTANT
        items.append(
            EvidenceItem(
                id=str(value.get("id") or ""),
                description=str(value.get("description") or ""),
                level=level,
                weight=float(value.get("weight") or 0.2),
                collected=bool(value.get("collected")),
                value=value.get("value"),
                source=value.get("source"),
                outcome=str(value.get("outcome") or "unknown"),
            )
        )
    return items


def _abnormal_pod_keys(handoff: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for value in handoff.get("abnormal_pods") or []:
        if not isinstance(value, dict):
            continue
        namespace = str(value.get("namespace") or "").strip()
        name = str(value.get("name") or "").strip()
        if name:
            keys.append(f"{namespace}/{name}" if namespace else name)
    return keys


def _token_count(*values: Any, model: str) -> int:
    return sum(count_tokens(value, model=model)["tokens"] for value in values)


def replay_run(
    run_dir: Path,
    *,
    model: str,
    context_window: int,
    input_ratio: float,
    output_reserved: int,
    safety_tokens: int,
) -> dict[str, Any]:
    node_input = _read_json(run_dir / "node_inputs" / "rca.input.json")
    archived_budget = _read_json(run_dir / "budget" / "rca.json")
    evidence_handoff = _read_json(
        run_dir / "handoff" / "evidence-to-rca.json"
    )
    layer_handoff = _read_json(run_dir / "layer" / "handoff.json")
    snapshot = evidence_handoff.get("snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError(f"missing evidence snapshot: {run_dir}")

    node = RootCauseAnalyzerNode()
    rebuilt_context = node._build_rca_context(
        {
            "layer_handoff": layer_handoff,
            "evidence_items": _evidence_items(snapshot.get("evidence_items")),
            "evidence_analysis": snapshot.get("evidence_analysis") or "{}",
        }
    )
    question = str(node_input.get("question") or "")
    layer = str(layer_handoff.get("layer") or "L2")
    system_prompt = get_workflow_prompt(
        "rca",
        prompt_language="zh",
    ).format(
        layer=layer,
        evidence_summary=(
            "证据上下文只在 user message 中提供，"
            "system prompt 不承载动态证据。"
        ),
    )
    rebuilt_user_message = (
        f"# 用户问题\n{question}\n\n"
        f"# 已采集证据\n{rebuilt_context}\n\n"
        "请直接基于以上证据进行根因分析，并通过 RCAOutput Pydantic "
        "schema 生成结构化结果。"
    )
    archived_user_message = str(node_input.get("user_message") or "")

    os.environ["MODEL_CONTEXT_WINDOW"] = str(context_window)
    ai_call = AICall(
        model=model,
        api_key="offline-replay",
        context_compaction_config={
            "hard_guard_enabled": True,
            "hard_guard_input_ratio": input_ratio,
            "hard_guard_safety_tokens": safety_tokens,
            "hard_guard_preserve_tail_tokens": 1200,
        },
    )
    (
        _final_system,
        guarded_user_message,
        hard_guard,
        _pre_budget,
        final_budget,
    ) = ai_call._prepare_structured_call_context(
        system_prompt=system_prompt,
        question=rebuilt_user_message,
        schema=RCAOutput,
        node_id="rca_replay",
        output_reserved=output_reserved,
    )

    schema = RCAOutput.model_json_schema()
    archived_input_tokens = _token_count(
        system_prompt,
        archived_user_message,
        schema,
        model=model,
    )
    rebuilt_input_tokens = _token_count(
        system_prompt,
        rebuilt_user_message,
        schema,
        model=model,
    )
    guarded_content_tokens = _token_count(
        system_prompt,
        guarded_user_message,
        schema,
        model=model,
    )
    guarded_input_tokens = int(
        final_budget.get("actual_context_tokens")
        or guarded_content_tokens
    )

    pod_keys = _abnormal_pod_keys(layer_handoff)
    rebuilt_fact_ids = sorted(set(FACT_ID_PATTERN.findall(rebuilt_user_message)))
    guarded_fact_ids = sorted(set(FACT_ID_PATTERN.findall(guarded_user_message)))
    rebuilt_refs = sorted(
        set(EVIDENCE_REF_PATTERN.findall(rebuilt_user_message))
    )
    guarded_refs = sorted(
        set(EVIDENCE_REF_PATTERN.findall(guarded_user_message))
    )
    missing_pods = [
        key
        for key in pod_keys
        if key.split("/", 1)[-1] not in guarded_user_message
    ]
    missing_fact_ids = sorted(set(rebuilt_fact_ids) - set(guarded_fact_ids))
    missing_evidence_refs = sorted(set(rebuilt_refs) - set(guarded_refs))

    return {
        "run_id": run_dir.name,
        "archive_source": str(run_dir),
        "context_window": context_window,
        "hard_input_limit": hard_guard.get("max_input_tokens"),
        "archived_recorded_input_tokens": archived_budget.get(
            "actual_context_tokens"
        ),
        "archived_recorded_usage_ratio": archived_budget.get("usage_ratio"),
        "archived_message_recount_tokens": archived_input_tokens,
        "rebuilt_input_tokens": rebuilt_input_tokens,
        "guarded_input_tokens": guarded_input_tokens,
        "guarded_content_tokens": guarded_content_tokens,
        "archived_user_message_chars": len(archived_user_message),
        "rebuilt_user_message_chars": len(rebuilt_user_message),
        "guarded_user_message_chars": len(guarded_user_message),
        "hard_guard": hard_guard,
        "final_budget": {
            "actual_context_tokens": final_budget.get(
                "actual_context_tokens"
            ),
            "usage_ratio": final_budget.get("usage_ratio"),
        },
        "abnormal_pods": pod_keys,
        "missing_abnormal_pods": missing_pods,
        "fact_ids_before_guard": rebuilt_fact_ids,
        "fact_ids_after_guard": guarded_fact_ids,
        "fact_id_check_applicable": bool(rebuilt_fact_ids),
        "missing_fact_ids": missing_fact_ids,
        "evidence_refs_before_guard": len(rebuilt_refs),
        "evidence_refs_after_guard": len(guarded_refs),
        "missing_evidence_refs": missing_evidence_refs,
        "checks": {
            "within_hard_input_limit": guarded_input_tokens
            <= int(hard_guard.get("max_input_tokens") or 0),
            "all_abnormal_pods_preserved": not missing_pods,
            "all_fact_ids_preserved": not missing_fact_ids,
            "all_evidence_refs_preserved": not missing_evidence_refs,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline replay of archived RCA context budgets."
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
    )
    parser.add_argument(
        "--run-id",
        action="append",
        dest="run_ids",
        help="Run ID to replay; repeat for multiple runs.",
    )
    parser.add_argument(
        "--model",
        default="openai/Qwen3.6-35B-A3B",
    )
    parser.add_argument("--context-window", type=int, default=32000)
    parser.add_argument("--input-ratio", type=float, default=0.72)
    parser.add_argument("--output-reserved", type=int, default=6000)
    parser.add_argument("--safety-tokens", type=int, default=2000)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON replay report.",
    )
    args = parser.parse_args()

    run_ids = tuple(args.run_ids or DEFAULT_RUN_IDS)
    reports = [
        replay_run(
            args.archive_root / run_id,
            model=args.model,
            context_window=args.context_window,
            input_ratio=args.input_ratio,
            output_reserved=args.output_reserved,
            safety_tokens=args.safety_tokens,
        )
        for run_id in run_ids
    ]
    payload = {
        "archive_root": str(args.archive_root),
        "model": args.model,
        "run_count": len(reports),
        "runs": reports,
        "passed": all(
            all(report["checks"].values())
            for report in reports
        ),
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
