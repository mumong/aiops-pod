"""Golden complete outputs before the final evidence policy relocation."""

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

from app.core.skills.models import Layer
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode as Node


PLAN = [{"id": "p1", "tool": "kubectl_get_yaml", "level": "critical",
         "description": "获取状态", "command": "kubectl get pod api"}]
QUESTION = "问题 {literal}\n原文"


def _strict_output(strict, reason):
    node = Node()
    node.ai_call = object()
    captured = {}
    node._archive_node_input = lambda payload: captured.update(user=payload["user_message"])
    node._get_evidence_planning_mode = lambda: "structured"
    node._is_autonomous_observability_enabled = lambda: False
    node._generate_structured_evidence_plan = lambda system_prompt, user_message, layer_str: (
        captured.update(system=system_prompt) or [], ""
    )
    node._prepare_evidence_plan = lambda plan, handoff: []
    node._plan_evidence_with_llm(
        QUESTION, Layer.L2, [], [], strict_mode=strict, failure_reason=reason
    )
    assert set(captured) == {"user", "system"}
    return captured


def _retry_output():
    node = Node()
    calls = []

    def plan(**kwargs):
        calls.append(kwargs)
        return PLAN, [], "result"

    node._plan_evidence_with_llm = plan
    node._save_thinking = lambda *args: None
    node.execute({"question": QUESTION, "layer": Layer.L3, "layer_analysis": "{}"})
    assert len(calls) == 2
    return calls


def _continuation_output(summary, gate=False):
    node = Node()
    node._early_stop_state = {}
    node._is_observability_first_round_gate_enabled = lambda: gate
    node._is_autonomous_observability_enabled = lambda: gate
    node._ensure_autonomous_observability_gate_plan = lambda plan, handoff: plan
    node._is_early_stop_enabled = lambda **kwargs: False
    node._mandatory_case_targets = lambda plan: []
    node._remaining_unattempted_mandatory_items = lambda plan, events: (
        PLAN if len(events) == 1 else []
    )
    node._attempted_mandatory_case_targets = lambda events: []
    node._format_completed_mandatory_summary = lambda events: summary
    node._remaining_unattempted_autonomous_items = node._remaining_unattempted_mandatory_items
    node._attempted_autonomous_observability_gate_items = lambda events: []
    node._format_completed_autonomous_gate_summary = lambda events: summary
    calls = []

    def call(user, system, **kwargs):
        calls.append({"user": user, "system": system})
        return SimpleNamespace(result="text"), [{"type": "tool_result", "status": "success"}]

    node._call_llm = call
    node._execute_existing_evidence_plan(
        QUESTION, Layer.L2, [], [], "{}", "", {}, PLAN, "原始原因"
    )
    assert len(calls) == 2
    return calls


def _outputs():
    event = {"type": "tool_result", "tool_name": "query_pod_logs", "status": "error",
             "tool_args": {"q": "原文"}, "result": "错误 {x}\nline"}
    handoff = {"abnormal_pods": [{"namespace": "demo", "name": "api"}]}
    rich = {"current_abnormal_summary": {
        "status_counts": {"CrashLoopBackOff": 2}, "selected_rows": list(range(12))},
        "issue_groups": [{"entities": [{"name": "api", "namespace": "demo"}],
                          "status_keywords": ["Pending"], "compatible_layers": ["L2"]}]}
    # Only replace the outer workflow prompt: actual branch text/payload rendering runs.
    with patch("app.core.workflow.nodes.evidence_collector.get_workflow_prompt",
               return_value="system {layer} {possible_scenarios}"):
        return {
            "strict_off": _strict_output(False, ""),
            "strict_default": _strict_output(True, ""),
            "strict_reason": _strict_output(True, "错误 {raw}\nline"),
            "retry": _retry_output(),
            "continue_summary": _continuation_output("已完成 {x}\n日志"),
            "continue_empty": _continuation_output(""),
            "continue_gate": _continuation_output("已完成 {x}\n日志", gate=True),
            "handoff": Node._parse_layer_handoff(json.dumps(handoff)),
            "handoff_invalid": Node._parse_layer_handoff("invalid"),
            "conflict_missing": Node._build_evidence_conflicts(
                [{"tool": "kubectl", "data": 'pods "api" not found'}], handoff),
            "conflict_other": Node._build_evidence_conflicts(
                [{"data": "No events found"}], handoff),
            "baseline_failed": Node._append_baseline_handoff("user \n", [event]),
            "baseline_empty": Node._append_baseline_handoff("user \n", []),
            "baseline_success": Node._append_baseline_handoff(
                "user \n", [{**event, "status": "success", "result": "空结果"}]),
            "summary_empty": Node._format_current_abnormal_summary_for_prompt({}),
            "summary_rich": Node._format_current_abnormal_summary_for_prompt(rich),
            "default_execute": Node._build_evidence_user_message(
                QUESTION, "L2", "{}", existing_plan=PLAN),
            "default_strict": Node._build_evidence_user_message(
                QUESTION, "L2", "{}", strict_mode=True),
        }


EXPECTED = {
    "strict_off": "ae5d148f07e65394e26a39a593ebd5f9ed98c7e7e23a16c7d6234ccbb02bdbd0",
    "strict_default": "4b9cc79331664627dc43af05dc9b665f806643047fbfd3acc944255e4ac060e7",
    "strict_reason": "3fdb8066cc2b0ee9aaaee5bdeb53f8399222dd3a18596d8036d5df00f71226ba",
    "retry": "494a046ef23c4112c7af0d48cd9ce0f3bce035406b7aa95f2ad3823f50bf432e",
    "continue_summary": "34838870208b843ae2f581e8c9006610bbd9ed2c29d4559bd10f1a7029d447ce",
    "continue_empty": "cd3051b7e48c68642ff52b86e2204f652db17361e2e98b96326aff77460dec66",
    "continue_gate": "0f65c62094099ebb1cd1d97dec01ef31ca8aae8816b4896f1faee15579c4c6e4",
    "handoff": "e4ac15dd8ac57cf6d88ff10ab1fd95fb53edcdfee126c757f87db3e8c63cab1c",
    "handoff_invalid": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
    "conflict_missing": "52f680525434aede95bc078900f73482b6be7407423f9ffc4ec84fa12c150878",
    "conflict_other": "9bd5bdfa3371fd6bf2faef2a402f40070296c34c24093e6f905840af8cfcc1e5",
    "baseline_failed": "365092ac1bac0b129491eda194491cb3f249340954ef5ae5c7c5003cb5632899",
    "baseline_empty": "7e1547711460f0181ad08c792ac83a0863d4906cf7b18c0526c1f8e8f2288825",
    "baseline_success": "9f5e4e90dafedbdc5b09e143cfe0ed5495288481dac15f86d73e0f3b6e69d239",
    "summary_empty": "9048a566d38707263a1bcea77beb6a6a640afb0883c84832b441b03f468d182d",
    "summary_rich": "ce6364ee0f16fb353feae820a8d5901785f37d1a5bb14aae8f2a0d472f6dbe45",
    "default_execute": "6a73ed1baa5747da4f30b6fe096fcca5d4c20986b5fde7d8134734a843481aa4",
    "default_strict": "f4c2eb2bda14c713ed6d2054ecb67b31dff7fe1e870d5e085ebb99f7672eeae8",
}


def _digest(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), default=str
    ).encode("utf-8")).hexdigest()


def test_complete_policy_boundary_outputs():
    actual = _outputs()
    assert actual.keys() == EXPECTED.keys()
    for name, value in actual.items():
        assert _digest(value) == EXPECTED[name], name
