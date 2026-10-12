"""Intent-aware, persistent replacement of an agent's working history."""

import json
import asyncio
import os
from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from app.core.context.archive import ContextArchive
from app.core.context.handoff import protected_handoff, handoff_from_messages
from app.core.context.lifecycle_core import material_without_core, messages_without_core, core_notice
from app.core.context.budget import count_tokens
from app.core.context.evidence_policy import EvidencePolicy
from app.core.prompts import CONTEXT_SUMMARY_PROMPT as SUMMARY_PROMPT
from app.core.prompts import WORKING_CONTEXT_SUMMARY_PREFIX


def compact_message(message, *, include_refs=False):
    """Keep semantic content and call linkage, not usage/provider telemetry."""
    data = message if isinstance(message, dict) else message.model_dump(exclude_none=True)
    result = {key: data[key] for key in ("type", "role", "content", "name", "tool_calls", "tool_call_id")
              if key in data}
    extras = data.get("additional_kwargs") or {}
    provenance = {key: extras[key] for key in ("aiops_deduplicated", "aiops_original_tool_call_id", "aiops_tool_error") if key in extras}
    if include_refs:
        for key in ("aiops_raw_ref", "aiops_semantic_success"):
            if key in extras:
                provenance[key] = extras[key]
            elif key in (data.get("provenance") or {}):
                provenance[key] = data["provenance"][key]
    if provenance:
        result["provenance"] = provenance
    return result


def source_receipts(messages):
    """Index source addresses, not facts; avoid a forced read of full history."""
    calls, receipts = {}, {}

    def material(payload):
        if not isinstance(payload, dict):
            return
        for item in payload.get("observations") or []:
            if isinstance(item, dict) and item.get("raw_ref"):
                receipts[item["raw_ref"]] = {k: item.get(k) for k in
                                             ("tool_name", "tool_args", "raw_ref", "semantic_success")}
        scan(payload.get("recent_interactions") or [])
        for lane in payload.get("parallel_results") or []:
            if isinstance(lane, dict):
                material(lane.get("material") or {})

    def scan(items):
        for message in items:
            data = message if isinstance(message, dict) else message.model_dump(exclude_none=True)
            calls.update({call.get("id"): call for call in data.get("tool_calls") or []})
            extras = {**(data.get("provenance") or {}), **(data.get("additional_kwargs") or {})}
            ref = extras.get("aiops_raw_ref")
            if ref:
                call = calls.get(data.get("tool_call_id"), {})
                receipts[ref] = {"raw_ref": ref, "tool_name": data.get("name") or call.get("name"),
                                 "tool_args": call.get("args", {}),
                                 "semantic_success": extras.get("aiops_semantic_success")}
            if data.get("type", data.get("role")) in {"human", "user"}:
                content = data.get("content")
                if isinstance(content, str) and content.lstrip().startswith("{"):
                    try:
                        payload = json.loads(content)
                    except (ValueError, RecursionError):
                        continue
                    if isinstance(payload, dict) and "question" in payload:
                        material(payload)
    scan(messages)
    return list(receipts.values())


def message_groups(messages):
    """Do not separate an assistant's parallel calls from their tool responses."""
    groups = []
    index = 0
    while index < len(messages):
        group = [messages[index]]
        index += 1
        calls = group[0].get("tool_calls") if isinstance(group[0], dict) else getattr(group[0], "tool_calls", None)
        if calls:
            while index < len(messages) and (messages[index].get("type", messages[index].get("role")) if isinstance(messages[index], dict) else getattr(messages[index], "type", None)) == "tool":
                group.append(messages[index])
                index += 1
            expected = {str(c["id"]) for c in calls}
            actual = {str(m.get("tool_call_id") if isinstance(m, dict) else m.tool_call_id) for m in group[1:]}
            if expected != actual:
                raise RuntimeError("工具交互尚不完整，未压缩或拆分该交互")
        groups.append(group)
    return groups


def partition_recent(groups, window, *, keep_tokens=None):
    """Shared atomic suffix policy for agents and inter-node material."""
    keep_budget = min(8000, int(window * 0.15))
    if keep_tokens is not None:
        keep_budget = min(keep_budget, keep_tokens)
    used, cut = 0, len(groups)
    for group in reversed(groups):
        cost = count_tokens(json.dumps([compact_message(m) for m in group], ensure_ascii=False))["tokens"]
        if used + cost > keep_budget:
            break
        used += cost
        cut -= 1
    return groups[:cut], groups[cut:]


async def compact_working_material(model, material, progress=None, *, window=None):
    """Use the agent's suffix policy at node boundaries, retaining exact evidence.

    Observations already include the call arguments and result, so each is an
    atomic interaction. Do not concatenate independent lanes' message histories.
    """
    window = window or int(os.getenv("MODEL_CONTEXT_WINDOW", "32000"))
    protected = protected_handoff(material)
    material = material_without_core(material)
    groups = message_groups(material.get("recent_interactions") or [])
    groups += [[{"type": "human", "content": json.dumps({"tool_observation": item}, ensure_ascii=False, default=str)}]
               for item in material.get("observations") or []]
    head = {k: v for k, v in material.items() if k not in {"recent_interactions", "observations", "evidence_receipts", "protected_handoff"}}
    if core_notice(protected):
        head['protected_facts_available'] = core_notice(protected)
    # Fan-in retains lane identity, including inside retained raw interactions.
    # Compaction in one worker must never act as a global message replacement.
    if material.get("parallel_results"):
        head["parallel_results"] = []
        for lane in sorted(material["parallel_results"], key=lambda r: r.get("completed_at", 0)):
            data = lane.get("material") or {}
            head["parallel_results"].append({**lane, "material": {
                k: v for k, v in data.items() if k not in {"observations", "recent_interactions"}}})
            units = message_groups(data.get("recent_interactions") or [])
            units += [[{"type": "human", "content": json.dumps({"tool_observation": o}, ensure_ascii=False, default=str)}]
                      for o in data.get("observations") or []]
            groups += [[{"type": "human", "content": json.dumps({"lane_id": lane["group_id"],
                         "target": lane.get("target"), "interaction": unit}, ensure_ascii=False, default=str)}]
                       for unit in units]
    older, recent = partition_recent(groups, window)
    sections = [json.dumps(head, ensure_ascii=False, default=str) + "\n"]
    sections += [json.dumps(group, ensure_ascii=False, default=str) + "\n" for group in older]
    summary = await summarize_history(model, material["question"], "".join(sections), progress,
                                      window=window, sections=sections)
    return {**{k: material[k] for k in ("question", "original_question", "request_contract", "original_request_contract", "request_time_utc",
                                      "execution_incomplete", "diagnosis_target", "parallel_inventory", "evidence_receipts") if k in material},
            "protected_handoff": protected,
            "working_summary": summary, "recent_interactions": [m for group in recent for m in group],
            "observations": []}


def summary_chunks(question, serialized, *, window=None, sections=None):
    """Pack complete interactions by token budget; split only an oversized unit."""
    window = window or int(os.getenv("MODEL_CONTEXT_WINDOW", "32000"))
    # Reserve space for the rolling summary, output and protocol/estimation error.
    input_limit = min(int(window * 0.72), window - 5000)
    prefix = SUMMARY_PROMPT + json.dumps({"original_question": question}, ensure_ascii=False)
    capacity = input_limit - count_tokens(prefix)["tokens"] - 6000
    if capacity < 512:
        raise RuntimeError("摘要输入预算不足，未删除历史")
    def size(text):
        # Count escaped text as it will appear inside the JSON request.
        return count_tokens(json.dumps(text, ensure_ascii=False))["tokens"]
    units = sections if sections is not None else [serialized]
    chunks, current = [], ""
    for unit in units:
        if current and size(current + unit) > capacity:
            chunks.append(current)
            current = ""
        while size(unit) > capacity:
            low, high = 1, len(unit)
            while low < high:
                mid = (low + high + 1) // 2
                if size(unit[:mid]) <= capacity:
                    low = mid
                else:
                    high = mid - 1
            chunks.append(unit[:low])
            unit = unit[low:]
        current += unit
    if current:
        chunks.append(current)
    return chunks, input_limit


async def summarize_history(model, question, serialized, progress=None, *, window=None, sections=None, parallel=None, stats=None):
    """Prefer a single call; every input unit is consumed if segmentation is needed."""
    summary = ""
    stats = stats if stats is not None else {}
    chunks, input_limit = summary_chunks(question, serialized, window=window, sections=sections)
    total = len(chunks)
    def notify(status, content):
        if progress:
            progress(type="runtime_status", status=status, content=content)
    workers = max(1, min(3, int(os.getenv("AIOPS_COMPACTION_WORKERS", "3"))))
    if parallel is False:
        workers = 1
    if total >= 3 and workers > 1:
        # Map every byte; no tail clipping. Commit only after all cards merge.
        gate = asyncio.Semaphore(workers)
        done = 0
        async def map_chunk(index, chunk):
            nonlocal done
            async with gate:
                notify("running", f"正在并行整理较早上下文：已完成 {done}/{total} 段，最多 {workers} 路；随后合并为一份工作记忆。")
                request = [SystemMessage(content=SUMMARY_PROMPT), HumanMessage(content=json.dumps({
                    "mode": "map", "original_question": question,
                    "chunk_index": index, "is_last_chunk": index == total - 1,
                    "next_history_chunk": chunk,
                }, ensure_ascii=False))]
                if count_tokens(SUMMARY_PROMPT + request[-1].content)["tokens"] + 512 > input_limit:
                    raise RuntimeError("摘要请求超过预算，未删除历史")
                bounded_model = model.bind(max_tokens=2000) if hasattr(model, "bind") else model
                stats["calls"] = stats.get("calls", 0) + 1
                response = await bounded_model.ainvoke(request, config={"tags": ["nostream"], "metadata": {"aiops_internal_compaction": True}})
                card = response.content
                if not isinstance(card, str) or not card.strip() or count_tokens(card)["tokens"] > 5000:
                    raise RuntimeError("分段摘要为空或超预算，未替换历史")
                if (getattr(response, "response_metadata", {}) or {}).get("finish_reason") == "length":
                    raise RuntimeError("分段摘要被输出上限截断，未替换历史")
                done += 1
                return json.dumps({"source_order": index, "evidence_card": card}, ensure_ascii=False) + "\n"
        tasks = [asyncio.create_task(map_chunk(i, c)) for i, c in enumerate(chunks)]
        try:
            cards = await asyncio.gather(*tasks)  # source order, not completion order
            notify("running", f"分段整理完成 {total}/{total}，正在按原顺序合并工作记忆；近期原文保持不变。")
            return await summarize_history(model, question, "".join(cards), progress,
                                           window=window, sections=cards, parallel=False, stats=stats)
        except BaseException as exc:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            notify("cancelled" if isinstance(exc, asyncio.CancelledError) else "error", "上下文整理未完成，保留原工作历史。")
            raise
    offset = 0
    for index, chunk in enumerate(chunks):
        notify("running", f"正在整理工作记忆（进度 {index + 1}/{total}）：待摘要内容较多时分批合并为一份摘要，完成后继续分析；当前不是工具执行。")
        try:
            request = [
            SystemMessage(content=SUMMARY_PROMPT),
            HumanMessage(content=json.dumps({
                "original_question": question, "working_summary": summary,
                "mode": "reduce" if parallel is False else "rolling",
                "chunk_index": index, "is_last_chunk": index == total - 1,
                "history_offset": offset, "history_total_chars": len(serialized),
                "next_history_chunk": chunk,
            }, ensure_ascii=False)),
            ]
            if count_tokens(SUMMARY_PROMPT + request[-1].content)["tokens"] + 512 > input_limit:
                raise RuntimeError("摘要请求超过预算，未删除历史")
            stats["calls"] = stats.get("calls", 0) + 1
            response = await model.ainvoke(request, config={"tags": ["nostream"], "metadata": {"aiops_internal_compaction": True}})
        except asyncio.CancelledError:
            notify("cancelled", "上下文整理已取消，未替换工作历史。")
            raise
        except Exception:
            notify("error", "上下文整理失败，未替换工作历史。")
            raise
        summary = response.content
        if (getattr(response, "response_metadata", {}) or {}).get("finish_reason") == "length":
            notify("error", "摘要被输出上限截断，未替换工作历史。")
            raise RuntimeError("摘要输出被截断，未替换历史")
        if not isinstance(summary, str) or not summary.strip():
            notify("error", "上下文整理返回空内容，未替换工作历史。")
            raise RuntimeError("上下文整理返回空内容，未替换原工作历史")
        if len(summary) > 18000 or count_tokens(json.dumps(summary, ensure_ascii=False))["tokens"] > 5000:
            notify("error", "上下文整理结果过长，未替换工作历史。")
            raise RuntimeError("上下文整理未遵守输出预算，未替换原工作历史")
        offset += len(chunk)
    notify("complete", "上下文摘要已生成，正在校验预算并继续处理。")
    return summary


class WorkingContextMiddleware(AgentMiddleware):
    def __init__(self, client, model, summary_model, tools, system_prompt, question, run_id, node_id, emit, response_format=None):
        self.client, self.model, self.summary_model = client, model, summary_model
        self.tools, self.system_prompt, self.question = tools, system_prompt, question
        self.run_id, self.node_id, self.emit = run_id, node_id, emit
        self.sequence = 0
        self.response_format = response_format
        self.evidence_policy = EvidencePolicy.from_env()

    @staticmethod
    def tool_history_tokens(messages):
        """Recount active atomic interactions; no process-global/monotonic counter.

        Includes explicit archive reads and call arguments. Historical summaries
        and system prompts remain covered by the independent whole-request guard.
        """
        total = 0
        for group in message_groups(messages):
            items = [compact_message(m) for m in group]
            if any(m.get("type", m.get("role")) == "tool" for m in items):
                total += count_tokens(json.dumps(items, ensure_ascii=False))["tokens"]
                continue
            # Node handoffs carry observations inside one human message rather
            # than ToolMessages. Count the explicit material contract as well;
            # starting a new collection node must not reset inherited evidence.
            for item in items:
                content = item.get("content")
                if not isinstance(content, str) or not content.lstrip().startswith("{"):
                    continue
                try:
                    payload = json.loads(content)
                except (ValueError, RecursionError):
                    continue
                if isinstance(payload, dict) and "question" in payload:
                    evidence = {k: payload[k] for k in ("observations", "recent_interactions", "parallel_results")
                                if payload.get(k)}
                    if evidence:
                        total += count_tokens(json.dumps(evidence, ensure_ascii=False))["tokens"]
        return total

    def probe(self, messages):
        return self.client._guard_agent_model_request(ModelRequest(
            model=self.model, messages=messages, tools=self.tools,
            system_message=SystemMessage(content=self.system_prompt),
            response_format=self.response_format,
        ), node_id=self.node_id)

    async def abefore_model(self, state, runtime):
        from app.core.aicall.client import StructuredContextBudgetError
        messages = state["messages"]
        trigger = "request_budget"
        try:
            _, pre_budget = self.probe(messages)
            window = int(pre_budget.get("context_window") or os.getenv("MODEL_CONTEXT_WINDOW", "32000"))
            high, _ = self.evidence_policy.limits(window)
            if not self.evidence_policy.enabled or self.tool_history_tokens(messages) <= high:
                return None
            trigger = "evidence_history_budget"
        except StructuredContextBudgetError as exc:
            if "working_context_compaction_required" not in str(exc):
                raise
            pre_budget = exc.pre_budget
        self.sequence += 1
        archive = ContextArchive(run_id=self.run_id)
        source = [self.client._serialize_agent_message(m) for m in messages]
        source_ref = archive.write_json(f"compactions/{self.node_id}-{self.sequence:03d}.before.json", source)
        window = int(pre_budget.get("context_window") or os.getenv("MODEL_CONTEXT_WINDOW", "32000"))
        high, low = self.evidence_policy.limits(window)
        protected = handoff_from_messages(messages)
        groups = message_groups(messages_without_core(messages))
        # A bounded suffix preserves the newest complete interactions verbatim.
        if self.evidence_policy.enabled:
            old_groups, recent_groups = partition_recent(groups[1:], window, keep_tokens=low)
        else:
            old_groups, recent_groups = partition_recent(groups[1:], window)
        old_groups = groups[:1] + old_groups
        retained = [m for group in recent_groups for m in group]
        older = [m for group in old_groups for m in group]
        sections = [json.dumps([compact_message(m, include_refs=self.evidence_policy.enabled) for m in group], ensure_ascii=False) + "\n"
                    for group in old_groups]
        if core_notice(protected):
            sections.insert(0, json.dumps({'protected_facts_available': core_notice(protected)}, ensure_ascii=False) + '\n')
        history = "".join(sections)
        stats = {}
        self.emit(type="runtime_status", status="running", content=(
            "累计工具证据达到工作预算，正在整理早期历史；近期完整交互与原文归档保留，完成后继续。"
            if trigger == "evidence_history_budget" else "上下文达到预算，正在整理早期历史并保留近期完整交互。"))
        summary = await summarize_history(self.summary_model, self.question,
                                          history, self.emit, window=window, sections=sections, stats=stats)
        # Keep provenance outside model-written text as well as in the snapshot.
        summary += f"\n压缩前完整工作历史归档：{source_ref}"
        if self.evidence_policy.enabled:
            receipts = source_receipts(older)
            if receipts:
                refs_path = archive.write_json(f"compactions/{self.node_id}-{self.sequence:03d}.sources.json", receipts)
                summary += f"\n原始工具结果来源目录（工具名、参数、raw_ref；可定向检索，无需遍历整段历史）：{refs_path}"
        replacement = [HumanMessage(content=self.question), HumanMessage(
            content=WORKING_CONTEXT_SUMMARY_PREFIX + summary), *retained]
        if protected:
            replacement.insert(1, HumanMessage(content=json.dumps(
                {"protected_handoff": protected}, ensure_ascii=False)))
        try:
            _, post_budget = self.probe(replacement)
            if self.evidence_policy.enabled and self.tool_history_tokens(replacement) > low:
                raise RuntimeError("整理后工具证据未降至保留预算，未替换原工作历史")
        except Exception:
            self.emit(type="runtime_status", status="error",
                      content="整理后的上下文仍未通过预算检查，未替换原工作历史。")
            raise
        archive.write_json(f"compactions/{self.node_id}-{self.sequence:03d}.after.json", {
            "messages": [m.model_dump() for m in replacement],
            "pre_budget": pre_budget, "post_budget": post_budget,
            "summarized_messages": len(older), "retained_messages": len(retained),
            "summary_calls": stats.get("calls", 0),
            "trigger": trigger,
            "evidence_budget": {"enabled": self.evidence_policy.enabled,
                                "high_tokens": high, "recent_tokens": low},
        })
        self.emit(type="context_compacted", working_summary=summary, protected_handoff=protected,
                  source_ref=source_ref, original_messages=len(messages), replacement_messages=len(replacement),
                  retained_messages=[compact_message(m, include_refs=self.evidence_policy.enabled) for m in retained])
        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *replacement]}
