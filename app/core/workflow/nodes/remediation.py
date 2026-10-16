"""Read-only preparation of a Pod remediation plan; never executes writes."""

import json
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.prompts import POD_REMEDIATION_PROMPT
from app.core.workflow.nodes.query_answer import (
    QueryAnswer,
    QueryCollectNode,
    _configure_query_runtime,
    finalize_query_answer,
)


class RepairTarget(BaseModel):
    namespace: str
    pod: str
    pod_uid: str = ""
    group_id: str
    owner_kind: str = ""
    owner_name: str = ""
    owner_uid: str = ""


class RepairAction(BaseModel):
    id: str
    group_id: str
    description: str
    risk: str
    dry_run_command: str = ""
    execute_command: str
    verify_command: str = ""
    rollback_advice: str
    configuration_change: str = ""
    verification_conditions: list[str] = Field(default_factory=list)


class RepairAssessment(BaseModel):
    group_id: str
    status: Literal["ready", "needs_input", "not_actionable", "needs_evidence"]
    reason: str
    missing: list[str] = Field(default_factory=list)


class RepairDraft(QueryAnswer):
    targets: list[RepairTarget] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    runbook_unavailable_reason: str = ""
    assessments: list[RepairAssessment] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def bind_single_group(cls, data):
        """With exactly one target there is no ambiguity: bind actions/assessments to it.

        A bookkeeping field, not a strategy decision; the model still chooses every
        command. Live: a retry fixed a piped command and broke `group_id` instead.
        """
        if not isinstance(data, dict):
            return data
        targets = data.get("targets") or []
        if len(targets) != 1 or not isinstance(targets[0], dict) or not targets[0].get("group_id"):
            return data
        gid = targets[0]["group_id"]
        for key in ("actions", "assessments"):
            items = data.get(key) or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("group_id") != gid:
                        item["group_id"] = gid
        return data

    @model_validator(mode="after")
    def command_contract(self):
        # Validate transport/schema only; the agent chooses the repair strategy.
        from app.core.remediation.policy import named_resources, validate_target_command

        groups = {target.group_id: target for target in self.targets}
        if len(groups) != len(self.targets):
            raise ValueError("targets 的 group_id 必须唯一")
        for action in self.actions:
            if action.group_id not in groups:
                raise ValueError("动作必须绑定已列出的 group_id")
            target = groups[action.group_id]
            allowed = {(target.namespace, "pod", target.pod)}
            if target.owner_name and target.owner_uid:
                allowed.add((target.namespace, target.owner_kind.lower(), target.owner_name))
            for stage, command in (
                ("execute", action.execute_command),
                ("verify", action.verify_command),
                ("dry_run", action.dry_run_command),
            ):
                if not command and stage in {"dry_run", "verify"}:
                    continue
                validate_target_command(command, allowed)
                # Identity, not strategy: a command that names the target's controller
                # kind must name the controller the diagnosis verified (live: a plan
                # patched "deployment workload-5487445f9", the ReplicaSet's name).
                owner_kind = (target.owner_kind or "").strip().lower()
                if owner_kind and target.owner_name:
                    for kind, name in named_resources(command):
                        if kind == owner_kind and name != target.owner_name:
                            raise ValueError(
                                f"{stage}_command 中的 {owner_kind} 名称 {name} 与目标 Pod 的控制器 "
                                f"{target.owner_kind}/{target.owner_name} 不一致；请使用核实过的控制器名称"
                            )
        decisions = {item.group_id: item for item in self.assessments}
        if len(decisions) != len(self.assessments) or any(g not in groups for g in decisions):
            raise ValueError("assessments 必须唯一关联已列出的目标")
        # Every listed target gets an explicit decision; prose is not a plan. Live run
        # 78d29cdd5bc94230 put the correct kubectl patch in `answer` with empty
        # actions/assessments and the executor could only skip.
        if self.status == "answered" and self.targets and not self.actions and not self.assessments:
            raise ValueError(
                "没有 actions 时，每个 target 都必须在 assessments 中给出 "
                "ready/needs_input/not_actionable/needs_evidence 判断及原因"
            )
        if not self.actions and _mentions_kubectl_command(self.answer):
            raise ValueError(
                "answer 中出现了 kubectl 命令但 actions 为空：可执行命令必须作为 actions 提交（含 group_id、"
                "description、risk、execute_command、rollback_advice），正文只做说明"
            )
        actionable = {a.group_id for a in self.actions}
        for gid, decision in decisions.items():
            if (decision.status == "ready") != (gid in actionable):
                raise ValueError("ready 必须有对应动作；其他规划状态不能包含执行动作")
        return self


def _mentions_kubectl_command(text):
    """A fenced or line-leading kubectl write in prose (describe/get/logs are explanation)."""
    import re

    for match in re.finditer(r"(?m)^\s*(?:\$\s*)?kubectl\s+([a-z-]+)", text or ""):
        if match.group(1) not in {"get", "describe", "logs", "top", "explain", "events", "wait", "rollout"}:
            return True
    return False


class RemediationNode(QueryCollectNode):
    @property
    def node_id(self):
        return "remediation"

    @property
    def node_name(self):
        return "制定 Pod 修复方案"

    def execute(self, state):
        _configure_query_runtime(self)
        question = state.get("original_question") or state.get("question", "")
        self.ai_call.query_session_context = state.get("query_session_context") or {}
        self.ai_call.working_context_original_question = question
        catalog = self._prepare_query_tools()
        diagnosis = ((state.get("repair_context") or {}).get("diagnosis") or {}).get(
            "payload"
        ) or {}
        material = {
            "question": question,
            "request_contract": state.get("request_contract"),
            "current_repair_group": (
                {
                    "group_id": diagnosis["group_id"],
                    "targets": [g.get("target") for g in diagnosis.get("groups", [])],
                }
                if diagnosis.get("group_id")
                else None
            ),
            "latest_diagnosis": state.get("conclusion") or state.get("query_draft"),
            "repair_context": state.get("repair_context"),
        }
        self._archive_node_input(material)
        response, events = self._call_llm(
            json.dumps(material, ensure_ascii=False),
            POD_REMEDIATION_PROMPT + "\nRunbook 目录：\n" + catalog,
            blocked_tool_names={
                tool.name
                for tool in getattr(self, "tools", [])
                if tool.name not in self.READ_TOOLS
            },
            skip_remediation_policy=True,
            expect_json=True,
            response_schema=RepairDraft,
        )
        # Fail closed if the schema is invalid; prose is never an executable plan.
        if getattr(self, "current_run_id", None):
            from app.core.context.archive import ContextArchive

            ContextArchive(run_id=self.current_run_id).write_json(
                "remediation/planning-response.json",
                {
                    "raw": response.result or "",
                    "execution_incomplete": [
                        e.get("reason") for e in events if e.get("type") == "execution_incomplete"
                    ],
                },
            )
        planning_error = None
        try:
            draft = RepairDraft.model_validate_json(response.result or "")
        except ValueError:
            reasons = [
                str(e.get("reason", "")) for e in events if e.get("type") == "execution_incomplete"
            ]
            interrupted = any(
                any(
                    s in r.lower()
                    for s in (
                        "stream disconnected",
                        "closed before response.completed",
                        "connection error",
                        "unexpected eof",
                    )
                )
                for r in reasons
            )
            failure = (
                "模型服务连接中断，方案未生成"
                if interrupted
                else "上下文整理或预算检查未完成"
                if any("compaction" in r for r in reasons)
                else "达到工具执行步数上限"
                if "step_limit" in reasons
                else "工具规划执行超时"
                if "agent_timeout" in reasons
                else "未获得完整有效的结构化修复方案"
            )
            planning_error = {
                "code": "model_connection_interrupted" if interrupted else "planning_incomplete",
                "message": failure + "。尚未执行修复，可重新生成本组方案。",
            }
            draft = RepairDraft(
                intent=question,
                scope="本次请求范围",
                status="partial",
                answer=f"修复规划未完成：{failure}。未提交可执行动作，也没有执行修复；这不代表故障没有修复方法。",
                missing=[failure],
            )
        answer = QueryAnswer.model_validate(draft.model_dump())
        material_state = {
            **state,
            "thinking_events": [*(state.get("thinking_events") or []), *events],
        }
        output = finalize_query_answer(
            self, material_state, answer.model_dump_json(), [], require_structured=True
        )
        payload = draft.model_dump()
        if planning_error:
            payload["planning_error"] = (
                planning_error  # Server outcome, never a model-selected field.
            )
        output.update(request_route="remediation", remediation_draft=payload)
        if getattr(self, "current_run_id", None):
            from app.core.context.archive import ContextArchive

            ContextArchive(run_id=self.current_run_id).write_json("remediation/plan.json", payload)
        self._archive_node_output(output)
        return output
