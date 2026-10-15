"""Stage-owned diagnostic deliverables, not a copy of a worker's context.

The model writes diagnostic content. The caller binds run/group/entity identity
from the assigned task. A full report is stored separately from the bounded
index sent to the overview model; neither contains execution authorization.
"""

import re
from copy import deepcopy
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=320)]
EvidenceRef = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=640)
]


class CaseFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: ShortText
    observed_at: str = Field(default="", max_length=80)
    evidence_refs: list[EvidenceRef] = Field(
        min_length=1,
        max_length=3,
        description="原样使用工具结果中的 raw_ref 或 structured_ref 归档地址；不自编工具描述作为地址",
    )


class EvidenceStageOutput(BaseModel):
    """Only selected evidence survives compression; analysis remains ordinary text."""

    model_config = ConfigDict(extra="forbid")

    analysis: str = Field(min_length=1)
    key_facts: list[CaseFact] = Field(default_factory=list, max_length=8)
    unresolved: list[ShortText] = Field(default_factory=list, max_length=6)
    runbook_refs: list[EvidenceRef] = Field(default_factory=list, max_length=6)


class DiagnosisCaseOutput(BaseModel):
    """RCA's result: full user-facing report plus a bounded handoff.

    Facts and unknowns are selected by the agent, not fault-name heuristics.
    Schema overflow is a delivery error, never silently clipped evidence.
    """

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["abnormal", "recovered", "inconclusive"]
    summary: ShortText
    cause: str = Field(default="", max_length=480)
    certainty: Literal["unknown", "hypothesis", "supported", "confirmed"]
    key_facts: list[CaseFact] = Field(default_factory=list, max_length=8)
    unresolved: list[ShortText] = Field(default_factory=list, max_length=6)
    runbook_refs: list[EvidenceRef] = Field(default_factory=list, max_length=6)
    report: str = Field(
        min_length=1,
        description="供用户直接阅读的完整 Markdown：诊断结论、异常现象、真实工具证据及来源、原因分析、待核实与采集边界；不是一句摘要。不包含其他组，不生成修复命令",
    )


def normalize_report_paragraphs(report):
    """Repair double-escaped prose paragraph breaks, never decode code/log literals.

    No unicode_escape decoding: JSON has already been decoded, and real paths,
    regexes, log snippets and single escaped newlines must remain unchanged.
    """
    parts = re.split(r"(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]*`)", report)
    return "".join(
        part if index % 2 else part.replace(r"\n\n", "\n\n") for index, part in enumerate(parts)
    )


def bind_case_result(output, *, group_id, target, result_ref):
    """Assign identity outside model output; history remains in its archive."""
    parsed = DiagnosisCaseOutput.model_validate(output).model_dump()
    parsed["report"] = normalize_report_paragraphs(parsed["report"])
    if not isinstance(group_id, str) or not group_id.strip():
        raise ValueError("case group_id is required")
    if not isinstance(target, dict) or not target.get("target_id") or not target.get("entities"):
        raise ValueError("assigned target identity is required")
    if not isinstance(result_ref, str) or not result_ref.strip():
        raise ValueError("case result archive reference is required")
    return {
        "contract_version": "diagnosis-case.v1",
        "group_id": group_id,
        "target": deepcopy(target),
        "result_ref": result_ref,
        "execution_status": "completed",
        **parsed,
    }


def case_index(result):
    """Overview sees a result index, never report/history/tool bodies.

    The result catalog retains every group, including failed workers. This
    projection deliberately has no policy for choosing/omitting cases.
    """
    target = result.get("target") or {}
    return {
        "group_id": result["group_id"],
        "target_id": target.get("target_id"),
        "entities": deepcopy(target.get("entities") or []),
        "execution_status": result.get("execution_status", "partial"),
        "outcome": result.get("outcome", "inconclusive"),
        "summary": result.get("summary", "未交付完整诊断结果"),
        "certainty": result.get("certainty", "unknown"),
        "result_ref": result.get("result_ref"),
    }


def evidence_fallback_report(evidence_handoff, evidence_analysis=""):
    """Report built from this group's own evidence when RCA delivered nothing.

    Facts and open questions come verbatim from the evidence stage (tool-backed);
    no cause is inferred here. Returns "" when there is nothing real to show.
    """
    handoff = evidence_handoff if isinstance(evidence_handoff, dict) else {}
    facts = [
        f for f in handoff.get("key_facts") or [] if isinstance(f, dict) and f.get("statement")
    ]
    unresolved = [str(u) for u in handoff.get("unresolved") or [] if u]
    analysis = str(evidence_analysis or "").strip()
    if not facts and not analysis:
        return ""
    lines = [
        "### 诊断结论",
        "根因分析阶段未交付结构化结果；以下是本组取证阶段的真实观察，不构成根因结论。",
    ]
    if analysis:
        lines += ["", "### 取证分析", analysis]
    if facts:
        lines += ["", "### 关键证据", "| 观察 | 时间 | 证据引用 |", "|---|---|---|"]
        for fact in facts:
            refs = ", ".join(f"`{r}`" for r in fact.get("evidence_refs") or [])
            lines.append(
                f"| {fact['statement']} | {fact.get('observed_at') or '—'} | {refs or '—'} |"
            )
    if unresolved:
        lines += ["", "### 待核实"] + [f"- {item}" for item in unresolved]
    return "\n".join(lines)
