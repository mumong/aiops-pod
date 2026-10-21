"""Task routing before observation collection; never infer intent from Pod health.

The contract describes the requested work, not a predetermined tool sequence.
Depth and scope are independent. Structured validation does not rewrite the
model's route; both branches retain the original question and scope.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Literal

from openai import APIStatusError, APITimeoutError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.aicall.output_budget import OutputBudget
from app.core.prompts import REQUEST_ROUTER_PROMPT
from app.core.workflow.nodes.base import WorkflowNode


class RequestContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: Literal["full_diagnosis", "focused", "clarify", "remediation", "unsupported"] = Field(
        description="处理深度；full_diagnosis 不代表扩大到全集群；unsupported=请求不在支持范围"
    )
    task: Literal[
        "inspect", "query", "diagnose", "explain", "mixed", "unsupported", "repair", "operate"
    ]
    scope: Literal["cluster", "namespace", "pod", "unspecified"] = Field(
        description="明确指定 Pod 时为 pod；不限 Pod 的命名空间范围才是 namespace"
    )
    namespaces: list[str] = Field(
        default_factory=list, description="用户或会话明确的命名空间；ns/pod 中斜杠左侧"
    )
    pod_names: list[str] = Field(
        default_factory=list, description="用户或会话明确的 Pod 名称；ns/pod 中斜杠右侧"
    )
    requested_outputs: list[str] = Field(
        default_factory=list, description="用户实际要求的答案项目，不扩写为工具列表或采集计划"
    )
    time_range: str | None = Field(
        default=None, description="用户明确指定的时间范围；未指定必须 null，不补默认 1h 等窗口"
    )
    # Exact user wording is retained for audit; it is not model confidence.
    scope_basis: str = ""
    clarification: str = ""


class MultiClusterRequestContract(RequestContract):
    """Router contract in multi-cluster deployments only (specs/008-multi-cluster)."""

    cluster_mode: Literal["single", "multiple", "center", "inventory", "unspecified"] = Field(
        default="unspecified",
        description=(
            "一个集群 / 多个集群 / 中心集群 / inventory=询问集群本身（有哪些集群、在线状态）；"
            "问题和会话都没说明时为 unspecified"
        ),
    )
    clusters: list[str] = Field(
        default_factory=list,
        description='用户说的集群名或别名（原样）；全部集群为 ["*"]；追问沿用上文集群',
    )
    cluster_labels: list[str] = Field(default_factory=list, description="由系统填写，保持为空")


def _contract_model():
    from app.core import multicluster

    return MultiClusterRequestContract if multicluster.multi() else RequestContract


def router_failure(exc, history_loaded=False):
    """Public, sanitized error presentation; never expose provider bodies or credentials."""
    from app.core.aicall.errors import model_transport_message

    transport_message = model_transport_message(exc)
    status = getattr(exc, "status_code", None) if isinstance(exc, APIStatusError) else None
    if transport_message:
        code, title, detail = "model_connection", "LLM API 服务连接异常", transport_message
        if isinstance(exc, APITimeoutError):
            code, title = "model_timeout", "LLM API 服务响应超时"
    elif status is not None:
        code, title, detail = (
            "model_service",
            "模型服务请求失败",
            f"理解任务时模型服务返回 HTTP {status}。",
        )
        detail += (
            "请检查模型服务认证或配置。"
            if status in (401, 403)
            else "请稍后重试；持续失败请检查模型网关和上游服务。"
        )
    elif isinstance(exc, (ValidationError, ValueError)):
        code, title, detail = (
            "route_format",
            "任务路由输出格式异常",
            "未获得有效的结构化路由结果，请重试；这不表示问题描述不清。",
        )
    else:
        code, title, detail = (
            "route_execution",
            "任务路由执行异常",
            "任务路由未能完成，请重试；持续失败请根据 run_id 检查服务日志。",
        )
    if history_loaded:
        detail += "本次已加载会话上下文，不是会话记忆缺失。"
    detail += "尚未启动集群查询或诊断。"
    return {
        "code": code,
        "title": title,
        "message": detail,
        "http_status": status,
        "history_loaded": history_loaded,
    }


class RequestRouterNode(WorkflowNode):
    def __init__(
        self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None
    ):
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
        from app.core.aicall.client import StructuredContextBudgetError
        from app.core.workflow.nodes.query_answer import _configure_query_runtime

        _configure_query_runtime(self)
        question = state.get("original_question") or state.get("question", "")
        if state.get("repair_entry_requested"):
            # A clicked repair/revision entry explicitly chooses the workflow;
            # the model still decides evidence, repair strategy and actions.
            context = state.get("repair_context") or {}
            source = context.get("diagnosis") or context.get("previous_plan") or {}
            scope = (source.get("payload") or {}).get("request_contract") or {}
            cluster_scope = (
                {
                    "clusters": scope.get("clusters") or [],
                    "cluster_mode": scope.get("cluster_mode") or "unspecified",
                }
                if _contract_model() is MultiClusterRequestContract
                else {}
            )
            contract = _contract_model()(
                route="remediation",
                task="repair",
                scope=scope.get("scope") or "unspecified",
                namespaces=scope.get("namespaces") or [],
                pod_names=scope.get("pod_names") or [],
                requested_outputs=["修复方案与执行审查"],
                scope_basis="用户通过报告或方案入口明确发起；历史记录已校验归属，修复节点自主核实当前事实。",
                **cluster_scope,
            )
            output = {"request_route": "remediation", "request_contract": contract.model_dump()}
            self._archive_node_input({"question": question, "source_run_id": source.get("run_id")})
            self._archive_node_output(output)
            return output
        history = state.get("query_session_context") or {}
        # Answers contain newly discovered referents absent from the original contract.
        # Preserve dialogue, not bulky tool payloads; budget overflow uses compaction below.
        context = {
            "question": question,
            "history": [
                {
                    "question": turn.get("question"),
                    "answer": turn.get("answer"),
                    "observed_at": turn.get("observed_at"),
                    "scope": turn.get("scope"),
                    "request_contract": turn.get("request_contract"),
                }
                for turn in history.get("turns", [])
            ],
            "working_summary": history.get("working_summary"),
        }
        self._archive_node_input(context)
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise RuntimeError("请求已取消")
        started = time.monotonic()
        from app.core import multicluster

        contract_model = _contract_model()
        system_prompt = REQUEST_ROUTER_PROMPT + (
            multicluster.router_prompt() if contract_model is MultiClusterRequestContract else ""
        )
        try:

            def classify(material):
                return self.ai_call.call_structured(
                    system_prompt=system_prompt,
                    question=material,
                    schema=contract_model,
                    node_id=self.node_id,
                    run_id=getattr(self, "current_run_id", ""),
                    # Classification only: no tools, no user-facing reasoning. As an
                    # internal (no-thinking) call it answers in seconds; with thinking
                    # on, 2 of 4 live router calls today ended in a gateway HTTP 500
                    # after ~60s of reasoning against a small output reserve.
                    max_tokens=(
                        getattr(self.ai_call, "output_budget", None) or OutputBudget.from_config()
                    ).router,
                    internal_model=True,
                    raise_on_error=True,
                )

            serialized = json.dumps(context, ensure_ascii=False) if history else question
            try:
                contract, _ = classify(serialized)
            except StructuredContextBudgetError as exc:
                if "working_context_compaction_required" not in str(exc):
                    raise
                import asyncio

                from app.core.aicall.working_context import compact_working_material

                model = self.ai_call.create_compaction_model()
                reduced = asyncio.run(
                    compact_working_material(
                        model,
                        {
                            "question": question,
                            "working_summary": context["working_summary"],
                            "recent_interactions": [
                                {"type": "human", "content": json.dumps(turn, ensure_ascii=False)}
                                for turn in context["history"]
                            ],
                        },
                        lambda **event: self.ai_call._push(
                            self._event_queue, self.node_id, [], **event
                        ),
                    )
                )
                self._archive_node_input(
                    {"before_compaction": context, "after_compaction": reduced}
                )
                contract, _ = classify(json.dumps(reduced, ensure_ascii=False))
            if contract is None:
                raise ValueError("任务分类未返回有效结构化结果")
            contract = contract_model.model_validate(
                contract.model_dump() if isinstance(contract, BaseModel) else contract
            )
        except Exception as exc:
            from app.core.aicall.errors import raise_on_model_disconnect

            raise_on_model_disconnect(exc)
            # Never convert a failed classifier into permission for a scan.
            failure = router_failure(exc, bool(context["history"] or context["working_summary"]))
            output = {
                "request_contract": None,
                "request_route": "stop",
                "request_error": failure,
                "conclusion": f"{failure['title']}\n\n{failure['message']}",
                "errors": [*(state.get("errors") or []), f"request_router: {failure['code']}"],
            }
            self._archive_node_output(output)
            return output
        finally:
            if self.metrics is not None:
                self.metrics.record_llm_call(self.node_id, (time.monotonic() - started) * 1000)
        if contract.route == "unsupported":
            # A refusal is an answer, not a format error: say why, run nothing.
            reason = (contract.clarification or "").strip().rstrip("。.") or (
                "任意主机或非 Pod 的破坏性操作不在支持范围"
            )
            failure = {
                "code": "unsupported_request",
                "title": "请求不在支持范围",
                "message": f"{reason}。本次未执行任何命令，也未启动集群查询或诊断。",
                "http_status": None,
                "history_loaded": bool(context["history"] or context["working_summary"]),
            }
            output = {
                "request_contract": contract.model_dump(),
                "request_route": "stop",
                "request_error": failure,
                "conclusion": f"{failure['title']}\n\n{failure['message']}",
                "errors": [*(state.get("errors") or []), "request_router: unsupported_request"],
            }
            self._archive_node_output(output)
            return output
        if (
            contract.route == "remediation"
            and state.get("repair_auto_plan")
            and not (state.get("repair_context") or {}).get("diagnosis")
        ):
            # repair=plan (API / A2A) with no diagnosis in the session: diagnose first;
            # the executor then starts the per-group batch, whose approvals API callers
            # can see. The web chat never sets repair=plan and keeps its route.
            contract = contract.model_copy(
                update={
                    "route": "full_diagnosis",
                    "task": "diagnose",
                    "scope_basis": (contract.scope_basis + "；" if contract.scope_basis else "")
                    + "repair=plan 且会话中尚无诊断：先诊断，再按异常组生成修复方案",
                }
            )
        if contract_model is MultiClusterRequestContract and contract.route != "clarify":
            # The scope is resolved by code against the registry; an unclear or
            # unknown scope becomes a question, whatever route the model chose.
            resolved, question_back = multicluster.resolve_contract(
                contract.model_dump(), evidence=json.dumps(context, ensure_ascii=False)
            )
            update = {
                "clusters": resolved["clusters"],
                "cluster_mode": resolved["cluster_mode"],
                # Labels only for a resolved scope; a clarification has none.
                "cluster_labels": []
                if question_back
                else multicluster.labels(resolved["clusters"]),
            }
            if question_back:
                update.update(route="clarify", clarification=question_back)
            contract = contract.model_copy(update=update)
        output = {
            "request_contract": contract.model_dump(),
            "request_route": contract.route,
        }
        if contract.route == "clarify":
            output["conclusion"] = contract.clarification
            output["query_session_memory"] = {
                **history,
                "turns": [
                    *(history.get("turns") or []),
                    {
                        "question": question,
                        "answer": contract.clarification,
                        "scope": contract.scope,
                        "request_contract": contract.model_dump(),
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                    },
                ],
            }
        self._archive_node_output(output)
        return output
