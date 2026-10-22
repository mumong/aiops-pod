"""Agent-owned Pod assessment; code checks delivery/coverage, not fault semantics."""

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.workflow.contract_coercion import TextItems


class PodAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["healthy", "abnormal", "inconclusive"] = "inconclusive"
    scope: str = Field(min_length=1, max_length=320)
    observed_at: str = Field(min_length=1, max_length=80)
    recent_signals_reviewed: bool = False
    unresolved: Annotated[list[str], TextItems] = Field(default_factory=list, max_length=20)
    evidence_refs: Annotated[list[str], TextItems] = Field(default_factory=list, max_length=20)
    reason: str = Field(min_length=1, max_length=600)


POD_DETECTION_GUIDANCE = """
# 产品范围与结束条件：Pod 异常检测
本深度诊断是指定范围的 Pod 异常检测，不是全栈集群体检。“我的集群有什么问题”默认检查全集群 Pod。
基于当前状态和近期 10 分钟线索决定是否调查；Running 不等于健康，仍需结合就绪、删除状态、容器状态等事实。
最近 10 分钟发生过重启或其他异常线索，先列为待核实并针对性调查，不能仅凭当前 Running/Ready 直接 healthy。
累计重启不代表近期重启；只有当前快照/最近一次终止时，不能声称掌握完整 10 分钟历史。时间未知时不猜测。
本次检查的是当前及近10分钟异常，不追溯所有历史故障。最后终止明确早于窗口、当前正常且无其他近期异常线索时，历史重启次数或历史 Error/Unknown 本身不构成待调查目标。
history_complete=false 或 restart_count_in_window=null 是历史数据能力限制，不单独构成异常或阻止当前范围的 healthy；在报告中说明限制即可。存在近期线索但其时间/恢复情况不明才需要核实。
例如：当前Ready、最后终止为5天前，即使累计重启很多也不因此建组；当前Ready但5分钟前重启，则先调查恢复情况。healthy 表示本次检查未发现当前或可见近期未解决的Pod异常，不保证完整历史或业务绝对健康。
Agent 自主选择足以核实线索的证据，不要求固定调用日志、指标或链路。仅为解释目标 Pod 的实际线索，才调查关联对象。
无当前异常也无待核实近期线索，且范围已完整覆盖，可结束。已核实近期异常属于已恢复且无持续问题，也可 healthy，但说明依据与历史。
用户明确提出服务失败等反例时，Pod Ready 不能否定用户现象；针对目标补查，无法解释则 inconclusive。
查询失败、遗漏分页、证据冲突、线索尚未核实不能判 healthy；必要的针对性补查后仍不足就说明检查不完整，不无限扩大范围。
定位 handoff.pod_assessment 填 status、scope、observed_at、recent_signals_reviewed、unresolved、真实 evidence_refs 和 reason。引用只填写实际提供的原文路径或证据来源 ID，不把描述句当引用。不从只查健康对象的筛选子集宣称完整覆盖。
healthy 要求 coverage=complete、无 investigate/deferred 目标、无 unresolved，且近期线索已核实（无近期线索也明确记录）。
abnormal 保留所有待调查 Pod；inconclusive 明确缺口，不编造故障或健康。定位没有待调查目标时，不为执行后续节点制造问题。
targets.status：investigate=需要取证；assessed=定位已用真实证据说明原因，仍是异常，照常写入报告；deferred=本次暂缓并说明原因；excluded 只由系统按运维声明核验后设置，不要自行填写。测试标签、环境变量、命名或注释只解释背景，不能把当前异常判为预期、正常或无需调查。
后续采证/RCA也遵守此范围；足以回答当前 Pod 问题就结束，不把未检查的无关维度当必须补齐的缺口。
"""


def healthy_check_report(assessment):
    """Fixed-format report for a check the code already verified as healthy.

    ``assess_delivery`` only keeps ``healthy`` when coverage is complete, nothing is
    pending and recent signals were reviewed, so restating it needs no model call.
    """
    lines = [
        "### 检查结论：未发现 Pod 异常（Healthy）",
        "",
        f"- **检查范围**：{assessment.get('scope') or '本次请求范围'}",
        f"- **检查时间**：{assessment.get('observed_at') or '—'}",
        f"- **依据**：{assessment.get('reason') or '—'}",
        "- **近期线索**：已核实（当前状态与近 10 分钟的终止、重启线索）",
    ]
    refs = [r for r in assessment.get("evidence_refs") or [] if r]
    if refs:
        lines.append("- **证据引用**：" + "、".join(f"`{r}`" for r in refs[:5]))
    lines += [
        "",
        "本次为 Pod 异常检测：检查当前状态与近 10 分钟线索，不代表业务或集群其他层面全部健康。",
    ]
    return "\n".join(lines)


INVENTORY_TOOL = "query_pod_lifecycle"


def _is_repeat_notice(event):
    """The dedup guard's own answer to a repeated call (flag, or its fixed prefix)."""
    if event.get("deduplicated"):
        return True
    text = event.get("result") or event.get("result_preview") or ""
    return isinstance(text, str) and text.lstrip().startswith("【重复调用")


def _scope_key(tool, args):
    """Same tool over the same object scope (filters and fields may differ)."""
    args = args if isinstance(args, dict) else {}
    return (
        tool,
        str(args.get("namespace") or ""),
        str(args.get("label_selector") or ""),
        str(args.get("pod") or args.get("name") or ""),
    )


def assess_delivery(handoff, events, material=None):
    assessment = handoff.get("pod_assessment")
    if not isinstance(assessment, dict):
        return handoff
    handoff = {**handoff, "pod_assessment": dict(assessment)}
    assessment = handoff["pod_assessment"]
    if assessment.get("status") != "healthy":
        return handoff
    problems = []
    if handoff.get("coverage") != "complete":
        problems.append("检查范围未完整覆盖")
    if any(
        t.get("status", "investigate") in ("investigate", "deferred")
        for t in handoff.get("targets", [])
    ):
        problems.append("仍有待核实或暂缓的目标")
    if not assessment.get("recent_signals_reviewed") or assessment.get("unresolved"):
        problems.append("近期线索或未解决事项尚未核实")
    refs, consumed = set(), set()
    # IDs in producer-owned source maps are as valid as archive paths; prose is not.
    protected = (material or {}).get("protected_handoff") or {}
    sources = (protected.get("lifecycle_core") or {}).get("sources") or {}
    for identifier, source in sources.items():
        if isinstance(source, dict):
            refs.add(identifier)
            refs.update(
                source[k]
                for k in ("raw_ref", "structured_ref", "summary_ref")
                if isinstance(source.get(k), str)
            )
    for observation in (material or {}).get("observations") or []:
        refs.update(
            observation[k]
            for k in ("raw_ref", "structured_ref", "summary_ref")
            if isinstance(observation.get(k), str)
        )
    inventory_refs, other_failures = [], []
    failed_scopes = set()
    continuations, complete_scopes = {}, set()
    incomplete = False
    for event in events:
        if event.get("type") == "execution_incomplete":
            incomplete = True
        if event.get("type") != "tool_result" or _is_repeat_notice(event):
            continue  # repeat notices are the guard's own messages, not collection
        tool = event.get("tool_name")
        args = event.get("tool_args") or {}
        if isinstance(args, dict) and args.get("continue_token"):
            consumed.add(args["continue_token"])
        raw = event.get("result") or event.get("result_preview") or ""
        try:
            packet = json.loads(raw) if isinstance(raw, str) else raw
        except (ValueError, TypeError):
            packet = {}
        packet = packet if isinstance(packet, dict) else {}
        if (
            event.get("status") in ("error", "failed")
            or event.get("semantic_success") is False
            or packet.get("status") == "error"
        ):
            if tool and tool != INVENTORY_TOOL:
                other_failures.append(tool)
            else:
                failed_scopes.add(_scope_key(tool, args))
            continue
        refs.update(
            event[k]
            for k in ("raw_ref", "structured_ref", "summary_ref")
            if isinstance(event.get(k), str)
        )
        pagination = packet.get("pagination") or {}
        token = packet.get("next_continue_token") or pagination.get("next_continue_token")
        scope = _scope_key(tool, args)
        failed_scopes.discard(scope)  # a later success in the same scope corrected it
        if token:
            continuations[token] = scope
        elif tool == INVENTORY_TOOL and not pagination.get("source_has_more"):
            complete_scopes.add(scope)  # a later complete read of the same scope
        if tool == INVENTORY_TOOL and isinstance(event.get("raw_ref"), str):
            inventory_refs.append(event["raw_ref"])
    outstanding = {
        t
        for t, scope in continuations.items()
        if t not in consumed and scope not in complete_scopes
    }
    if outstanding:
        problems.append("存在未续读的数据页")
    if failed_scopes:
        problems.append("采集存在失败或未解析结果")
    inventory_complete = bool(inventory_refs) and not outstanding and not failed_scopes
    pending = any(
        t.get("status", "investigate") in ("investigate", "deferred")
        for t in handoff.get("targets", [])
    )
    if incomplete:
        if inventory_complete and not pending:
            # The stage ran out of steps after the inventory was complete and nothing was
            # pending (live: run 69c93246 kept reading unrelated YAML until step_limit).
            note = "（定位阶段在步数上限结束；Pod 清单已完整，未留下待调查目标）"
            assessment["reason"] = (str(assessment.get("reason") or "") + note)[:600]
        else:
            problems.append("本次执行存在未完成事项")
    if other_failures:
        if inventory_complete:
            # Exploratory side queries do not change a complete Pod inventory; say so.
            note = f"（另有与 Pod 状态判断无关的查询失败：{'、'.join(dict.fromkeys(other_failures))}）"
            assessment["reason"] = (str(assessment.get("reason") or "") + note)[:600]
        else:
            problems.append("采集存在失败或未解析结果")
    cited = set(assessment.get("evidence_refs") or [])
    if not cited and inventory_complete:
        # The model cited nothing; the code knows which successful reads the verdict rests on.
        assessment["evidence_refs"] = list(dict.fromkeys(inventory_refs))[:5]
        cited = set(assessment["evidence_refs"])
    if not cited or not cited <= refs:
        problems.append("健康判断缺少本次真实工具引用")
    if problems:
        assessment["status"] = "inconclusive"
        assessment["unresolved"] = list(
            dict.fromkeys([*(assessment.get("unresolved") or []), *problems])
        )
    return handoff


def after_location(state):
    handoff = state.get("diagnosis_handoff") or {}
    assessment = handoff.get("pod_assessment") or {}
    pending = any(
        t.get("status", "investigate") == "investigate" for t in handoff.get("targets", [])
    )
    if assessment.get("status") in ("healthy", "inconclusive") and not pending:
        return "conclusion"
    return "parallel_evidence" if len(state.get("autonomous_groups") or []) > 1 else "evidence"
