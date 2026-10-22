"""Read-only preparation of a Pod remediation plan; never executes writes."""

import json
import logging
import re
from typing import Callable, ClassVar, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.core.prompts import POD_REMEDIATION_PROMPT
from app.core.remediation.execution_guard import RepairCommandDenied
from app.core.remediation.ownership import ControllerChain, chains_for_targets, managed_write_error
from app.core.workflow.nodes.query_answer import (
    QueryAnswer,
    QueryCollectNode,
    _configure_query_runtime,
    finalize_query_answer,
)

_POLICY_BLOCK = re.compile(r"高危规则拦截（([\w.]+)）：(.+?)；")


def policy_block_message(reasons) -> str:
    """'方案中的命令被高危规则拦截…' when the plan failed on blacklisted commands, else ''."""
    hits = []
    for reason in reasons or []:
        for rule, command in _POLICY_BLOCK.findall(str(reason)):
            item = f"{command.strip()}（{rule}）"
            if item not in hits:
                hits.append(item)
    if not hits:
        return ""
    return "方案中的命令被高危规则拦截：" + "；".join(hits[:3]) + "，未写入方案，也未执行"


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
    targets: list[RepairTarget] = Field(
        default_factory=list,
        description="本方案处理的对象（namespace、pod、group_id）；有 actions 时必填，每个动作的 group_id 必须在这里列出",
    )
    actions: list[RepairAction] = Field(default_factory=list)
    runbook_unavailable_reason: str = ""
    assessments: list[RepairAssessment] = Field(default_factory=list)

    # Cluster facts bound per planning call (``with_controller_chains``): the Pod's
    # ownerReferences chain, keyed "namespace/pod". Empty = unknown, nothing enforced.
    controller_chains: ClassVar[Dict[str, ControllerChain]] = {}
    # Planning call only (``with_preflight``): dry-runs the write commands on the plan's
    # cluster; a failure goes back to the model as a validation error to fix.
    preflight: ClassVar[Optional[Callable[[list], List[str]]]] = None

    @classmethod
    def with_controller_chains(cls, chains: Dict[str, ControllerChain]):
        """A schema bound to this call's ownership facts; the tool name stays RepairDraft."""
        if not chains:
            return cls
        return type(
            cls.__name__, (cls,), {"controller_chains": dict(chains), "__module__": cls.__module__}
        )

    @classmethod
    def with_preflight(cls, check):
        return type(
            cls.__name__, (cls,), {"preflight": staticmethod(check), "__module__": cls.__module__}
        )

    @model_validator(mode="after")
    def commands_pass_dry_run(self):
        check = type(self).preflight
        if check is None or not self.actions:
            return self
        errors = check(self.actions)
        if errors:
            raise ValueError(
                "命令预检未通过（kubectl --dry-run=client，在本组集群上执行，未做任何修改）："
                + "；".join(errors)
                + "。请按 kubectl 的报错修正命令（语法、参数、对象名或命名空间）后重新提交"
            )
        return self

    @classmethod
    def chain_for(cls, namespace: str, pod: str):
        return cls.controller_chains.get(f"{namespace}/{pod}")

    @model_validator(mode="before")
    @classmethod
    def bind_controller_facts(cls, data):
        """Owner identity comes from the cluster, not from the model, when it is known."""
        if not isinstance(data, dict) or not cls.controller_chains:
            return data
        for target in data.get("targets") or []:
            if not isinstance(target, dict):
                continue
            chain = cls.chain_for(str(target.get("namespace") or ""), str(target.get("pod") or ""))
            if chain is None:
                continue
            root = chain.root
            if root is not None:
                target["owner_kind"], target["owner_name"], target["owner_uid"] = (
                    root.kind,
                    root.name,
                    root.uid,
                )
            elif chain.complete:
                target["owner_kind"], target["owner_name"], target["owner_uid"] = "", "", ""
            if chain.pod and chain.pod.uid and not target.get("pod_uid"):
                target["pod_uid"] = chain.pod.uid
        return data

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
                # Say what is missing: "group_id not listed" alone sent the model into
                # re-checking a group_id that was already right (live 5f585d7b51e44b9c).
                if not groups:
                    raise ValueError(
                        f"targets 为空：动作 {action.id} 的 group_id={action.group_id} 必须先在 targets 中列出"
                        "（namespace、pod、group_id）"
                    )
                raise ValueError(
                    f"动作 {action.id} 的 group_id={action.group_id} 不在 targets 中"
                    f"（已列出：{', '.join(sorted(groups))}）"
                )
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
                try:
                    validate_target_command(command, allowed)
                except RepairCommandDenied as denied:
                    # Tagged so a plan that fails only on policy is reported as such.
                    raise ValueError(
                        f"高危规则拦截（{denied.rule or 'policy'}）：{command}；"
                        "该命令不能进入方案，请改用不在黑名单中的方式，或不提交该动作并在 answer 说明"
                    ) from None
                # Write where the controller writes: a managed member of the ownership
                # chain (ReplicaSet under a Deployment, Job under a CronJob) is rewritten
                # by its controller, so a patch there is accepted and changes nothing.
                managed = managed_write_error(
                    command, type(self).chain_for(target.namespace, target.pod)
                )
                if managed:
                    raise ValueError(f"{stage}_command：{managed}")
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
        if (
            self.status == "answered"
            and self.targets
            and not self.actions
            and not self.assessments
        ):
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
        if match.group(1) not in {
            "get",
            "describe",
            "logs",
            "top",
            "explain",
            "events",
            "wait",
            "rollout",
        }:
            return True
    return False


def _request_targets(contract):
    """Pods named in the request, when their namespace is unambiguous."""
    contract = contract or {}
    namespaces = [n for n in contract.get("namespaces") or [] if n]
    pods = [p for p in contract.get("pod_names") or [] if p]
    if len(namespaces) != 1 or not pods:
        return []
    return [{"entities": [{"kind": "Pod", "namespace": namespaces[0], "name": p} for p in pods]}]


class RemediationNode(QueryCollectNode):
    @property
    def node_id(self):
        return "remediation"

    def _controller_chains(self, diagnosis, request_contract=None) -> Dict[str, ControllerChain]:
        """Read-only ownerReferences lookups for the Pods being repaired; failures leave it empty.

        Targets come from the diagnosis group when there is one, otherwise from the
        request itself, so the node also works without an upstream diagnosis.
        """
        targets = [
            g.get("target") for g in (diagnosis or {}).get("groups", []) if isinstance(g, dict)
        ] or _request_targets(request_contract)
        if not targets:
            return {}
        try:
            from app.core.remediation.executor import run_local_command

            return chains_for_targets(targets, run_local_command)
        except Exception as exc:  # planning continues without ownership facts
            logging.getLogger(__name__).warning("[remediation] 控制器链解析失败: %s", exc)
            return {}

    @property
    def node_name(self):
        return "修复与执行"

    @staticmethod
    def _group_dispatch(state):
        """Hand a chat repair request to the per-group batch when a grouped diagnosis exists.

        Returns ``{"diagnosis_run_id", "group_ids"}`` (empty ids: nothing left to repair)
        or None to plan here: no grouped diagnosis, a job already scoped to one group,
        a revision of an earlier plan, or a request naming objects the diagnosis lacks.
        """
        from app.core.remediation.group_context import repairable_groups, select_groups

        context = state.get("repair_context") or {}
        record = context.get("diagnosis")
        if not isinstance(record, dict) or context.get("previous_plan"):
            return None
        payload = record.get("payload") or {}
        if payload.get("contract_version") != "diagnosis-record.v2" or payload.get("group_id"):
            return None
        open_groups = repairable_groups(record)
        selected = select_groups(open_groups, state.get("request_contract"))
        if open_groups and not selected:
            return None  # the user named something else; plan it here
        return {
            "diagnosis_run_id": record.get("run_id"),
            "group_ids": [g["group_id"] for g in selected],
        }

    def _dispatch_output(self, state, question, dispatch):
        from app.core.workflow.group_runner import group_display_name

        if dispatch["group_ids"]:
            lines = "\n".join(f"- {group_display_name(g)}" for g in dispatch["group_ids"])
            text = (
                "已转入上一轮诊断的按组修复批次（每组一个独立规划任务，并行进行；"
                "同一诊断已有批次时沿用原批次）。各组方案、状态和审批见下方修复工作区：\n\n"
                f"{lines}"
            )
        else:
            text = "上一轮诊断未发现需要修复的异常组，本次不生成修复方案。"
        answer = QueryAnswer(
            intent=question, scope="上一轮诊断的异常组", status="answered", answer=text
        )
        output = finalize_query_answer(
            self, state, answer.model_dump_json(), [], require_structured=True
        )
        output.update(
            request_route="remediation",
            remediation_draft=None,
            remediation_dispatch=dispatch,
            conclusion=text,
            conclusion_formatted=text,
        )
        self._archive_node_output(output)
        return output

    def execute(self, state):
        _configure_query_runtime(self)
        question = state.get("original_question") or state.get("question", "")
        dispatch = self._group_dispatch(state)
        if dispatch is not None:
            return self._dispatch_output(state, question, dispatch)
        self.ai_call.query_session_context = state.get("query_session_context") or {}
        self.ai_call.working_context_original_question = question
        catalog = self._prepare_query_tools()
        diagnosis = ((state.get("repair_context") or {}).get("diagnosis") or {}).get(
            "payload"
        ) or {}
        chains = self._controller_chains(diagnosis, state.get("request_contract"))
        from app.core.remediation.preflight import is_remote, preflight_errors, runner_for

        run = runner_for(state.get("request_contract"))
        remote = is_remote(state.get("request_contract"))
        schema = RepairDraft.with_controller_chains(chains).with_preflight(
            lambda actions: preflight_errors(actions, run, remote=remote)
        )
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
            # Cluster facts: where each Pod's spec is owned (writes go to the root).
            "controller_chains": {key: chain.to_dict() for key, chain in chains.items()},
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
            response_schema=schema,
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
            draft = schema.model_validate_json(response.result or "")
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
            blocked = policy_block_message(reasons)
            failure = (
                blocked
                if blocked
                else "模型服务连接中断，方案未生成"
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
                "code": "policy_blocked"
                if blocked
                else "model_connection_interrupted"
                if interrupted
                else "planning_incomplete",
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
