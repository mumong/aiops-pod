"""Read-only preparation of a Pod remediation plan; never executes writes."""
import json

from pydantic import BaseModel, Field, model_validator

from app.core.prompts import POD_REMEDIATION_PROMPT
from app.core.workflow.nodes.query_answer import (
    QueryAnswer, QueryCollectNode, _configure_query_runtime, finalize_query_answer,
)


class RepairTarget(BaseModel):
    namespace: str
    pod: str
    pod_uid: str
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
    verify_command: str
    rollback_advice: str


class RepairDraft(QueryAnswer):
    targets: list[RepairTarget] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    runbook_unavailable_reason: str = ""

    @model_validator(mode="after")
    def command_contract(self):
        # Schema feedback helps the planning agent correct syntax before asking
        # a person to approve. Runtime still independently verifies all identities.
        from app.core.remediation.policy import validate_target_command
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
            for stage, command in (("execute", action.execute_command), ("verify", action.verify_command),
                                   ("dry_run", action.dry_run_command)):
                if not command and stage == "dry_run":
                    continue
                argv, operation = validate_target_command(command, allowed)
                if stage == "execute" and operation not in {"set_resources", "patch", "rollout_restart"}:
                    raise ValueError("actions 只包含写修复动作；只读后续检查放入 answer 或 verify_command")
                if stage == "verify" and operation not in {"get", "describe", "logs", "top", "rollout_status"}:
                    raise ValueError("verify_command 必须只读")
                if stage == "dry_run" and "--dry-run=server" not in argv:
                    raise ValueError("dry_run_command 必须包含 --dry-run=server")
        return self


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
        material = {"question": question, "request_contract": state.get("request_contract"),
                    "latest_diagnosis": state.get("conclusion") or state.get("query_draft")}
        self._archive_node_input(material)
        response, events = self._call_llm(
            json.dumps(material, ensure_ascii=False),
            POD_REMEDIATION_PROMPT + "\nRunbook 目录：\n" + catalog,
            blocked_tool_names={tool.name for tool in getattr(self, "tools", [])
                                if tool.name not in self.READ_TOOLS},
            skip_remediation_policy=True, expect_json=True, response_schema=RepairDraft,
        )
        # Fail closed if the schema is invalid; prose is never an executable plan.
        if getattr(self, "current_run_id", None):
            from app.core.context.archive import ContextArchive
            ContextArchive(run_id=self.current_run_id).write_json("remediation/planning-response.json", {
                "raw": response.result or "", "execution_incomplete": [
                    e.get("reason") for e in events if e.get("type") == "execution_incomplete"]})
        try:
            draft = RepairDraft.model_validate_json(response.result or "")
        except ValueError:
            reasons = [str(e.get("reason", "")) for e in events if e.get("type") == "execution_incomplete"]
            failure = ("上下文整理或预算检查未完成" if any("compaction" in r for r in reasons)
                       else "达到工具执行步数上限" if "step_limit" in reasons
                       else "工具规划执行超时" if "agent_timeout" in reasons
                       else "未获得完整有效的结构化修复方案")
            draft = RepairDraft(intent=question, scope="本次请求范围", status="partial",
                answer=f"修复规划未完成：{failure}。未提交可执行动作，也没有执行修复；这不代表故障没有修复方法。",
                missing=[failure])
        answer = QueryAnswer.model_validate(draft.model_dump())
        material_state = {**state, "thinking_events": [*(state.get("thinking_events") or []), *events]}
        output = finalize_query_answer(self, material_state, answer.model_dump_json(), [],
                                       require_structured=True)
        output.update(request_route="remediation", remediation_draft=draft.model_dump())
        if getattr(self, "current_run_id", None):
            from app.core.context.archive import ContextArchive
            ContextArchive(run_id=self.current_run_id).write_json("remediation/plan.json", draft.model_dump())
        self._archive_node_output(output)
        return output
