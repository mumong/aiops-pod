"""Bounded, task-oriented read-only investigation without diagnostic fan-out."""

import json
import time
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.core.prompts import (
    FOCUSED_PROMPT,
    FOCUSED_RESULT_PROMPT,
    FOCUSED_RUNBOOK_DESCRIPTION_PREFIX,
    FOCUSED_REQUEST_TIME_TEMPLATE,
)
from app.core.skills.models import Layer
from app.core.workflow.nodes.base import WorkflowNode


class FocusedResult(BaseModel):
    answer: str = Field(description="直接回答用户原问题的中文 Markdown；数值表应注明单位、时间和百分比分母")
    missing: list[str] = Field(default_factory=list, description="未回答的请求项及原因；没有采集到不等于不存在")
    evidence_refs: list[str] = Field(default_factory=list, description="支撑当前环境结论的实际工具 raw_ref，逐字复制，不能编造")





class FocusedTaskNode(WorkflowNode):
    # Explicit capability allowlist: no arbitrary shell, exec, or mutation tool.
    READ_TOOLS = {
        "kubectl_get_by_name", "kubectl_get_by_kind_in_namespace",
        "kubectl_get_by_kind_in_cluster", "kubectl_find_resource", "kubectl_get_yaml",
        "kubectl_describe", "kubectl_events", "kubectl_logs", "kubectl_previous_logs",
        "kubectl_logs_all_containers", "kubectl_previous_logs_all_containers",
        "kubectl_container_logs", "kubectl_container_previous_logs",
        "kubectl_lineage_children", "kubectl_lineage_parents",
        "execute_pod_promql", "query_pod_logs", "query_pod_tracing", "query_pod_topology",
        "execute_prometheus_instant_query", "execute_prometheus_range_query",
        "get_metric_names", "get_label_values", "get_all_labels", "get_series",
        "get_metric_metadata", "fetch_runbook", "read_context_archive",
    }

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

    @property
    def node_id(self):
        return "focused"

    @property
    def node_name(self):
        return "按问题查询与分析"

    def should_inject_runbook_catalog(self):
        return False

    def execute(self, state):
        contract = state.get("request_contract") or {}
        question = state.get("question", "")
        request_time = datetime.now(timezone.utc).isoformat()
        self._archive_node_input({"question": question, "request_contract": contract, "request_time_utc": request_time})
        if contract.get("task") == "unsupported":
            return {"conclusion": "当前路径仅支持只读查询与分析，不执行变更。请说明需要检查的对象和问题。"}
        allowed = {"fetch_runbook"} if contract.get("task") == "explain" else self.READ_TOOLS
        blocked = {tool.name for tool in getattr(self, "tools", []) if tool.name not in allowed}
        # Legacy MCP descriptions restrict general PromQL to the /query URL.
        # This task route is also a query capability; do not let stale endpoint
        # wording override the current user's task. Clone, never mutate tools
        # shared with the full-diagnosis branch or concurrent requests.
        self.tools = [
            tool.model_copy(update={"description": tool.description.split(" AIOps boundary:", 1)[0]})
            if hasattr(tool, "model_copy") and " AIOps boundary:" in getattr(tool, "description", "")
            else tool
            for tool in getattr(self, "tools", [])
        ]
        self.tools = [
            tool.model_copy(update={"description": (
                FOCUSED_RUNBOOK_DESCRIPTION_PREFIX
                + ", ".join(getattr(tool, "allowed_runbook_ids", []))
            )})
            if tool.name == "fetch_runbook" and hasattr(tool, "model_copy") else tool
            for tool in self.tools
        ]
        response, events = self._call_llm(
            question + "\n\n任务合同：\n" + json.dumps(contract, ensure_ascii=False)
            + FOCUSED_REQUEST_TIME_TEMPLATE.format(request_time=request_time),
            FOCUSED_PROMPT,
            blocked_tool_names=blocked,
            skip_remediation_policy=True,
        )
        # Keep final-output tools out of the collection loop: some small models
        # otherwise select the schema tool immediately and invent observations.
        observations = [
            {key: event.get(key) for key in (
                "tool_name", "tool_args", "status", "semantic_success", "raw_ref", "result"
            )}
            for event in events if event.get("type") == "tool_result"
        ]
        result = None
        started = time.monotonic()
        try:
            result, _ = self.ai_call.call_structured(
                system_prompt=(
                    FOCUSED_RESULT_PROMPT
                ),
                question=json.dumps({
                    "question": question, "request_contract": contract,
                    "observations": observations,
                    # Environmental answers are rebuilt from observations;
                    # do not anchor the formatter to unverified agent prose.
                    "analysis_draft": (response.result or "")[:6000] if contract.get("task") == "explain" else "",
                }, ensure_ascii=False),
                schema=FocusedResult, node_id="focused_output",
                run_id=getattr(self, "current_run_id", ""), max_tokens=4000,
            )
            result = FocusedResult.model_validate(result)
        except (ValueError, TypeError):
            # Do not publish an unvalidated fallback diagnosis as a completed answer.
            result = FocusedResult(answer="本次未形成有效的结构化回答。", missing=["请重试；已采集结果保留在运行归档中。"])
        finally:
            if self.metrics is not None:
                self.metrics.record_llm_call(self.node_id, (time.monotonic() - started) * 1000)

        sources = {
            event["raw_ref"]: event
            for event in events
            if event.get("type") == "tool_result" and event.get("raw_ref")
        }
        # Reference validation checks provenance, not positive diagnostic support.
        # NotFound/empty/permission errors are usable evidence of absence or of
        # collection limitations; excluding them suppresses legitimate answers.
        invalid = set(result.evidence_refs) - sources.keys()
        verified_refs = [ref for ref in result.evidence_refs if ref in sources]
        if contract.get("task") != "explain" and (invalid or not verified_refs):
            result.answer = "本次回答缺少可核验的工具来源，暂不能确认环境结论。"
            result.missing.append("需要有效工具证据及对应引用；未将无来源分析作为完成结果。")
        result.evidence_refs = verified_refs
        report = result.answer
        if result.missing:
            report += "\n\n未完成或限制：\n\n" + "\n".join(f"- {item}" for item in result.missing)
        output = {
            "layer": Layer.QUERY,
            "focused_result": result.model_dump(),
            "conclusion": report,
            "conclusion_formatted": report,
            "thinking_events": [*(state.get("thinking_events") or []), *events],
            "tool_artifact_refs": [
                {"tool": sources[ref].get("tool_name"), "raw_ref": ref}
                for ref in verified_refs
            ],
        }
        self._archive_node_output(output)
        return output
