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
from typing import Any, Dict, List, Optional

from app.core.workflow.fact_contract import (
    OBSERVABILITY_QUERY_TOOLS,
    project_final_observability_events,
)
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import QueryConclusionOutput, QueryResult
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer
from app.core.prompts import (
    MULTI_GROUP_CONCLUSION_PROMPT,
    REMEDIATION_PLAN_PROMPT,
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
                # 多异常并发模式：LLM 读各组摘要写结论 + 代码确定性拼接真实数据
                conclusion = self._generate_multi_group_report(
                    question=question,
                    group_results=group_results,
                    conclusion_max_tokens=state.get("conclusion_max_tokens"),
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
        plan_total = data.get("plan_total")
        plan_collected = data.get("plan_collected")
        completeness = data.get("plan_completeness")
        if plan_total is not None:
            pct = f"{float(completeness or 0):.0%}"
            lines.append(f"- 采集完成度: {plan_collected}/{plan_total} ({pct})")
        sufficiency = data.get("diagnostic_sufficiency_label") or ""
        if sufficiency:
            lines.append(f"- 诊断充分度: {sufficiency}")
        summary = (data.get("collection_summary") or "").strip()
        if summary:
            lines.append(f"- 采集总结: {summary}")

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
        confidence = data.get("confidence")
        if confidence is not None:
            try:
                lines.append(f"- 置信度: {float(confidence):.0%}")
            except (TypeError, ValueError):
                pass
        reason = (data.get("confidence_reason") or "").strip()
        if reason:
            lines.append(f"- 置信依据: {reason[:300]}")

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

        instruction = f"""# 指令
请基于以上三个阶段的分析结果和工具真实数据，严格按照 system prompt 中的报告模板生成最终诊断报告。

⚠️ 最重要的规则：用户的原始问题是「{question}」，报告必须首先回答这个问题。
- 如果用户问的是数据/指标（如 CPU、内存、磁盘），报告开头先用表格展示查到的实际数据，再展开诊断
- 证据链表格的「原始数据」列必须摘自「工具采集的真实数据」段落，禁止编造

{REMEDIATION_PLAN_PROMPT}"""

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
    # 多异常并发模式：LLM 读摘要写结论 + 代码确定性拼接真实数据
    # ------------------------------------------------------------------
    def _generate_multi_group_report(
        self,
        *,
        question: str,
        group_results: List[Dict[str, Any]],
        conclusion_max_tokens: Optional[int] = None,
    ) -> str:
        """多异常报告：结论/现象/关键逻辑由 LLM 基于各组摘要整理，
        结构化真实数据由代码确定性拼接在报告后（永不因组多而丢失）。"""
        max_tokens = self._resolve_conclusion_max_tokens(
            layer=None, requested=conclusion_max_tokens,
        )

        # ---- LLM 部分：每组紧凑摘要 → 结论叙述 ----
        group_sections = []
        for r in group_results:
            gid = r.get("group_id", "?")
            entities = ", ".join(
                f"{e.get('namespace', '')}/{e.get('name', '')}"
                for e in (r.get("entities") or []) if isinstance(e, dict)
            ) or "?"
            statuses = "/".join(r.get("status_keywords") or []) or "?"
            summary = str(r.get("summary") or "").strip() or "（该组无分析摘要）"
            collection = str(r.get("collection_summary") or "").strip()
            error = r.get("error")
            lines = [
                f"## 组 {gid}",
                f"- 实体: {entities}",
                f"- 异常状态: {statuses} | 类型: {r.get('pod_abnormal_type') or '未归类'}",
            ]
            if collection:
                lines.append(f"- 采集情况: {collection[:220]}")
            if error:
                lines.append(f"- ⚠️ 该组采集失败: {error}")
            lines.append(f"- 该组分析摘要:\n{summary}")
            group_sections.append("\n".join(lines))

        user_message = (
            f"# 用户问题\n{question}\n\n"
            f"# 各异常组独立采集分析结果（共 {len(group_results)} 组）\n\n"
            + "\n\n".join(group_sections)
            + "\n\n# 指令\n请基于以上各组摘要，按 system prompt 的结构生成多异常诊断报告。"
            f"\n\n{REMEDIATION_PLAN_PROMPT}"
        )

        ai_call = getattr(self, "ai_call", None)
        narrative = ""
        if ai_call is not None:
            logger.info(
                "📍 [conclusion] 多异常模式 | %d 组, max_tokens=%d",
                len(group_results), max_tokens,
            )
            self._archive_node_input({
                "node": self.node_id,
                "mode": "multi_group",
                "question": question,
                "user_message": user_message,
                "group_count": len(group_results),
                "max_tokens": max_tokens,
            })
            narrative = self._strip_think_blocks(
                ai_call.call_simple(
                    system_prompt=MULTI_GROUP_CONCLUSION_PROMPT,
                    question=user_message,
                    max_tokens=max_tokens,
                ) or ""
            )
        if not narrative.strip():
            # 回退：确定性组装各组摘要
            narrative = self._format_multi_group_fallback(question, group_results)

        # ---- 代码确定性部分：各组结构化真实数据（永不丢失） ----
        evidence_sections = ["## 📋 各异常组真实采集证据（结构化，系统确定性拼接）"]
        for r in group_results:
            gid = r.get("group_id", "?")
            entities = ", ".join(
                f"{e.get('namespace', '')}/{e.get('name', '')}"
                for e in (r.get("entities") or []) if isinstance(e, dict)
            )
            evidence_sections.append(
                f"\n### 组 {gid}: {entities} — {r.get('pod_abnormal_type') or '/'.join(r.get('status_keywords') or [])}"
            )
            events = r.get("thinking_events") or []
            rendered = self._build_tool_data_section(events) if events else ""
            if rendered:
                evidence_sections.append(rendered)
            else:
                evidence_sections.append("（该组无已归档的工具真实数据）")
            archive_ref = r.get("archive_run_id")
            if archive_ref:
                evidence_sections.append(f"*完整归档: context_archives/{archive_ref}*")

        return narrative.rstrip() + "\n\n---\n\n" + "\n".join(evidence_sections)

    @staticmethod
    def _format_multi_group_fallback(
        question: str,
        group_results: List[Dict[str, Any]],
    ) -> str:
        """LLM 不可用时的多组确定性回退：直接罗列各组摘要。"""
        lines = [
            "# 🔬 集群多异常诊断报告（确定性回退模板）",
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
            lines.append(
                f"## 异常组 {r.get('group_id', '?')}: {entities} — "
                f"{r.get('pod_abnormal_type') or '/'.join(r.get('status_keywords') or [])}"
            )
            lines.append("")
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
