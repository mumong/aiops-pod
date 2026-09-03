"""Deterministic quality evaluation for current AIOps diagnosis reports.

The evaluator intentionally stays outside the diagnosis workflow.  Ground truth
is never sent to the model.  It scores final root-cause claims, Evidence Plan
execution completeness, and an independent fixed-contract evidence audit.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


NEGATION_MARKERS = (
    "排除",
    "不是",
    "并非",
    "不属于",
    "无证据",
    "缺乏",
    "未发现",
    "未见",
    "无法确认",
    "不能确认",
    "not ",
    "no evidence",
    "without",
    "excluded",
    "unlikely",
)

INCONCLUSIVE_MARKERS = (
    "证据不足",
    "无法确认",
    "不能确认",
    "未确认",
    "rca 未定",
    "inconclusive",
    "insufficient evidence",
    "root cause is unknown",
)


@dataclass(frozen=True)
class RootCauseExpectation:
    id: str
    include_all: tuple[str, ...] = ()
    include_any: tuple[str, ...] = ()
    exclude_any: tuple[str, ...] = ()
    aliases: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, fallback_id: str) -> "RootCauseExpectation":
        aliases: dict[str, tuple[str, ...]] = {}
        for key, items in (value.get("aliases") or {}).items():
            if isinstance(items, str):
                aliases[str(key)] = (items,)
            else:
                aliases[str(key)] = tuple(str(item) for item in (items or []))
        return cls(
            id=str(value.get("id") or fallback_id),
            include_all=tuple(str(item) for item in (value.get("include_all") or [])),
            include_any=tuple(str(item) for item in (value.get("include_any") or [])),
            exclude_any=tuple(str(item) for item in (value.get("exclude_any") or [])),
            aliases=aliases,
        )


@dataclass(frozen=True)
class RootClaim:
    group: str
    text: str
    full_section: str
    inconclusive: bool = False


@dataclass(frozen=True)
class ExpectationMatch:
    expectation_id: str
    matched: bool
    group: str = ""
    matched_all: tuple[str, ...] = ()
    matched_any: tuple[str, ...] = ()
    missing_all: tuple[str, ...] = ()
    missing_any: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()


@dataclass(frozen=True)
class RootCauseScore:
    passed: bool
    expected_count: int
    matched_count: int
    diagnosed_claim_count: int
    matched_claim_count: int
    recall: float
    precision: float
    matches: tuple[ExpectationMatch, ...]
    unexpected_claim_groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceLaneScore:
    lane: str
    collected: int
    planned: int
    source: str = ""

    @property
    def completeness(self) -> Optional[float]:
        return self.collected / self.planned if self.planned else None


@dataclass(frozen=True)
class EvidenceScore:
    collected: int
    planned: int
    completeness: Optional[float]
    lanes: tuple[EvidenceLaneScore, ...]
    source: str
    error: str = ""
    mode: str = "dynamic_plan"
    matches: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class EvidenceExpectation:
    """One reusable semantic evidence requirement in a benchmark contract.

    The requirement describes *what fact must exist*, not which concrete tool,
    query string, Pod name, or call order the agent must use.
    """

    id: str
    description: str
    weight: int = 1
    required: bool = True
    dimensions: tuple[str, ...] = ()
    tools_any: tuple[str, ...] = ()
    attributes_any: tuple[str, ...] = ()
    include_all: tuple[str, ...] = ()
    include_any: tuple[str, ...] = ()
    min_observations: int = 1
    require_trend_evaluable: bool = False
    distinct_value_key: str = ""
    min_distinct_values: int = 0
    correlate_by: str = ""
    correlation_dimensions: tuple[str, ...] = ()
    allow_negative: bool = False

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any], *, fallback_id: str
    ) -> "EvidenceExpectation":
        weight = max(1, int(value.get("weight") or 1))
        return cls(
            id=str(value.get("id") or fallback_id),
            description=str(value.get("description") or value.get("id") or fallback_id),
            weight=weight,
            required=bool(value.get("required", True)),
            dimensions=tuple(str(item).casefold() for item in (value.get("dimensions") or [])),
            tools_any=tuple(str(item) for item in (value.get("tools_any") or [])),
            attributes_any=tuple(str(item) for item in (value.get("attributes_any") or [])),
            include_all=tuple(str(item) for item in (value.get("include_all") or [])),
            include_any=tuple(str(item) for item in (value.get("include_any") or [])),
            min_observations=max(1, int(value.get("min_observations") or 1)),
            require_trend_evaluable=bool(value.get("require_trend_evaluable", False)),
            distinct_value_key=str(value.get("distinct_value_key") or ""),
            min_distinct_values=max(0, int(value.get("min_distinct_values") or 0)),
            correlate_by=str(value.get("correlate_by") or ""),
            correlation_dimensions=tuple(
                str(item).casefold() for item in (value.get("correlation_dimensions") or [])
            ),
            allow_negative=bool(value.get("allow_negative", False)),
        )


@dataclass(frozen=True)
class EvidenceObservation:
    tool: str
    dimension: str
    attribute: str
    text: str
    ref: str
    record: Mapping[str, Any] = field(default_factory=dict)
    positive: bool = True


@dataclass(frozen=True)
class RunbookScore:
    expected: tuple[str, ...]
    found: tuple[str, ...]
    matched: tuple[str, ...]
    coverage: Optional[float]
    passed: bool


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"[\s\u00a0]+", " ", text)
    return text.strip()


def _normalize_runbook_id(value: str) -> str:
    normalized = _normalize(value).strip("`*[](){}.,;:，。；：")
    return normalized[:-3] if normalized.endswith(".md") else normalized


def extract_runbook_ids(report: str) -> tuple[str, ...]:
    """Extract exact runbook IDs from the final human-facing report.

    The current reporter emits IDs such as ``pod-config-error`` in its
    ``Runbook 参考`` block.  Matching the final report keeps this metric
    auditable and avoids treating a runbook merely present in the global
    catalog as selected by the diagnosis lane.
    """

    found: set[str] = set()
    for match in re.finditer(r"(?i)(?<![a-z0-9_-])(pod-[a-z0-9][a-z0-9_.-]*)(?![a-z0-9_-])", report or ""):
        runbook_id = _normalize_runbook_id(match.group(1))
        if runbook_id:
            found.add(runbook_id)
    return tuple(sorted(found))


def score_runbooks(
    expected: Sequence[str],
    report: str,
    *,
    observations: Sequence[str] = (),
) -> RunbookScore:
    expected_ids = tuple(
        dict.fromkeys(
            item for item in (_normalize_runbook_id(value) for value in expected) if item
        )
    )
    found_ids = extract_runbook_ids("\n".join((report, *observations)))
    found_set = set(found_ids)
    matched = tuple(item for item in expected_ids if item in found_set)
    coverage = len(matched) / len(expected_ids) if expected_ids else None
    return RunbookScore(
        expected=expected_ids,
        found=found_ids,
        matched=matched,
        coverage=coverage,
        passed=bool(expected_ids) and len(matched) == len(expected_ids),
    )


def _occurrences(text: str, phrase: str) -> Iterable[tuple[int, int]]:
    normalized_text = _normalize(text)
    normalized_phrase = _normalize(phrase)
    if not normalized_phrase:
        return
    if re.fullmatch(r"[a-z0-9_.:/-]+", normalized_phrase):
        pattern = re.compile(
            rf"(?<![a-z0-9_]){re.escape(normalized_phrase)}(?![a-z0-9_])",
            re.IGNORECASE,
        )
        for match in pattern.finditer(normalized_text):
            yield match.start(), match.end()
        return
    start = normalized_text.find(normalized_phrase)
    while start >= 0:
        yield start, start + len(normalized_phrase)
        start = normalized_text.find(normalized_phrase, start + len(normalized_phrase))


def _is_negated(text: str, start: int, end: int) -> bool:
    normalized = _normalize(text)
    before = normalized[max(0, start - 40):start]
    after = normalized[end:min(len(normalized), end + 18)]
    if any(marker in before for marker in NEGATION_MARKERS):
        return True
    # Chinese reports frequently use the compact form ``非 OOMKilled``.
    # Treat only an immediately preceding ``非`` as negation; adding the
    # single character to NEGATION_MARKERS would incorrectly negate a term
    # whenever an unrelated ``非`` appeared anywhere in the 40-char window.
    if re.search(r"非\s*$", before):
        return True
    # A few report forms place the negation after the term, for example
    # "OOMKilled 不是根因".  Keep this suffix window deliberately narrow so a
    # later sentence such as "已排除 liveness" does not negate OOMKilled too.
    return any(
        marker in after
        for marker in ("不是根因", "并非根因", "已排除", "被排除", "不成立", "not the root cause")
    )


def _term_variants(expectation: RootCauseExpectation, term: str) -> tuple[str, ...]:
    configured = expectation.aliases.get(term, ())
    variants = [term, *configured]
    unique: list[str] = []
    for item in variants:
        if item and item not in unique:
            unique.append(item)
    return tuple(unique)


def _positive_term_present(text: str, expectation: RootCauseExpectation, term: str) -> bool:
    for variant in _term_variants(expectation, term):
        for start, end in _occurrences(text, variant):
            if not _is_negated(text, start, end):
                return True
    return False


def _conflicting_term_present(text: str, expectation: RootCauseExpectation, term: str) -> bool:
    for variant in _term_variants(expectation, term):
        for start, end in _occurrences(text, variant):
            if not _is_negated(text, start, end):
                return True
    return False


def _claim_body(section: str) -> str:
    conclusion = re.search(
        r"(?ims)^###\s*(?:🎯\s*)?根因结论\s*$\n(?P<body>.*?)(?=^###\s+|^##\s+|\Z)",
        section,
    )
    if conclusion and conclusion.group("body").strip():
        return conclusion.group("body").strip()
    return section.strip()


def _claim_is_inconclusive(claim: str) -> bool:
    normalized = _normalize(claim)
    # A report may confirm the causal mechanism while explicitly leaving a
    # secondary detail unknown (for example, *which* dependency is down or
    # *why* an object was deleted).  That caveat must not erase the confirmed
    # root cause.  Prefer explicit confirmation before generic caveat words.
    confirmed = (
        "已确认根因",
        "已确认的根因",
        "确认现象根因",
        "根本原因是",
        "root cause confirmed",
    )
    if any(marker in normalized for marker in confirmed):
        return False

    root_unknown = (
        "rca 未定",
        "根因无法确认",
        "根因不能确认",
        "根因未确认",
        "无法确认该组根因",
        "不能确认该组根因",
        "无法诊断初始",
        "inconclusive",
        "root cause is unknown",
    )
    if any(marker in normalized for marker in root_unknown):
        return True

    # Generic insufficient-evidence wording is root-level only when it opens
    # the conclusion.  Later occurrences normally qualify an already stated
    # diagnosis and are retained as uncertainty rather than changing status.
    leading_unknown = (
        "证据不足",
        "现有证据不足",
        "insufficient evidence",
    )
    leading = normalized.lstrip("#*-：: `\n\t")
    if any(leading.startswith(marker) for marker in leading_unknown):
        return True

    # Keep compatibility with concise reports that do not use the preferred
    # confirmation phrase but still state a concrete root cause.
    concrete_root = re.search(
        r"(?:根因(?:结论)?|根本原因)\s*(?:是|为|：|:)\s*"
        r"(?!无法|不能|未确认|未知|证据不足)",
        normalized,
    )
    if concrete_root:
        return False
    return any(marker in normalized for marker in INCONCLUSIVE_MARKERS)


def extract_root_claims(report: str) -> list[RootClaim]:
    """Extract one final claim per current per-lane root-cause section."""

    heading = re.compile(
        r"(?im)^##\s*(?:🎯\s*)?根因分析(?:\s*[·:：-]\s*(?P<group>[^\n]+))?\s*$"
    )
    matches = list(heading.finditer(report or ""))
    claims: list[RootClaim] = []
    for index, match in enumerate(matches):
        start = match.end()
        next_heading = re.search(r"(?m)^##\s+", (report or "")[start:])
        end = start + next_heading.start() if next_heading else len(report or "")
        section = (report or "")[start:end].strip()
        claim = _claim_body(section)
        if not claim:
            continue
        claims.append(
            RootClaim(
                group=(match.group("group") or f"claim-{index + 1}").strip(),
                text=claim,
                full_section=section,
                inconclusive=_claim_is_inconclusive(claim),
            )
        )

    if claims:
        return claims

    fallback = re.search(
        r"(?ims)^###\s*(?:🎯\s*)?根因结论\s*$\n(?P<body>.*?)(?=^###\s+|^##\s+|\Z)",
        report or "",
    )
    if fallback and fallback.group("body").strip():
        body = fallback.group("body").strip()
        return [
            RootClaim(
                group="claim-1",
                text=body,
                full_section=body,
                inconclusive=_claim_is_inconclusive(body),
            )
        ]
    return []


def match_expectation(expectation: RootCauseExpectation, claim: RootClaim) -> ExpectationMatch:
    matched_all = tuple(
        term for term in expectation.include_all
        if _positive_term_present(claim.text, expectation, term)
    )
    missing_all = tuple(term for term in expectation.include_all if term not in matched_all)
    matched_any = tuple(
        term for term in expectation.include_any
        if _positive_term_present(claim.text, expectation, term)
    )
    missing_any = () if matched_any or not expectation.include_any else expectation.include_any
    conflicts = tuple(
        term for term in expectation.exclude_any
        if _conflicting_term_present(claim.text, expectation, term)
    )
    matched = not claim.inconclusive and not missing_all and not missing_any and not conflicts
    return ExpectationMatch(
        expectation_id=expectation.id,
        matched=matched,
        group=claim.group,
        matched_all=matched_all,
        matched_any=matched_any,
        missing_all=missing_all,
        missing_any=missing_any,
        conflicts=conflicts,
    )


def _candidate_rank(match: ExpectationMatch) -> tuple[int, int, int, int]:
    return (
        1 if match.matched else 0,
        len(match.matched_all) + len(match.matched_any),
        -len(match.missing_all) - len(match.missing_any),
        -len(match.conflicts),
    )


def score_root_causes(
    expectations: Sequence[RootCauseExpectation],
    claims: Sequence[RootClaim],
) -> RootCauseScore:
    best_matches: list[ExpectationMatch] = []
    matched_claim_groups: set[str] = set()
    for expectation in expectations:
        candidates = [match_expectation(expectation, claim) for claim in claims]
        if candidates:
            best = max(candidates, key=_candidate_rank)
        else:
            best = ExpectationMatch(
                expectation_id=expectation.id,
                matched=False,
                missing_all=expectation.include_all,
                missing_any=expectation.include_any,
            )
        best_matches.append(best)
        if best.matched:
            matched_claim_groups.add(best.group)

    diagnosed_claims = [claim for claim in claims if not claim.inconclusive]
    unexpected = tuple(
        claim.group for claim in diagnosed_claims if claim.group not in matched_claim_groups
    )
    matched_count = sum(1 for item in best_matches if item.matched)
    expected_count = len(expectations)
    matched_claim_count = sum(1 for claim in diagnosed_claims if claim.group in matched_claim_groups)
    recall = matched_count / expected_count if expected_count else 0.0
    precision = matched_claim_count / len(diagnosed_claims) if diagnosed_claims else 0.0
    passed = bool(expectations) and matched_count == expected_count and not unexpected
    return RootCauseScore(
        passed=passed,
        expected_count=expected_count,
        matched_count=matched_count,
        diagnosed_claim_count=len(diagnosed_claims),
        matched_claim_count=matched_claim_count,
        recall=recall,
        precision=precision,
        matches=tuple(best_matches),
        unexpected_claim_groups=unexpected,
    )


def _tool_dimension(tool: str) -> str:
    name = _normalize(tool)
    if "promql" in name or "prometheus" in name:
        return "metrics"
    if "tracing" in name or "trace" in name:
        return "tracing"
    if "topology" in name:
        return "topology"
    if "log" in name:
        return "logging"
    if "kubectl" in name or "kubernetes" in name:
        return "kubernetes"
    return "unknown"


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _tool_data_is_positive(data: Any) -> bool:
    text = str(data or "").strip()
    if not text:
        return False
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, Mapping):
        coverage = _normalize(str(payload.get("coverage") or ""))
        if coverage in {"empty", "absent", "error", "failed", "unselected"}:
            return False
        status = _normalize(str(payload.get("status") or ""))
        if status in {"query failed", "tool failed", "command failed", "error"}:
            return False
        counts = payload.get("counts")
        if isinstance(counts, Mapping) and any(key in counts for key in ("matched", "returned")):
            if max(int(counts.get("matched") or 0), int(counts.get("returned") or 0)) <= 0:
                return False
        return True
    return not bool(
        re.search(
            r"no events found|no matching|没有找到事件|未找到匹配|查询为空|"
            r"command failed|error from server.*notfound|\bnotfound\b|\bnot found\b",
            text,
            re.IGNORECASE,
        )
    )


def evidence_observations_from_payloads(
    payloads: Sequence[tuple[str, Mapping[str, Any]]],
) -> tuple[EvidenceObservation, ...]:
    """Extract only real tool observations/canonical facts from Evidence output.

    ``llm_analysis``, the final report, plans, and inventory descriptions are
    intentionally excluded so model prose cannot satisfy its own benchmark.
    Canonical fact records are preferred.  A deterministic tool summary is used
    only when that successful tool result has no canonical ledger.
    """

    observations: list[EvidenceObservation] = []
    for archive_path, payload in payloads:
        tool_data = payload.get("tool_data") or []
        if not isinstance(tool_data, list):
            continue
        for tool_index, item in enumerate(tool_data, start=1):
            if not isinstance(item, Mapping) or item.get("semantic_success") is False:
                continue
            tool = str(item.get("tool") or "unknown")
            ledger = item.get("fact_ledger") or {}
            records = ledger.get("records") if isinstance(ledger, Mapping) else []
            canonical_records = [record for record in (records or []) if isinstance(record, Mapping)]
            if canonical_records:
                for record_index, record in enumerate(canonical_records, start=1):
                    fact_id = str(record.get("fact_id") or "")
                    observations.append(
                        EvidenceObservation(
                            tool=tool,
                            dimension=str(record.get("dimension") or _tool_dimension(tool)).casefold(),
                            attribute=str(record.get("attribute") or ""),
                            text=_json_text(record),
                            ref=fact_id or f"{archive_path}#{tool_index}.{record_index}",
                            record=record,
                            positive=True,
                        )
                    )

            data = item.get("data")
            if data not in (None, ""):
                observations.append(
                    EvidenceObservation(
                        tool=tool,
                        dimension=_tool_dimension(tool),
                        attribute="",
                        text=str(data),
                        ref=str(item.get("structured_ref") or item.get("raw_ref") or f"{archive_path}#{tool_index}"),
                        record={},
                        positive=_tool_data_is_positive(data),
                    )
                )
    return tuple(observations)


def _attribute_matches(attribute: str, patterns: Sequence[str]) -> bool:
    if not patterns:
        return True
    normalized = _normalize(attribute)
    return any(fnmatchcase(normalized, _normalize_glob(pattern)) for pattern in patterns)


def _tool_matches(tool: str, patterns: Sequence[str]) -> bool:
    if not patterns:
        return True
    normalized = _normalize(tool)
    return any(fnmatchcase(normalized, _normalize_glob(pattern)) for pattern in patterns)


def _normalize_glob(value: str) -> str:
    """Normalize a glob while preserving ``*``/``?`` operators."""

    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[`_]", "", text)
    text = re.sub(r"[\s\u00a0]+", " ", text)
    return text.strip()


def _positive_phrase_present(text: str, phrase: str) -> bool:
    return any(not _is_negated(text, start, end) for start, end in _occurrences(text, phrase))


def _nested_values(value: Any, key: str) -> set[str]:
    wanted = _normalize(key)
    found: set[str] = set()

    def walk(current: Any) -> None:
        if isinstance(current, str):
            stripped = current.strip()
            if stripped[:1] in {"{", "["}:
                try:
                    walk(json.loads(stripped))
                except json.JSONDecodeError:
                    pass
            return
        if isinstance(current, Mapping):
            for item_key, item_value in current.items():
                if _normalize(str(item_key)) == wanted and item_value not in (None, ""):
                    found.add(_json_text(item_value))
                walk(item_value)
            return
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            for item in current:
                walk(item)

    walk(value)
    return found


def _trend_evaluable(observation: EvidenceObservation) -> bool:
    values = _nested_values(observation.record, "trend_evaluable")
    return "true" in {_normalize(value) for value in values}


def _match_evidence_expectation(
    expectation: EvidenceExpectation,
    observations: Sequence[EvidenceObservation],
) -> Mapping[str, Any]:
    candidates = [
        item
        for item in observations
        if (not expectation.dimensions or item.dimension in expectation.dimensions)
        and (item.positive or expectation.allow_negative)
        and _tool_matches(item.tool, expectation.tools_any)
        and _attribute_matches(item.attribute, expectation.attributes_any)
    ]
    corpus = "\n".join(item.text for item in candidates)
    contributing_refs: list[str] = []

    def add_contributors(term: str) -> None:
        for item in candidates:
            if _positive_phrase_present(item.text, term) and item.ref not in contributing_refs:
                contributing_refs.append(item.ref)

    missing_all = tuple(
        term for term in expectation.include_all if not _positive_phrase_present(corpus, term)
    )
    for term in expectation.include_all:
        if term not in missing_all:
            add_contributors(term)
    any_matched = tuple(
        term for term in expectation.include_any if _positive_phrase_present(corpus, term)
    )
    for term in any_matched:
        add_contributors(term)
    missing_any = bool(expectation.include_any and not any_matched)
    enough_observations = len(candidates) >= expectation.min_observations
    trend_matched = (
        not expectation.require_trend_evaluable
        or any(_trend_evaluable(item) for item in candidates)
    )
    if expectation.require_trend_evaluable and trend_matched:
        for item in candidates:
            if _trend_evaluable(item) and item.ref not in contributing_refs:
                contributing_refs.append(item.ref)

    distinct_values: set[str] = set()
    if expectation.distinct_value_key:
        for item in candidates:
            item_values = _nested_values(item.record, expectation.distinct_value_key)
            distinct_values.update(item_values)
            if item_values and item.ref not in contributing_refs:
                contributing_refs.append(item.ref)
    distinct_matched = (
        not expectation.distinct_value_key
        or len(distinct_values) >= expectation.min_distinct_values
    )

    correlation_values: set[str] = set()
    correlation_matched = True
    if expectation.correlate_by:
        dimensions = expectation.correlation_dimensions or expectation.dimensions
        per_dimension: list[set[str]] = []
        for dimension in dimensions:
            values: set[str] = set()
            for item in candidates:
                if item.dimension == dimension:
                    values.update(_nested_values(item.record, expectation.correlate_by))
            per_dimension.append(values)
        correlation_values = set.intersection(*per_dimension) if per_dimension and all(per_dimension) else set()
        correlation_matched = bool(correlation_values)
        if correlation_matched:
            for item in candidates:
                values = _nested_values(item.record, expectation.correlate_by)
                if values.intersection(correlation_values) and item.ref not in contributing_refs:
                    contributing_refs.append(item.ref)

    matched = bool(candidates) and not missing_all and not missing_any
    matched = matched and enough_observations and trend_matched and distinct_matched and correlation_matched
    return {
        "id": expectation.id,
        "description": expectation.description,
        "weight": expectation.weight,
        "required": expectation.required,
        "matched": matched,
        "dimensions": list(expectation.dimensions),
        "matched_refs": contributing_refs[:12] if matched else [],
        "missing_all": list(missing_all),
        "missing_any": list(expectation.include_any) if missing_any else [],
        "observation_count": len(candidates),
        "min_observations": expectation.min_observations,
        "trend_required": expectation.require_trend_evaluable,
        "trend_matched": trend_matched,
        "distinct_value_key": expectation.distinct_value_key,
        "distinct_value_count": len(distinct_values),
        "min_distinct_values": expectation.min_distinct_values,
        "correlate_by": expectation.correlate_by,
        "correlation_dimensions": list(expectation.correlation_dimensions),
        "correlation_values": sorted(correlation_values)[:5],
    }


def score_evidence_contract(
    expectations: Sequence[EvidenceExpectation],
    payloads: Sequence[tuple[str, Mapping[str, Any]]],
    *,
    source: str = "fixed_contract",
    error: str = "",
) -> EvidenceScore:
    observations = evidence_observations_from_payloads(payloads)
    matches = tuple(
        _match_evidence_expectation(expectation, observations)
        for expectation in expectations
    )
    planned = sum(expectation.weight for expectation in expectations)
    collected = sum(int(item["weight"]) for item in matches if item["matched"])
    return EvidenceScore(
        collected=collected,
        planned=planned,
        completeness=collected / planned if planned else None,
        lanes=(),
        source=source,
        error=error,
        mode="fixed_contract",
        matches=matches,
    )


def evidence_lane_from_payload(payload: Mapping[str, Any], *, source: str, lane: str) -> EvidenceLaneScore:
    planned = int(payload.get("plan_total") or 0)
    collected = int(payload.get("plan_collected") or 0)
    collected = min(max(collected, 0), max(planned, 0))
    return EvidenceLaneScore(
        lane=lane,
        collected=collected,
        planned=max(planned, 0),
        source=source,
    )


def score_evidence_lanes(lanes: Sequence[EvidenceLaneScore], *, source: str, error: str = "") -> EvidenceScore:
    collected = sum(item.collected for item in lanes)
    planned = sum(item.planned for item in lanes)
    return EvidenceScore(
        collected=collected,
        planned=planned,
        completeness=collected / planned if planned else None,
        lanes=tuple(lanes),
        source=source,
        error=error,
    )


def load_evidence_files(paths: Sequence[Path]) -> EvidenceScore:
    lanes: list[EvidenceLaneScore] = []
    errors: list[str] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            lanes.append(evidence_lane_from_payload(payload, source=str(path), lane=path.parent.parent.name))
        except Exception as exc:  # pragma: no cover - defensive I/O boundary
            errors.append(f"{path}: {exc}")
    return score_evidence_lanes(
        lanes,
        source="archive_files" if lanes else "missing",
        error="; ".join(errors),
    )


def evidence_from_final_metrics(metrics: Mapping[str, Any]) -> EvidenceScore:
    block = metrics.get("evidence_completeness") or {}
    if not isinstance(block, Mapping):
        return score_evidence_lanes([], source="missing", error="invalid final metrics evidence block")
    lane = EvidenceLaneScore(
        lane="workflow",
        collected=int(block.get("collected") or 0),
        planned=int(block.get("planned") or 0),
        source="sse.final.metrics",
    )
    return score_evidence_lanes([lane] if lane.planned else [], source="sse.final.metrics")
