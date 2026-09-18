"""Task routing before observation collection; never infer intent from Pod health.

The contract describes the requested work, not a predetermined tool sequence.
Depth and scope are independent. Structured validation does not rewrite the
model's route; both branches retain the original question and scope.
"""

from typing import Any, Literal
import time

from pydantic import BaseModel, ConfigDict, Field
from app.core.prompts import REQUEST_ROUTER_PROMPT
import json
from datetime import datetime, timezone

from app.core.workflow.nodes.base import WorkflowNode


class RequestContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: Literal["full_diagnosis", "focused", "clarify"] = Field(
        description="处理深度；full_diagnosis 不代表扩大到全集群")
    task: Literal["inspect", "query", "diagnose", "explain", "mixed", "unsupported"]
    scope: Literal["cluster", "namespace", "pod", "unspecified"] = Field(description="明确指定 Pod 时为 pod；不限 Pod 的命名空间范围才是 namespace")
    namespaces: list[str] = Field(default_factory=list, description="用户或会话明确的命名空间；ns/pod 中斜杠左侧")
    pod_names: list[str] = Field(default_factory=list, description="用户或会话明确的 Pod 名称；ns/pod 中斜杠右侧")
    requested_outputs: list[str] = Field(default_factory=list, description="用户实际要求的答案项目，不扩写为工具列表或采集计划")
    time_range: str | None = Field(default=None, description="用户明确指定的时间范围；未指定必须 null，不补默认 1h 等窗口")
    # Exact user wording is retained for audit; it is not model confidence.
    scope_basis: str = ""
    clarification: str = ""


ROUTER_PROMPT = REQUEST_ROUTER_PROMPT  # Compatibility import; editable source is prompts.py.


class RequestRouterNode(WorkflowNode):
    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

    @property
    def node_id(self) -> str:
        return "request_router"

    @property
    def node_name(self) -> str:
        return "理解用户任务"

    def should_inject_runbook_catalog(self) -> bool:
        return False

    def execute(self, state):
        from app.core.workflow.nodes.query_answer import _configure_query_runtime
        from app.core.aicall.client import StructuredContextBudgetError
        _configure_query_runtime(self)
        question = state.get("original_question") or state.get("question", "")
        history = state.get("query_session_context") or {}
        # Answers contain newly discovered referents absent from the original contract.
        # Preserve dialogue, not bulky tool payloads; budget overflow uses compaction below.
        context = {"question": question, "history": [
            {"question": turn.get("question"), "answer": turn.get("answer"),
             "observed_at": turn.get("observed_at"), "scope": turn.get("scope"),
             "request_contract": turn.get("request_contract")}
            for turn in history.get("turns", [])],
            "working_summary": history.get("working_summary")}
        self._archive_node_input(context)
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise RuntimeError("请求已取消")
        started = time.monotonic()
        try:
            def classify(material):
                return self.ai_call.call_structured(
                    system_prompt=REQUEST_ROUTER_PROMPT, question=material,
                    schema=RequestContract, node_id=self.node_id,
                    run_id=getattr(self, "current_run_id", ""), max_tokens=1200,
                )
            serialized = json.dumps(context, ensure_ascii=False) if history else question
            try:
                contract, _ = classify(serialized)
            except StructuredContextBudgetError as exc:
                if "working_context_compaction_required" not in str(exc):
                    raise
                import asyncio
                from app.core.aicall.working_context import compact_working_material
                model = self.ai_call._create_chat_model(node_id="context_compaction", disable_streaming=True).bind(max_tokens=3000)
                reduced = asyncio.run(compact_working_material(model, {
                    "question": question, "working_summary": context["working_summary"],
                    "recent_interactions": [{"type": "human", "content": json.dumps(turn, ensure_ascii=False)}
                                            for turn in context["history"]]},
                    lambda **event: self.ai_call._push(self._event_queue, self.node_id, [], **event)))
                self._archive_node_input({"before_compaction": context, "after_compaction": reduced})
                contract, _ = classify(json.dumps(reduced, ensure_ascii=False))
            if contract is None:
                raise ValueError("任务分类未返回有效结构化结果")
            contract = RequestContract.model_validate(contract)
        except Exception as exc:
            # Never convert a failed classifier into permission for a scan.
            output = {
                "request_contract": None,
                "request_route": "stop",
                "conclusion": "暂时无法可靠识别本次任务，未启动集群检查。请重试。",
                "errors": [*(state.get("errors") or []), f"request_router: {exc}"],
            }
            self._archive_node_output(output)
            return output
        finally:
            if self.metrics is not None:
                self.metrics.record_llm_call(self.node_id, (time.monotonic() - started) * 1000)
        output = {
            "request_contract": contract.model_dump(),
            "request_route": contract.route,
        }
        if contract.route == "clarify":
            output["conclusion"] = contract.clarification
            output["query_session_memory"] = {
                **history, "turns": [*(history.get("turns") or []), {
                    "question": question, "answer": contract.clarification,
                    "scope": contract.scope, "request_contract": contract.model_dump(),
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                }],
            }
        self._archive_node_output(output)
        return output
