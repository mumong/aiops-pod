"""Question-led diagnosis roles using the same evidence and memory path as QUERY.

No baseline calls, inferred abnormal-group fanout, fault-specific stop checkers,
or programmatic causal decisions. The graph assigns roles, not diagnoses.
"""

import asyncio
import json

from app.core.prompts import (
    AUTONOMOUS_RUNBOOK_CATALOG_HEADER,
    DEEP_EVIDENCE_PROMPT,
    DEEP_LAYER_PROMPT,
    DEEP_RCA_PROMPT,
    DIAGNOSIS_HANDOFF_GUIDANCE,
    DIAGNOSTIC_TOOL_GUIDANCE,
    PARALLEL_LANE_TASK_PREFIX,
)
from app.core.workflow.case_result import (
    DiagnosisCaseOutput,
    EvidenceStageOutput,
    bind_case_result,
    evidence_fallback_report,
    request_scope_target,
)
from app.core.workflow.diagnosis_contract import LocationOutput
from app.core.workflow.nodes.query_answer import (
    QueryCollectNode,
    _configure_query_runtime,
    build_working_material,
)
from app.core.workflow.pod_detection import POD_DETECTION_GUIDANCE, assess_delivery
from app.core.workflow.stage_material import stage_material

# Prometheus catalog exploration: metric/label discovery for ad-hoc queries. Diagnosis
# lanes query Pod metrics via execute_pod_promql; across ~50k archived evidence calls
# these were used <50 times, yet their schemas were sent on every request.
_METRIC_CATALOG_TOOLS = frozenset(
    {
        "get_metric_names",
        "get_label_values",
        "get_all_labels",
        "get_series",
        "get_metric_metadata",
        "get_prometheus_target",
        "list_prometheus_rules",
    }
)


def serial_case_target(handoff):
    """Identity of the single serial case: every target the location stage handed over.

    The serial path runs whenever lane fan-out is not possible (a non-Pod target such
    as the owning Deployment, a Pod without namespace, historical input). Its one RCA
    then covers all of those targets, so the case identity lists all of them; a valid
    report must not be discarded because the handoff named more than one object.
    """
    targets = [
        t
        for t in (handoff or {}).get("targets") or []
        if isinstance(t, dict) and t.get("target_id") and isinstance(t.get("entity"), dict)
    ]
    active = [t for t in targets if t.get("status", "investigate") == "investigate"] or targets
    if not active:
        return None
    return {
        "group_id": "single",
        "target_id": "+".join(t["target_id"] for t in active),
        "entities": [t["entity"] for t in active],
    }


class DiagnosisStageNode(QueryCollectNode):
    stage_id = "layer"
    stage_name = "问题定位"
    stage_prompt = DEEP_LAYER_PROMPT
    collect = True
    # Location = Pod inventory + verify recent signals + runbook. Deeper evidence
    # (metrics/logs/traces/topology) belongs to the evidence stage. Historically these
    # 15 tools covered ~99% of layer calls; the schema shrinks ~8k -> ~3k tokens per
    # request, which matters for the 54k-token window of small models.
    READ_TOOLS = frozenset(
        {
            "query_pod_lifecycle",
            "kubectl_get_by_name",
            "kubectl_get_by_kind_in_namespace",
            "kubectl_get_by_kind_in_cluster",
            "kubectl_get_yaml",
            "kubectl_describe",
            "kubectl_events",
            "kubectl_logs",
            "kubectl_previous_logs",
            "kubernetes_jq_query",
            "kubernetes_tabular_query",
            "kubernetes_count",
            "fetch_runbook",
            "read_context_archive",
            "TodoWrite",
        }
    )

    @property
    def node_id(self):
        return self.stage_id

    @property
    def node_name(self):
        return self.stage_name

    def execute(self, state):
        from app.core import multicluster

        if (
            self.node_id == "layer"
            and multicluster.multi()
            and len(multicluster.run_clusters(state)) > 1
        ):
            # One deep diagnosis over several clusters: locate each cluster on its own.
            from app.core.workflow.multicluster_location import per_cluster_location

            output = per_cluster_location(self, state)
            self._archive_node_output(output)
            return output
        _configure_query_runtime(self)
        if getattr(self, "ai_call", None) is not None:
            # History is already in material; do not insert it twice.
            self.ai_call.query_session_context = {}
            self.ai_call.working_context_original_question = (
                state.get("question", "")
                if state.get("diagnosis_target")
                else state.get("original_question") or state.get("question", "")
            )
        material = stage_material(state, self.node_id)
        material["request_contract"] = state.get("request_contract")
        if multicluster.multi():
            material["cluster_notes"] = multicluster.virtual_node_note()
        locating = self.node_id == "layer"
        publishing = self.node_id == "rca"
        collecting = self.node_id == "evidence"
        prompt = self.stage_prompt + ("\n" + DIAGNOSIS_HANDOFF_GUIDANCE if locating else "")
        if state.get("diagnosis_target"):
            from app.core.prompts import PARALLEL_LANE_PROMPT

            prompt = (
                PARALLEL_LANE_PROMPT
                + PARALLEL_LANE_TASK_PREFIX
                + material.get("task", material["question"])
                + "\n"
                + prompt
            )
        if self.collect:
            prompt += "\n" + DIAGNOSTIC_TOOL_GUIDANCE
            prompt += AUTONOMOUS_RUNBOOK_CATALOG_HEADER + self._prepare_query_tools()
        self._archive_node_input(material)
        prompt += "\n" + POD_DETECTION_GUIDANCE
        if collecting:
            prompt += "\n输出 EvidenceStageOutput JSON：analysis 保留本组证据分析；key_facts 选择最多 8 条对判断原因有价值的观察事实及真实证据引用，unresolved 保留缺口，runbook_refs 仅引用实际读取的手册。关键字段将交接给 RCA；不要塞入工具全文、正常对象清单或其他组材料。"
        if publishing:
            prompt += "\n本节点交付本组正式诊断：report 为供用户查看的完整诊断，summary 为总览使用的短结论。key_facts 仅选择支撑当前判断的关键事实与真实证据引用，unresolved 保留未解决条件。不要重复历史版本、其他组背景或工具全文。不得生成修复命令。输出 DiagnosisCaseOutput JSON，不输出定位 handoff。"

        def call(payload):
            return self._call_llm(
                json.dumps(payload, ensure_ascii=False, default=str),
                prompt,
                force_no_tools=not self.collect,
                skip_remediation_policy=True,
                **(
                    {"expect_json": True, "response_schema": LocationOutput}
                    if locating
                    else {"expect_json": True, "response_schema": DiagnosisCaseOutput}
                    if publishing
                    else {"expect_json": True, "response_schema": EvidenceStageOutput}
                    if collecting
                    else {}
                ),
                blocked_tool_names={
                    t.name for t in getattr(self, "tools", []) if t.name not in self.READ_TOOLS
                },
            )

        events = list(state.get("thinking_events") or [])
        from app.core.aicall.client import StructuredContextBudgetError

        try:
            response, stage_events = call(material)
        except StructuredContextBudgetError as exc:
            if "working_context_compaction_required" not in str(exc):
                raise
            from app.core.aicall.working_context import compact_working_material

            model = self.ai_call.create_compaction_model()
            compact = asyncio.run(
                compact_working_material(
                    model,
                    material,
                    lambda **event: self.ai_call._push(
                        self._event_queue, self.node_id, events, **event
                    ),
                )
            )
            events.append(
                {
                    "type": "context_compacted",
                    "working_summary": compact["working_summary"],
                    "protected_handoff": compact.get("protected_handoff", {}),
                    "retained_messages": compact["recent_interactions"],
                }
            )
            self._archive_node_input({"before_compaction": material, "after_compaction": compact})
            response, stage_events = call(compact)
        raw = response.result or ""
        combined_events = [*events, *stage_events]
        draft = raw
        output = {"diagnosis_context_policy": "identity.v1"}
        if collecting:
            try:
                evidence = EvidenceStageOutput.model_validate_json(raw).model_dump()
                draft = evidence.pop("analysis")
                output["diagnosis_evidence_handoff"] = evidence
            except (ValueError, TypeError) as exc:
                output["diagnosis_evidence_handoff"] = {
                    "key_facts": [],
                    "unresolved": ["证据结构化交接无效；需核查原始采集材料"],
                    "runbook_refs": [],
                }
                combined_events.append(
                    {
                        "type": "execution_incomplete",
                        "node": self.node_id,
                        "reason": f"证据交接无效：{exc}",
                    }
                )
        if publishing:
            from app.core.context.archive import ContextArchive

            archive = ContextArchive(
                run_id=getattr(self, "current_run_id", "") or state.get("run_id", "unknown")
            )
            target = (
                state.get("diagnosis_target")
                or serial_case_target(state.get("diagnosis_handoff"))
                or request_scope_target(state.get("request_contract"))
            )
            group_id = (target or {}).get("group_id", "single")
            result_ref = str(archive.root / "cases/result.json")
            try:
                case = bind_case_result(
                    json.loads(raw), group_id=group_id, target=target, result_ref=result_ref
                )
                draft = case["report"]
            except (ValueError, TypeError) as exc:
                archive.write_text("cases/invalid-output.txt", raw)
                summary = "本组诊断结果交付不完整；已保留采集记录，不能据此确认根因或恢复。"
                # The evidence stage already delivered tool-backed facts for this group;
                # show them instead of an empty placeholder (still marked partial).
                draft = (
                    evidence_fallback_report(
                        state.get("diagnosis_evidence_handoff"), state.get("evidence_analysis")
                    )
                    or summary
                )
                case = {
                    "contract_version": "diagnosis-case.v1",
                    "group_id": group_id,
                    "target": target,
                    "execution_status": "partial",
                    "outcome": "inconclusive",
                    "summary": summary,
                    "report": draft,
                    "result_ref": result_ref,
                    "unresolved": ["RCA 结构化结果或目标身份无效"],
                }
                combined_events.append(
                    {
                        "type": "execution_incomplete",
                        "node": self.node_id,
                        "reason": f"RCA 结果交付无效：{exc}",
                    }
                )
            # This code-owned fallback remains resolvable even if a model cites
            # a tool label instead of its exact archive path. Bodies stay out
            # of the handoff; only this group's acquisition directory is stored.
            refs = {}
            for event in combined_events[state.get("diagnosis_events_start", 0) :]:
                if event.get("type") == "tool_result" and event.get("raw_ref"):
                    refs[event["raw_ref"]] = {
                        k: event[k]
                        for k in (
                            "tool_name",
                            "tool_args",
                            "raw_ref",
                            "structured_ref",
                            "timestamp",
                            "status",
                            "semantic_success",
                        )
                        if k in event
                    }
            case["evidence_index_ref"] = str(archive.root / "cases/evidence-index.json")
            archive.write_json_atomic(
                "cases/evidence-index.json",
                {"group_id": group_id, "observations": list(refs.values())},
            )
            archive.write_json_atomic("cases/result.json", case)
            output["diagnosis_case_result"] = case
        if locating:
            try:
                parsed = LocationOutput.model_validate_json(raw)
                draft = parsed.analysis
                output["diagnosis_handoff"] = parsed.handoff.model_dump()
            except (ValueError, TypeError) as exc:
                # Preserve prose/evidence and explicitly mark incomplete; no
                # second model extraction or invented targets.
                reason = f"定位结构化交接无效：{exc}"
                output["diagnosis_handoff"] = {
                    "contract_version": "location-handoff.v1",
                    "targets": [],
                    "coverage": "partial",
                    "coverage_note": "定位交接无效，参见未完成事项",
                }
                combined_events.append(
                    {"type": "execution_incomplete", "node": self.node_id, "reason": reason}
                )
        output.update({"query_draft": draft, "thinking_events": combined_events})
        # These fields are only stage prose, not verified facts or forced classifications.
        output[
            {"layer": "layer_analysis", "evidence": "evidence_analysis", "rca": "rca_analysis"}[
                self.node_id
            ]
        ] = draft
        if self.node_id == "layer" and output.get("diagnosis_handoff"):
            output["diagnosis_handoff"] = assess_delivery(
                output["diagnosis_handoff"],
                combined_events,
                build_working_material({**state, "thinking_events": combined_events}),
            )
            output["diagnosis_events_start"] = len(combined_events)
            from app.core.workflow.expected_states import apply_expected_states

            output["diagnosis_handoff"], excluded = apply_expected_states(
                output["diagnosis_handoff"], state
            )
            if excluded:
                output["expected_exclusions"] = [
                    *(state.get("expected_exclusions") or []),
                    *excluded,
                ]
        if self.node_id == "layer" and getattr(self, "autonomous_parallel_enabled", False):
            from app.core.workflow.nodes.autonomous_parallel import plan_groups

            output.update(plan_groups(self, {**state, **output}))
        self._archive_node_output(output)
        return output


class DiagnosisEvidenceNode(DiagnosisStageNode):
    stage_id = "evidence"
    stage_name = "证据采集"
    stage_prompt = DEEP_EVIDENCE_PROMPT
    # One known Pod (namespace/name/uid come from the handoff): cross-check it with real
    # metrics/logs/traces/topology plus its own Kubernetes objects. Cluster listing, grep
    # and catalog tools stay out; 30 -> 17 schemas (~6.6k -> ~3.8k tokens per request)
    # and fewer look-alike choices for small models.
    # Real observability data first in the tool list; the rest keep service order.
    PREFERRED_TOOLS = (
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
        "query_pod_topology",
    )
    READ_TOOLS = frozenset(
        {
            "execute_pod_promql",
            "query_pod_logs",
            "query_pod_tracing",
            "query_pod_topology",
            "query_pod_lifecycle",
            "kubectl_describe",
            "kubectl_events",
            "kubectl_get_yaml",
            "kubectl_get_by_name",
            "kubectl_logs",
            "kubectl_previous_logs",
            "kubectl_container_logs",
            "kubectl_container_previous_logs",
            "execute_prometheus_instant_query",
            "execute_prometheus_range_query",
            "fetch_runbook",
            "read_context_archive",
        }
    )


class DiagnosisRootCauseNode(DiagnosisStageNode):
    stage_id = "rca"
    stage_name = "根因分析"
    stage_prompt = DEEP_RCA_PROMPT
    collect = False
