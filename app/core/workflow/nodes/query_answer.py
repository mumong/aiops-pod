"""Direct structured query answers and the separate deep-diagnosis conclusion."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.core.aicall.errors import public_error_text
from app.core.prompts import (
    DEEP_CONCLUSION_PRESENTATION,
    QUERY_COLLECT_PROMPT,
    QUERY_CONCLUSION_PROMPT,
    QUERY_RUNBOOK_CATALOG_HEADER,
    QUERY_RUNBOOK_DESCRIPTION,
    QUERY_TASK_AUTHORITY_PREFIX,
)
from app.core.runbook.catalog import reference_description
from app.core.skills.models import Layer
from app.core.workflow.nodes.focused import FocusedTaskNode

# Re-export legacy imports while keeping contracts separate from orchestration.
from app.core.workflow.query_contract import QueryAnswer, parse_query_answer
from app.core.workflow.working_material import build_working_material


def _configure_query_runtime(node):
    """Shared transport and budget policy for routing, quick and deep agents."""
    client = getattr(node, "ai_call", None)
    if client is not None:
        client.query_raw_passthrough = True
        client.query_context_state_compaction = True
        client.query_tool_timeout = max(
            1.0, float(os.getenv("AIOPS_QUERY_TOOL_TIMEOUT_SECONDS", "60"))
        )


class QueryCollectNode(FocusedTaskNode):
    WRITE_TOOLS = {"run_bash_command", "kubectl_run_image"}

    def _allowed_query_tools(self, state):
        # Ordinary operations stay on QUERY; diagnostic subclasses keep READ_TOOLS.
        contract = state.get("request_contract") or {}
        return self.READ_TOOLS | (self.WRITE_TOOLS if contract.get("task") == "operate" else set())

    READ_TOOLS = FocusedTaskNode.READ_TOOLS | {
        "kubernetes_count",
        "kubernetes_jq_query",
        "kubernetes_tabular_query",
        "kubectl_logs_grep",
        "kubectl_logs_all_containers_grep",
        "get_prometheus_target",
        "list_prometheus_rules",
        "TodoWrite",
    }

    def _prepare_query_tools(self):
        catalog = {
            str(getattr(e, "link", "")): str(getattr(e, "description", ""))
            for e in getattr(self.runbook_catalog, "catalog", [])
        }
        prepared = []
        for tool in getattr(self, "tools", []):
            if tool.name == "fetch_runbook" and hasattr(tool, "model_copy"):
                ids = set()
                for directory in getattr(tool, "runbook_dirs", []):
                    for path in Path(directory).glob("*.md"):
                        ids.add(path.stem)
                        if not catalog.get(path.name):
                            catalog[path.name] = reference_description(path)
                tool = tool.model_copy(
                    update={
                        "allowed_runbook_ids": sorted(ids)
                        or getattr(tool, "allowed_runbook_ids", []),
                        "description": QUERY_RUNBOOK_DESCRIPTION,
                    }
                )
            elif hasattr(tool, "model_copy") and " AIOps boundary:" in getattr(
                tool, "description", ""
            ):
                tool = tool.model_copy(
                    update={"description": tool.description.split(" AIOps boundary:", 1)[0]}
                )
            prepared.append(tool)
        self.tools = prepared
        return "\n".join(f"- {name}: {desc}" for name, desc in sorted(catalog.items()) if name)

    @property
    def node_id(self):
        return "query_collect"

    @property
    def node_name(self):
        return "自主查询"

    def execute(self, state):
        _configure_query_runtime(self)
        question = state.get("original_question") or state.get("question", "")
        if getattr(self, "ai_call", None) is not None:
            self.ai_call.query_session_context = state.get("query_session_context") or {}
            self.ai_call.working_context_original_question = question
        catalog = self._prepare_query_tools()
        self._archive_node_input(
            {
                "question": question,
                "request_contract": state.get("request_contract"),
                "runbook_catalog": catalog,
            }
        )
        from app.core.aicall.client import StructuredContextBudgetError

        try:
            response, events = self._call_llm(
                question
                + "\n当前 UTC 时间："
                + datetime.now(timezone.utc).isoformat()
                + QUERY_TASK_AUTHORITY_PREFIX
                + json.dumps(state.get("request_contract"), ensure_ascii=False),
                QUERY_COLLECT_PROMPT
                + QUERY_RUNBOOK_CATALOG_HEADER
                + catalog
                + "\n最终输出 schema：\n"
                + json.dumps(QueryAnswer.model_json_schema(), ensure_ascii=False),
                blocked_tool_names={
                    t.name
                    for t in getattr(self, "tools", [])
                    if t.name not in self._allowed_query_tools(state)
                },
                skip_remediation_policy=True,
                expect_json=True,
                response_schema=QueryAnswer,
            )
            raw = response.result or ""
        except StructuredContextBudgetError as exc:
            events = [{"type": "execution_incomplete", "reason": public_error_text(exc)}]
            raw = QueryAnswer(
                intent=question,
                scope="本次请求范围",
                status="partial",
                answer="上下文预算不足，本次查询未完成。",
                missing=[str(exc)],
            ).model_dump_json()
        output = {
            "layer": Layer.QUERY,
            "request_route": "query",
            "query_draft": raw,
            "thinking_events": [*(state.get("thinking_events") or []), *events],
        }
        output.update(
            finalize_query_answer(self, {**state, **output}, raw, [], require_structured=True)
        )
        self._archive_node_output(output)
        return output


class QueryConclusionNode(FocusedTaskNode):
    @property
    def node_id(self):
        return "conclusion"

    @property
    def node_name(self):
        return "查询结果整理"

    def _healthy_check_output(self, state, assessment):
        """Verified healthy location result: fixed-format report, no model call."""
        from app.core.workflow.pod_detection import healthy_check_report

        text = healthy_check_report(assessment)
        answer = QueryAnswer(
            intent=state.get("original_question") or state.get("question", ""),
            scope=assessment.get("scope") or "本次请求范围",
            status="answered",
            answer=text,
            evidence_refs=[r for r in assessment.get("evidence_refs") or [] if r],
        )
        # assess_delivery only kept "healthy" after judging any stage incompleteness
        # harmless (and wrote that into the reason); do not re-add it as a missing item.
        settled = {
            **state,
            "thinking_events": [
                e
                for e in state.get("thinking_events") or []
                if e.get("type") != "execution_incomplete"
            ],
        }
        return finalize_query_answer(
            self, settled, answer.model_dump_json(), [], require_structured=True
        )

    def execute(self, state):
        _configure_query_runtime(self)
        if (
            state.get("diagnosis_case_result")
            or state.get("autonomous_groups")
            or state.get("autonomous_group_results")
        ):
            from app.core.workflow.case_report import conclude_cases

            if getattr(self, "ai_call", None) is not None:
                self.ai_call.query_session_context = {}
            return conclude_cases(self, state)
        events = state.get("thinking_events") or []
        assessment = (state.get("diagnosis_handoff") or {}).get("pod_assessment") or {}
        if (
            (state.get("request_contract") or {}).get("route") == "full_diagnosis"
            and assessment.get("status") == "healthy"
            and not state.get("rca_analysis")
        ):
            return self._healthy_check_output(state, assessment)
        payload = build_working_material(state)
        payload["request_contract"] = state.get("request_contract")
        payload["pod_assessment"] = (state.get("diagnosis_handoff") or {}).get("pod_assessment")
        if getattr(self, "ai_call", None) is not None:
            self.ai_call.query_session_context = {}
        self._archive_node_input(payload)
        from app.core.aicall.client import StructuredContextBudgetError

        final_compacted_summary = None
        pod_check = False
        try:
            prompt = QUERY_CONCLUSION_PROMPT
            if (payload.get("request_contract") or {}).get("route") == "full_diagnosis":
                assessment = payload.get("pod_assessment") or {}
                if assessment.get("status") in ("healthy", "inconclusive") and not state.get(
                    "rca_analysis"
                ):
                    pod_check = True
                    prompt += "\n这是定位后直接结束的 Pod 检查，只输出简短检查结论、范围/时间/数量、关键依据及限制。不要套用异常概览、根因、三维证据表，不把没有调查的无关维度列成待办。inconclusive 必须明确具体缺口。历史累计重启不冒充近期异常；仅当近期线索仍未解释才列为待核实。"
                else:
                    prompt += "\n" + DEEP_CONCLUSION_PRESENTATION
                prompt += "\n本产品深度诊断是 Pod 异常检测，不是全面集群健康评估。若 pod_assessment 为 healthy，简述 Healthy、本次范围/时间/证据与近期线索核实结果，无需异常根因表；只说明本次检查未发现 Pod 异常，不承诺业务全健康。若为 inconclusive，明确检查不完整及缺口，不输出 healthy。不因未采集无关指标日志链路而扩展检查。"
            prompt += "\n输出 schema：\n" + json.dumps(
                QueryAnswer.model_json_schema(), ensure_ascii=False
            )

            def conclude(material):
                return self._call_llm(
                    json.dumps(material, ensure_ascii=False, default=str),
                    prompt,
                    force_no_tools=True,
                    skip_remediation_policy=True,
                    expect_json=True,
                    # A location-only Pod check restates collected facts: one tool-free
                    # structured delivery (internal, no thinking) like RCA, not a
                    # streamed thinking call (runs c187251f / 3dab7e34: 28 s / 64 s).
                    **({"response_schema": QueryAnswer} if pod_check else {}),
                )

            try:
                response, final_events = conclude(payload)
            except StructuredContextBudgetError as exc:
                if "working_context_compaction_required" not in str(exc):
                    raise
                import asyncio

                from app.core.aicall.working_context import compact_working_material

                model = self.ai_call.create_compaction_model()
                compact_payload = asyncio.run(
                    compact_working_material(
                        model,
                        payload,
                        lambda **event: self.ai_call._push(
                            self._event_queue, self.node_id, events, **event
                        ),
                    )
                )
                final_compacted_summary = compact_payload["working_summary"]
                self._archive_node_input(
                    {"before_compaction": payload, "after_compaction": compact_payload}
                )
                response, final_events = conclude(compact_payload)
        except StructuredContextBudgetError as exc:
            answer = str(exc)
            result = QueryAnswer(
                intent=payload["question"],
                scope="本次已采集范围，未完成整理",
                status="partial",
                answer=answer,
                missing=[answer],
                evidence_refs=[o["raw_ref"] for o in payload["observations"] if o.get("raw_ref")],
            ).model_dump()
            output = {
                "conclusion": answer,
                "conclusion_formatted": answer,
                "query_answer": result,
                "thinking_events": events,
            }
            self._archive_node_output(output)
            return output
        output = finalize_query_answer(
            self,
            state,
            response.result or "",
            final_events,
            final_compacted_summary=final_compacted_summary,
            compact_payload=compact_payload if final_compacted_summary else None,
        )
        return output


def finalize_query_answer(
    node,
    state,
    raw,
    final_events,
    *,
    require_structured=False,
    final_compacted_summary=None,
    compact_payload=None,
):
    """Render and save an answer without another model call; shared with deep conclusion."""
    events = state.get("thinking_events") or []
    last_compaction = next(
        (
            i
            for i in range(len(events) - 1, -1, -1)
            if events[i].get("type") == "context_compacted" and not events[i].get("lane_id")
        ),
        -1,
    )
    payload = build_working_material(state)
    result, repaired = parse_query_answer(raw)
    if getattr(node, "current_run_id", None):
        from app.core.context.archive import ContextArchive

        ContextArchive(run_id=node.current_run_id).write_json(
            f"{node.node_id}/render_audit.json",
            {"raw": raw, "format_repaired": repaired, "schema_valid": result is not None},
        )
    looks_structured = raw.lstrip().startswith(("{", "[", "```json"))
    if result:
        answer = result["answer"]
    elif looks_structured:
        # Never render a broken JSON envelope as Markdown or invent a successful schema.
        draft = state.get("query_draft") or ""
        if draft.lstrip().startswith(("{", "[", "```json")):
            draft = ""
        answer = (
            "结果整理格式异常，以下为采集阶段分析草稿，尚未完成最终整理。\n\n" + draft
            if draft
            else "结果整理格式异常，未能生成可展示报告。原始输出已保留，请重试。"
        )
    else:
        answer = raw or "本次结果整理未返回内容，请重试。"
    if require_structured and result is None:
        # No silent second LLM or fabricated success when the output contract fails.
        limitation = "未获得有效的结构化回答，以下内容未完成格式整理。"
        answer = limitation + "\n\n" + answer
        result = QueryAnswer(
            intent=payload["question"],
            scope="本次请求范围",
            status="partial",
            answer=answer,
            missing=[limitation],
            evidence_refs=[o["raw_ref"] for o in payload["observations"] if o.get("raw_ref")],
        ).model_dump()
    if payload["execution_incomplete"]:
        limitation = "执行未完成：" + "；".join(str(r) for r in payload["execution_incomplete"])
        answer += "\n\n" + limitation
        if result:
            result["status"] = "partial"
            result["answer"] = answer
            result["missing"].append(limitation)
    output = {
        "conclusion": answer,
        "conclusion_formatted": answer,
        "query_answer": result,
        "thinking_events": [*events, *final_events],
    }
    previous = state.get("query_session_context") or {}
    memory = (
        {"working_summary": payload["working_summary"], "turns": []}
        if last_compaction >= 0
        else {
            "working_summary": previous.get("working_summary"),
            "turns": list(previous.get("turns") or []),
        }
    )
    memory["turns"].append(
        {
            "question": payload["question"],
            "answer": answer,
            "scope": (result or {}).get("scope"),
            "request_contract": state.get("request_contract"),
            "recent_interactions": payload["recent_interactions"],
            "observations": payload["observations"],
            "parallel_results": payload["parallel_results"],
            "execution_incomplete": payload["execution_incomplete"],
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    if final_compacted_summary:
        memory = {
            "working_summary": final_compacted_summary,
            "turns": [
                {
                    "question": payload["question"],
                    "answer": answer,
                    "scope": (result or {}).get("scope"),
                    "request_contract": state.get("request_contract"),
                    "recent_interactions": compact_payload["recent_interactions"],
                    "protected_handoff": compact_payload.get("protected_handoff", {}),
                    "execution_incomplete": payload["execution_incomplete"],
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
    output["query_session_memory"] = memory
    node._archive_node_output(output)
    return output
