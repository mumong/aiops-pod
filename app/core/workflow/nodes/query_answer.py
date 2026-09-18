"""Autonomous read-only collection followed by a tool-free answer agent."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.skills.models import Layer
from app.core.workflow.nodes.focused import FocusedTaskNode
from app.core.prompts import QUERY_COLLECT_PROMPT, QUERY_CONCLUSION_PROMPT, DEEP_CONCLUSION_PRESENTATION


def _configure_query_runtime(node):
    """Shared transport and budget policy for routing, quick and deep agents."""
    client = getattr(node, "ai_call", None)
    if client is not None:
        client.query_raw_passthrough = True
        client.query_context_state_compaction = True
        client.query_tool_timeout = max(1.0, float(os.getenv("AIOPS_QUERY_TOOL_TIMEOUT_SECONDS", "60")))




class QueryAnswer(BaseModel):
    intent: str = Field(description="本次理解的用户目标，不是固定故障分类")
    scope: str = Field(description="实际回答的对象与时间范围；未知时明确说明")
    status: str = Field(description="answered / partial / clarify / unavailable")
    answer: str = Field(description="可直接展示的完整中文 Markdown 回答，包括必要事实、解释、限制或澄清")
    evidence_refs: list[str] = Field(default_factory=list, description="实际工具返回中的来源引用，不编造")
    runbooks: list[str] = Field(default_factory=list, description="本次实际读取的手册，不是所有可用手册")
    missing: list[str] = Field(default_factory=list, description="未回答的项目和原因")


def build_working_material(state):
    """Carry the user task and only the latest working evidence representation."""
    events = state.get("thinking_events") or []
    last_compaction = next((i for i in range(len(events) - 1, -1, -1)
                            if events[i].get("type") == "context_compacted"), -1)
    return {
        "question": state.get("original_question") or state.get("question", ""),
        "request_contract": state.get("request_contract"),
        "request_time_utc": state.get("request_time_utc") or datetime.now(timezone.utc).isoformat(),
        "analysis_draft": state.get("query_draft", ""),
        "working_summary": events[last_compaction].get("working_summary") if last_compaction >= 0 else None,
        "recent_interactions": events[last_compaction].get("retained_messages", []) if last_compaction >= 0 else [],
        "session_history": state.get("query_session_context") if last_compaction < 0 else None,
        "execution_incomplete": [event.get("reason") for event in events if event.get("type") == "execution_incomplete"],
        "observations": [
            {key: event.get(key) for key in (
                "tool_name", "tool_args", "status", "semantic_success",
                "result", "raw_ref", "structured_ref",
            )}
            for event in events[last_compaction + 1:] if event.get("type") == "tool_result"
        ],
    }


def parse_query_answer(raw):
    """Validate JSON; narrowly recover unescaped quotes/newlines inside answer only."""
    from app.core.aicall.client import AICall
    parsed = AICall.extract_json_payload(raw)
    try:
        return QueryAnswer.model_validate(parsed).model_dump(), False
    except (ValueError, TypeError):
        pass
    text = raw.strip()
    if text.startswith('```json') and text.endswith('```'):
        text = text[7:-3].strip()
    start = re.search(r'"answer"\s*:\s*"', text)
    if not start or not text.startswith('{'):
        return None, False
    candidates = []
    for end in re.finditer(r'"\s*,\s*"(?:evidence_refs|runbooks|missing)"\s*:', text[start.end():]):
        stop = start.end() + end.start()
        body = text[start.end():stop]
        escaped, index = [], 0
        while index < len(body):
            char = body[index]
            if char == '\\' and index + 1 < len(body):
                escaped.append(body[index:index + 2])
                index += 2
                continue
            escaped.append(json.dumps(char, ensure_ascii=False)[1:-1])
            index += 1
        try:
            # Prefix and suffix must already be valid; never infer missing fields.
            value = json.loads(text[:start.end()] + ''.join(escaped) + text[stop:])
            candidates.append(QueryAnswer.model_validate(value).model_dump())
        except (ValueError, TypeError):
            continue
    return (candidates[0], True) if len(candidates) == 1 else (None, False)


class QueryCollectNode(FocusedTaskNode):
    READ_TOOLS = FocusedTaskNode.READ_TOOLS | {
        "kubernetes_count", "kubernetes_jq_query", "kubernetes_tabular_query",
        "kubectl_logs_grep", "kubectl_logs_all_containers_grep",
        "get_prometheus_target", "list_prometheus_rules", "TodoWrite",
    }

    def _prepare_query_tools(self):
        catalog = {str(getattr(e, "link", "")): str(getattr(e, "description", ""))
                   for e in getattr(self.runbook_catalog, "catalog", [])}
        prepared = []
        for tool in getattr(self, "tools", []):
            if tool.name == "fetch_runbook" and hasattr(tool, "model_copy"):
                ids = set()
                for directory in getattr(tool, "runbook_dirs", []):
                    for path in Path(directory).glob("*.md"):
                        ids.add(path.stem)
                        catalog.setdefault(path.name, "运维参考手册")
                tool = tool.model_copy(update={
                    "allowed_runbook_ids": sorted(ids) or getattr(tool, "allowed_runbook_ids", []),
                    "description": "读取指定 Runbook 全文作为参考。按原问题选取相关知识，不要求执行全部步骤；手册不是环境事实。",
                })
            elif hasattr(tool, "model_copy") and " AIOps boundary:" in getattr(tool, "description", ""):
                tool = tool.model_copy(update={"description": tool.description.split(" AIOps boundary:", 1)[0]})
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
        self._archive_node_input({"question": question, "request_contract": state.get("request_contract"), "runbook_catalog": catalog})
        response, events = self._call_llm(
            question + "\n当前 UTC 时间：" + datetime.now(timezone.utc).isoformat()
            + "\n任务理解（以原问题为准）：" + json.dumps(state.get("request_contract"), ensure_ascii=False),
            QUERY_COLLECT_PROMPT + "\n可用 Runbook 目录（按需读取）：\n" + catalog,
            blocked_tool_names={t.name for t in getattr(self, "tools", []) if t.name not in self.READ_TOOLS},
            skip_remediation_policy=True,
        )
        output = {
            "layer": Layer.QUERY,
            "request_route": "query",
            "query_draft": response.result or "",
            "thinking_events": [*(state.get("thinking_events") or []), *events],
        }
        self._archive_node_output(output)
        return output




class QueryConclusionNode(FocusedTaskNode):
    @property
    def node_id(self):
        return "conclusion"

    @property
    def node_name(self):
        return "查询结果整理"

    def execute(self, state):
        _configure_query_runtime(self)
        events = state.get("thinking_events") or []
        last_compaction = next((i for i in range(len(events) - 1, -1, -1)
                                if events[i].get("type") == "context_compacted"), -1)
        payload = build_working_material(state)
        payload["request_contract"] = state.get("request_contract")
        if getattr(self, "ai_call", None) is not None:
            self.ai_call.query_session_context = {}
        self._archive_node_input(payload)
        from app.core.aicall.client import StructuredContextBudgetError
        final_compacted_summary = None
        try:
            prompt = QUERY_CONCLUSION_PROMPT
            if (payload.get("request_contract") or {}).get("route") == "full_diagnosis":
                prompt += "\n" + DEEP_CONCLUSION_PRESENTATION
            prompt += "\n输出 schema：\n" + json.dumps(QueryAnswer.model_json_schema(), ensure_ascii=False)
            def conclude(material):
                return self._call_llm(json.dumps(material, ensure_ascii=False, default=str), prompt,
                                      force_no_tools=True, skip_remediation_policy=True, expect_json=True)
            try:
                response, final_events = conclude(payload)
            except StructuredContextBudgetError as exc:
                if "working_context_compaction_required" not in str(exc):
                    raise
                import asyncio
                from app.core.aicall.working_context import summarize_history
                model = self.ai_call._create_chat_model(node_id="context_compaction", disable_streaming=True).bind(max_tokens=3000)
                summary = asyncio.run(summarize_history(model, payload["question"],
                                                        json.dumps(payload, ensure_ascii=False, default=str),
                                                        lambda **event: self.ai_call._push(
                                                            self._event_queue, self.node_id, events, **event)))
                final_compacted_summary = summary
                compact_payload = {"question": payload["question"], "working_summary": summary,
                                   "request_contract": payload["request_contract"],
                                   "request_time_utc": payload["request_time_utc"],
                                   "execution_incomplete": payload["execution_incomplete"]}
                self._archive_node_input({"before_compaction": payload, "after_compaction": compact_payload})
                response, final_events = conclude(compact_payload)
        except StructuredContextBudgetError as exc:
            answer = str(exc)
            result = QueryAnswer(intent=payload["question"], scope="本次已采集范围，未完成整理",
                                status="partial", answer=answer, missing=[answer],
                                evidence_refs=[o["raw_ref"] for o in payload["observations"] if o.get("raw_ref")]).model_dump()
            output = {"conclusion": answer, "conclusion_formatted": answer,
                      "query_answer": result, "thinking_events": events}
            self._archive_node_output(output)
            return output
        raw = response.result or ""
        result, repaired = parse_query_answer(raw)
        if getattr(self, "current_run_id", None):
            from app.core.context.archive import ContextArchive
            ContextArchive(run_id=self.current_run_id).write_json("conclusion/render_audit.json", {
                "raw": raw, "format_repaired": repaired, "schema_valid": result is not None})
        looks_structured = raw.lstrip().startswith(('{', '[', '```json'))
        if result:
            answer = result["answer"]
        elif looks_structured:
            # Never render a broken JSON envelope as Markdown or invent a successful schema.
            draft = state.get("query_draft") or ""
            if draft.lstrip().startswith(('{', '[', '```json')):
                draft = ""
            answer = ("结果整理格式异常，以下为采集阶段分析草稿，尚未完成最终整理。\n\n" + draft
                      if draft else "结果整理格式异常，未能生成可展示报告。原始输出已保留，请重试。")
        else:
            answer = raw or "本次结果整理未返回内容，请重试。"
        if payload["execution_incomplete"]:
            limitation = "执行未完成：" + "；".join(str(r) for r in payload["execution_incomplete"])
            answer += "\n\n" + limitation
            if result:
                result["status"] = "partial"
                result["answer"] = answer
                result["missing"].append(limitation)
        output = {"conclusion": answer, "conclusion_formatted": answer,
                  "query_answer": result,
                  "thinking_events": [*events, *final_events]}
        previous = state.get("query_session_context") or {}
        memory = {"working_summary": payload["working_summary"], "turns": []} if last_compaction >= 0 else {
            "working_summary": previous.get("working_summary"), "turns": list(previous.get("turns") or [])}
        memory["turns"].append({"question": payload["question"], "answer": answer,
                                "scope": (result or {}).get("scope"),
                                "request_contract": state.get("request_contract"),
                                "recent_interactions": payload["recent_interactions"],
                                "observations": payload["observations"],
                                "execution_incomplete": payload["execution_incomplete"],
                                "observed_at": datetime.now(timezone.utc).isoformat()})
        if final_compacted_summary:
            memory = {"working_summary": final_compacted_summary, "turns": [{
                "question": payload["question"], "answer": answer,
                "scope": (result or {}).get("scope"),
                "request_contract": state.get("request_contract"),
                "observed_at": datetime.now(timezone.utc).isoformat()}]}
        output["query_session_memory"] = memory
        self._archive_node_output(output)
        return output
