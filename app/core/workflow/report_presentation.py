"""Human-facing projection for source-backed diagnostic evidence.

This module is intentionally fault-agnostic.  It renders generic fact fields
and provider coverage; root-cause authority remains in the Fact Ledger claim
validator and the machine-verifiable appendix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.core.workflow.schemas import FactLedger, FactRecord


DIMENSION_LABELS = {
    "metrics": "Metrics",
    "logging": "Logging",
    "tracing": "Tracing",
    "kubernetes": "Kubernetes",
    "topology": "Topology",
}

_LOG_TOOLS = frozenset({
    "kubectl_logs",
    "kubectl_previous_logs",
    "kubectl_logs_all_containers",
    "kubectl_previous_logs_all_containers",
    "kubectl_container_logs",
    "kubectl_container_previous_logs",
    "kubectl_logs_grep",
    "kubectl_logs_all_containers_grep",
})
_EMPTY_COVERAGE = frozenset({"empty", "absent", "error", "failed", "weak", "partial"})


def _cell(value: Any) -> str:
    return str(value or "").replace("|", r"\|").replace("\n", " ").strip()


def _bold(value: Any) -> str:
    return f"**{_cell(value)}**"


@dataclass(frozen=True)
class DimensionPresentation:
    dimension: str
    label: str
    state: str
    sources: tuple[str, ...]
    signals: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def render_markdown(self) -> str:
        source = "、".join(self.sources) or "已执行的数据源"
        signal = (
            "<br>".join(self.signals)
            or "查询完成，当前窗口未发现匹配记录"
        )
        state = {
            "present": "已有数据",
            "partial": "部分数据",
            "empty": "查询完成",
        }[self.state]
        return f"| **{self.label}** | {source} | {state} | {signal} |"


def _coverage_state(record: FactRecord) -> str:
    value = record.value
    if isinstance(value, Mapping):
        value = value.get("coverage")
    return str(value or "").strip().lower()


def _fact_signal(record: FactRecord) -> str:
    value = record.value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = None
        if isinstance(decoded, (dict, list)):
            value = decoded

    if isinstance(value, Mapping):
        message = value.get("message") or value.get("observed")
        if message not in (None, ""):
            return _bold(message)

        method = value.get("request_type") or value.get("method")
        resource = (
            value.get("request_resource")
            or value.get("resource")
            or value.get("path")
        )
        if method or resource:
            request = " ".join(
                part for part in (_cell(method), _cell(resource)) if part
            )
            parts = [_bold(request)]
            response = value.get("response_code") or value.get("status_code")
            if response not in (None, ""):
                parts.append(f"响应 {_bold(response)}")
            duration = value.get("duration_us") or value.get("duration_ms")
            if duration not in (None, ""):
                unit = "us" if value.get("duration_us") is not None else "ms"
                parts.append(f"耗时 {_bold(f'{duration} {unit}')}")
            trace_id = value.get("trace_id") or value.get("traceid")
            if trace_id:
                parts.append(f"trace {_bold(trace_id)}")
            return "，".join(parts)

        preferred = (
            "state",
            "status",
            "reason",
            "error",
            "error_code",
            "exit_code",
            "value",
        )
        pairs = [
            (key, value[key])
            for key in preferred
            if key in value and value[key] not in (None, "")
        ]
        if pairs:
            rendered = "，".join(
                f"{_cell(key)}={_bold(item)}" for key, item in pairs
            )
            return (
                f"{_bold(record.entity_name or record.entity_kind)} 的 "
                f"{_bold(record.attribute)}：{rendered}"
            )
        compact = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return (
            f"{_bold(record.entity_name or record.entity_kind)} 的 "
            f"{_bold(record.attribute)} 为 {_bold(compact)}"
        )

    unit = f" {record.unit}" if record.unit else ""
    return (
        f"{_bold(record.entity_name or record.entity_kind)} 的 "
        f"{_bold(record.attribute)} 为 {_bold(f'{value}{unit}')}"
    )


def _observation_log_signal(
    observation: Mapping[str, object],
) -> tuple[str, str, tuple[str, ...]] | None:
    tool = str(observation.get("tool") or "").strip()
    if tool not in _LOG_TOOLS or observation.get("semantic_success") is not True:
        return None
    structured = observation.get("structured")
    if not isinstance(structured, Mapping):
        return None
    selected = structured.get("selected_lines")
    if not isinstance(selected, list):
        return None
    line = next((str(item).strip() for item in selected if str(item).strip()), "")
    if not line:
        return None
    refs = tuple(
        str(observation.get(key)).strip()
        for key in ("raw_ref", "structured_ref", "summary_ref")
        if str(observation.get(key) or "").strip()
    )
    return tool, _bold(line), refs


def build_dimension_presentations(
    ledgers: Sequence[FactLedger],
    observations: Sequence[Mapping[str, object]] = (),
) -> dict[str, DimensionPresentation]:
    """Build display rows by evidence dimension, never by fault name."""
    records: dict[str, list[FactRecord]] = {
        dimension: [] for dimension in DIMENSION_LABELS
    }
    coverage: dict[str, list[str]] = {
        dimension: [] for dimension in DIMENSION_LABELS
    }
    for ledger in ledgers:
        for record in ledger.records:
            dimension = str(record.dimension or "").strip().lower()
            if dimension not in records:
                continue
            if record.fact_type == "coverage":
                coverage[dimension].append(_coverage_state(record))
            else:
                records[dimension].append(record)

    observation_signals: dict[
        str, list[tuple[str, str, tuple[str, ...]]]
    ] = {dimension: [] for dimension in DIMENSION_LABELS}
    for observation in observations:
        if not isinstance(observation, Mapping):
            continue
        signal = _observation_log_signal(observation)
        if signal is not None:
            observation_signals["logging"].append(signal)

    result: dict[str, DimensionPresentation] = {}
    for dimension, label in DIMENSION_LABELS.items():
        dimension_records = records[dimension]
        extra = observation_signals[dimension]
        has_signal = bool(dimension_records or extra)
        states = [state for state in coverage[dimension] if state]
        if has_signal:
            state = (
                "partial"
                if any(item in _EMPTY_COVERAGE for item in states)
                else "present"
            )
        elif states:
            state = "empty"
        else:
            continue

        sources = list(dict.fromkeys([
            *(record.source_system for record in dimension_records),
            *(item[0] for item in extra),
        ]))
        signals = [
            *(_fact_signal(record) for record in dimension_records),
            *(item[1] for item in extra),
        ]
        bounded_signals: list[str] = []
        visible_chars = 0
        for signal in signals:
            remaining = 600 - visible_chars
            if remaining <= 0 or len(bounded_signals) >= 3:
                break
            bounded = signal if len(signal) <= remaining else signal[:remaining].rstrip()
            if bounded:
                bounded_signals.append(bounded)
                visible_chars += len(bounded)
        refs = list(dict.fromkeys([
            *(ref for record in dimension_records for ref in record.evidence_refs),
            *(ref for item in extra for ref in item[2]),
        ]))
        result[dimension] = DimensionPresentation(
            dimension=dimension,
            label=label,
            state=state,
            sources=tuple(sources),
            signals=tuple(bounded_signals),
            evidence_refs=tuple(refs),
        )
    return result


def _record_index(ledgers: Sequence[FactLedger]) -> dict[str, FactRecord]:
    return {
        record.fact_id: record
        for ledger in ledgers
        for record in ledger.records
    }


def _entity_label(record: FactRecord) -> str:
    if record.namespace and record.entity_name:
        return f"{record.namespace}/{record.entity_name}"
    return record.entity_name or record.entity_kind


def render_human_report(
    *,
    model_content: str,
    ledgers: Sequence[FactLedger],
    validated_claim: Mapping[str, Any],
    dimensions: Mapping[str, DimensionPresentation],
) -> str:
    """Render a readable fallback body; grounded model prose is added later."""
    del model_content
    records = _record_index(ledgers)
    non_coverage = [
        record for record in records.values() if record.fact_type != "coverage"
    ]
    first = non_coverage[0] if non_coverage else None
    status = str(validated_claim.get("diagnostic_status") or "inconclusive")
    try:
        confidence = float(validated_claim.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = min(max(confidence, 0.0), 1.0)
    subject = _entity_label(first) if first else "当前诊断对象"

    lines = [
        "# K8s 诊断报告",
        "",
        "## 诊断概览",
        "",
        f"- **诊断状态**：**{status}**",
        f"- **影响对象**：**{subject}**",
        f"- **结论置信度**：**{confidence:.0%}**",
        "",
        "## 现象描述",
        "",
    ]
    if first:
        lines.append(f"- {_fact_signal(first)}。")
    else:
        lines.append("- 当前诊断已完成证据收集，具体信号见下方摘要。")

    lines.extend(["", "## 关键证据", ""])
    key_signals = [
        signal
        for item in dimensions.values()
        for signal in item.signals
    ][:6]
    lines.extend(
        [f"- {signal}" for signal in key_signals]
        or ["- 当前没有可展示的来源证据。"]
    )

    lines.extend([
        "",
        "## 可观测性摘要",
        "",
        "| 维度 | 数据来源 | 状态 | 关键信号 |",
        "|---|---|---|---|",
    ])
    lines.extend(
        item.render_markdown()
        for item in dimensions.values()
        if item.dimension != "topology"
    )

    validation = validated_claim.get("claim_validation")
    if not isinstance(validation, Mapping):
        validation = {}
    supporting_ids = [
        str(item)
        for item in validation.get("valid_supporting_fact_ids", []) or []
        if str(item) in records
    ]
    supporting = [records[item] for item in supporting_ids]
    lines.extend(["", "## 证据关联与因果链", ""])
    if supporting:
        lines.append(
            "- " + " → ".join(_fact_signal(record) for record in supporting)
        )
    else:
        lines.append("- 当前证据用于描述现象，尚未形成可确认的因果链。")

    lines.extend(["", "## 根因结论", ""])
    if status == "diagnosed" and supporting:
        lines.append(
            "- 已验证证据共同指向："
            + "；".join(_fact_signal(record) for record in supporting[:3])
            + "。"
        )
    else:
        lines.append("- 当前证据支持继续按上述关键事实开展人工研判。")

    lines.extend([
        "",
        "## 修复建议",
        "",
        "- 根据根因证据确认变更对象与参数，经人工审批后实施；当前报告不授权写操作。",
        "",
        "## 验证步骤",
        "",
        f"1. 使用只读查询复核 **{subject}** 的当前状态。",
        "2. 重复采集关键证据，确认异常状态或错误不再出现。",
        "3. 对照 Metrics、Logging 与 Tracing 观察恢复后的真实信号。",
        "",
        "## 注意事项",
        "",
        "- 可观测性背景信号用于解释影响范围，只有已验证支持事实进入根因链。",
    ])
    return "\n".join(lines).rstrip() + "\n"
