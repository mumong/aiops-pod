"""
节点4：汇总总结

职责：
- 整合前3个节点的分析结果和工具真实数据
- 单次 LLM 调用生成人类可读的最终诊断报告（CONCLUSION_FORMATTER_PROMPT 富模板）
- 输出：conclusion, conclusion_formatted

设计（第一性原理精简版）：
- 报告格式稳定性来自单一富模板 system prompt，而非事后正则矫正
- 真实工具数据（metrics / logging / tracing / kubectl）是报告的核心输入
- HEALTHY / QUERY-direct 走确定性快速路径，不调 LLM
- LLM 失败或返回空时回退到确定性模板
"""

import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import asdict
from typing import Any, Dict, List, Mapping, Optional

from app.core.workflow.fact_contract import (
    OBSERVABILITY_QUERY_TOOLS,
    project_final_observability_events,
)
from app.core.remediation.plans import extract_remediation_plan
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import QueryConclusionOutput, QueryResult
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer
from app.core.prompts import (
    get_conclusion_mode_instruction,
    get_workflow_prompt,
)

logger = logging.getLogger(__name__)

# 模型单次输出上限：仅当 API 传入的 conclusion_max_tokens 超过此值时才使用此值。
# 可通过环境变量 CONCLUSION_MAX_TOKENS_CAP 覆盖，默认 8192。
def _get_conclusion_max_tokens_cap() -> int:
    try:
        v = os.environ.get("CONCLUSION_MAX_TOKENS_CAP", "")
        if v and v.isdigit():
            return int(v)
    except Exception:
        pass
    return 8192


CONCLUSION_MAX_TOKENS_CAP = _get_conclusion_max_tokens_cap()

# 用户消息中各段落的字符上限（超出按头部保留截断，防止超过模型窗口）
_SECTION_CHAR_LIMITS = {
    "layer": 6000,
    "evidence": 8000,
    "rca": 8000,
    "tool_data": 16000,
}

# 工具真实数据：单条上限与总条数上限
_TOOL_ENTRY_CHAR_LIMIT = 1500
_TOOL_ENTRY_MAX_COUNT = 24
# 可观测性工具：每次调用保留的结构化事实条数上限（丢整条低价值事实，绝不砍值）
_OBS_FACTS_PER_CALL = 8
# 单条事实值的字符上限（一条日志/一个 flow 是自成单元的一条，不是 blob）
_OBS_FACT_VALUE_LIMIT = 500


class ConclusionFormatterNode(WorkflowNode):
    """汇总总结节点：整合前置分析 + 真实工具数据，生成最终报告。"""

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

    @property
    def node_id(self) -> str:
        return "conclusion"

    @property
    def node_name(self) -> str:
        return "汇总总结"

    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def execute(self, state: WorkflowState) -> WorkflowState:
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            question = state.get("question", "")
            layer = state.get("layer")
            layer_analysis = self._select_layer_context(state)
            evidence_analysis = state.get("evidence_analysis") or "{}"
            rca_analysis = state.get("rca_analysis") or "{}"
            query_result = state.get("query_result")
            thinking_events = state.get("thinking_events", [])

            group_results = state.get("group_results")

            if layer == Layer.HEALTHY:
                conclusion = self._format_healthy_fast_path(
                    question=question,
                    layer_analysis=layer_analysis,
                    thinking_events=thinking_events,
                )
            elif layer == Layer.QUERY and self._get_query_mode() == "direct" and query_result:
                conclusion = self._render_query_result(query_result)
            elif group_results:
                # N=1 与 N>1 使用同一份 canonical facts 和同一富文本合同。
                conclusion = self._generate_multi_group_report(
                    question=question,
                    group_results=group_results,
                    conclusion_max_tokens=state.get("conclusion_max_tokens"),
                )
            elif layer != Layer.QUERY:
                formal_rca = self._parse_formal_rca(rca_analysis)
                can_use_report_agent = (
                    getattr(self, "ai_call", None) is not None
                    and self._formal_rca_is_valid(formal_rca)
                )
                if can_use_report_agent:
                    conclusion = self._generate_with_llm(
                        question=question,
                        layer_analysis=layer_analysis,
                        evidence_analysis=evidence_analysis,
                        rca_analysis=rca_analysis,
                        conclusion_max_tokens=state.get("conclusion_max_tokens"),
                        layer=layer,
                        tool_data_text=self._build_tool_data_section(
                            thinking_events
                        ),
                        query_result=query_result,
                    )
                else:
                    conclusion = self._render_single_authoritative_report(
                        question=question,
                        state=state,
                        rca_analysis=rca_analysis,
                    )
            elif getattr(self, "ai_call", None) is not None:
                tool_data_text = self._build_tool_data_section(thinking_events)
                conclusion = self._generate_with_llm(
                    question=question,
                    layer_analysis=layer_analysis,
                    evidence_analysis=evidence_analysis,
                    rca_analysis=rca_analysis,
                    conclusion_max_tokens=state.get("conclusion_max_tokens"),
                    layer=layer,
                    tool_data_text=tool_data_text,
                    query_result=query_result,
                )
            else:
                logger.info("⚠️ 无 LLM 服务，使用模板格式化")
                conclusion = ""

            if not (conclusion or "").strip():
                conclusion = self._format_with_template(
                    question=question,
                    layer=layer,
                    layer_analysis=layer_analysis,
                    evidence_analysis=evidence_analysis,
                    rca_analysis=rca_analysis,
                    errors=state.get("errors", []),
                    warnings=state.get("warnings", []),
                )

            new_state.update({
                "conclusion": conclusion,
                "conclusion_formatted": conclusion,
            })

            conclusion_thinking = getattr(self, "_conclusion_thinking", [])
            self._save_thinking(state, new_state, conclusion_thinking)

            logger.info(f"✅ 汇总总结完成: {len(conclusion)} 字符")

        except Exception as e:
            logger.error(f"汇总总结失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "conclusion": f"报告生成失败: {str(e)}",
                "conclusion_formatted": f"报告生成失败: {str(e)}",
            })
            self._save_thinking(state, new_state, [])

        return new_state

    # ------------------------------------------------------------------
    # 上下文选择与构建
    # ------------------------------------------------------------------
    def _select_layer_context(self, state: WorkflowState) -> str:
        """Prefer compact layer_handoff over deprecated full layer text."""
        handoff = state.get("layer_handoff")
        if handoff:
            return json.dumps(handoff, ensure_ascii=False, indent=2, default=str)
        layer_analysis = state.get("layer_analysis")
        if layer_analysis:
            return layer_analysis
        legacy_full = state.get("layer_full_analysis")
        if legacy_full:
            return self._summarize_snippet(legacy_full, limit=2000)
        return "{}"

    def _build_tool_data_section(self, thinking_events: list) -> str:
        """
        从 thinking_events 中提取所有节点的工具真实输出，
        构建报告的核心数据段落（metrics / logging / tracing / kubectl 真实结果）。

        只提取 tool_result 类型且 status=success 的事件；
        可观测性查询工具只保留最终有效投影，避免同一查询多轮重复。
        """
        parts = []
        seen = set()
        final_observability_events = project_final_observability_events(thinking_events)
        final_observability_event_ids = {id(event) for event in final_observability_events}
        projected_tools = {
            str(event.get("tool_name") or "").strip().lower()
            for event in final_observability_events
        }
        for ev in thinking_events:
            if ev.get("type") != "tool_result":
                continue
            if ev.get("status") != "success":
                continue
            tool_name = ev.get("tool_name", "unknown")
            normalized_tool = str(tool_name or "").strip().lower()
            if (
                normalized_tool in OBSERVABILITY_QUERY_TOOLS
                and id(ev) not in final_observability_event_ids
                # 只有当同一工具已有最终投影代表时才丢弃（多轮重试去重）；
                # 元数据不全导致无投影时保留原始数据，避免真实数据静默丢失
                and normalized_tool in projected_tools
            ):
                continue
            # 第一性原理：可观测性工具的真实值以结构化 facts 承载在
            # ev["structured"] 里。直接从结构化事实确定性渲染，保护高价值
            # 真实数据（metric 数值+趋势、trace 请求→响应+trace_id、决定性
            # 日志行）不被盲截断；丢弃巨大的 QUERY DSL 噪声。
            # K8s / 其他工具的 result 文本本身可读，保持原路径（头尾保护截断）。
            if normalized_tool in OBSERVABILITY_QUERY_TOOLS:
                data = self._render_observability_structured(ev)
            else:
                data = str(ev.get("result") or ev.get("result_preview") or "")
                if len(data) > _TOOL_ENTRY_CHAR_LIMIT:
                    head_len = int(_TOOL_ENTRY_CHAR_LIMIT * 0.4)
                    tail_len = _TOOL_ENTRY_CHAR_LIMIT - head_len - 24
                    data = (
                        data[:head_len]
                        + "\n…(中段元数据已截断)…\n"
                        + data[-tail_len:]
                    )
            if not data.strip():
                continue
            node = ev.get("node", "")
            tool_args = ev.get("tool_args") or {}
            # 去重键必须包含调用参数：可观测性工具的结果都以相同的
            # OBSERVABILITY_QUERY 契约头开场，只按结果前缀去重会把
            # 补采结果（如 trace_id 定向 span、range 趋势）当成重复丢掉。
            args_key = ""
            if isinstance(tool_args, dict) and tool_args:
                try:
                    args_key = json.dumps(
                        tool_args, ensure_ascii=False, sort_keys=True
                    )[:150]
                except Exception:
                    args_key = str(sorted(tool_args.keys()))
            key = f"{tool_name}:{args_key}:{data[:80]}"
            if key in seen:
                continue
            seen.add(key)
            args_text = ""
            if isinstance(tool_args, dict) and tool_args:
                try:
                    args_text = json.dumps(tool_args, ensure_ascii=False)[:200]
                except Exception:
                    args_text = ""
            header = f"### [{node}] {tool_name}"
            if args_text:
                header += f" | 参数: {args_text}"
            parts.append(f"{header}\n{data}")

        if not parts:
            return ""
        return "\n\n".join(parts[:_TOOL_ENTRY_MAX_COUNT])

    @classmethod
    def _render_observability_structured(cls, ev: dict) -> str:
        """从可观测性工具的 ev["structured"] 确定性渲染真实值。

        第一性原理：结构化事实（facts）里每一条都是自成单元的真实值，
        逐条紧凑渲染并按条数上限保留（丢整条、不砍值）。QUERY DSL 噪声丢弃，
        只保留短查询提示。coverage=empty/absent 如实呈现（诚实空结果）。
        无 structured 时回退到 result 文本（头尾保护截断）。
        """
        structured = ev.get("structured")
        if not isinstance(structured, dict):
            return cls._fallback_result_text(ev)

        dimension = str(structured.get("dimension") or "").strip()
        coverage = str(structured.get("coverage") or "").strip()
        facts = structured.get("facts")
        if not isinstance(facts, list) or not facts:
            # 真实空结果：诚实呈现，不编造
            hint = cls._observability_query_hint(structured)
            tail = f" | 查询: {hint}" if hint else ""
            return f"[{dimension or '可观测性'}] coverage={coverage or 'empty'}（本次查询未返回真实数据）{tail}"

        lines = []
        for fact in facts[:_OBS_FACTS_PER_CALL]:
            if not isinstance(fact, dict):
                continue
            rendered = cls._render_observability_fact(fact)
            if rendered:
                lines.append(f"- {rendered}")
        hint = cls._observability_query_hint(structured)
        header = f"[{dimension or '可观测性'}] coverage={coverage or 'present'}"
        if hint:
            header += f" | 查询: {hint}"
        dropped = len(facts) - len(lines)
        body = "\n".join(lines)
        if dropped > 0:
            body += f"\n- …（另有 {dropped} 条真实事实，已按条数上限省略）"
        return f"{header}\n{body}" if body else header

    @staticmethod
    def _observability_query_hint(structured: dict) -> str:
        """从结构化 query 里提取简短查询提示（丢弃冗长 DSL）。"""
        query = structured.get("query")
        if not isinstance(query, dict):
            return ""
        # metric: promql 一行足够短且有价值
        promql = query.get("promql")
        if isinstance(promql, str) and promql:
            return promql[:180]
        # logging: index + keywords
        idx = query.get("index")
        if idx:
            kw = query.get("keywords") or []
            kw_txt = (",".join(str(k) for k in kw)) if kw else ""
            return f"index={idx}" + (f" keywords={kw_txt}" if kw_txt else "")
        # tracing: 只标注数据源，丢弃巨大 SQL
        if query.get("sql"):
            return "DeepFlow L7 / Tempo"
        return ""

    @classmethod
    def _render_observability_fact(cls, fact: dict) -> str:
        """把一条结构化事实渲染成紧凑的人类可读真实值。"""
        name = str(fact.get("name") or "").strip()
        value = fact.get("value")
        dimension = str(fact.get("dimension") or "").strip()

        # Tracing：l7_flow / application_span → 请求 → 响应 + trace_id
        if name in {"l7_flow", "application_span", "span", "flow"} and isinstance(value, dict):
            req_type = (
                value.get("request_type")
                or value.get("http.request.method")
                or (value.get("attributes") or {}).get("http.request.method")
                or ""
            )
            resource = (
                value.get("request_resource")
                or value.get("http.route")
                or value.get("name")
                or (value.get("attributes") or {}).get("http.route")
                or ""
            )
            code = (
                value.get("response_code")
                or value.get("http.response.status_code")
                or (value.get("attributes") or {}).get("http.response.status_code")
            )
            dur = value.get("response_duration") or value.get("duration_us")
            tid = fact.get("trace_id") or value.get("trace_id")
            src, dst = value.get("src_ip"), value.get("dst_ip")
            seg = []
            call = f"{req_type} {resource}".strip()
            if call:
                seg.append(call)
            if code is not None:
                seg.append(f"→ {code}")
            if src and dst:
                seg.append(f"{src}→{dst}")
            if dur:
                seg.append(f"{dur}us" if isinstance(dur, (int, float)) else str(dur))
            if tid:
                seg.append(f"trace_id={tid}")
            label = "Span" if name in {"application_span", "span"} else "Flow"
            return f"{label}: " + " ".join(seg) if seg else f"{label}: {cls._compact_value(value)}"

        # Metric：数值 + 单位 + 趋势
        stats = fact.get("stats") if isinstance(fact.get("stats"), dict) else {}
        if dimension == "metrics" or fact.get("unit") or name.startswith(("kube_", "container_", "node_")):
            unit = fact.get("unit")
            base = f"{name} = {value}"
            if unit:
                base += f" {unit}"
            first, last = stats.get("first"), stats.get("last")
            if first is not None and last is not None and first != last:
                base += f"（趋势 {first}→{last}）"
            return base

        # Logging：日志原文（一条，非 blob）
        if name in {"log.message", "message"} or dimension == "logging":
            return f"日志: {cls._compact_value(value)}"

        # 其他（topology/k8s/generic）
        return f"{name}: {cls._compact_value(value)}" if name else cls._compact_value(value)

    @staticmethod
    def _compact_value(value) -> str:
        if isinstance(value, str):
            text = value
        else:
            try:
                text = json.dumps(value, ensure_ascii=False)
            except Exception:
                text = str(value)
        return text[:_OBS_FACT_VALUE_LIMIT]

    @staticmethod
    def _fallback_result_text(ev: dict) -> str:
        data = str(ev.get("result") or ev.get("result_preview") or "")
        if len(data) > _TOOL_ENTRY_CHAR_LIMIT:
            head_len = int(_TOOL_ENTRY_CHAR_LIMIT * 0.4)
            tail_len = _TOOL_ENTRY_CHAR_LIMIT - head_len - 24
            data = data[:head_len] + "\n…(中段已截断)…\n" + data[-tail_len:]
        return data

    @staticmethod
    def _build_evidence_summary(evidence_analysis: str) -> str:
        """把 evidence_analysis JSON 压成人类可读的采集摘要（不含大段原始数据）。"""
        try:
            data = json.loads(evidence_analysis) if evidence_analysis else {}
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, TypeError, json.JSONDecodeError):
            text = str(evidence_analysis or "")
            return text[:_SECTION_CHAR_LIMITS["evidence"]]

        lines: List[str] = []
        inventory = data.get("evidence_inventory") or []
        if inventory:
            lines.append("- 已采集证据清单:")
            for item in inventory[:20]:
                if isinstance(item, dict):
                    desc = (
                        item.get("description")
                        or item.get("id")
                        or item.get("evidence_type")
                        or ""
                    )
                    status = item.get("status") or item.get("state") or ""
                    tool = item.get("tool") or item.get("source") or ""
                    entry = " | ".join(str(x) for x in [desc, tool, status] if x)
                    lines.append(f"  - {entry[:200]}")
                else:
                    lines.append(f"  - {str(item)[:200]}")

        missing = data.get("diagnostic_evidence_missing") or []
        missing_reasons = data.get("missing_reasons") or []
        if missing:
            lines.append("- 缺失证据: " + "; ".join(str(m)[:120] for m in missing[:10]))
        if missing_reasons:
            lines.append("- 缺失原因: " + "; ".join(str(m)[:120] for m in missing_reasons[:10]))

        text = "\n".join(lines) if lines else "（无结构化采集摘要）"
        return text[:_SECTION_CHAR_LIMITS["evidence"]]

    @staticmethod
    def _build_rca_summary(rca_analysis: str) -> str:
        """把 rca_analysis JSON 压成人类可读的根因分析摘要。"""
        try:
            data = json.loads(rca_analysis) if rca_analysis else {}
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, TypeError, json.JSONDecodeError):
            text = str(rca_analysis or "")
            return text[:_SECTION_CHAR_LIMITS["rca"]]

        lines: List[str] = []
        status = data.get("diagnostic_status") or ""
        if status:
            lines.append(f"- 诊断状态: {status}")
        root_cause = (data.get("root_cause") or "").strip()
        if root_cause:
            lines.append(f"- 根因结论: {root_cause}")
        causal_chain = data.get("causal_chain") or {}
        if isinstance(causal_chain, dict) and causal_chain:
            lines.append("- 因果链:")
            for key, value in list(causal_chain.items())[:6]:
                lines.append(f"  - {key}: {str(value)[:200]}")

        for entry in (data.get("evidence_analysis") or [])[:10]:
            if isinstance(entry, dict):
                text = entry.get("analysis") or entry.get("conclusion") or ""
                evid = entry.get("evidence") or entry.get("evidence_id") or ""
                combined = " | ".join(str(x) for x in [evid, text] if x)
                if combined:
                    lines.append(f"- 证据分析: {combined[:250]}")

        unknowns = data.get("unknowns") or []
        if unknowns:
            lines.append("- 未确认项: " + "; ".join(str(u)[:120] for u in unknowns[:6]))
        limitations = (data.get("limitations") or "").strip()
        if limitations:
            lines.append(f"- 局限性: {limitations[:300]}")

        text = "\n".join(lines) if lines else "（无结构化根因分析）"
        return text[:_SECTION_CHAR_LIMITS["rca"]]

    @staticmethod
    def _parse_formal_rca(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        try:
            parsed = json.loads(value) if value else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @classmethod
    def _formal_rca_is_valid(cls, rca: Mapping[str, Any]) -> bool:
        claim = rca.get("claim_validation")
        validation_disabled = (
            isinstance(claim, dict) and claim.get("enabled") is False
        )
        if validation_disabled:
            return (
                str(rca.get("diagnostic_status") or "") == "diagnosed"
                and bool(
                    str(
                        rca.get("root_cause_summary")
                        or rca.get("root_cause")
                        or ""
                    ).strip()
                )
            )
        if not isinstance(claim, dict):
            return False
        publishable = claim.get(
            "diagnosis_publishable",
            claim.get("diagnosis_supported"),
        )
        if publishable is None:
            publishable = (
                claim.get("valid") is True
                and bool(rca.get("supporting_fact_ids"))
            )
        return (
            str(rca.get("diagnostic_status") or "") == "diagnosed"
            and publishable is True
        )

    @classmethod
    def _render_single_authoritative_report(
        cls,
        *,
        question: str,
        state: WorkflowState,
        rca_analysis: Any,
    ) -> str:
        """Render one diagnosis without granting narrative text fact authority."""
        rca = cls._parse_formal_rca(rca_analysis)
        valid = cls._formal_rca_is_valid(rca)
        status = "diagnosed" if valid else "inconclusive"
        claim = (
            rca.get("claim_validation")
            if isinstance(rca.get("claim_validation"), dict)
            else {}
        )
        rca_input = (
            state.get("rca_input_projection")
            if isinstance(state.get("rca_input_projection"), dict)
            else {}
        )
        selected_facts = [
            fact
            for fact in (rca_input.get("selected_facts") or [])
            if isinstance(fact, dict)
        ]
        snapshot = (
            state.get("entity_evidence_snapshot")
            if isinstance(state.get("entity_evidence_snapshot"), dict)
            else {}
        )
        dimension_evidence = (
            snapshot.get("dimension_evidence_by_entity")
            if isinstance(snapshot.get("dimension_evidence_by_entity"), dict)
            else {}
        )
        root_cause = (
            str(
                rca.get("root_cause_summary")
                or rca.get("root_cause")
                or "证据不足"
            )
            if valid
            else "证据不足"
        )
        supporting_ids = [
            str(fact_id)
            for fact_id in (rca.get("supporting_fact_ids") or [])
        ] if valid else []
        lines = [
            "# 🔬 单实体诊断报告（确定性事实权威）",
            "",
            f"> 用户问题：{question}",
            "",
            f"diagnostic_status: {status}",
            f"claim_validation: {'valid' if valid else 'invalid'}",
            f"root_cause: {root_cause}",
            f"confidence: {float(rca.get('confidence') or 0.0):.0%}",
        ]
        entity_ids = [
            str(item)
            for item in (rca_input.get("authoritative_entity_ids") or [])
            if str(item).strip()
        ]
        if entity_ids:
            lines.append("authoritative_entities: " + ", ".join(entity_ids))
        lines.append(
            "supporting_fact_ids: "
            + (", ".join(supporting_ids) if supporting_ids else "[]")
        )
        reasons = [
            str(item)
            for item in [
                *(claim.get("reasons") or []),
                *(rca.get("unknowns") or []),
            ]
            if str(item).strip()
        ]
        if reasons:
            lines.extend([
                "",
                "## 校验边界",
                *[f"- {item}" for item in dict.fromkeys(reasons)],
            ])

        lines.extend([
            "",
            "## 可观测性真实事实",
            "",
            "| 维度 | 状态 | 真实结果 |",
            "|---|---|---|",
        ])
        for dimension in ("kubernetes", "metrics", "logging", "tracing"):
            facts = [
                fact
                for fact in selected_facts
                if str(fact.get("dimension") or "") == dimension
            ]
            rendered = "<br>".join(
                "[{source}] {value} `(fact_id={fact_id})`".format(
                    source=fact.get("source_system") or "unknown",
                    value=cls._display_fact_with_semantics(fact),
                    fact_id=fact.get("fact_id") or "unknown",
                )
                for fact in facts
            ) or "未选择到可展示的真实事实"
            observed_statuses = [
                str(dimensions.get(dimension, {}).get("status") or "")
                for dimensions in dimension_evidence.values()
                if isinstance(dimensions, dict)
                and isinstance(dimensions.get(dimension), dict)
            ]
            status_priority = (
                "present",
                "error",
                "unknown",
                "absent",
                "not_applicable",
                "unselected",
            )
            dimension_status = next(
                (
                    status
                    for status in status_priority
                    if status in observed_statuses
                ),
                "unselected",
            )
            if facts:
                dimension_status = "present"
            lines.append(
                "| {dimension} | {status} | {facts} |".format(
                    dimension=dimension,
                    status=dimension_status,
                    facts=cls._multi_group_table_cell(rendered),
                )
            )
        return "\n".join(lines)

    @staticmethod
    def _render_structured_remediation_only(content: str) -> str:
        """Retain the typed remediation contract, never an unvalidated diagnosis."""
        try:
            plan = extract_remediation_plan(content or "")
        except Exception as exc:
            logger.warning(
                "⚠️ [conclusion] 丢弃无效结构化修复计划: %s",
                exc,
            )
            return ""
        if plan is None:
            return ""
        payload = asdict(plan)
        return (
            "## 🧩 结构化修复计划（不构成根因证据）\n\n"
            "```json\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n```"
        )

    # ------------------------------------------------------------------
    # LLM 生成
    # ------------------------------------------------------------------
    def _get_response_language(self) -> str:
        if self.holmes_service and hasattr(self.holmes_service, "get_response_language"):
            return self.holmes_service.get_response_language()
        return "zh"

    def _get_conclusion_prompt(self) -> str:
        return get_workflow_prompt(
            "conclusion",
            prompt_language=self._get_prompt_language(),
            response_language=self._get_response_language(),
        )

    def _get_query_conclusion_prompt(self) -> str:
        return """你是 K8s 查询结果总结器。

任务：把输入中的 `QUERY 结构化结果` 和真实工具数据总结为面向用户的 Markdown。
输出契约：只输出一个 JSON 对象，schema 为 `{"markdown_report": "..."}`，不要输出 ```json 代码块之外的任何文字。
边界：
- 只回答用户明确询问的对象、维度和指标。
- 必须使用表格展示已获取的数据。
- 必须说明数据来源和单位。
- 不要做根因分析，不要写修复建议，除非用户明确要求。
- 不要编造、补算、猜测缺失值；缺失项写“未获取到”。
- 输出必须是中文。"""

    def _get_query_mode(self) -> str:
        wf_config = getattr(self, "workflow_config_override", None) or {}
        return str(wf_config.get("query_mode", "full")).strip().lower() or "full"

    def _get_conclusion_config(self) -> Dict[str, Any]:
        workflow_config = self._get_workflow_config()
        if not isinstance(workflow_config, dict):
            return {}
        conclusion_config = workflow_config.get("conclusion")
        return conclusion_config if isinstance(conclusion_config, dict) else {}

    def _get_conclusion_presentation_mode(self) -> str:
        """Use the report agent by default; deterministic cards are opt-in only."""
        mode = str(
            self._get_conclusion_config().get("presentation_mode") or "agent"
        ).strip().lower()
        return mode if mode in {"agent", "deterministic"} else "agent"

    def _include_raw_evidence_appendix(self) -> bool:
        """Raw tool output remains archived and is not duplicated in reports by default."""
        return bool(
            self._get_conclusion_config().get("include_raw_evidence_appendix", False)
        )

    def _resolve_conclusion_max_tokens(
        self,
        *,
        layer: Optional[Layer],
        requested: Optional[int],
    ) -> int:
        """QUERY 回答较短、诊断报告较长，可分别配置输出预算。"""
        cap = _get_conclusion_max_tokens_cap()
        configured: Optional[int] = None
        wf_config = self._get_workflow_config()
        conclusion_cfg = wf_config.get("conclusion", {}) if isinstance(wf_config, dict) else {}
        if isinstance(conclusion_cfg, dict):
            max_tokens_cfg = conclusion_cfg.get("max_tokens")
            if isinstance(max_tokens_cfg, dict):
                mode_key = "query" if layer == Layer.QUERY else "diagnosis"
                configured = self._parse_positive_int(max_tokens_cfg.get(mode_key))
            else:
                configured = self._parse_positive_int(max_tokens_cfg)

        selected = self._parse_positive_int(requested) or configured or cap
        return min(selected, cap)

    @staticmethod
    def _parse_positive_int(value: Any) -> Optional[int]:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def _resolve_context_token_budget(self, *, output_reserved: int) -> int:
        """从真实模型窗口推导输入预算；CONCLUSION_TOKEN_BUDGET 可显式覆盖。"""
        explicit = self._parse_positive_int(os.getenv("CONCLUSION_TOKEN_BUDGET"))
        if explicit:
            return explicit

        window = self._parse_positive_int(os.getenv("MODEL_CONTEXT_WINDOW")) or 32000
        safety_margin = self._parse_positive_int(os.getenv("CONCLUSION_CONTEXT_SAFETY_MARGIN")) or 2048
        budget = window - max(output_reserved, 0) - safety_margin
        return max(2048, budget)

    def _generate_with_llm(
        self,
        question: str,
        layer_analysis: str,
        evidence_analysis: str,
        rca_analysis: str,
        conclusion_max_tokens: Optional[int] = None,
        layer: Optional[Layer] = None,
        tool_data_text: str = "",
        query_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """单次 LLM 调用生成最终报告。

        诊断报告是面向人的 Markdown 输出，使用纯文本生成（call_simple），
        由 CONCLUSION_FORMATTER_PROMPT 富模板保证结构稳定。
        QUERY 模式使用短 JSON schema，便于稳定渲染查询摘要。
        """
        max_tokens = self._resolve_conclusion_max_tokens(
            layer=layer,
            requested=conclusion_max_tokens,
        )
        self._conclusion_thinking = []

        if layer == Layer.QUERY:
            return self._generate_query_with_llm(
                question=question,
                tool_data_text=tool_data_text,
                query_result=query_result,
                max_tokens=max_tokens,
            )

        # ---- 诊断模式：富模板 + 真实数据，单次纯文本调用 ----
        layer_section = layer_analysis[:_SECTION_CHAR_LIMITS["layer"]]
        evidence_summary = self._build_evidence_summary(evidence_analysis)
        rca_summary = self._build_rca_summary(rca_analysis)
        tool_section = tool_data_text[:_SECTION_CHAR_LIMITS["tool_data"]]

        instruction = f"""# 任务
用户的原始问题是「{question}」。只按 system prompt 中唯一的报告结构组织输入事实；
证据表的“真实原始结果”必须摘自工具数据，不输出修复建议或验证步骤。"""

        system_prompt_text = self._get_conclusion_prompt()

        def build_user_message() -> str:
            return f"""# 用户问题
{question}

# 阶段1：问题定位
{layer_section}

# 阶段2：证据采集摘要
{evidence_summary}

# 阶段3：根因分析
{rca_summary}

# 工具采集的真实数据（重要！报告必须引用这些真实数据）
{tool_section or "（本轮未采集到工具数据）"}

{instruction}"""

        user_message = build_user_message()

        # Token 预算控制：超出预算时按段落大小从大到小硬截断（不再二次调 LLM 压缩）
        token_budget = self._resolve_context_token_budget(output_reserved=max_tokens)
        estimated = self._estimate_tokens(system_prompt_text + user_message)
        logger.info(
            "📦 [conclusion] context budget | estimated=%d budget=%d",
            estimated, token_budget,
        )
        if estimated > token_budget:
            overflow_chars = (estimated - token_budget) * 2
            sections = sorted(
                [
                    ("tool_section", tool_section),
                    ("layer_section", layer_section),
                    ("evidence_summary", evidence_summary),
                    ("rca_summary", rca_summary),
                ],
                key=lambda x: len(x[1]),
                reverse=True,
            )
            for name, content in sections:
                if overflow_chars <= 0:
                    break
                keep = max(1000, len(content) - overflow_chars)
                if keep < len(content):
                    overflow_chars -= len(content) - keep
                    truncated = content[:keep] + "\n…（超出上下文预算已截断）"
                    if name == "tool_section":
                        tool_section = truncated
                    elif name == "layer_section":
                        layer_section = truncated
                    elif name == "evidence_summary":
                        evidence_summary = truncated
                    elif name == "rca_summary":
                        rca_summary = truncated
            user_message = build_user_message()
            logger.info(
                "📦 [conclusion] 截断后预估 %d tokens",
                self._estimate_tokens(system_prompt_text + user_message),
            )

        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            raise RuntimeError("[conclusion] ai_call 未设置，无法生成报告")

        start_time = time.time()
        logger.info("📍 [conclusion] plain markdown 开始 | max_tokens=%d", max_tokens)
        self._archive_node_input({
            "node": self.node_id,
            "question": question,
            "user_message": user_message,
            "system_prompt_chars": len(system_prompt_text),
            "user_message_chars": len(user_message),
            "max_tokens": max_tokens,
            "structured_method": "plain_markdown",
        })
        content = ai_call.call_simple(
            system_prompt=system_prompt_text,
            question=user_message,
            max_tokens=max_tokens,
        )
        llm_duration_ms = (time.time() - start_time) * 1000
        if self.metrics:
            self.metrics.record_llm_call("conclusion", llm_duration_ms)
        logger.info(
            "LLM 报告生成完成 (耗时 %.0fms, 长度: %d)",
            llm_duration_ms, len(content or ""),
        )
        return self._strip_think_blocks(content or "")

    def _generate_query_with_llm(
        self,
        *,
        question: str,
        tool_data_text: str,
        query_result: Optional[Dict[str, Any]],
        max_tokens: int,
    ) -> str:
        """QUERY 模式：短 JSON schema 结构化总结。"""
        query_result_section = ""
        if query_result:
            try:
                query_result_section = (
                    "\n# QUERY 结构化结果（来自上游真实工具结果整理）\n"
                    f"{json.dumps(query_result, ensure_ascii=False)}\n"
                )
            except Exception:
                query_result_section = ""

        tool_section = ""
        if tool_data_text:
            tool_section = (
                "\n# 工具采集的真实数据（必须引用）\n"
                f"{tool_data_text[:_SECTION_CHAR_LIMITS['tool_data']]}\n"
            )

        instruction = get_conclusion_mode_instruction(
            "query",
            question,
            prompt_language=self._get_prompt_language(),
        )
        user_message = f"""# 用户问题
{question}

{query_result_section}
{tool_section}
{instruction}"""

        start_time = time.time()
        structured, _response, thinking_events = self._call_structured_agent(
            question=user_message,
            system_prompt=self._get_query_conclusion_prompt(),
            schema=QueryConclusionOutput,
            use_tools=False,
            max_tokens=max_tokens,
            use_native_structured=False,
            allow_text_fallback=True,
        )
        if self.metrics:
            self.metrics.record_llm_call("conclusion", (time.time() - start_time) * 1000)
        self._conclusion_thinking = thinking_events or []
        content = structured.markdown_report if structured is not None else ""
        return self._strip_think_blocks(content or "")

    # ------------------------------------------------------------------
    # 多异常并发模式：正式组级 RCA + 代码确定性拼接真实数据
    # ------------------------------------------------------------------
    def _generate_multi_group_report(
        self,
        *,
        question: str,
        group_results: List[Dict[str, Any]],
        conclusion_max_tokens: Optional[int] = None,
    ) -> str:
        """Let the report agent explain canonical group facts in human language.

        Root causes and facts remain authoritative structured inputs.  The
        conclusion model controls only presentation: evidence selection,
        wording, cross-dimension correlation, and Markdown layout.
        """
        group_results = self._project_formal_group_authority(group_results)

        if self._get_conclusion_presentation_mode() == "agent":
            try:
                report = self._generate_multi_group_report_with_agent(
                    question=question,
                    group_results=group_results,
                    conclusion_max_tokens=conclusion_max_tokens,
                )
            except Exception as exc:
                logger.exception(
                    "[conclusion] multi-group report agent failed; using minimal fallback: %s",
                    exc,
                )
                report = ""
            if report.strip():
                return report.strip()

        return self._generate_multi_group_deterministic_fallback(
            question=question,
            group_results=group_results,
        )

    @staticmethod
    def _parse_json_object(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if not isinstance(value, str) or not value.strip():
            return {}
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _canonical_fact_for_report_agent(fact: Mapping[str, Any]) -> Dict[str, Any]:
        """Forward raw fact semantics without generating presentation prose."""
        raw_value = fact.get("value")
        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if stripped.startswith(("{", "[")):
                try:
                    raw_value = json.loads(stripped)
                except (TypeError, ValueError, json.JSONDecodeError):
                    pass

        payload: Dict[str, Any] = {}
        for key in (
            "fact_id",
            "dimension",
            "fact_type",
            "attribute",
            "source_system",
            "timestamp",
            "unit",
            "evidence_role",
        ):
            value = fact.get(key)
            if value not in (None, "", [], {}):
                payload[key] = value
        payload["value"] = raw_value

        metadata = fact.get("metadata") if isinstance(fact.get("metadata"), Mapping) else {}
        report_metadata = {
            key: metadata[key]
            for key in (
                "labels",
                "stats",
                "sample_count",
                "trend_evaluable",
                "pattern_count",
                "pattern_exemplar",
                "trace_id",
                "span_id",
            )
            if metadata.get(key) not in (None, "", [], {})
        }
        if report_metadata:
            payload["metadata"] = report_metadata
        return payload

    @staticmethod
    def _json_signature(value: Any) -> str:
        """Return a stable signature for structural grouping only."""
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _numeric_value(value: Any) -> Optional[float]:
        if isinstance(value, bool):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _ordered_unique(values: List[Any], *, limit: Optional[int] = None) -> List[Any]:
        result: List[Any] = []
        seen = set()
        for value in values:
            if value in (None, ""):
                continue
            signature = str(value)
            if signature in seen:
                continue
            seen.add(signature)
            result.append(value)
            if limit is not None and len(result) >= limit:
                break
        return result

    @classmethod
    def _deduplicate_report_facts(
        cls,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Collapse exact semantic duplicates without choosing report evidence."""
        buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for fact in facts:
            semantic = {
                key: value
                for key, value in fact.items()
                if key not in {"fact_id", "timestamp"}
            }
            buckets[cls._json_signature(semantic)].append(fact)

        compacted: List[Dict[str, Any]] = []
        for bucket in buckets.values():
            if len(bucket) == 1:
                compacted.append(bucket[0])
                continue
            item = {
                key: value
                for key, value in bucket[0].items()
                if key not in {"fact_id", "timestamp"}
            }
            item["aggregation"] = "exact_semantic_duplicates"
            item["occurrence_count"] = len(bucket)
            item["fact_ids"] = cls._ordered_unique(
                [fact.get("fact_id") for fact in bucket]
            )
            timestamps = sorted(
                str(fact.get("timestamp"))
                for fact in bucket
                if fact.get("timestamp") not in (None, "")
            )
            if timestamps:
                item["time_range"] = {
                    "first": timestamps[0],
                    "last": timestamps[-1],
                }
            compacted.append(item)
        return compacted

    @classmethod
    def _compact_metric_facts(
        cls,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Keep metric semantics while removing repeated entity labels and zero siblings."""
        redundant_labels = {
            "__name__", "namespace", "pod", "uid", "instance", "job",
            "endpoint", "prometheus", "prometheus_replica",
        }
        normalized: List[Dict[str, Any]] = []
        for source in facts:
            fact = dict(source)
            metadata = dict(fact.get("metadata") or {})
            labels = metadata.get("labels")
            if isinstance(labels, Mapping):
                labels = {
                    key: value
                    for key, value in labels.items()
                    if key not in redundant_labels
                }
                if labels:
                    metadata["labels"] = labels
                else:
                    metadata.pop("labels", None)

            sample_count = cls._parse_positive_int(metadata.get("sample_count"))
            if not metadata.get("trend_evaluable") and (sample_count or 0) <= 1:
                # first=last=min=max on an instant sample is duplicate data, not a trend.
                metadata.pop("stats", None)
            if metadata:
                fact["metadata"] = metadata
            else:
                fact.pop("metadata", None)
            normalized.append(fact)

        zero_buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        passthrough: List[Dict[str, Any]] = []
        for fact in normalized:
            numeric = cls._numeric_value(fact.get("value"))
            if numeric != 0:
                passthrough.append(fact)
                continue
            signature = cls._json_signature({
                "source_system": fact.get("source_system"),
                "fact_type": fact.get("fact_type"),
                "attribute": fact.get("attribute"),
                "unit": fact.get("unit"),
                "evidence_role": fact.get("evidence_role"),
            })
            zero_buckets[signature].append(fact)

        for bucket in zero_buckets.values():
            if len(bucket) == 1:
                passthrough.append(bucket[0])
                continue
            first = bucket[0]
            grouped = {
                key: first[key]
                for key in (
                    "source_system", "fact_type", "attribute", "unit", "evidence_role"
                )
                if first.get(key) not in (None, "")
            }
            grouped.update({
                "aggregation": "zero_valued_series",
                "value": 0,
                "series_count": len(bucket),
                "series_labels": [
                    fact.get("metadata", {}).get("labels") or {}
                    for fact in bucket
                ],
                "fact_ids": cls._ordered_unique(
                    [fact.get("fact_id") for fact in bucket]
                ),
                "metadata": {
                    "sample_count_per_series": [
                        fact.get("metadata", {}).get("sample_count")
                        for fact in bucket
                    ],
                    "trend_evaluable": False,
                },
            })
            passthrough.append(grouped)
        return cls._deduplicate_report_facts(passthrough)

    @classmethod
    def _compact_kubernetes_facts(
        cls,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Group same-attribute Kubernetes records while retaining every value."""
        buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for fact in cls._deduplicate_report_facts(facts):
            signature = cls._json_signature({
                "source_system": fact.get("source_system"),
                "fact_type": fact.get("fact_type"),
                "attribute": fact.get("attribute"),
                "evidence_role": fact.get("evidence_role"),
            })
            buckets[signature].append(fact)

        compacted: List[Dict[str, Any]] = []
        for bucket in buckets.values():
            if len(bucket) == 1:
                compacted.append(bucket[0])
                continue
            first = bucket[0]
            compacted.append({
                **{
                    key: first[key]
                    for key in (
                        "source_system", "fact_type", "attribute", "evidence_role"
                    )
                    if first.get(key) not in (None, "")
                },
                "aggregation": "same_attribute_records",
                "record_count": len(bucket),
                "records": [
                    {
                        key: fact[key]
                        for key in ("fact_id", "fact_ids", "timestamp", "value", "metadata")
                        if fact.get(key) not in (None, "", [], {})
                    }
                    for fact in bucket
                ],
            })
        return compacted

    @classmethod
    def _compact_log_facts(
        cls,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Aggregate repeated structured log records without writing display prose."""
        buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        unstructured: List[Dict[str, Any]] = []
        identity_keys = {
            "timestamp", "trace_id", "span_id", "parent_span_id", "case_run_id",
            "duration_ms", "duration_us", "pod",
        }
        status_keys = {
            "http_status", "status", "status_code", "response_code", "exit_code", "code",
        }

        for fact in facts:
            value = fact.get("value")
            if not isinstance(value, Mapping):
                unstructured.append(fact)
                continue
            pattern: Dict[str, Any] = {}
            dynamic_numeric: Dict[str, Any] = {}
            for key, item in value.items():
                if key in identity_keys:
                    continue
                numeric = cls._numeric_value(item)
                if numeric is not None and key not in status_keys:
                    dynamic_numeric[key] = item
                else:
                    pattern[key] = item
            signature = cls._json_signature({
                "source_system": fact.get("source_system"),
                "attribute": fact.get("attribute"),
                "pattern": pattern,
            })
            buckets[signature].append({
                "fact": fact,
                "pattern": pattern,
                "dynamic_numeric": dynamic_numeric,
                "trace_id": value.get("trace_id")
                or (fact.get("metadata") or {}).get("trace_id"),
            })

        compacted = cls._deduplicate_report_facts(unstructured)
        for bucket in buckets.values():
            bucket.sort(key=lambda item: str(item["fact"].get("timestamp") or ""))
            first_fact = bucket[0]["fact"]
            numeric_fields: Dict[str, Dict[str, Any]] = {}
            numeric_keys = cls._ordered_unique([
                key
                for item in bucket
                for key in item["dynamic_numeric"].keys()
            ])
            for key in numeric_keys:
                ordered = [
                    item["dynamic_numeric"].get(key)
                    for item in bucket
                    if cls._numeric_value(item["dynamic_numeric"].get(key)) is not None
                ]
                if not ordered:
                    continue
                numeric = [cls._numeric_value(value) for value in ordered]
                numeric_fields[key] = {
                    "first": ordered[0],
                    "last": ordered[-1],
                    "min": min(numeric),
                    "max": max(numeric),
                }
            timestamps = [
                str(item["fact"].get("timestamp"))
                for item in bucket
                if item["fact"].get("timestamp") not in (None, "")
            ]
            aggregated: Dict[str, Any] = {
                "aggregation": "repeated_log_pattern",
                "source_system": first_fact.get("source_system"),
                "fact_type": first_fact.get("fact_type"),
                "attribute": first_fact.get("attribute"),
                "pattern": bucket[0]["pattern"],
                "occurrence_count": len(bucket),
                "fact_ids": cls._ordered_unique(
                    [item["fact"].get("fact_id") for item in bucket]
                ),
                "trace_ids": cls._ordered_unique(
                    [item.get("trace_id") for item in bucket], limit=12
                ),
            }
            if timestamps:
                aggregated["time_range"] = {
                    "first": timestamps[0],
                    "last": timestamps[-1],
                }
            if numeric_fields:
                aggregated["numeric_fields"] = numeric_fields
            compacted.append({
                key: value
                for key, value in aggregated.items()
                if value not in (None, "", [], {})
            })
        return compacted

    @classmethod
    def _compact_tracing_facts(
        cls,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Aggregate equivalent network flows; preserve application spans separately."""
        flow_buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        spans_and_other: List[Dict[str, Any]] = []
        for fact in facts:
            value = fact.get("value")
            is_flow = (
                str(fact.get("fact_type") or "").lower() == "flow"
                or str(fact.get("attribute") or "").lower() == "l7_flow"
            )
            if not is_flow or not isinstance(value, Mapping):
                spans_and_other.append(fact)
                continue
            pattern = {
                key: value.get(key)
                for key in (
                    "protocol", "request_type", "request_resource", "response_code",
                    "response_status", "src_ip", "dst_ip",
                )
                if value.get(key) not in (None, "")
            }
            signature = cls._json_signature({
                "source_system": fact.get("source_system"),
                "attribute": fact.get("attribute"),
                "pattern": pattern,
            })
            flow_buckets[signature].append({"fact": fact, "pattern": pattern})

        compacted = cls._deduplicate_report_facts(spans_and_other)
        for bucket in flow_buckets.values():
            bucket.sort(key=lambda item: str(item["fact"].get("timestamp") or ""))
            first_fact = bucket[0]["fact"]
            durations = []
            for item in bucket:
                duration = cls._numeric_value(item["fact"].get("value", {}).get("duration_us"))
                if duration is not None:
                    durations.append(duration)
            timestamps = [
                str(item["fact"].get("timestamp"))
                for item in bucket
                if item["fact"].get("timestamp") not in (None, "")
            ]
            trace_ids = cls._ordered_unique([
                item["fact"].get("value", {}).get("trace_id")
                or (item["fact"].get("metadata") or {}).get("trace_id")
                for item in bucket
            ], limit=12)
            aggregated: Dict[str, Any] = {
                "aggregation": "equivalent_l7_flows",
                "source_system": first_fact.get("source_system"),
                "fact_type": "flow",
                "attribute": first_fact.get("attribute"),
                "flow": bucket[0]["pattern"],
                "occurrence_count": len(bucket),
                "fact_ids": cls._ordered_unique(
                    [item["fact"].get("fact_id") for item in bucket]
                ),
                "trace_ids": trace_ids,
            }
            if timestamps:
                aggregated["time_range"] = {
                    "first": timestamps[0],
                    "last": timestamps[-1],
                }
            if durations:
                aggregated["duration_us"] = {
                    "min": min(durations),
                    "max": max(durations),
                }
            compacted.append({
                key: value
                for key, value in aggregated.items()
                if value not in (None, "", [], {})
            })
        return compacted

    @classmethod
    def _compact_facts_for_report_agent(
        cls,
        dimension: str,
        facts: List[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        canonical = [cls._canonical_fact_for_report_agent(fact) for fact in facts]
        if dimension == "metrics":
            return cls._compact_metric_facts(canonical)
        if dimension == "logging":
            return cls._compact_log_facts(canonical)
        if dimension == "tracing":
            return cls._compact_tracing_facts(canonical)
        if dimension == "kubernetes":
            return cls._compact_kubernetes_facts(canonical)
        return cls._deduplicate_report_facts(canonical)

    @classmethod
    def _failed_tool_attempts_for_report_agent(
        cls,
        events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        failures: List[Dict[str, Any]] = []
        for event in events or []:
            if not isinstance(event, dict) or event.get("type") != "tool_result":
                continue
            structured = event.get("structured") if isinstance(event.get("structured"), dict) else {}
            coverage = str(structured.get("coverage") or "").strip().lower()
            structured_status = str(structured.get("status") or "").strip().lower()
            failed = (
                event.get("status") != "success"
                or coverage == "error"
                or structured_status.endswith("failed")
                or structured_status in {"tool_error", "query_parse_failed", "command_failed"}
            )
            if not failed:
                continue
            failure = {
                "tool": event.get("tool_name") or "unknown",
                "status": structured.get("status") or event.get("status") or "error",
                "coverage": structured.get("coverage") or "error",
                "arguments": event.get("tool_args") or {},
            }
            detail = (
                structured.get("raw_preview")
                or structured.get("error")
                or event.get("error")
                or event.get("result_preview")
                or event.get("result")
            )
            if detail not in (None, ""):
                failure["detail"] = str(detail)[:1000]
            failures.append(failure)

        # Retries often repeat the same backend error. Preserve retry count and
        # purposes, rather than spending report context on duplicate payloads.
        buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for failure in failures:
            signature = cls._json_signature({
                "tool": failure.get("tool"),
                "status": failure.get("status"),
                "coverage": failure.get("coverage"),
                "detail": failure.get("detail"),
            })
            buckets[signature].append(failure)
        compacted: List[Dict[str, Any]] = []
        for bucket in buckets.values():
            item = dict(bucket[0])
            if len(bucket) > 1:
                item["attempt_count"] = len(bucket)
                item["arguments"] = [
                    failure.get("arguments") or {}
                    for failure in bucket
                ]
            compacted.append(item)
        return compacted

    @classmethod
    def _build_multi_group_report_context(
        cls,
        question: str,
        group_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build an evidence-rich, presentation-neutral report contract.

        The snapshot's RCA input manifest is independent from the RCA model's
        optional supporting_fact_ids.  It bounds context while preserving all
        facts that were already made available to root-cause analysis.
        """
        groups: List[Dict[str, Any]] = []
        for group in group_results:
            snapshot = (
                group.get("entity_evidence_snapshot")
                if isinstance(group.get("entity_evidence_snapshot"), dict)
                else {}
            )
            manifest = (
                snapshot.get("selection_manifest")
                if isinstance(snapshot.get("selection_manifest"), dict)
                else {}
            )
            selected_ids = [
                str(item)
                for item in (manifest.get("rca_input_fact_ids") or [])
                if str(item).strip()
            ]
            selected_set = set(selected_ids)
            dimensions_by_entity = (
                group.get("dimension_evidence_by_entity")
                if isinstance(group.get("dimension_evidence_by_entity"), dict)
                else {}
            )

            entities: List[Dict[str, Any]] = []
            summaries = {
                f"{item.get('namespace', '')}/{item.get('name', '')}": item
                for item in (group.get("entity_summaries") or [])
                if isinstance(item, dict)
            }
            authoritative_entities = [
                item for item in (group.get("entities") or []) if isinstance(item, dict)
            ]
            entity_keys = list(dict.fromkeys([
                *summaries.keys(),
                *[
                    f"{item.get('namespace', '')}/{item.get('name', '')}"
                    for item in authoritative_entities
                ],
            ]))
            for entity_key in entity_keys:
                dimension_payload: Dict[str, Any] = {}
                for dimension in ("kubernetes", "metrics", "logging", "tracing"):
                    summary = (
                        dimensions_by_entity.get(entity_key, {}).get(dimension, {})
                        if isinstance(dimensions_by_entity.get(entity_key), dict)
                        else {}
                    )
                    all_facts = [
                        fact for fact in (summary.get("facts") or [])
                        if isinstance(fact, dict)
                    ]
                    visible_facts = (
                        [fact for fact in all_facts if str(fact.get("fact_id") or "") in selected_set]
                        if selected_set
                        else all_facts
                    )
                    compact_facts = cls._compact_facts_for_report_agent(
                        dimension,
                        visible_facts,
                    )
                    dimension_payload[dimension] = {
                        "status": summary.get("status") or "unselected",
                        "source_systems": summary.get("source_systems") or [],
                        "limitations": summary.get("limitations") or [],
                        "facts": compact_facts,
                    }
                raw_entity_summary = summaries.get(entity_key) or {}
                entity_summary = {
                    key: raw_entity_summary[key]
                    for key in (
                        "namespace", "name", "status", "diagnostic_status",
                        "phenomenon", "unknowns", "limitations",
                    )
                    if raw_entity_summary.get(key) not in (None, "", [], {})
                }
                entities.append({
                    "entity": entity_key,
                    "diagnosis": entity_summary,
                    "dimensions": dimension_payload,
                })

            evidence_analysis = cls._parse_json_object(group.get("evidence_analysis"))
            collection = {
                key: evidence_analysis[key]
                for key in (
                    "missing_reasons",
                    "unresolved_questions",
                )
                if evidence_analysis.get(key) not in (None, "", [], {})
            }
            source_coverage = evidence_analysis.get("source_coverage")
            if isinstance(source_coverage, dict):
                query_buckets: Dict[str, Dict[str, Any]] = {}
                for query in source_coverage.get("queries") or []:
                    if not isinstance(query, dict):
                        continue
                    compact_query = {
                        key: query[key]
                        for key in (
                            "tool",
                            "source_system",
                            "dimension",
                            "coverage",
                            "directness",
                        )
                        if query.get(key) not in (None, "", [], {})
                    }
                    signature = cls._json_signature(compact_query)
                    if signature not in query_buckets:
                        query_buckets[signature] = {
                            **compact_query,
                            "query_count": 0,
                        }
                    query_buckets[signature]["query_count"] += 1
                compact_queries = list(query_buckets.values())
                if compact_queries:
                    collection["source_coverage"] = {"queries": compact_queries}
            formal_rca = cls._parse_formal_rca(group.get("rca_analysis"))
            formal_rca_payload = {
                key: formal_rca[key]
                for key in (
                    "diagnostic_status",
                    "root_cause",
                    "causal_chain",
                    "limitations",
                    "unknowns",
                )
                if formal_rca.get(key) not in (None, "", [], {})
            }
            formal_rca_payload["supporting_fact_ids_hint"] = list(
                formal_rca.get("supporting_fact_ids") or []
            )
            claim_validation = (
                formal_rca.get("claim_validation")
                if isinstance(formal_rca.get("claim_validation"), dict)
                else {}
            )
            publication_value = claim_validation.get(
                "diagnosis_publishable",
                claim_validation.get("diagnosis_supported"),
            )
            if publication_value is None:
                publication_value = (
                    claim_validation.get("enabled") is False
                    and formal_rca.get("diagnostic_status") == "diagnosed"
                )
            formal_rca_payload["publication"] = {
                "diagnosis_publishable": bool(publication_value),
                "reasons": list(claim_validation.get("reasons") or []),
            }

            groups.append({
                "group_id": group.get("group_id") or "?",
                "entities": entities,
                "formal_rca": formal_rca_payload,
                "collection": collection,
                "failed_tool_attempts": cls._failed_tool_attempts_for_report_agent(
                    group.get("thinking_events") or []
                ),
            })
        return {
            "contract_version": "aiops.conclusion-agent-context.v2",
            "fact_encoding": {
                "authority": "canonical normalized facts",
                "aggregation": (
                    "repeated logs and equivalent L7 flows may be structurally grouped; "
                    "counts, time ranges, numeric ranges, trace_ids and fact_ids remain explicit"
                ),
                "trend_rule": (
                    "metric trend is valid only when trend_evaluable=true and sample_count>=2"
                ),
            },
            "question": question,
            "group_count": len(groups),
            "groups": groups,
        }

    def _generate_multi_group_report_with_agent(
        self,
        *,
        question: str,
        group_results: List[Dict[str, Any]],
        conclusion_max_tokens: Optional[int],
    ) -> str:
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            raise RuntimeError("[conclusion] ai_call 未设置，无法生成多组富文本报告")

        max_tokens = self._resolve_conclusion_max_tokens(
            layer=Layer.ABNORMAL,
            requested=conclusion_max_tokens,
        )
        context = self._build_multi_group_report_context(question, group_results)
        context_json = json.dumps(context, ensure_ascii=False, default=str)
        system_prompt = self._get_conclusion_prompt()
        user_message = f"""# 用户问题
{question}

# 结构化诊断与真实事实
下面 JSON 是本轮报告的唯一事实来源。普通 fact 的 `value` 以及聚合 fact 的 `pattern/flow/records/numeric_fields`、labels、stats、timestamp、trace_ids 均来自原始规范化事实；聚合只合并重复记录，不改变事实含义。不要复述 JSON 结构，要把它组织成人类可读的诊断报告。

{context_json}

# 任务
严格使用 system prompt 中唯一的富文本结构；覆盖全部异常组，由你选择并组织高价值真实证据。
"""
        estimated_tokens = self._estimate_tokens(system_prompt + user_message)
        input_budget = self._resolve_context_token_budget(output_reserved=max_tokens)
        logger.info(
            "📦 [conclusion] multi-group semantic context | estimated=%d budget=%d groups=%d",
            estimated_tokens,
            input_budget,
            len(group_results),
        )
        if estimated_tokens > input_budget:
            logger.warning(
                "[conclusion] semantic report context exceeds model input budget "
                "(estimated=%d budget=%d); preserving group facts without blind truncation",
                estimated_tokens,
                input_budget,
            )
        self._archive_node_input({
            "node": self.node_id,
            "question": question,
            "user_message": user_message,
            "system_prompt_chars": len(system_prompt),
            "user_message_chars": len(user_message),
            "max_tokens": max_tokens,
            "structured_method": "unified_agent_markdown",
            "report_context_contract": context["contract_version"],
            "estimated_input_tokens": estimated_tokens,
            "input_token_budget": input_budget,
        })
        start_time = time.time()
        content = ai_call.call_simple(
            system_prompt=system_prompt,
            question=user_message,
            max_tokens=max_tokens,
        )
        if self.metrics:
            self.metrics.record_llm_call(
                "conclusion",
                (time.time() - start_time) * 1000,
            )
        return self._strip_think_blocks(content or "")

    def _generate_multi_group_deterministic_fallback(
        self,
        *,
        question: str,
        group_results: List[Dict[str, Any]],
    ) -> str:
        """Minimal availability fallback; rich deterministic cards are opt-in."""
        narrative = self._format_multi_group_fallback(question, group_results)
        if self._get_conclusion_presentation_mode() != "deterministic":
            return narrative

        # ---- 代码确定性部分：可读实体卡片 + 折叠逐工具原始证据 ----
        entity_cards = self._render_multi_group_entity_cards(group_results)
        sections = [narrative.rstrip()]
        if entity_cards:
            sections.extend(["---", entity_cards])
        if self._include_raw_evidence_appendix():
            evidence_sections = ["## 🔎 逐工具原始证据与归档"]
            for r in group_results:
                gid = r.get("group_id", "?")
                entities = ", ".join(
                    f"{e.get('namespace', '')}/{e.get('name', '')}"
                    for e in (r.get("entities") or []) if isinstance(e, dict)
                )
                title = f"组 {gid}: {entities} — {r.get('pod_abnormal_type') or '/'.join(r.get('status_keywords') or [])}"
                evidence_sections.append(f"\n<details>\n<summary>{title} · 逐工具原始证据</summary>\n")
                events = r.get("thinking_events") or []
                rendered = self._build_tool_data_section(events) if events else ""
                evidence_sections.append(rendered or "（该组无已归档的工具真实数据）")
                archive_ref = r.get("archive_run_id")
                if archive_ref:
                    evidence_sections.append(f"*完整归档: context_archives/{archive_ref}*")
                evidence_sections.append("</details>")
            sections.extend(["---", "\n".join(evidence_sections)])
        return "\n\n".join(sections)

    @classmethod
    def _project_formal_group_authority(
        cls,
        group_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Replace group narrative claims with the validated formal RCA fields."""
        projected_groups: List[Dict[str, Any]] = []
        for group in group_results:
            projected = dict(group)
            rca = cls._parse_formal_rca(group.get("rca_analysis"))
            valid = cls._formal_rca_is_valid(rca)
            claim = (
                rca.get("claim_validation")
                if isinstance(rca.get("claim_validation"), dict)
                else {}
            )
            reasons = list(dict.fromkeys(
                str(item)
                for item in [
                    *(claim.get("reasons") or []),
                    *(rca.get("unknowns") or []),
                ]
                if str(item).strip()
            ))
            entities = []
            for entity in group.get("entity_summaries") or []:
                if not isinstance(entity, dict):
                    continue
                item = dict(entity)
                if valid:
                    item.update({
                        "diagnostic_status": "diagnosed",
                        "root_cause": str(
                            rca.get("root_cause_summary")
                            or rca.get("root_cause")
                            or "证据不足"
                        ),
                        "confidence": float(rca.get("confidence") or 0.0),
                        "supporting_fact_ids": list(
                            rca.get("supporting_fact_ids") or []
                        ),
                        "contradicting_fact_ids": list(
                            rca.get("contradicting_fact_ids") or []
                        ),
                        "claim_validation": claim,
                    })
                else:
                    item.update({
                        "diagnostic_status": "inconclusive",
                        "root_cause": "证据不足",
                        "causal_chain": [],
                        "confidence": min(
                            float(rca.get("confidence") or 0.0),
                            0.49,
                        ),
                        "supporting_fact_ids": [],
                        "contradicting_fact_ids": [],
                        "unknowns": reasons or ["正式 RCA claim validation 未通过"],
                        "claim_validation": claim or {"valid": False},
                    })
                entities.append(item)
            projected["entity_summaries"] = entities
            projected["diagnostic_status"] = (
                "diagnosed" if valid else "inconclusive"
            )
            projected_groups.append(projected)
        return projected_groups

    @staticmethod
    def _multi_group_table_cell(value: Any) -> str:
        text = str(value or "-").replace("\n", " ").replace("|", "\\|")
        return text

    @classmethod
    def _render_multi_group_entity_cards(
        cls,
        group_results: List[Dict[str, Any]],
    ) -> str:
        """Render every entity and required evidence dimension deterministically."""
        dimension_labels = {
            "kubernetes": "Kubernetes",
            "metrics": "Metrics",
            "logging": "Logging",
            "tracing": "Tracing",
        }
        dimension_roles = {
            "kubernetes": "确认生命周期、状态和事件",
            "metrics": "量化状态、资源和变化趋势",
            "logging": "确认应用或容器错误原文",
            "tracing": "串联请求、响应与 Trace",
        }
        sections = ["# 📊 各异常实体结构化诊断"]
        rendered_count = 0
        for group in group_results:
            gid = str(group.get("group_id") or "?")
            dimensions_by_entity = group.get("dimension_evidence_by_entity") or {}
            for entity in group.get("entity_summaries") or []:
                if not isinstance(entity, dict):
                    continue
                key = f"{entity.get('namespace', '')}/{entity.get('name', '')}"
                dimensions = dimensions_by_entity.get(key) or {}
                rendered_count += 1
                sections.extend([
                    f"## 异常组 {gid} · {key}",
                    "",
                    f"**状态**：{entity.get('status') or '未归类'}",
                    "",
                    f"**现象**：{entity.get('phenomenon') or '未提取'}",
                    "",
                    f"**根因**：{entity.get('root_cause') or '证据不足'}",
                    "",
                    "**关键逻辑**：" + (
                        " → ".join(str(item) for item in (entity.get("causal_chain") or []))
                        or "证据不足，尚未形成完整因果链"
                    ),
                    "",
                    f"**置信度**：{float(entity.get('confidence') or 0):.0%}",
                    "",
                    "| 维度 | 状态 | 真实结果 | 诊断作用 |",
                    "|---|---|---|---|",
                ])
                all_limitations = []
                for dimension in ("kubernetes", "metrics", "logging", "tracing"):
                    summary = dimensions.get(dimension) or {}
                    facts = [
                        item for item in (summary.get("facts") or [])
                        if isinstance(item, dict)
                    ]
                    ordered_facts = cls._select_multi_group_display_facts(facts, entity)
                    fact_text = "<br>".join(
                        "[{source}] {value} `(fact_id={fact_id})`".format(
                            source=item.get("source_system") or "unknown",
                            value=cls._display_fact_with_semantics(item),
                            fact_id=item.get("fact_id") or "unknown",
                        )
                        for item in ordered_facts
                    ) or "未采集到真实事实"
                    omitted = len(facts) - len(ordered_facts)
                    if omitted > 0:
                        fact_text += f"<br>…另有 {omitted} 条上下文事实见完整归档"
                    sections.append(
                        "| {label} | {status} | {facts} | {role} |".format(
                            label=dimension_labels[dimension],
                            status=cls._multi_group_table_cell(summary.get("status") or "absent"),
                            facts=cls._multi_group_table_cell(fact_text),
                            role=dimension_roles[dimension],
                        )
                    )
                    all_limitations.extend(
                        f"{dimension_labels[dimension]}：{item}"
                        for item in (summary.get("limitations") or [])
                        if str(item).strip()
                    )
                if all_limitations:
                    sections.extend([
                        "",
                        "**采集边界**：",
                        "",
                        *[f"- {item}" for item in all_limitations],
                    ])
                unknowns = [str(item) for item in (entity.get("unknowns") or []) if str(item).strip()]
                if unknowns:
                    sections.extend(["", "**未决问题**：", "", *[f"- {item}" for item in unknowns]])
                archive_ref = group.get("archive_run_id")
                if archive_ref:
                    sections.extend(["", f"*完整归档：`context_archives/{archive_ref}`*"])
                sections.append("")
        return "\n".join(sections).strip() if rendered_count else ""

    @classmethod
    def _display_fact_with_semantics(cls, fact: Dict[str, Any]) -> str:
        value = (
            fact.get("display_value")
            or cls._compact_value(fact.get("value"))
            or "-"
        )
        metadata = fact.get("metadata") if isinstance(fact.get("metadata"), dict) else {}
        role = str(
            fact.get("evidence_role")
            or metadata.get("evidence_role")
            or ""
        ).strip().lower()
        if role == "negative_observation":
            return f"[负向观测/排除] {value}"
        if role == "symptom" and "restart" in str(fact.get("attribute") or "").lower():
            return f"[症状/持续性] {value}"
        return str(value)

    @staticmethod
    def _fact_quality_rank(fact: Dict[str, Any]) -> tuple[int, int, int, int]:
        metadata = fact.get("metadata") if isinstance(fact.get("metadata"), dict) else {}
        evidence_role = {
            "causal_candidate": 0,
            "symptom": 1,
            "contradicting": 2,
            "negative_observation": 3,
            "context": 4,
        }.get(str(
            fact.get("evidence_role")
            or metadata.get("evidence_role")
            or ""
        ).lower(), 2)
        strength = {
            "critical": 0,
            "strong": 1,
            "supporting": 2,
            "context": 3,
        }.get(str(fact.get("strength") or "").lower(), 4)
        directness = {
            "direct": 0,
            "derived": 1,
            "related_context": 2,
        }.get(str(fact.get("directness") or "").lower(), 3)
        confidence = {
            "high": 0,
            "medium": 1,
            "low": 2,
            "weak": 3,
        }.get(str(fact.get("confidence") or "").lower(), 4)
        return evidence_role, strength, directness, confidence

    @classmethod
    def _select_multi_group_display_facts(
        cls,
        facts: List[Dict[str, Any]],
        entity: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Show every RCA reference first, then at most three context facts."""
        supporting = [str(item) for item in entity.get("supporting_fact_ids") or []]
        contradicting = [str(item) for item in entity.get("contradicting_fact_ids") or []]
        reference_order = {
            fact_id: (0, index)
            for index, fact_id in enumerate(supporting)
        }
        reference_order.update({
            fact_id: (1, index)
            for index, fact_id in enumerate(contradicting)
            if fact_id not in reference_order
        })

        referenced: List[tuple[tuple[int, int], int, Dict[str, Any]]] = []
        context: List[tuple[tuple[int, int, int, int], int, Dict[str, Any]]] = []
        for index, fact in enumerate(facts):
            fact_id = str(fact.get("fact_id") or "")
            if fact_id in reference_order:
                referenced.append((reference_order[fact_id], index, fact))
            else:
                context.append((cls._fact_quality_rank(fact), index, fact))
        referenced.sort(key=lambda item: (item[0], item[1]))
        context.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in referenced] + [item[2] for item in context[:3]]

    @staticmethod
    def _format_multi_group_fallback(
        question: str,
        group_results: List[Dict[str, Any]],
    ) -> str:
        """Authoritative deterministic overview of validated group diagnoses."""
        lines = [
            "# 🔬 集群多异常诊断报告（确定性汇总）",
            "",
            f"> 用户问题：{question}",
            "",
            f"检测到 {len(group_results)} 个独立异常组：",
            "",
        ]
        for r in group_results:
            entities = ", ".join(
                f"{e.get('namespace', '')}/{e.get('name', '')}"
                for e in (r.get("entities") or []) if isinstance(e, dict)
            )
            lines.append(f"## 异常组 {r.get('group_id', '?')}: {entities}")
            lines.append("")
            if r.get("error"):
                lines.append(f"- 状态：采集失败 — {r['error']}")
            summaries = [
                item for item in (r.get("entity_summaries") or [])
                if isinstance(item, dict)
            ]
            if summaries:
                for entity in summaries:
                    key = f"{entity.get('namespace', '')}/{entity.get('name', '')}"
                    status = entity.get("diagnostic_status") or r.get("diagnostic_status") or "inconclusive"
                    confidence = float(entity.get("confidence") or 0.0)
                    lines.append(
                        f"- `{key}` | {status} | {entity.get('root_cause') or '证据不足'} "
                        f"| 置信度 {confidence:.0%}"
                    )
            else:
                lines.append(str(r.get("summary") or "（无分析摘要）"))
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _strip_think_blocks(content: str) -> str:
        """移除模型可能输出的 <think>...</think> 推理块。"""
        if not content:
            return content
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        cleaned = re.sub(r"^\s*<think>.*", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    # ------------------------------------------------------------------
    # 确定性快速路径与回退模板
    # ------------------------------------------------------------------
    def _render_query_result(self, query_result: Dict[str, Any]) -> str:
        """QUERY 模式仅渲染结构化 QueryResult，不再做二次 LLM 理解。"""
        parsed = QueryResult.model_validate(query_result or {})
        target = parsed.query_target
        collection_summary = parsed.collection_summary
        columns = [item.model_dump() for item in parsed.columns]
        rows = parsed.rows
        notes = parsed.notes
        missing = [item.model_dump() for item in parsed.missing]
        sources = [item.model_dump() for item in parsed.sources]

        lines = [
            "## 📊 查询结果",
            "",
            f"- **查询目标**: {target}",
            "- **模式**: QUERY 结构化回复",
        ]
        if collection_summary:
            lines.append(f"- **采集情况**: {collection_summary}")
        lines.append("")

        if columns:
            normalized_columns = [
                c if isinstance(c, dict) else {"key": str(c), "label": str(c)}
                for c in columns
            ]
            labels = [c.get("label", c.get("key", "")) for c in normalized_columns]
            keys = [c.get("key", "") for c in normalized_columns]
            lines.append("## 📈 数据摘要")
            lines.append("")
            lines.append("| " + " | ".join(labels) + " |")
            lines.append("|" + "|".join(["------"] * len(labels)) + "|")
            for row in rows:
                row_data = row if isinstance(row, dict) else {"value": row}
                values = [str(row_data.get(key, "未获取到")) for key in keys]
                lines.append("| " + " | ".join(values) + " |")
            lines.append("")

        if notes or missing:
            lines.append("## 🔎 补充说明")
            lines.append("")
            for note in notes:
                lines.append(f"- {note}")
            for item in missing:
                if isinstance(item, dict):
                    lines.append(f"- **未获取到** `{item.get('field', '?')}`: {item.get('reason', '未知原因')}")
                else:
                    lines.append(f"- **未获取到**: {item}")
            lines.append("")

        if sources:
            lines.append("## 🧪 查询来源")
            lines.append("")
            lines.append("| 工具 | 查询语句 |")
            lines.append("|------|----------|")
            for source in sources:
                if isinstance(source, dict):
                    lines.append(f"| {source.get('tool', '-')} | {source.get('query', '-') or '-'} |")
                else:
                    lines.append(f"| - | {source} |")
            lines.append("")

        return "\n".join(lines)

    def _format_healthy_fast_path(
        self,
        question: str,
        layer_analysis: str,
        thinking_events: list,
    ) -> str:
        """HEALTHY 模式快速路径：直接返回简洁健康摘要，不再调用 LLM。"""
        checks = []

        if layer_analysis:
            checks.append(self._summarize_snippet(layer_analysis, limit=220))

        tool_text = self._build_tool_data_section(thinking_events)
        if tool_text:
            checks.append(self._summarize_snippet(tool_text, limit=220))

        lines = [
            "## ✅ 健康检查结果",
            "",
            f"- **用户问题**: {question}",
            "- **结论**: 当前集群运行正常，未发现异常",
            "- **模式**: HEALTHY 快速回复",
            "",
        ]

        if checks:
            lines.append("## 🔎 检查摘要")
            lines.append("")
            for item in checks[:3]:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _summarize_snippet(text: str, limit: int = 120) -> str:
        """将多行工具输出压成单行摘要，便于快速回复。"""
        compact = " ".join((text or "").split())
        if not compact:
            return "-"
        return compact[:limit] + ("..." if len(compact) > limit else "")

    def _format_with_template(
        self,
        question: str,
        layer: Optional[Layer],
        layer_analysis: str,
        evidence_analysis: str,
        rca_analysis: str,
        errors: List[str],
        warnings: List[str],
    ) -> str:
        """LLM 不可用或返回空时的确定性回退模板：直接展示各阶段真实结果。"""
        if layer == Layer.QUERY:
            mode_text = "QUERY - 直接查询"
        elif layer == Layer.HEALTHY:
            mode_text = "HEALTHY - 集群健康"
        elif layer is not None:
            mode_text = "ABNORMAL - 异常诊断"
        else:
            mode_text = "未确定"
        # 从 layer 分析中提取真实 Pod 异常状态
        status_text = ""
        try:
            layer_data = json.loads(layer_analysis) if layer_analysis else {}
            if isinstance(layer_data, dict):
                status_text = " / ".join(
                    x for x in [
                        str(layer_data.get("pod_status_keyword") or ""),
                        str(layer_data.get("pod_abnormal_type") or ""),
                    ] if x
                )
        except (ValueError, TypeError):
            pass
        rca_summary = self._build_rca_summary(rca_analysis)
        evidence_summary = self._build_evidence_summary(evidence_analysis)

        lines = [
            "# 🔬 K8s 诊断报告（确定性回退模板）",
            "",
            "## 📊 诊断概览",
            "",
            "| 项目 | 结果 |",
            "|------|------|",
            f"| **诊断模式** | {mode_text} |",
            f"| **Pod 异常状态** | {status_text or '未确定'} |",
            "",
            "## 🎯 用户问题",
            "",
            f"> {question}",
            "",
            "## 📍 阶段1：问题定位",
            "",
            "```json",
            layer_analysis[:4000],
            "```",
            "",
            "## 🔍 阶段2：证据采集摘要",
            "",
            evidence_summary,
            "",
            "## 🎯 阶段3：根因分析",
            "",
            rca_summary,
            "",
        ]

        if warnings or errors:
            lines.append("## ⚠️ 注意事项")
            lines.append("")
            for w in warnings:
                lines.append(f"- ⚠️ {w}")
            for e in errors:
                lines.append(f"- ❌ {e}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*报告由 K8s AIOps Copilot 工作流生成（LLM 汇总不可用，展示原始阶段结果）*")
        return "\n".join(lines)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """粗估 token 数（混合中英文 ~2 chars/token），只用于判断是否需要截断。"""
        return len(text) // 2
