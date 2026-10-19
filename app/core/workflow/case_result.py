"""Stage-owned diagnostic deliverables, not a copy of a worker's context.

The model writes diagnostic content. The caller binds run/group/entity identity
from the assigned task. A full report is stored separately from the bounded
index sent to the overview model; neither contains execution authorization.
"""

import re
from copy import deepcopy
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.workflow.fact_contract import tool_dimension

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
        description="供用户直接阅读的完整 Markdown：诊断结论、异常现象、真实工具证据及来源、原因分析；不是一句摘要。不包含其他组，不生成修复命令",
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


_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_DROPPED_SECTION = re.compile(r"^待核实")
_EVIDENCE_SECTION = re.compile(r"^关键证据")
_TOOL_NAME = re.compile(r"\b((?:kubectl|kubernetes|execute|query)_[a-z_]+)\b")
# A cell that already opens with its dimension ("Kubernetes / Lifecycle", "Metrics · …").
_LABELLED = re.compile(r"^(kubernetes|metrics|logging|tracing|topology)(?![a-z])")
# Fallback when the cell names a category instead of a tool; first match wins.
_SOURCE_KEYWORDS = (
    ("tracing", re.compile(r"tracing|trace|span|deepflow|链路")),
    ("metrics", re.compile(r"prometheus|promql|metric|指标")),
    ("logging", re.compile(r"logging|\blogs?\b|日志")),
    (
        "kubernetes",
        re.compile(
            r"kubernetes|kubectl|\bk8s\b|\bpod\b|configmap|secret|deployment|describe|"
            r"events?\b|lifecycle|事件|yaml|生命周期"
        ),
    ),
)
DIMENSION_LABELS = {
    "kubernetes": "Kubernetes",
    "metrics": "Metrics",
    "logging": "Logging",
    "tracing": "Tracing",
    "topology": "Topology",
}


def drop_open_item_sections(report):
    """Remove "待核实…" sections; open items stay in ``unresolved`` for the handoff."""
    lines = report.split("\n")
    kept, skip_level = [], 0
    for line in lines:
        heading = _HEADING.match(line.strip())
        if heading:
            level = len(heading.group(1))
            if skip_level and level > skip_level:
                continue
            skip_level = level if _DROPPED_SECTION.match(heading.group(2).strip()) else 0
            if skip_level:
                continue
        elif skip_level:
            continue
        kept.append(line)
    return report if len(kept) == len(lines) else "\n".join(kept).rstrip()


def _first_cell_end(row):
    """Index of the pipe closing the first table cell; pipes inside backticks don't count."""
    in_code = False
    for index in range(1, len(row)):
        char = row[index]
        if char == "`":
            in_code = not in_code
        elif char == "|" and not in_code and row[index - 1] != "\\":
            return index
    return -1


def label_evidence_sources(report):
    """Prefix each 关键证据 row's source cell with the dimension of the tool it names.

    The mapping is the tool's, not the model's wording, so every card reads
    Kubernetes / Metrics / Logging / Tracing the same way.
    """
    lines = report.split("\n")
    in_section, row_index = False, 0
    for number, line in enumerate(lines):
        heading = _HEADING.match(line.strip())
        if heading:
            in_section = bool(_EVIDENCE_SECTION.match(heading.group(2).strip()))
            row_index = 0
            continue
        stripped = line.strip()
        if not in_section or not stripped.startswith("|"):
            row_index = 0
            continue
        row_index += 1
        if row_index <= 2:  # header and separator
            continue
        end = _first_cell_end(stripped)
        if end < 0:
            continue
        cell = stripped[1:end].strip()
        plain = cell.replace("*", "").replace("`", "").strip().lower()
        if _LABELLED.match(plain):
            continue
        match = _TOOL_NAME.search(plain)
        dimension = tool_dimension(match.group(1)) if match else "other"
        if dimension == "other":
            dimension = next((d for d, pattern in _SOURCE_KEYWORDS if pattern.search(plain)), "")
        label = DIMENSION_LABELS.get(dimension)
        if label:
            lines[number] = f"| **{label}** · {cell} {stripped[end:]}"
    return "\n".join(lines)


def bind_case_result(output, *, group_id, target, result_ref):
    """Assign identity outside model output; history remains in its archive."""
    parsed = DiagnosisCaseOutput.model_validate(output).model_dump()
    parsed["report"] = label_evidence_sources(
        drop_open_item_sections(normalize_report_paragraphs(parsed["report"]))
    )
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
    if unresolved:
        lines.append("尚未确认：" + "；".join(unresolved))
    if analysis:
        lines += ["", "### 取证分析", analysis]
    if facts:
        lines += ["", "### 关键证据", "| 观察 | 时间 | 证据引用 |", "|---|---|---|"]
        for fact in facts:
            refs = ", ".join(f"`{r}`" for r in fact.get("evidence_refs") or [])
            lines.append(
                f"| {fact['statement']} | {fact.get('observed_at') or '—'} | {refs or '—'} |"
            )
    return "\n".join(lines)
