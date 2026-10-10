"""Question-led diagnosis roles using the same evidence and memory path as QUERY.

No baseline calls, inferred abnormal-group fanout, fault-specific stop checkers,
or programmatic causal decisions. The graph assigns roles, not diagnoses.
"""
import asyncio
import json

from app.core.prompts import (
    DIAGNOSTIC_TOOL_GUIDANCE, DEEP_LAYER_PROMPT, DEEP_EVIDENCE_PROMPT, DEEP_RCA_PROMPT,
    AUTONOMOUS_RUNBOOK_CATALOG_HEADER, PARALLEL_LANE_TASK_PREFIX,
)
from app.core.workflow.nodes.query_answer import (
    QueryCollectNode, build_working_material, _configure_query_runtime,
)


class DiagnosisStageNode(QueryCollectNode):
    stage_id = "layer"
    stage_name = "问题定位"
    stage_prompt = DEEP_LAYER_PROMPT
    collect = True

    @property
    def node_id(self):
        return self.stage_id

    @property
    def node_name(self):
        return self.stage_name

    def execute(self, state):
        _configure_query_runtime(self)
        if getattr(self, "ai_call", None) is not None:
            # History is already in material; do not insert it twice.
            self.ai_call.query_session_context = {}
            self.ai_call.working_context_original_question = state.get("question", "") if state.get("diagnosis_target") else state.get("original_question") or state.get("question", "")
        material = build_working_material(state)
        material["request_contract"] = state.get("request_contract")
        prompt = self.stage_prompt
        if state.get("diagnosis_target"):
            from app.core.prompts import PARALLEL_LANE_PROMPT
            prompt = PARALLEL_LANE_PROMPT + PARALLEL_LANE_TASK_PREFIX + material["question"] + "\n" + prompt
        if self.collect:
            prompt += "\n" + DIAGNOSTIC_TOOL_GUIDANCE
            prompt += AUTONOMOUS_RUNBOOK_CATALOG_HEADER + self._prepare_query_tools()
        self._archive_node_input(material)

        def call(payload):
            return self._call_llm(
                json.dumps(payload, ensure_ascii=False, default=str), prompt,
                force_no_tools=not self.collect, skip_remediation_policy=True,
                blocked_tool_names={t.name for t in getattr(self, "tools", []) if t.name not in self.READ_TOOLS},
            )

        events = list(state.get("thinking_events") or [])
        from app.core.aicall.client import StructuredContextBudgetError
        try:
            response, stage_events = call(material)
        except StructuredContextBudgetError as exc:
            if "working_context_compaction_required" not in str(exc):
                raise
            from app.core.aicall.working_context import compact_working_material
            model = self.ai_call._create_chat_model(node_id="context_compaction", disable_streaming=True).bind(max_tokens=3000)
            compact = asyncio.run(compact_working_material(
                model, material,
                lambda **event: self.ai_call._push(self._event_queue, self.node_id, events, **event),
            ))
            events.append({"type": "context_compacted", "working_summary": compact["working_summary"],
                           "protected_handoff": compact.get("protected_handoff", {}),
                           "retained_messages": compact["recent_interactions"]})
            self._archive_node_input({"before_compaction": material, "after_compaction": compact})
            response, stage_events = call(compact)
        draft = response.result or ""
        output = {"query_draft": draft, "thinking_events": [*events, *stage_events]}
        # These fields are only stage prose, not verified facts or forced classifications.
        output[{"layer": "layer_analysis", "evidence": "evidence_analysis", "rca": "rca_analysis"}[self.node_id]] = draft
        if self.node_id == "layer" and getattr(self, "autonomous_parallel_enabled", False):
            from app.core.workflow.nodes.autonomous_parallel import plan_groups
            output.update(plan_groups(self, {**state, **output}))
        self._archive_node_output(output)
        return output


class DiagnosisEvidenceNode(DiagnosisStageNode):
    stage_id = "evidence"
    stage_name = "证据采集"
    stage_prompt = DEEP_EVIDENCE_PROMPT


class DiagnosisRootCauseNode(DiagnosisStageNode):
    stage_id = "rca"
    stage_name = "根因分析"
    stage_prompt = DEEP_RCA_PROMPT
    collect = False
