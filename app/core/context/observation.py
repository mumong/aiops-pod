"""Bounded tool observation processing.

The processor archives full raw tool output, extracts compact structured facts
for known heavy K8s tools, and returns a summary small enough to feed back to the
main agent.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, Optional

import yaml

from app.core.workflow.fact_contract import (
    is_forbidden_fact_key,
    normalize_fact_ledger,
    sanitize_evidence_value,
    validate_canonical_fact_ledger_contract,
)

from .archive import ContextArchive, get_archive_root
from .observability_projection import (
    CONTRACT_VERSION as OBSERVABILITY_PROJECTION_VERSION,
    project_observability_payload,
    render_observability_summary,
)


Summarizer = Callable[[str, str, str], Optional[str]]


class ObservationProcessor:
    RECENT_RESTART_WINDOW_SECONDS = 15 * 60

    HEAVY_TOOLS = {
        "kubectl_get_by_kind_in_cluster",
        "kubectl_get_by_kind_in_namespace",
        "kubectl_get_yaml",
        "kubectl_describe",
        "kubectl_events",
        "kubernetes_jq_query",
        "kubernetes_tabular_query",
    }
    MEDIUM_TOOLS = {
        "kubectl_get_by_name",
        "kubectl_find_resource",
        "kubectl_lineage_children",
        "kubectl_lineage_parents",
        "execute_prometheus_instant_query",
        "get_prometheus_target",
    }
    LOG_TOOLS = {
        "kubectl_logs",
        "kubectl_previous_logs",
        "kubectl_logs_all_containers",
        "kubectl_previous_logs_all_containers",
        "kubectl_container_logs",
        "kubectl_container_previous_logs",
        "kubectl_logs_grep",
        "kubectl_logs_all_containers_grep",
    }
    FULL_PASSTHROUGH_TOOLS = {
        "kubectl_run_image",
        "run_bash_command",
        "fetch_runbook",
    }
    AIOPS_CASE_TOOLS = {
        "collect_aiops_case",
        "get_aiops_case",
        "get_aiops_case_evidence",
        "search_aiops_cases",
    }
    OBSERVABILITY_QUERY_TOOLS = {
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
        "query_pod_topology",
    }
    OBSERVABILITY_QUERY_REQUIRED_FIELDS = {
        "ok",
        "status",
        "source_system",
        "dimension",
        "entity",
        "purpose",
        "coverage",
        "directness",
        "query",
        "facts",
        "samples",
        "evidence_refs",
        "truncated",
        "limits",
    }

    def __init__(
        self,
        archive_root: Optional[str] = None,
        max_observation_chars: int = 3000,
        summarizer: Optional[Summarizer] = None,
        summary_mode: str = "rule",
        context_pressure_threshold: float = 0.8,
    ):
        self.archive_root = archive_root or get_archive_root()
        self.max_observation_chars = max_observation_chars
        self.summarizer = summarizer
        normalized = (summary_mode or "rule").strip().lower()
        self.summary_mode = normalized if normalized in {"rule", "ai"} else "rule"
        self.context_pressure_threshold = float(context_pressure_threshold or 0.8)

    def process(
        self,
        run_id: str,
        node_id: str,
        sequence: int,
        tool_name: str,
        raw_content: str,
        context_usage_ratio: Optional[float] = None,
        tool_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raw = raw_content or ""
        tool = tool_name or "unknown"
        structured: Dict[str, Any]
        summary: str
        processor = "passthrough"
        full_passthrough = tool in self.FULL_PASSTHROUGH_TOOLS

        if full_passthrough:
            structured, _, extracted_processor = self._extract(
                tool,
                raw,
                tool_args=tool_args,
            )
            if tool == "fetch_runbook":
                self._attach_runbook_metadata(structured, tool_args or {})
            summary = raw
            processor = f"{extracted_processor}+passthrough_full"
        else:
            try:
                structured, summary, processor = self._extract(
                    tool,
                    raw,
                    tool_args=tool_args,
                )
                if tool == "fetch_runbook":
                    self._attach_runbook_metadata(structured, tool_args or {})
            except Exception as exc:
                structured = {"status": "extract_failed", "error": str(exc)}
                summary = self._generic_summary(tool, raw)
                processor = "generic"

        semantic_success = self._is_semantically_successful(structured, summary)

        over_context_threshold = (
            context_usage_ratio is not None
            and context_usage_ratio >= self.context_pressure_threshold
        )
        deterministic_summary = (
            tool in self.AIOPS_CASE_TOOLS
            or tool in self.OBSERVABILITY_QUERY_TOOLS
        )
        if deterministic_summary:
            should_llm_summarize = False
        elif full_passthrough:
            should_llm_summarize = over_context_threshold
        else:
            should_llm_summarize = (
                over_context_threshold
                or self.summary_mode == "ai"
                or len(summary) > self.max_observation_chars
            )
        if should_llm_summarize and self.summarizer:
            llm_summary = self.summarizer(tool, raw, summary)
            if llm_summary:
                summary = llm_summary
                processor = f"{processor}+llm_budget" if full_passthrough else f"{processor}+llm"

        if not full_passthrough or should_llm_summarize:
            before_len = len(summary)
            summary = self._bound_summary(summary, raw)
            if over_context_threshold and len(summary) < before_len and "+llm" not in processor:
                processor = f"{processor}+context_guard_truncate"

        archive = ContextArchive(run_id=run_id, root=self.archive_root)
        refs = archive.write_tool_artifact(
            node_id=node_id,
            sequence=sequence,
            tool_name=tool,
            raw=raw,
            structured=structured,
            summary=summary,
        )
        observation_audit: Dict[str, Any] = {}
        if (
            tool in self.OBSERVABILITY_QUERY_TOOLS
            and structured.get("contract_version")
            == OBSERVABILITY_PROJECTION_VERSION
        ):
            truncation = (
                structured.get("truncation")
                if isinstance(structured.get("truncation"), dict)
                else {}
            )
            structured["retrieval"] = {
                "available": True,
                "tool": "read_context_archive",
                "raw_ref": refs.get("raw_ref"),
                "scope": "complete_mcp_response",
                "mcp_response_complete": truncation.get(
                    "mcp_response_truncated"
                )
                is not True,
            }
            summary, observation_audit = render_observability_summary(
                structured,
                self.max_observation_chars,
            )
            structured["agent_projection"] = observation_audit
            # Rewrite the same deterministic artifact paths so structured and
            # summary both carry the retrievable reference Agent actually saw.
            refs = archive.write_tool_artifact(
                node_id=node_id,
                sequence=sequence,
                tool_name=tool,
                raw=raw,
                structured=structured,
                summary=summary,
            )
        return {
            "tool": tool,
            "status": "success",
            "semantic_success": semantic_success,
            "summary": summary,
            "structured": structured,
            "raw_chars": len(raw),
            "summary_chars": len(summary),
            "processed": True,
            "processor": processor,
            "observation_audit": observation_audit,
            "context_usage_ratio": context_usage_ratio,
            **refs,
        }

    def _extract(
        self,
        tool: str,
        raw: str,
        *,
        tool_args: Optional[Dict[str, Any]] = None,
    ) -> tuple[Dict[str, Any], str, str]:
        if tool == "fetch_runbook":
            return self._extract_runbook(raw)
        if re.search(r"is not a valid tool|try one of \[", raw, re.IGNORECASE):
            return {
                "status": "invalid_tool",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "invalid_tool"
        if tool in self.AIOPS_CASE_TOOLS:
            return self._extract_aiops_case(tool, raw)
        if tool in self.OBSERVABILITY_QUERY_TOOLS:
            return self._extract_observability_query(tool, raw)

        # Tool-specific processors must see successful describe/events/log output
        # before generic failure detection. Kubernetes diagnostic payloads often
        # contain strings like `configmap ... not found` inside Events; that is
        # evidence, not a failed tool invocation.
        if tool == "kubectl_events":
            return self._extract_events(raw)
        if tool == "kubectl_describe":
            return self._extract_describe(raw, tool_args=tool_args)
        if tool in self.LOG_TOOLS:
            return self._extract_logs(tool, raw)

        if self._is_command_failure(raw):
            return {
                "status": "command_failed",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "generic_failure"
        if re.search(r"^\s*no resources found", raw, re.IGNORECASE):
            return {
                "status": "empty",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, "工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。", "generic_empty"

        if tool == "kubectl_get_yaml":
            return self._extract_yaml(raw)
        if tool == "kubectl_run_image":
            return self._extract_run_image(raw)
        if tool == "run_bash_command":
            return self._extract_command_result(tool, raw)
        if tool in {"execute_prometheus_instant_query", "execute_prometheus_range_query"}:
            return self._extract_prometheus_result(tool, raw)
        if tool in {"kubectl_get_by_kind_in_cluster", "kubectl_get_by_kind_in_namespace", "kubernetes_tabular_query"}:
            if self._looks_like_secret_table(raw):
                return self._extract_secret_table(tool, raw)
            return self._extract_table(tool, raw)
        if tool == "kubernetes_jq_query":
            return self._extract_jq(raw)

        if tool in self.MEDIUM_TOOLS and len(raw) <= self.max_observation_chars:
            return {"status": "kept_small_output"}, raw, "passthrough"
        return {"status": "generic_summary"}, self._generic_summary(tool, raw), "generic"

    def _extract_observability_query(
        self,
        tool: str,
        raw: str,
    ) -> tuple[Dict[str, Any], str, str]:
        try:
            payload = json.loads(raw or "{}")
        except Exception:
            return {
                "status": "query_parse_failed",
                "tool": tool,
                "coverage": "error",
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "observability_query_parse_failed"

        if not isinstance(payload, dict):
            return {
                "status": "query_parse_failed",
                "tool": tool,
                "coverage": "error",
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "observability_query_parse_failed"

        contract_errors = self._observability_query_contract_errors(payload)
        normalized_ledger = None
        if not contract_errors and "fact_ledger" in payload:
            ledger_input = payload.get("fact_ledger")
            normalized_ledger, ledger_reasons = (
                validate_canonical_fact_ledger_contract(
                    ledger_input
                    if isinstance(ledger_input, dict)
                    else {}
                )
            )
            if normalized_ledger is None:
                contract_errors.append(
                    "invalid_fact_ledger="
                    + ",".join(ledger_reasons)
                )
        if contract_errors:
            structured = {
                "status": "query_parse_failed",
                "tool": tool,
                "coverage": "error",
                "contract_errors": contract_errors,
                "raw_preview": raw[:1000],
            }
            return (
                structured,
                (
                    f"{tool} 返回不完整或无效的 MCP contract: "
                    + "; ".join(contract_errors)
                ),
                "observability_query_parse_failed",
            )

        projection = project_observability_payload(
            payload,
            tool=tool,
            max_chars=self.max_observation_chars,
        )
        return (
            projection["structured"],
            projection["summary"],
            "observability_query",
        )

    @classmethod
    def _has_source_backed_observability_fact(
        cls,
        payload: Dict[str, Any],
    ) -> bool:
        default_source = str(payload.get("source_system") or "").strip()
        for fact in payload.get("evidence") or []:
            if not isinstance(fact, dict):
                continue
            refs = fact.get("evidence_refs") or []
            if fact.get("id"):
                refs = [*refs, fact.get("id")]
            if any(str(ref or "").strip() for ref in refs) and str(
                fact.get("source_system") or default_source
            ).strip():
                return True
        for fact in payload.get("facts") or []:
            if not isinstance(fact, dict):
                continue
            refs = [
                fact.get("ref"),
                fact.get("evidence_ref"),
            ]
            if isinstance(fact.get("evidence_refs"), list):
                refs.extend(fact["evidence_refs"])
            has_ref = any(str(ref or "").strip() for ref in refs)
            source_system = str(
                fact.get("source_system") or default_source
            ).strip()
            if has_ref and source_system:
                return True
        return False

    @classmethod
    def _observability_query_contract_errors(
        cls,
        payload: Dict[str, Any],
    ) -> list[str]:
        missing = sorted(cls.OBSERVABILITY_QUERY_REQUIRED_FIELDS - payload.keys())
        errors = [f"missing={','.join(missing)}"] if missing else []

        expected_types = {
            "ok": bool,
            "status": str,
            "source_system": str,
            "dimension": str,
            "entity": dict,
            "purpose": str,
            "coverage": str,
            "directness": str,
            "query": dict,
            "facts": list,
            "samples": list,
            "evidence_refs": list,
            "truncated": bool,
            "limits": dict,
        }
        for field, expected_type in expected_types.items():
            if field in payload and not isinstance(payload[field], expected_type):
                errors.append(f"{field}_type={type(payload[field]).__name__}")

        coverage = payload.get("coverage")
        if coverage is not None and coverage not in {
            "present",
            "empty",
            "absent",
            "weak",
            "partial",
            "error",
        }:
            errors.append(f"coverage={coverage}")
        directness = payload.get("directness")
        if directness is not None and directness not in {
            "direct",
            "related_context",
        }:
            errors.append(f"directness={directness}")

        status = str(payload.get("status") or "").strip()
        if status == "query_partial":
            if payload.get("ok") is True and "error" in payload:
                errors.append("error_present_for_success")
            if (
                coverage != "partial"
                or not cls._has_source_backed_observability_fact(
                    payload
                )
            ):
                errors.append("invalid_partial_contract")
        elif payload.get("ok") is False:
            error = payload.get("error")
            if (
                status != "query_rejected"
                or coverage != "error"
                or not isinstance(error, dict)
                or not str(error.get("code") or "").strip()
                or not str(error.get("message") or "").strip()
            ):
                errors.append("invalid_rejection_contract")
        elif payload.get("ok") is True:
            if "error" in payload:
                errors.append("error_present_for_success")
            if (
                status != "query_succeeded"
                or coverage in {"partial", "error"}
            ):
                errors.append("invalid_success_contract")

        return errors

    def _extract_aiops_case(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        try:
            payload = json.loads(raw or "{}")
        except Exception:
            return {
                "status": "case_parse_failed",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "aiops_case_parse_failed"

        if not isinstance(payload, dict):
            return {
                "status": "case_parse_failed",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "aiops_case_parse_failed"

        if payload.get("ok") is False:
            error = str(payload.get("error") or "aiops case tool returned ok=false")
            structured = {
                "status": "case_error",
                "tool": tool,
                "error": error,
            }
            if payload.get("case_id"):
                structured["case_id"] = payload.get("case_id")
            return structured, f"{tool} 采集失败: {error}", "aiops_case_error"

        if tool == "search_aiops_cases":
            cases = payload.get("cases") if isinstance(payload.get("cases"), list) else []
            structured = {
                "status": "case_search_result",
                "tool": tool,
                "total": payload.get("total", len(cases)),
                "cases": [
                    self._select_keys(item, ["case_id", "abnormal_type", "namespace", "pod", "package_ref"])
                    for item in cases[:20]
                    if isinstance(item, dict)
                ],
            }
            lines = [
                f"{tool} 摘要: total={structured['total']} returned={len(structured['cases'])}",
            ]
            for item in structured["cases"][:10]:
                lines.append(
                    "- case_id={case_id} abnormal_type={abnormal_type} pod={namespace}/{pod}".format(
                        case_id=item.get("case_id", ""),
                        abnormal_type=item.get("abnormal_type", ""),
                        namespace=item.get("namespace", ""),
                        pod=item.get("pod", ""),
                    )
                )
            return structured, "\n".join(lines), "aiops_case"

        if tool == "get_aiops_case_evidence":
            structured = {
                "status": "case_evidence_loaded",
                "tool": tool,
                "case_id": payload.get("case_id"),
                "ref": payload.get("ref"),
                "truncated": payload.get("truncated"),
            }
            if isinstance(payload.get("record"), dict):
                record = payload["record"]
                structured["record"] = self._select_keys(
                    record,
                    [
                        "evidence_id",
                        "timestamp",
                        "source_system",
                        "dimension",
                        "summary",
                        "severity",
                        "confidence",
                        "directness",
                        "trace_correlation",
                    ],
                )
                evidence_payload = self._sanitize_aiops_evidence_payload(
                    str(record.get("dimension") or ""),
                    record.get("payload"),
                )
                if evidence_payload:
                    structured["record"]["payload"] = evidence_payload
            content = str(payload.get("content") or "").strip()
            if content:
                structured["content_chars"] = len(content)
            lines = [
                f"{tool} 摘要: case_id={structured.get('case_id')} ref={structured.get('ref')}",
            ]
            if structured.get("truncated") is not None:
                lines.append(f"truncated={structured.get('truncated')}")
            if structured.get("record"):
                lines.append("record=" + json.dumps(structured["record"], ensure_ascii=False, default=str))
            elif content:
                lines.append(f"content_chars={len(content)}")
                lines.append("content omitted from prompt; use evidence_id records or an approved evidence ref, not evaluator files.")
            return structured, "\n".join(lines), "aiops_case"

        primary = payload.get("primary_entity") if isinstance(payload.get("primary_entity"), dict) else {}
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        topology = payload.get("topology_summary") if isinstance(payload.get("topology_summary"), dict) else {}
        evidence_refs = [
            str(ref)
            for ref in (payload.get("evidence_refs") or [])
            if ref
        ][:30]
        signals = [
            self._select_keys(item, ["signal_id", "dimension", "strength", "observed", "evidence_refs"])
            for item in (payload.get("signals_summary") or [])[:12]
            if isinstance(item, dict)
        ]
        timeline = [
            self._select_keys(item, ["timestamp", "dimension", "summary", "evidence_refs"])
            for item in (payload.get("timeline_summary") or [])[:12]
            if isinstance(item, dict)
        ]
        inventory = [
            self._select_keys(item, ["ref", "exists", "bytes", "records"])
            for item in (payload.get("evidence_inventory") or [])[:20]
            if isinstance(item, dict)
        ]
        recommended_refs = payload.get("recommended_refs_by_dimension")
        if not isinstance(recommended_refs, dict):
            recommended_refs = {}
        recommended_refs = {
            str(key): [str(ref) for ref in value[:8] if ref]
            for key, value in recommended_refs.items()
            if isinstance(value, list)
        }
        dimension_details = self._sanitize_aiops_dimension_details(payload.get("dimension_details"))
        fact_ledger = normalize_fact_ledger(payload.get("fact_ledger"))
        status = "case_collected" if tool == "collect_aiops_case" else "case_loaded"
        structured = {
            "status": status,
            "tool": tool,
            "case_id": payload.get("case_id"),
            "abnormal_type": payload.get("abnormal_type"),
            "scenario": payload.get("scenario"),
            "primary_entity": self._select_keys(primary, ["kind", "namespace", "name", "uid", "node", "pod_ip"]),
            "coverage": sanitize_evidence_value(coverage),
            "signals_summary": signals,
            "timeline_summary": timeline,
            "topology_summary": self._select_keys(
                topology,
                ["entity_count", "edge_count", "entity_kinds", "relations", "directness", "confidence"],
            ),
            "dimension_details": dimension_details,
            "evidence_inventory": inventory,
            "evidence_refs": evidence_refs,
            "recommended_refs_by_dimension": recommended_refs,
            "package_ref": payload.get("package_ref"),
        }
        if fact_ledger is not None:
            structured["fact_ledger"] = fact_ledger.model_dump(
                mode="json",
                exclude_none=True,
            )

        summary = self._build_aiops_case_prompt_summary(structured)
        return structured, summary, "aiops_case"

    def _build_aiops_case_prompt_summary(self, structured: Dict[str, Any]) -> str:
        """Render deterministic high-value facts for the evidence agent.

        This summary is itself a control boundary. It must preserve source-
        specific trace IDs and exact topology relationships, so it is not sent
        through another LLM summarizer.
        """
        details = structured.get("dimension_details")
        if not isinstance(details, dict):
            details = {}
        primary = structured.get("primary_entity")
        if not isinstance(primary, dict):
            primary = {}
        coverage = structured.get("coverage")
        if not isinstance(coverage, dict):
            coverage = {}

        lines: list[str] = []

        def compact(value: Any, limit: int = 120) -> str:
            if value is None:
                text = ""
            elif isinstance(value, bool):
                text = str(value).lower()
            else:
                text = str(value)
            text = text.replace("\n", " ").strip()
            return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."

        def add(line: str) -> None:
            if not line:
                return
            projected = len("\n".join([*lines, line]))
            if projected <= self.max_observation_chars:
                lines.append(line)

        case_id = compact(structured.get("case_id"), 160)
        abnormal_type = compact(structured.get("abnormal_type"), 60)
        add(
            f"AIOPS_CASE case_id={case_id} status={structured.get('status')} "
            f"abnormal_type={abnormal_type} {structured.get('tool')} 摘要"
        )
        add(
            "ENTITY entity={kind} {namespace}/{name} node={node} pod_ip={pod_ip}".format(
                kind=compact(primary.get("kind"), 30),
                namespace=compact(primary.get("namespace"), 80),
                name=compact(primary.get("name"), 100),
                node=compact(primary.get("node"), 60),
                pod_ip=compact(primary.get("pod_ip"), 60),
            )
        )
        coverage_text = " ".join(f"{key}={value}" for key, value in sorted(coverage.items()))
        add(f"COVERAGE {coverage_text or '-'}")

        signals = structured.get("signals_summary")
        if isinstance(signals, list):
            for item in signals:
                if not isinstance(item, dict):
                    continue
                dimension = str(item.get("dimension") or "").strip().lower()
                strength = str(item.get("strength") or "").strip().lower()
                observed = item.get("observed")
                if (
                    dimension not in {"k8s", "kubernetes"}
                    or strength not in {"strong", "critical"}
                    or not isinstance(observed, str)
                    or not observed.strip()
                ):
                    continue
                refs = [
                    str(ref)
                    for ref in (item.get("evidence_refs") or [])[:5]
                    if ref
                ]
                add(
                    "K8S_SIGNAL strength={strength} observed={observed} evidence_refs={refs}".format(
                        strength=compact(strength, 20),
                        observed=json.dumps(compact(observed, 240), ensure_ascii=False),
                        refs=json.dumps(refs, ensure_ascii=False, separators=(",", ":")),
                    )
                )
                break

        metrics = details.get("metrics") if isinstance(details.get("metrics"), dict) else {}
        for item in (metrics.get("highlights") or [])[:1]:
            if not isinstance(item, dict):
                continue
            add(
                "METRIC metric={metric} start={start} max={max} last={last} limit={limit} "
                "ratio={ratio}".format(
                    metric=compact(item.get("metric"), 80),
                    start=compact(item.get("start"), 30),
                    max=compact(item.get("max"), 30),
                    last=compact(item.get("last"), 30),
                    limit=compact(item.get("limit"), 30),
                    ratio=compact(item.get("max_limit_ratio"), 30),
                )
            )

        logs = details.get("logs") if isinstance(details.get("logs"), dict) else {}
        log_trace_ids: set[str] = set()
        for item in (logs.get("samples") or [])[:1]:
            if not isinstance(item, dict):
                continue
            message = str(item.get("message") or "")
            parsed: Dict[str, Any] = {}
            try:
                decoded = json.loads(message)
                if isinstance(decoded, dict):
                    parsed = decoded
            except json.JSONDecodeError:
                parsed = {}
            trace_id = str(parsed.get("trace_id") or "")
            if trace_id:
                log_trace_ids.add(trace_id)
            log_fields = [
                ("event", parsed.get("event")),
                ("trace_id", trace_id),
                ("path", parsed.get("path") or message),
                ("error_code", parsed.get("error_code")),
                ("missing_config", parsed.get("missing_config")),
                ("http_status", parsed.get("http_status")),
                ("exit_code", parsed.get("exit_code")),
                ("alloc_mib", parsed.get("alloc_mib")),
                ("allocated_mib", parsed.get("allocated_mib")),
            ]
            add("LOG " + " ".join(
                f"{key}={compact(value, 120)}"
                for key, value in log_fields
                if value is not None and value != ""
            ))

        tracing = details.get("tracing") if isinstance(details.get("tracing"), dict) else {}
        flows = [item for item in (tracing.get("flows") or []) if isinstance(item, dict)]
        spans = [item for item in (tracing.get("spans") or []) if isinstance(item, dict)]
        deepflow_trace_ids = {
            str(item.get("trace_id"))
            for item in flows
            if item.get("trace_id")
        }
        tempo_trace_ids = {
            str(item.get("trace_id"))
            for item in spans
            if item.get("trace_id")
        }
        log_tempo_trace_ids = sorted(log_trace_ids & tempo_trace_ids)
        source_trace_sets = [
            trace_ids
            for trace_ids in (
                log_trace_ids,
                tempo_trace_ids,
                deepflow_trace_ids,
            )
            if trace_ids
        ]
        do_not_merge = (
            len(source_trace_sets) >= 2
            and any(
                trace_ids != source_trace_sets[0]
                for trace_ids in source_trace_sets[1:]
            )
        )
        if log_tempo_trace_ids or deepflow_trace_ids:
            add(
                "TRACE_CORRELATION log_tempo_trace_id={log_tempo} "
                "deepflow_trace_id={deepflow} do_not_merge={do_not_merge}".format(
                    log_tempo=",".join(log_tempo_trace_ids) or "-",
                    deepflow=",".join(sorted(deepflow_trace_ids)) or "-",
                    do_not_merge=str(do_not_merge).lower(),
                )
            )

        for item in flows[:1]:
            add(
                "DEEPFLOW src={src} dst={dst} request={request} response_code={code} "
                "duration_us={duration} trace_id={trace_id}".format(
                    src=compact(item.get("src"), 60),
                    dst=compact(item.get("dst"), 60),
                    request=compact(item.get("request"), 120),
                    code=compact(item.get("response_code"), 30),
                    duration=compact(item.get("duration_us"), 30),
                    trace_id=compact(item.get("trace_id"), 64),
                )
            )
        if any(str(item.get("duration_us") or "").strip() in {"0", "0.0"} for item in flows):
            add("DEEPFLOW_SEMANTICS duration_us=0 is_not_failure_evidence=true")

        for item in spans[:1]:
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            span_fields = [
                ("trace_id", item.get("trace_id")),
                ("service", item.get("service")),
                ("span", item.get("name")),
                ("http.response.status_code", attrs.get("http.response.status_code")),
                ("error.type", attrs.get("error.type")),
                ("config.key", attrs.get("config.key")),
                ("config.present", attrs.get("config.present")),
                ("allocated_before", attrs.get("aiops.allocated_mib.before")),
                ("allocated_after", attrs.get("aiops.allocated_mib.after")),
            ]
            add("TEMPO " + " ".join(
                f"{key}={compact(value, 120)}"
                for key, value in span_fields
                if value is not None and value != ""
            ))

        complete = self._aiops_case_dimensions_complete(coverage)
        add(
            "DIMENSION_DETAILS complete={complete} action={action}".format(
                complete=str(complete).lower(),
                action=(
                    "post_case_reconciliation"
                    if complete
                    else "supplement_missing_dimensions"
                ),
            )
        )
        add("REF_POLICY do_not_guess_evidence_refs=true")

        topology = details.get("topology") if isinstance(details.get("topology"), dict) else {}
        topology_edges = [
            item
            for item in (topology.get("edges") or [])[:8]
            if isinstance(item, dict)
        ]

        def add_topology_edge(item: Dict[str, Any]) -> None:
            relationship = json.dumps(str(item.get("relationship") or ""), ensure_ascii=False)
            add(
                "TOPOLOGY relationship={relationship} source={source} target={target} "
                "directness={directness} confidence={confidence}".format(
                    relationship=relationship,
                    source=compact(item.get("source"), 90),
                    target=compact(item.get("target"), 90),
                    directness=compact(item.get("directness"), 30),
                    confidence=compact(item.get("confidence"), 30),
                )
            )

        for item in topology_edges[:4]:
            add_topology_edge(item)

        recommended = structured.get("recommended_refs_by_dimension")
        if isinstance(recommended, dict) and recommended:
            add(
                "recommended_refs_by_dimension="
                + compact(json.dumps(recommended, ensure_ascii=False, separators=(",", ":")), 500)
            )

        for item in topology_edges[4:]:
            add_topology_edge(item)

        topology_summary = structured.get("topology_summary")
        if isinstance(topology_summary, dict):
            add(
                "TOPOLOGY_SUMMARY directness={directness} confidence={confidence}".format(
                    directness=topology_summary.get("directness", {}),
                    confidence=topology_summary.get("confidence", {}),
                )
            )

        return "\n".join(lines)

    @staticmethod
    def _aiops_case_dimensions_complete(coverage: Dict[str, Any]) -> bool:
        present = {"present", "observed"}

        def status(*keys: str) -> str:
            for key in keys:
                if key in coverage:
                    return str(coverage.get(key) or "").strip().lower()
            return ""

        required_statuses = [
            status("k8s", "kubernetes"),
            status("metrics"),
            status("logs", "logging"),
            status("tracing"),
            status("topology"),
        ]
        if "trace" in coverage:
            required_statuses.append(status("trace"))
        return bool(required_statuses) and all(item in present for item in required_statuses)

    def _sanitize_aiops_dimension_details(self, value: Any) -> Dict[str, Any]:
        sanitized = sanitize_evidence_value(value)
        details = sanitized if isinstance(sanitized, dict) else {}
        metrics = details.get("metrics") if isinstance(details.get("metrics"), dict) else {}
        logs = details.get("logs") if isinstance(details.get("logs"), dict) else {}
        tracing = details.get("tracing") if isinstance(details.get("tracing"), dict) else {}
        topology = details.get("topology") if isinstance(details.get("topology"), dict) else {}
        return {
            "metrics": {
                "coverage": metrics.get("coverage"),
                "highlights": [
                    self._select_keys(
                        item,
                        [
                            "metric", "pod", "container", "start", "max", "last",
                            "limit", "max_limit_ratio", "samples", "evidence_ref",
                        ],
                    )
                    for item in (metrics.get("highlights") or [])[:5]
                    if isinstance(item, dict)
                ],
            },
            "logs": {
                "coverage": logs.get("coverage"),
                "samples": [
                    self._select_keys(
                        item,
                        ["timestamp", "message", "container", "role", "evidence_ref"],
                    )
                    for item in (logs.get("samples") or [])[:8]
                    if isinstance(item, dict)
                ],
            },
            "tracing": {
                "coverage": tracing.get("coverage"),
                "deepflow_coverage": tracing.get("deepflow_coverage"),
                "tempo_coverage": tracing.get("tempo_coverage"),
                "flows": [
                    self._select_keys(
                        item,
                        [
                            "timestamp", "src", "dst", "protocol", "request",
                            "response_code", "duration_us", "trace_id", "span_id",
                            "evidence_ref",
                        ],
                    )
                    for item in (tracing.get("flows") or [])[:5]
                    if isinstance(item, dict)
                ],
                "spans": [
                    {
                        **self._select_keys(
                            item,
                            ["trace_id", "service", "name", "start", "end", "evidence_ref"],
                        ),
                        "attributes": self._sanitize_scalar_mapping(item.get("attributes"), max_items=8),
                    }
                    for item in (tracing.get("spans") or [])[:3]
                    if isinstance(item, dict)
                ],
                "call_chains": [
                    {
                        **self._select_keys(item, ["syscall_trace_id", "hop_count", "evidence_ref"]),
                        "hops": [
                            self._select_keys(
                                hop,
                                ["src", "dst", "proto", "endpoint", "code", "duration_us"],
                            )
                            for hop in (item.get("hops") or [])[:5]
                            if isinstance(hop, dict)
                        ],
                    }
                    for item in (tracing.get("call_chains") or [])[:3]
                    if isinstance(item, dict)
                ],
            },
            "topology": {
                "coverage": topology.get("coverage"),
                "entities": [
                    {
                        **self._select_keys(
                            item,
                            ["entity_id", "kind", "namespace", "name", "evidence_refs"],
                        ),
                        "attributes": self._sanitize_scalar_mapping(item.get("attributes"), max_items=8),
                    }
                    for item in (topology.get("entities") or [])[:10]
                    if isinstance(item, dict)
                ],
                "edges": [
                    self._select_keys(
                        item,
                        [
                            "relationship", "source", "target", "source_system",
                            "directness", "confidence", "evidence_refs",
                        ],
                    )
                    for item in (topology.get("edges") or [])[:12]
                    if isinstance(item, dict)
                ],
            },
        }

    def _sanitize_aiops_evidence_payload(self, dimension: str, value: Any) -> Dict[str, Any]:
        sanitized = sanitize_evidence_value(value)
        payload = sanitized if isinstance(sanitized, dict) else {}
        if dimension == "metrics":
            return self._sanitize_aiops_dimension_details(
                {"metrics": {"highlights": payload.get("highlights") or []}}
            )["metrics"]
        if dimension in {"logs", "caller_logs"}:
            result = self._sanitize_aiops_dimension_details(
                {"logs": {"samples": payload.get("samples") or []}}
            )["logs"]
            if payload.get("log_preview"):
                result["log_preview"] = str(payload["log_preview"])[-2000:]
            return result
        if dimension == "tracing":
            tracing = self._sanitize_aiops_dimension_details(
                {
                    "tracing": {
                        "flows": payload.get("samples") or [],
                        "call_chains": payload.get("call_chains") or [],
                    }
                }
            )["tracing"]
            return {"samples": tracing["flows"], "call_chains": tracing["call_chains"]}
        if dimension == "trace":
            tracing = self._sanitize_aiops_dimension_details(
                {"tracing": {"spans": payload.get("spans") or []}}
            )["tracing"]
            return {"spans": tracing["spans"]}
        if dimension == "k8s":
            return {
                key: payload[key]
                for key in ("last_terminated", "events_preview", "log_preview")
                if key in payload
            }
        return {}

    @staticmethod
    def _sanitize_scalar_mapping(value: Any, max_items: int) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        result: Dict[str, Any] = {}
        for key, item in list(value.items())[:max_items]:
            if is_forbidden_fact_key(key):
                continue
            if isinstance(item, str):
                result[str(key)] = item[:200]
            elif isinstance(item, (int, float, bool)) or item is None:
                result[str(key)] = item
            else:
                result[str(key)] = str(item)[:200]
        return result

    @staticmethod
    def _aiops_dimension_detail_lines(details: Dict[str, Any]) -> list[str]:
        lines = ["dimension_details（真实可观测性原始信号）:"]
        metrics = details.get("metrics") or {}
        lines.append(f"- Metrics coverage={metrics.get('coverage')}")
        for item in (metrics.get("highlights") or [])[:3]:
            lines.append(
                "  metric={metric} container={container} start={start} max={max} "
                "last={last} limit={limit} ratio={ratio} samples={samples} ref={ref}".format(
                    metric=item.get("metric", ""),
                    container=item.get("container", ""),
                    start=item.get("start", ""),
                    max=item.get("max", ""),
                    last=item.get("last", ""),
                    limit=item.get("limit", ""),
                    ratio=item.get("max_limit_ratio", ""),
                    samples=item.get("samples", []),
                    ref=item.get("evidence_ref", ""),
                )
            )
        logs = details.get("logs") or {}
        lines.append(f"- Logging coverage={logs.get('coverage')}")
        for item in (logs.get("samples") or [])[:4]:
            lines.append(
                f"  {item.get('timestamp', '')} container={item.get('container', '')} "
                f"message={item.get('message', '')} ref={item.get('evidence_ref', '')}"
            )
        tracing = details.get("tracing") or {}
        lines.append(
            f"- Tracing coverage={tracing.get('coverage')} "
            f"deepflow={tracing.get('deepflow_coverage')} tempo={tracing.get('tempo_coverage')}"
        )
        for item in (tracing.get("flows") or [])[:3]:
            lines.append(
                f"  flow {item.get('src', '')}->{item.get('dst', '')} "
                f"{item.get('protocol', '')} {item.get('request', '')} "
                f"code={item.get('response_code', '')} duration_us={item.get('duration_us', '')} "
                f"trace_id={item.get('trace_id', '')} ref={item.get('evidence_ref', '')}"
            )
        for item in (tracing.get("spans") or [])[:2]:
            lines.append(
                f"  span trace_id={item.get('trace_id', '')} service={item.get('service', '')} "
                f"name={item.get('name', '')} attributes={item.get('attributes', {})} "
                f"ref={item.get('evidence_ref', '')}"
            )
        topology = details.get("topology") or {}
        lines.append(f"- Topology coverage={topology.get('coverage')}")
        for item in (topology.get("edges") or [])[:5]:
            lines.append(
                f"  {item.get('source', '')}: {item.get('relationship', '')} -> {item.get('target', '')} "
                f"directness={item.get('directness', '')} confidence={item.get('confidence', '')} "
                f"refs={item.get('evidence_refs', [])}"
            )
        return lines

    @staticmethod
    def _select_keys(payload: Dict[str, Any], keys: list[str]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        selected = {
            key: payload[key]
            for key in keys
            if (
                key in payload
                and payload.get(key) is not None
                and not is_forbidden_fact_key(key)
            )
        }
        sanitized = sanitize_evidence_value(selected)
        return sanitized if isinstance(sanitized, dict) else {}

    def _extract_runbook(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        if re.match(r"^\s*Error:\s*Runbook\b", raw or "", re.IGNORECASE):
            return {
                "status": "command_failed",
                "tool": "fetch_runbook",
                "raw_preview": raw[:1000],
            }, self._generic_summary("fetch_runbook", raw), "runbook"

        title = None
        match = re.search(r"^\s*#\s+(.+)$", raw or "", re.MULTILINE)
        if match:
            title = match.group(1).strip()
        return {
            "status": "runbook_loaded",
            "title": title,
            "raw_chars": len(raw or ""),
        }, raw, "runbook"

    @staticmethod
    def _attach_runbook_metadata(structured: Dict[str, Any], tool_args: Dict[str, Any]) -> None:
        runbook_id = str((tool_args or {}).get("runbook_id") or "").strip()
        if not runbook_id:
            return
        structured["runbook_id"] = runbook_id
        structured["runbook_name"] = runbook_id[:-3] if runbook_id.endswith(".md") else runbook_id

    def _extract_events(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        if self._is_command_failure(raw):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary("kubectl_events", raw), "k8s_events"
        if re.search(r"no events found|no resources found", raw, re.IGNORECASE):
            structured = {"status": "no_events_found", "warnings": []}
            return structured, "工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。", "k8s_events"

        lines = [ln for ln in raw.splitlines() if ln.strip()]
        diagnostic_lines = self._extract_diagnostic_lines(raw, limit=20)
        warning_lines = [ln for ln in lines if re.search(r"\bWarning\b|Failed|BackOff|x509|ErrImagePull|ImagePullBackOff", ln)]
        selected = diagnostic_lines or warning_lines[:20] or lines[:20]
        structured = {
            "status": "events_found",
            "warning_count": len(warning_lines),
            "selected_events": selected,
            "key_events": diagnostic_lines,
        }
        summary_lines = ["kubectl_events 摘要:"]
        if diagnostic_lines:
            summary_lines.append("关键诊断行:")
            summary_lines.extend(diagnostic_lines)
            remaining = [ln for ln in selected if ln not in diagnostic_lines]
            if remaining:
                summary_lines.append("其他事件:")
                summary_lines.extend(remaining)
        else:
            summary_lines.extend(selected)
        summary = "\n".join(summary_lines)
        return structured, summary, "k8s_events"

    def _extract_describe(
        self,
        raw: str,
        *,
        tool_args: Optional[Dict[str, Any]] = None,
    ) -> tuple[Dict[str, Any], str, str]:
        if self._is_command_failure(raw):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary("kubectl_describe", raw), "k8s_describe"

        fields = {}
        for key in ["Name", "Namespace", "Node", "Status", "Reason", "Message"]:
            match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.MULTILINE)
            if match:
                fields[key.lower()] = match.group(1).strip()

        pod_sections = self._extract_describe_pod_sections(raw)
        interesting = []
        for line in raw.splitlines():
            if re.search(r"aiops\.e2e/expected-", line, re.IGNORECASE):
                continue
            if re.search(
                r"State:|Last State:|Reason:|Exit Code:|Warning|Failed|BackOff|"
                r"ImagePullBackOff|ErrImagePull|CrashLoopBackOff|OOMKilled|"
                r"FailedScheduling|MountVolume|x509|NotReady|"
                r"Termination Grace Period:|Command:|Args:|Restart Count:",
                line,
            ):
                interesting.append(line.rstrip())
        diagnostic_lines = self._extract_diagnostic_lines(raw, limit=40)
        merged_signals = self._dedupe_lines([
            *diagnostic_lines,
            *interesting,
            *pod_sections.get("signals", []),
        ])

        primary_entity: Dict[str, Any] = {}
        pod_name = str(fields.get("name") or "").strip()
        namespace = str(fields.get("namespace") or "").strip()
        if (
            pod_name
            and namespace
            and self._is_exact_pod_request(tool_args)
        ):
            primary_entity = {
                "kind": "Pod",
                "namespace": namespace,
                "name": pod_name,
            }
            pod_uid = self._extract_describe_pod_uid(
                raw,
                pod_name=pod_name,
                namespace=namespace,
            )
            if pod_uid:
                primary_entity["uid"] = pod_uid

        structured = {
            **fields,
            **(
                {"primary_entity": primary_entity}
                if primary_entity
                else {}
            ),
            "lifecycle": pod_sections.get("lifecycle", {}),
            "containers": pod_sections.get("containers", []),
            "scheduling": pod_sections.get("scheduling", {}),
            "volumes": pod_sections.get("volumes", []),
            "events": pod_sections.get("events", []),
            "signals": merged_signals[:80],
            "key_events": diagnostic_lines,
        }
        summary_lines = [
            "kubectl_describe 摘要:",
            *[f"{k}: {v}" for k, v in fields.items()],
        ]
        if diagnostic_lines:
            summary_lines.append("关键诊断行:")
            summary_lines.extend(diagnostic_lines[:40])
        section_summary = pod_sections.get("summary_lines") or []
        if section_summary:
            summary_lines.append("Pod 关键区块:")
            summary_lines.extend(section_summary[:80])
        if interesting:
            summary_lines.append("关键状态/事件:")
            section_seen = set(section_summary)
            summary_lines.extend([
                ln for ln in interesting[:40]
                if ln not in diagnostic_lines and ln not in section_seen
            ])
        return structured, "\n".join(summary_lines), "k8s_describe"

    @staticmethod
    def _is_exact_pod_request(
        tool_args: Optional[Dict[str, Any]],
    ) -> bool:
        if not isinstance(tool_args, dict):
            return False
        kind = str(
            tool_args.get("kind")
            or tool_args.get("resource_kind")
            or tool_args.get("resource_type")
            or ""
        ).strip().lower()
        namespace = str(tool_args.get("namespace") or "").strip()
        name = str(
            tool_args.get("pod")
            or tool_args.get("pod_name")
            or tool_args.get("name")
            or tool_args.get("resource_name")
            or ""
        ).strip()
        return kind in {"pod", "pods", "po"} and bool(
            namespace and name
        )

    @staticmethod
    def _extract_describe_pod_uid(
        raw: str,
        *,
        pod_name: str,
        namespace: str,
    ) -> str:
        direct_match = re.search(
            r"^UID:\s*([A-Za-z0-9][A-Za-z0-9._-]{7,127})\s*$",
            raw,
            re.MULTILINE,
        )
        candidates = (
            {direct_match.group(1)}
            if direct_match
            else set()
        )

        event_pattern = re.compile(
            rf"\bpod\s+{re.escape(pod_name)}_{re.escape(namespace)}"
            r"\(([A-Za-z0-9][A-Za-z0-9._-]{7,127})\)",
            re.IGNORECASE,
        )
        candidates.update(event_pattern.findall(raw))
        return next(iter(candidates)) if len(candidates) == 1 else ""

    @classmethod
    def _extract_describe_pod_sections(cls, raw: str) -> Dict[str, Any]:
        """Extract stable high-value sections from `kubectl describe pod`.

        Describe output is not YAML, but its Pod sections map closely to
        metadata/spec/status/events. Keep only compact fields that help classify
        root cause; raw output remains archived for full detail.
        """
        lifecycle: Dict[str, Any] = {}
        scheduling: Dict[str, Any] = {}
        signals: list[str] = []
        summary_lines: list[str] = []

        field_map = {
            "Termination Grace Period": ("termination_grace_period", lifecycle),
            "Controlled By": ("controlled_by", lifecycle),
            "QoS Class": ("qos_class", lifecycle),
            "Node-Selectors": ("node_selectors", scheduling),
            "Tolerations": ("tolerations", scheduling),
        }
        for label, (key, target) in field_map.items():
            match = re.search(rf"^{re.escape(label)}:\s*(.+)$", raw, re.MULTILINE)
            if match:
                value = match.group(1).strip()
                target[key] = value
                line = f"{label}:  {value}" if label == "Termination Grace Period" else f"{label}: {value}"
                summary_lines.append(line)
                signals.append(line)

        containers, container_lines = cls._extract_describe_containers(raw)
        volumes, volume_lines = cls._extract_describe_named_section(
            raw,
            "Volumes",
            keep_pattern=r"^\s{2}\S.*:|^\s{4}(Type|ConfigMapName|SecretName|ClaimName|Name|Optional|Path|HostPath|Mounted By):",
            max_lines=30,
        )
        events = cls._extract_describe_events(raw, max_lines=20)

        if container_lines:
            summary_lines.append("Containers:")
            summary_lines.extend(container_lines)
            signals.extend(container_lines)
        if volume_lines:
            summary_lines.append("Volumes:")
            summary_lines.extend(volume_lines)
            signals.extend(volume_lines)
        if events:
            summary_lines.append("Events:")
            summary_lines.extend(events)
            signals.extend(events)

        return {
            "lifecycle": lifecycle,
            "containers": containers,
            "scheduling": scheduling,
            "volumes": volumes,
            "events": events,
            "signals": cls._dedupe_lines(signals),
            "summary_lines": cls._dedupe_lines(summary_lines),
        }

    @classmethod
    def _extract_describe_containers(cls, raw: str) -> tuple[list[Dict[str, Any]], list[str]]:
        section = cls._section_lines(raw, "Containers")
        containers: list[Dict[str, Any]] = []
        summary: list[str] = []
        current: Optional[Dict[str, Any]] = None
        capture_multiline: Optional[str] = None
        resource_group: Optional[str] = None
        keep_keys = {
            "Container ID",
            "Image",
            "Image ID",
            "Command",
            "Args",
            "State",
            "Last State",
            "Reason",
            "Exit Code",
            "Started",
            "Finished",
            "Ready",
            "Restart Count",
            "Environment",
            "Mounts",
            "Liveness",
            "Readiness",
            "Startup",
        }

        for raw_line in section:
            line = raw_line.rstrip()
            container_match = re.match(r"^\s{2}([^:\s][^:]*):\s*$", line)
            if container_match:
                current = {"name": container_match.group(1).strip(), "lines": []}
                containers.append(current)
                summary.append(line)
                capture_multiline = None
                resource_group = None
                continue

            resource_heading = re.match(
                r"^\s{4}(Limits|Requests):\s*$",
                line,
            )
            if resource_heading:
                resource_group = resource_heading.group(1).lower()
                capture_multiline = None
                if current is not None:
                    current.setdefault("resources", {}).setdefault(
                        resource_group,
                        {},
                    )
                summary.append(line)
                continue

            resource_quantity = re.match(
                r"^\s{6}([^:\s][^:]*):\s*(\S.*)$",
                line,
            )
            if resource_group and resource_quantity:
                resource_name = resource_quantity.group(1).strip()
                quantity = resource_quantity.group(2).strip()
                if current is not None:
                    current.setdefault("resources", {}).setdefault(
                        resource_group,
                        {},
                    )[resource_name] = quantity
                summary.append(line)
                continue

            key_match = re.match(r"^\s{4}([^:]+):\s*(.*)$", line)
            if key_match:
                key = key_match.group(1).strip()
                value = key_match.group(2).strip()
                resource_group = None
                capture_multiline = key if key in {"Command", "Args"} else None
                if key not in keep_keys:
                    continue
                if current is not None:
                    current["lines"].append(line)
                    current[cls._snake_key(key)] = value
                summary.append(line)
                continue

            if capture_multiline and re.match(r"^\s{6,}\S", line):
                if current is not None:
                    current["lines"].append(line)
                    current[capture_multiline.lower()] = (
                        (current.get(capture_multiline.lower()) or "") + " " + line.strip()
                    ).strip()
                summary.append(line)
                continue

            if re.search(r"\b(Reason|Exit Code|State|Ready|Restart Count):", line):
                summary.append(line)

        compact_containers = []
        for item in containers:
            compact = {k: v for k, v in item.items() if k != "lines"}
            if item.get("lines"):
                compact["signals"] = item["lines"][:40]
            compact_containers.append(compact)
        return compact_containers, cls._dedupe_lines(summary)[:60]

    @classmethod
    def _extract_describe_events(cls, raw: str, max_lines: int = 20) -> list[str]:
        section = cls._section_lines(raw, "Events", stop_at_next_section=False)
        if not section:
            return []
        selected = []
        for line in section:
            stripped = line.rstrip()
            if not stripped:
                continue
            if re.search(
                r"\b(Warning|Failed|BackOff|Killing|FailedMount|FailedScheduling|"
                r"FailedCreatePodSandBox|Unhealthy|probe failed|OOMKilled|"
                r"ImagePullBackOff|ErrImagePull|MountVolume|NotReady|Error)\b",
                stripped,
                re.IGNORECASE,
            ):
                selected.append(stripped)
        if not selected:
            selected = [line.rstrip() for line in section if line.strip()][-max_lines:]
        return cls._dedupe_lines(selected)[-max_lines:]

    @classmethod
    def _extract_describe_named_section(
        cls,
        raw: str,
        section_name: str,
        keep_pattern: str,
        max_lines: int,
    ) -> tuple[list[Dict[str, Any]], list[str]]:
        section = cls._section_lines(raw, section_name)
        selected = []
        current: Optional[Dict[str, Any]] = None
        items: list[Dict[str, Any]] = []
        for line in section:
            if re.match(r"^\s{2}([^:\s][^:]*):\s*$", line):
                current = {"name": line.strip().rstrip(":")}
                items.append(current)
            if re.search(keep_pattern, line):
                selected.append(line.rstrip())
                if current is not None:
                    current.setdefault("signals", []).append(line.rstrip())
        return items, cls._dedupe_lines(selected)[:max_lines]

    @staticmethod
    def _section_lines(raw: str, section_name: str, stop_at_next_section: bool = True) -> list[str]:
        lines = (raw or "").splitlines()
        start = None
        for idx, line in enumerate(lines):
            if re.match(rf"^{re.escape(section_name)}:\s*$", line):
                start = idx + 1
                break
        if start is None:
            return []
        result = []
        for line in lines[start:]:
            if (
                stop_at_next_section
                and result
                and re.match(r"^[A-Za-z][A-Za-z0-9 /()._-]*:\s*(?:\S.*)?$", line)
            ):
                break
            result.append(line)
        return result

    @staticmethod
    def _snake_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")

    def _extract_table(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        if not lines:
            return {"status": "empty"}, "工具返回为空；不能作为正向健康证据。", "k8s_table"
        if re.search(r"command failed|error from server|notfound|not found", raw, re.IGNORECASE):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary(tool, raw), "k8s_table"

        header = lines[0]
        columns = re.split(r"\s{2,}|\t+", header.strip())
        status_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"READY", "STATUS", "REASON", "PHASE"}
        }
        pure_status_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"STATUS", "REASON", "PHASE"}
        }
        endpoint_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"ENDPOINTS"}
        }
        restart_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"RESTARTS"}
        }
        abnormal = []
        recent_restart_rows = []
        for line in lines[1:]:
            if self._table_row_is_abnormal(
                line,
                status_indexes,
                pure_status_indexes,
                endpoint_indexes,
            ):
                abnormal.append(line)
                continue
            if self._table_row_has_recent_restart(
                line,
                pure_status_indexes,
                restart_indexes,
            ):
                abnormal.append(line)
                recent_restart_rows.append(line)
        status_counts: Dict[str, int] = {}
        for ln in lines[1:]:
            for status in re.findall(
                r"\b(Running|Pending|Failed|Succeeded|CrashLoopBackOff|ImagePullBackOff|"
                r"ErrImagePull|OOMKilled|Evicted|NotReady|Ready|Terminating|Unknown|Error)\b",
                ln,
            ):
                status_counts[status] = status_counts.get(status, 0) + 1

        selected = abnormal[:50] if abnormal else lines[1:21]
        structured = {
            "status": "table_summarized",
            "row_count": max(0, len(lines) - 1),
            "abnormal_count": len(abnormal),
            "recent_restart_count": len(recent_restart_rows),
            "recent_restart_rows": recent_restart_rows,
            "status_counts": status_counts,
            "header": header,
            "selected_rows": selected,
        }
        label = "异常行" if abnormal else "样例行"
        summary = (
            f"{tool} 表格摘要: rows={structured['row_count']} "
            f"abnormal={len(abnormal)} recent_restarts={len(recent_restart_rows)} "
            f"status_counts={status_counts}\n{header}\n# {label}\n"
            + "\n".join(selected)
        )
        return structured, summary, "k8s_table"

    @staticmethod
    def _looks_like_secret_table(raw: str) -> bool:
        lines = [ln for ln in (raw or "").splitlines() if ln.strip()]
        if not lines:
            return False
        header = lines[0].upper()
        if not all(col in header for col in ["NAME", "TYPE", "DATA", "AGE"]):
            return False
        body = "\n".join(lines[1:]).lower()
        return bool(re.search(r"\bkubernetes\.io/|opaque|helm\.sh/release\.v1", body))

    def _extract_secret_table(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        base_structured, base_summary, processor = self._extract_table(tool, raw)
        rows = base_structured.get("selected_rows") or []
        if not rows and base_structured.get("status") != "table_summarized":
            return base_structured, base_summary, processor

        docker_secret_rows = []
        docker_like_rows = []
        for row in rows:
            lowered = row.lower()
            if "kubernetes.io/dockerconfigjson" in lowered or "kubernetes.io/dockercfg" in lowered:
                docker_secret_rows.append(row)
            elif any(keyword in lowered for keyword in ["docker", "registry", "pull", "xnet-bmcs"]):
                docker_like_rows.append(row)

        structured = {
            **base_structured,
            "resource_kind": "Secret",
            "docker_secret_count": len(docker_secret_rows),
            "docker_like_rows": docker_like_rows[:20],
            "docker_secret_rows": docker_secret_rows[:20],
        }
        lines = [
            f"{tool} Secret 表摘要: rows={base_structured.get('row_count', 0)} abnormal={base_structured.get('abnormal_count', 0)}",
            f"docker_secret_count: {len(docker_secret_rows)}",
        ]
        if docker_secret_rows:
            lines.append("# kubernetes.io/dockerconfigjson/dockercfg Secret")
            lines.extend(docker_secret_rows[:20])
        else:
            lines.append("未发现 type 为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg 的 Secret。")
        if docker_like_rows:
            lines.append("# 名称疑似与镜像拉取相关但类型不一定有效")
            lines.extend(docker_like_rows[:20])
        lines.append("# 全量 Secret 行已落盘到 raw_ref，selected_rows 已落盘到 structured_ref。")
        return structured, "\n".join(lines), "k8s_secret_table"

    def _extract_jq(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        stripped = raw.strip()
        try:
            parsed = json.loads(stripped)
            structured = {
                "status": "json_summarized",
                "type": type(parsed).__name__,
                "count": len(parsed) if isinstance(parsed, (list, dict)) else 1,
            }
            summary = json.dumps(parsed, ensure_ascii=False)[: self.max_observation_chars]
            return structured, summary, "k8s_jq"
        except Exception:
            return {"status": "text_summarized"}, self._generic_summary("kubernetes_jq_query", raw), "k8s_jq"

    def _extract_yaml(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        if re.search(r"command failed|error from server|notfound|not found", raw, re.IGNORECASE):
            structured = {"status": "command_failed", "raw_preview": raw[:1000]}
            summary = self._generic_summary("kubectl_get_yaml", raw)
            return structured, summary, "k8s_yaml"

        try:
            doc = yaml.safe_load(raw) or {}
        except Exception as exc:
            structured = {"status": "yaml_parse_failed", "error": str(exc)}
            return structured, self._legacy_yaml_summary(raw), "k8s_yaml"

        if not isinstance(doc, dict):
            structured = {"status": "yaml_non_mapping", "type": type(doc).__name__}
            return structured, self._legacy_yaml_summary(raw), "k8s_yaml"

        kind = doc.get("kind")
        if kind == "Pod":
            return self._extract_pod_yaml(doc)
        if kind == "Secret":
            return self._extract_secret_yaml(doc)

        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        structured = {
            "status": "yaml_summarized",
            "kind": kind,
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
        }
        lines = [
            "kubectl_get_yaml 关键字段摘要:",
            f"kind: {kind}",
            f"name: {metadata.get('name')}",
            f"namespace: {metadata.get('namespace')}",
        ]
        return structured, "\n".join(lines), "k8s_yaml"

    def _extract_pod_yaml(self, doc: Dict[str, Any]) -> tuple[Dict[str, Any], str, str]:
        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        spec = doc.get("spec") if isinstance(doc.get("spec"), dict) else {}
        status = doc.get("status") if isinstance(doc.get("status"), dict) else {}
        labels = metadata.get("labels") if isinstance(metadata.get("labels"), dict) else {}
        annotations = metadata.get("annotations") if isinstance(metadata.get("annotations"), dict) else {}
        diagnostic_annotations = {
            str(key): value
            for key, value in annotations.items()
            if str(key).startswith(("aiops.", "robusta.", "kubernetes.io/change-cause"))
        }

        image_pull_secrets_raw = spec.get("imagePullSecrets")
        image_pull_secrets = [
            item.get("name")
            for item in image_pull_secrets_raw
            if isinstance(item, dict) and item.get("name")
        ] if isinstance(image_pull_secrets_raw, list) else []

        containers = []
        for container in spec.get("containers") or []:
            if not isinstance(container, dict):
                continue
            containers.append({
                "name": container.get("name"),
                "image": container.get("image"),
                "imagePullPolicy": container.get("imagePullPolicy"),
                "command": container.get("command") if isinstance(container.get("command"), list) else [],
                "args": container.get("args") if isinstance(container.get("args"), list) else [],
                "lifecycle": container.get("lifecycle") if isinstance(container.get("lifecycle"), dict) else {},
                "resources": container.get("resources") or {},
            })

        init_containers = []
        for container in spec.get("initContainers") or []:
            if not isinstance(container, dict):
                continue
            init_containers.append({
                "name": container.get("name"),
                "image": container.get("image"),
                "imagePullPolicy": container.get("imagePullPolicy"),
            })

        container_statuses = []
        for item in status.get("containerStatuses") or []:
            if not isinstance(item, dict):
                continue
            state = item.get("state") if isinstance(item.get("state"), dict) else {}
            last_state = item.get("lastState") if isinstance(item.get("lastState"), dict) else {}
            container_statuses.append({
                "name": item.get("name"),
                "ready": item.get("ready"),
                "restartCount": item.get("restartCount"),
                "image": item.get("image"),
                "imageID": item.get("imageID"),
                "waiting": state.get("waiting") if isinstance(state.get("waiting"), dict) else None,
                "terminated": state.get("terminated") if isinstance(state.get("terminated"), dict) else None,
                "lastTerminated": last_state.get("terminated") if isinstance(last_state.get("terminated"), dict) else None,
            })

        owner_refs = []
        for item in metadata.get("ownerReferences") or []:
            if isinstance(item, dict):
                owner_refs.append({"kind": item.get("kind"), "name": item.get("name")})

        volumes = []
        for volume in spec.get("volumes") or []:
            if not isinstance(volume, dict):
                continue
            volume_info = {"name": volume.get("name")}
            for source in ["configMap", "secret", "persistentVolumeClaim"]:
                if isinstance(volume.get(source), dict):
                    volume_info[source] = volume[source].get("name") or volume[source].get("claimName")
            volumes.append(volume_info)

        conditions = []
        for item in status.get("conditions") or []:
            if not isinstance(item, dict):
                continue
            conditions.append({
                "type": item.get("type"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "message": item.get("message"),
                "lastTransitionTime": item.get("lastTransitionTime"),
            })

        structured = {
            "status": "yaml_summarized",
            "kind": "Pod",
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "uid": metadata.get("uid"),
            "creationTimestamp": metadata.get("creationTimestamp"),
            "deletionTimestamp": metadata.get("deletionTimestamp"),
            "deletionGracePeriodSeconds": metadata.get("deletionGracePeriodSeconds"),
            "finalizers": metadata.get("finalizers") if isinstance(metadata.get("finalizers"), list) else [],
            "labels": labels,
            "diagnostic_annotations": diagnostic_annotations,
            "ownerReferences": owner_refs,
            "serviceAccountName": spec.get("serviceAccountName"),
            "nodeName": spec.get("nodeName"),
            "restartPolicy": spec.get("restartPolicy"),
            "terminationGracePeriodSeconds": spec.get("terminationGracePeriodSeconds"),
            "nodeSelector": spec.get("nodeSelector") if isinstance(spec.get("nodeSelector"), dict) else {},
            "tolerations": spec.get("tolerations") if isinstance(spec.get("tolerations"), list) else [],
            "affinity_present": isinstance(spec.get("affinity"), dict) and bool(spec.get("affinity")),
            "imagePullSecrets": image_pull_secrets,
            "imagePullSecrets_present": image_pull_secrets_raw is not None,
            "containers": containers,
            "initContainers": init_containers,
            "volumes": volumes,
            "phase": status.get("phase"),
            "reason": status.get("reason"),
            "message": status.get("message"),
            "conditions": conditions,
            "containerStatuses": container_statuses,
        }

        lines = [
            "kubectl_get_yaml 关键字段摘要:",
            "kind: Pod",
            f"name: {metadata.get('name')}",
            f"namespace: {metadata.get('namespace')}",
            f"creationTimestamp: {metadata.get('creationTimestamp')}",
            f"deletionTimestamp: {metadata.get('deletionTimestamp') or '<absent>'}",
            f"deletionGracePeriodSeconds: {metadata.get('deletionGracePeriodSeconds')}",
            "finalizers: " + (
                ", ".join(str(item) for item in structured["finalizers"])
                if structured["finalizers"] else "<none>"
            ),
            f"serviceAccountName: {spec.get('serviceAccountName')}",
            f"nodeName: {spec.get('nodeName')}",
            f"restartPolicy: {spec.get('restartPolicy')}",
            f"terminationGracePeriodSeconds: {spec.get('terminationGracePeriodSeconds')}",
            "imagePullSecrets: " + (", ".join(image_pull_secrets) if image_pull_secrets else "<absent>"),
            f"phase: {status.get('phase')}",
        ]
        if labels:
            label_facts = {
                key: labels.get(key)
                for key in sorted(labels)
                if key in {"app", "pod_abnormal_type", "expected_layer", "e2e-test"}
                or str(key).startswith(("aiops.", "robusta."))
            }
            if label_facts:
                lines.append("labels: " + ", ".join(f"{k}={v}" for k, v in label_facts.items()))
        if diagnostic_annotations:
            lines.append("diagnostic_annotations: " + ", ".join(
                f"{k}={v}" for k, v in sorted(diagnostic_annotations.items())
            ))
        if owner_refs:
            lines.append("ownerReferences: " + ", ".join(
                f"{item.get('kind')}/{item.get('name')}" for item in owner_refs
            ))
        if structured["nodeSelector"]:
            lines.append("nodeSelector: " + json.dumps(structured["nodeSelector"], ensure_ascii=False))
        if structured["tolerations"]:
            lines.append("tolerations_count: " + str(len(structured["tolerations"])))
        if structured["affinity_present"]:
            lines.append("affinity_present: True")
        if containers:
            lines.append("containers:")
            for item in containers:
                lines.append(
                    f"- {item.get('name')}: image={item.get('image')} imagePullPolicy={item.get('imagePullPolicy')}"
                )
                command = item.get("command") or []
                args = item.get("args") or []
                lifecycle = item.get("lifecycle") or {}
                if command:
                    lines.append("  command: " + " ".join(str(part) for part in command[:10]))
                if args:
                    args_text = " ".join(str(part) for part in args[:10])
                    lines.append("  args: " + (args_text[:500] + ("..." if len(args_text) > 500 else "")))
                if lifecycle:
                    lines.append("  lifecycle: " + json.dumps(lifecycle, ensure_ascii=False)[:800])
        if conditions:
            lines.append("conditions:")
            for item in conditions[:10]:
                detail = (
                    f"- {item.get('type')}: status={item.get('status')} "
                    f"reason={item.get('reason')}"
                )
                if item.get("message"):
                    detail += f" message={item.get('message')}"
                lines.append(detail)
        if container_statuses:
            lines.append("containerStatuses:")
            for item in container_statuses:
                waiting = item.get("waiting") or {}
                terminated = item.get("terminated") or item.get("lastTerminated") or {}
                reason = waiting.get("reason") or terminated.get("reason")
                message = waiting.get("message") or terminated.get("message")
                exit_code = terminated.get("exitCode")
                lines.append(
                    f"- {item.get('name')}: ready={item.get('ready')} restarts={item.get('restartCount')} "
                    f"reason={reason} exitCode={exit_code}"
                )
                if message:
                    lines.append(f"  message: {message}")
        if volumes:
            lines.append("volumes:")
            lines.extend(f"- {json.dumps(item, ensure_ascii=False)}" for item in volumes[:20])
        return structured, "\n".join(lines), "k8s_yaml"

    def _extract_secret_yaml(self, doc: Dict[str, Any]) -> tuple[Dict[str, Any], str, str]:
        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
        data_keys = sorted(str(key) for key in data.keys())
        secret_type = doc.get("type")
        has_dockerconfigjson = any(key in data for key in [".dockerconfigjson", "dockerconfigjson"])
        docker_secret_type_valid = secret_type in {"kubernetes.io/dockerconfigjson", "kubernetes.io/dockercfg"}
        structured = {
            "status": "yaml_summarized",
            "kind": "Secret",
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "type": secret_type,
            "data_keys": data_keys,
            "has_dockerconfigjson": has_dockerconfigjson,
            "docker_secret_type_valid": docker_secret_type_valid,
        }
        lines = [
            "kubectl_get_yaml 关键字段摘要:",
            "kind: Secret",
            f"name: {metadata.get('name')}",
            f"namespace: {metadata.get('namespace')}",
            f"type: {secret_type}",
            "data_keys: " + (", ".join(data_keys) if data_keys else "<none>"),
            f"has_dockerconfigjson: {has_dockerconfigjson}",
            f"docker_secret_type_valid: {docker_secret_type_valid}",
        ]
        return structured, "\n".join(lines), "k8s_yaml"

    def _legacy_yaml_summary(self, raw: str) -> str:
        keep = []
        for line in raw.splitlines():
            if re.search(
                r"^kind:|^\s*name:|^\s*namespace:|^\s*image:|^\s*resources:|"
                r"^\s*limits:|^\s*requests:|^\s*env:|^\s*envFrom:|"
                r"^\s*volumes:|^\s*volumeMounts:|^\s*phase:|^\s*reason:|"
                r"^\s*message:|^\s*containerStatuses:|^\s*deletionTimestamp:|"
                r"^\s*deletionGracePeriodSeconds:|^\s*finalizers:|"
                r"^\s*terminationGracePeriodSeconds:|^\s*lifecycle:|^\s*preStop:|"
                r"^\s*command:|^\s*args:",
                line,
            ):
                keep.append(line.rstrip())
        return "kubectl_get_yaml 关键字段摘要:\n" + "\n".join(keep[:120])

    def _table_row_is_abnormal(
        self,
        row: str,
        status_indexes: set[int],
        pure_status_indexes: set[int],
        endpoint_indexes: set[int],
    ) -> bool:
        cells = re.split(r"\s{2,}|\t+", row.strip())
        status_text = " ".join(
            cells[idx] for idx in status_indexes
            if idx < len(cells)
        )
        pure_status_text = " ".join(
            cells[idx] for idx in pure_status_indexes
            if idx < len(cells)
        )
        endpoint_text = " ".join(
            cells[idx] for idx in endpoint_indexes
            if idx < len(cells)
        )
        if endpoint_text and re.search(r"(^|\s)<none>($|\s)", endpoint_text, re.IGNORECASE):
            return True
        if pure_status_text:
            normalized = pure_status_text.strip().lower()
            if normalized in {"completed", "succeeded"}:
                return False
            # READY 未就绪（如 0/1）即为异常：readiness 探针失败时
            # STATUS 列仍显示 Running，不能只看状态关键字（c09 实测教训）。
            ready_indexes = status_indexes - pure_status_indexes
            ready_text = " ".join(
                cells[idx] for idx in ready_indexes if idx < len(cells)
            )
            ready_match = re.search(r"\b(\d+)/(\d+)\b", ready_text)
            if ready_match and int(ready_match.group(1)) < int(ready_match.group(2)):
                return True
            if normalized in {"running", "ready", "bound", "active"}:
                return False
            return True
        return bool(re.search(
            r"CrashLoopBackOff|ImagePullBackOff|ErrImagePull|OOMKilled|Evicted|"
            r"Pending|Failed|Error|NotReady|Unknown|0/\d+",
            status_text,
            re.IGNORECASE,
        ))

    @classmethod
    def _table_row_has_recent_restart(
        cls,
        row: str,
        pure_status_indexes: set[int],
        restart_indexes: set[int],
    ) -> bool:
        if not pure_status_indexes or not restart_indexes:
            return False
        cells = re.split(r"\s{2,}|\t+", row.strip())
        status_text = " ".join(
            cells[idx] for idx in pure_status_indexes
            if idx < len(cells)
        ).strip().lower()
        if status_text != "running":
            return False

        restart_text = " ".join(
            cells[idx] for idx in restart_indexes
            if idx < len(cells)
        ).strip()
        match = re.fullmatch(
            r"(?P<count>\d+)\s+\((?P<age>[^()]+?)\s+ago\)",
            restart_text,
            re.IGNORECASE,
        )
        if not match or int(match.group("count")) <= 0:
            return False

        age_seconds = cls._parse_kubectl_duration_seconds(match.group("age"))
        return (
            age_seconds is not None
            and age_seconds <= cls.RECENT_RESTART_WINDOW_SECONDS
        )

    @staticmethod
    def _parse_kubectl_duration_seconds(value: str) -> Optional[int]:
        normalized = re.sub(r"\s+", "", str(value or "").strip().lower())
        if not normalized:
            return None
        parts = re.findall(r"(\d+)([dhms])", normalized)
        if not parts:
            return None
        if "".join(f"{amount}{unit}" for amount, unit in parts) != normalized:
            return None
        multipliers = {
            "d": 24 * 60 * 60,
            "h": 60 * 60,
            "m": 60,
            "s": 1,
        }
        return sum(int(amount) * multipliers[unit] for amount, unit in parts)

    def _extract_run_image(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        stripped = (raw or "").strip()
        try:
            parsed = json.loads(stripped) if stripped else {}
        except Exception:
            parsed = None

        if not isinstance(parsed, dict):
            return {"status": "run_image_unparsed"}, self._generic_summary("kubectl_run_image", raw), "k8s_run_image"

        success = parsed.get("success")
        stdout = (parsed.get("stdout") or "").strip()
        stderr = (parsed.get("stderr") or "").strip()
        returncode = parsed.get("returncode")
        merged = "\n".join(part for part in [stdout, stderr] if part)
        signals = []
        for pattern, label in [
            (r"timed out|deadlineexceeded|i/o timeout", "timeout"),
            (r"no such host|nxdomain|server can't find|temporary failure in name resolution", "dns"),
            (r"x509|certificate signed by unknown authority|tls", "tls"),
            (r"connection refused|no route to host|network is unreachable", "network"),
            (r"imagepullbackoff|errimagepull|failed to pull", "image_pull"),
        ]:
            if re.search(pattern, merged, re.IGNORECASE):
                signals.append(label)

        structured = {
            "status": "run_image_result",
            "success": success,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "signals": signals,
        }
        summary_lines = [
            "kubectl_run_image 摘要:",
            f"success: {success}",
            f"returncode: {returncode}",
        ]
        if signals:
            summary_lines.append(f"signals: {', '.join(signals)}")
        if stdout:
            summary_lines.append(f"stdout: {stdout[:500]}")
        if stderr:
            summary_lines.append(f"stderr: {stderr[:1000]}")
        return structured, "\n".join(summary_lines), "k8s_run_image"

    def _extract_command_result(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        stripped = (raw or "").strip()
        try:
            parsed = json.loads(stripped) if stripped else {}
        except Exception:
            parsed = None
        if not isinstance(parsed, dict):
            return {"status": "command_unparsed"}, self._generic_summary(tool, raw), "command_result"
        stdout = (parsed.get("stdout") or "").strip()
        stderr = (parsed.get("stderr") or "").strip()
        structured = {
            "status": "command_result",
            "success": parsed.get("success"),
            "returncode": parsed.get("returncode"),
            "stdout_chars": len(stdout),
            "stderr_chars": len(stderr),
            "stdout_preview": stdout[:1000],
            "stderr_preview": stderr[:1000],
        }
        lines = [
            f"{tool} 输出摘要:",
            f"success: {parsed.get('success')}",
            f"returncode: {parsed.get('returncode')}",
        ]
        if stdout:
            lines.append(f"stdout: {stdout[:1000]}")
        if stderr:
            lines.append(f"stderr: {stderr[:1000]}")
        return structured, "\n".join(lines), "command_result"

    def _extract_logs(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        if self._is_command_failure(raw):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary(tool, raw), "k8s_logs"

        lines = [ln for ln in raw.splitlines() if ln.strip()]
        signal_patterns = (
            r"error|exception|traceback|panic|fatal|critical|failed|fail|warn|warning|"
            r"oom|killed|timeout|timed out|connection refused|permission denied|"
            r"no such file|not found|crash|segfault"
        )
        signal_lines = [ln for ln in lines if re.search(signal_patterns, ln, re.IGNORECASE)]
        selected = signal_lines[:40] or lines[-40:]
        structured = {
            "status": "logs_summarized",
            "line_count": len(lines),
            "signal_count": len(signal_lines),
            "selected_lines": selected,
        }
        summary_lines = [
            f"{tool} 日志摘要:",
            f"lines: {len(lines)}",
            f"signals: {len(signal_lines)}",
        ]
        if selected:
            summary_lines.append("关键日志:")
            summary_lines.extend(selected)
        else:
            summary_lines.append("日志为空；这是负向观察，不能证明应用无异常。")
        return structured, "\n".join(summary_lines), "k8s_logs"

    def _generic_summary(self, tool: str, raw: str) -> str:
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        head = "\n".join(lines[:40])
        return f"{tool} 输出摘要: raw_chars={len(raw)} lines={len(lines)}\n{head}"

    def _extract_prometheus_result(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        try:
            payload = json.loads(raw or "{}")
        except Exception:
            payload = {}

        error = str(payload.get("error") or "").strip()
        error_type = str(payload.get("errorType") or "").strip()
        query = str(payload.get("query") or "").strip()
        url = str(payload.get("url") or "").strip()
        status = str(payload.get("status") or "").strip().lower()
        if error or error_type or status == "error" or re.search(r"\b(?:400|500)\s+Client Error|Bad Request", raw or "", re.IGNORECASE):
            message = error or error_type or raw[:1000]
            structured = {
                "status": "prometheus_error",
                "tool": tool,
                "error": message,
            }
            summary_lines = [f"{tool} 查询失败: {message}"]
            if error_type:
                structured["error_type"] = error_type
                summary_lines.append(f"Prometheus errorType: {error_type}")
            if query:
                structured["query"] = query
                summary_lines.append(f"PromQL: {query}")
            if url:
                structured["url"] = url
            return structured, "\n".join(summary_lines), "prometheus_error"

        result = ((payload.get("data") or {}).get("result") or []) if isinstance(payload, dict) else []
        result_count = len(result) if isinstance(result, list) else 0
        if result_count == 0:
            structured = {
                "status": "prometheus_empty",
                "tool": tool,
                "result_count": 0,
            }
            return structured, f"{tool} 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。", "prometheus_empty"

        structured = {
            "status": "prometheus_result",
            "tool": tool,
            "result_count": result_count,
        }
        return structured, raw, "prometheus_result"

    @staticmethod
    def _is_semantically_successful(structured: Dict[str, Any], summary: str) -> bool:
        status = str((structured or {}).get("status", "")).lower()
        if status in {"query_rejected", "query_parse_failed"}:
            return False
        if status == "query_succeeded":
            return str((structured or {}).get("coverage") or "").lower() in {
                "present",
                "empty",
                "absent",
                "weak",
            }
        if status == "query_partial":
            return (
                str(
                    (structured or {}).get("coverage") or ""
                ).lower()
                == "partial"
                and ObservationProcessor._has_source_backed_observability_fact(
                    structured or {}
                )
            )
        if status in {
            "empty",
            "command_failed",
            "yaml_parse_failed",
            "invalid_tool",
            "prometheus_error",
            "prometheus_empty",
            "run_image_result",
            "command_result",
            "case_error",
            "case_parse_failed",
        }:
            if status in {"run_image_result", "command_result"}:
                return bool((structured or {}).get("success") is True)
            return False
        if status == "runbook_loaded":
            return True
        text = summary or ""
        if not text.strip():
            return False
        if ObservationProcessor._is_command_failure(text) or re.search(r"工具返回为空", text, re.IGNORECASE):
            return False
        return True

    def _bound_summary(self, summary: str, raw: str) -> str:
        if len(summary) <= self.max_observation_chars:
            return summary
        suffix = f"\n... (已压缩/截断，原始 {len(raw)} 字符，完整内容见 raw_ref)"
        limit = max(0, self.max_observation_chars - len(suffix))
        return summary[:limit] + suffix

    @staticmethod
    def _is_command_failure(raw: str) -> bool:
        """Return true only when the tool invocation failed.

        Do not treat diagnostic payload text such as Kubernetes Event
        `configmap ... not found` or application log `file not found` as a
        failed tool call. Those lines are often the highest-value evidence.
        """
        lines = [ln.strip() for ln in (raw or "").splitlines() if ln.strip()]
        if not lines:
            return False
        head = "\n".join(lines[:3])
        return bool(
            re.search(
                r"^(Command failed|Error from server|Error:\s|The server doesn't have a resource type)",
                head,
                re.IGNORECASE,
            )
        )

    @classmethod
    def _extract_diagnostic_lines(cls, raw: str, limit: int = 20) -> list[str]:
        patterns = (
            r"MountVolume\.SetUp failed|FailedMount|FailedAttachVolume|Unable to attach or mount volumes|"
            r"configmaps? .+ not found|secrets? .+ not found|couldn.t find key|"
            r"FailedScheduling|0/\d+ nodes are available|Insufficient|taint|didn.t match|"
            r"OOMKilled|Exit Code:\s*137|Reason:\s*OOMKilled|"
            r"ImagePullBackOff|ErrImagePull|Failed to pull image|pull access denied|x509|i/o timeout|"
            r"FailedCreatePodSandBox|failed to setup network|cni|ipam|"
            r"Readiness probe failed|Liveness probe failed|Startup probe failed|probe failed|"
            r"Back-off|CrashLoopBackOff|Error from server|NotFound|not found|"
            r"deletionTimestamp|finalizers?:|FailedKillPod|Killing|Unmount|Detach|"
            r"NodeLost|NotReady|node .*unreachable|PLEG"
        )
        selected = []
        for line in (raw or "").splitlines():
            stripped = line.rstrip()
            if not stripped or re.search(r"aiops\.e2e/expected-", stripped, re.IGNORECASE):
                continue
            if re.search(patterns, stripped, re.IGNORECASE):
                selected.append(stripped)
        return sorted(
            cls._dedupe_lines(selected),
            key=cls._diagnostic_line_score,
            reverse=True,
        )[:limit]

    @staticmethod
    def _diagnostic_line_score(line: str) -> int:
        text = line or ""
        score = 0
        weighted_patterns = [
            (r"MountVolume\.SetUp failed|configmaps? .+ not found|secrets? .+ not found", 100),
            (r"OOMKilled|Exit Code:\s*137|FailedScheduling|FailedCreatePodSandBox|probe failed", 90),
            (r"Failed to pull image|pull access denied|x509|i/o timeout|CrashLoopBackOff|Back-off", 80),
            (r"FailedMount|FailedAttachVolume|Unable to attach or mount volumes", 70),
            (r"Error from server|NotFound|not found", 60),
            (r"Reason:|Warning|Failed|Error", 40),
        ]
        for pattern, weight in weighted_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score = max(score, weight)
        return score

    @staticmethod
    def _dedupe_lines(lines: list[str]) -> list[str]:
        seen = set()
        result = []
        for line in lines:
            key = re.sub(r"\s+", " ", str(line or "").strip())
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(str(line))
        return result
