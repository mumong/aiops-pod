import json
from types import SimpleNamespace

from app.core.skills.models import Layer
from app.core.workflow.diagnosis_state import (
    DiagnosisSubmission,
    EvidenceSlotDiagnosisSubmission,
)
from app.core.workflow.fact_contract import _canonical_fact_id
from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
from app.core.workflow.nodes.parallel_evidence import ParallelEvidenceNode


def _handoff(count: int) -> dict:
    return {
        "layer": "ABNORMAL",
        "issue_groups": [
            {
                "group_id": f"g{index}",
                "status_keywords": ["Unknown"],
                "pod_abnormal_type": "",
                "entities": [
                    {
                        "kind": "Pod",
                        "namespace": f"ns-{index}",
                        "name": f"pod-{index}",
                        "uid": f"uid-{index}",
                    }
                ],
                "possible_scenarios": [],
            }
            for index in range(1, count + 1)
        ],
    }


def _snapshot(*, eligible: list[str]) -> dict:
    return {
        "contract_version": "aiops.entity-evidence-snapshot.v1",
        "selection_manifest": {
            "eligible_support_fact_ids": eligible,
            "direct_causal_candidate_fact_ids": eligible,
            "required_context_fact_ids": [],
            "rca_input_fact_ids": eligible,
            "unselected_higher_priority_causal_fact_ids": [],
        },
        "fact_index": {
            fact_id: {
                "fact_id": fact_id,
                "entity_id": "k8s.pod:demo/api:uid-api",
                "entity_kind": "Pod",
                "namespace": "demo",
                "entity_name": "api",
                "dimension": "kubernetes",
                "fact_type": "event",
                "attribute": "event.reason",
                "value": "source-backed reason",
                "source_system": "kubernetes",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
                "evidence_role": "causal_candidate",
                "evidence_refs": ["ref"],
            }
            for fact_id in eligible
        },
    }


def _compact_baseline_event() -> tuple[dict, str]:
    entity_id = "k8s.pod:demo/api:uid-api"
    record = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "kubernetes",
        "fact_type": "event",
        "attribute": "last_state.reason",
        "value": "source-backed termination reason",
        "source_system": "kubernetes",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["describe-ref"],
        "metadata": {},
        "evidence_role": "causal_candidate",
    }
    record["fact_id"] = _canonical_fact_id(record)
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "baseline-kubernetes",
        "scope_entity_ids": [entity_id],
        "records": [record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    return {
        "type": "tool_result",
        "tool_name": "kubectl_describe",
        "tool_args": {"kind": "pod", "namespace": "demo", "name": "api"},
        "status": "success",
        "semantic_success": True,
        "result": "source-backed termination reason",
        "structured": {
            "status": "query_succeeded",
            "source_system": "kubernetes",
            "dimension": "kubernetes",
            "coverage": "present",
            "entity": {
                "kind": "Pod",
                "namespace": "demo",
                "pod": "api",
                "pod_uid": "uid-api",
            },
            "fact_ledger": ledger,
        },
    }, record["fact_id"]


def test_parallel_lane_concurrency_defaults_to_all_discovered_lanes():
    node = ParallelEvidenceNode()
    node.workflow_config_override = {
        "evidence": {"parallel": {"max_concurrency": 3}}
    }

    assert node._max_concurrency(10) == 10

    node.workflow_config_override = {
        "evidence": {"parallel": {"lane_concurrency": 4}}
    }
    assert node._max_concurrency(10) == 4

    node.workflow_config_override = {
        "evidence": {"parallel": {"lane_concurrency": 0}}
    }
    assert node._max_concurrency(10) == 10


def test_minimum_rca_gate_retries_when_diagnosed_uses_no_causal_candidate():
    node = ParallelEvidenceNode()
    result = {
        "entity_evidence_snapshot": _snapshot(eligible=["fact-causal0001"]),
    }
    rca_update = {
        "rca_analysis": json.dumps({
            "diagnostic_status": "diagnosed",
            "supporting_fact_ids": ["fact-symptom001"],
            "contradicting_fact_ids": [],
            "hypotheses": [],
            "claim_validation": {
                "valid": True,
                "valid_supporting_fact_ids": ["fact-symptom001"],
                "valid_contradicting_fact_ids": [],
                "reasons": [],
            },
        }),
    }

    gate = node._minimum_rca_gate(result, rca_update)

    assert gate["verdict"] == "retry"
    assert "PRIMARY_CAUSAL_SUPPORT_MISSING" in gate["failure_codes"]
    assert gate["focus_fact_ids"] == ["fact-causal0001"]


def test_minimum_rca_gate_accepts_supported_diagnosis_with_audited_extra_ref():
    node = ParallelEvidenceNode()
    result = {
        "entity_evidence_snapshot": _snapshot(eligible=["fact-causal0001"]),
    }
    rca_update = {
        "rca_analysis": json.dumps({
            "diagnostic_status": "diagnosed",
            "supporting_fact_ids": ["fact-causal0001"],
            "contradicting_fact_ids": [],
            "hypotheses": [{
                "hypothesis_id": "hyp-supported",
                "supporting_fact_ids": ["fact-causal0001"],
                "contradicting_fact_ids": [],
            }],
            "claim_validation": {
                "valid": False,
                "diagnosis_supported": True,
                "valid_supporting_fact_ids": ["fact-causal0001"],
                "valid_contradicting_fact_ids": [],
                "invalid_fact_ids": ["fact-unknown0001"],
                "reasons": ["unknown supporting fact reference"],
            },
        }),
    }

    gate = node._minimum_rca_gate(result, rca_update)

    assert gate["verdict"] == "pass"
    assert gate["failure_codes"] == []


def test_minimum_rca_gate_does_not_require_every_supporting_symptom():
    node = ParallelEvidenceNode()
    snapshot = _snapshot(eligible=["fact-causal0001", "fact-symptom001"])
    snapshot["selection_manifest"]["direct_causal_candidate_fact_ids"] = [
        "fact-causal0001"
    ]
    result = {"entity_evidence_snapshot": snapshot}
    rca_update = {
        "rca_analysis": json.dumps({
            "diagnostic_status": "inconclusive",
            "supporting_fact_ids": ["fact-causal0001"],
            "contradicting_fact_ids": [],
            "hypotheses": [{
                "hypothesis_id": "hyp-partial",
                "supporting_fact_ids": ["fact-causal0001"],
                "contradicting_fact_ids": [],
            }],
            "claim_validation": {
                "valid": True,
                "diagnosis_supported": True,
                "valid_supporting_fact_ids": ["fact-causal0001"],
                "valid_contradicting_fact_ids": [],
                "reasons": [],
            },
        }),
    }

    gate = node._minimum_rca_gate(result, rca_update)

    assert gate["verdict"] == "pass"
    assert gate["focus_fact_ids"] == []


def test_minimum_rca_gate_retries_missing_fact_state_or_submission():
    gate = ParallelEvidenceNode._minimum_rca_gate(
        {
            "diagnosis_state": {"attempt_count": 1},
            "entity_evidence_snapshot": {
                "selection_manifest": {},
                "fact_index": {},
            },
        },
        {
            "rca_analysis": json.dumps({
                "diagnostic_status": "inconclusive",
                "supporting_fact_ids": [],
                "contradicting_fact_ids": [],
                "hypotheses": [],
                "claim_validation": {"valid": False},
            }),
            "rca_attempts": [{"submission_received": False}],
        },
    )

    assert gate["verdict"] == "retry"
    assert set(gate["failure_codes"]) >= {
        "NO_AUTHORITATIVE_FACTS",
        "DIAGNOSIS_SUBMISSION_MISSING",
    }


def test_parallel_validation_failure_starts_fresh_full_react_attempt(monkeypatch):
    collector_states: list[dict] = []
    collector_instances: list[object] = []

    class _Collector:
        def __init__(self, *args, **kwargs):
            self.current_run_id = ""
            self.single_react_session = False
            collector_instances.append(self)

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            collector_states.append(state)
            attempt = len(collector_states)
            return {
                "evidence_analysis": json.dumps({
                    "plan_completeness": 1.0,
                    "collection_summary": f"attempt-{attempt}",
                }),
                "thinking_events": [
                    {
                        "type": "tool_result",
                        "status": "success",
                        "tool_name": "query_pod_logs",
                        "tool_args": {
                            "namespace": "ns-1",
                            "pod": "pod-1",
                            "purpose": f"attempt-{attempt}",
                        },
                        "structured": {
                            "dimension": "logging",
                            "coverage": "present",
                            "facts": [
                                {
                                    "name": "message",
                                    "value": f"evidence-{attempt}",
                                    "dimension": "logging",
                                }
                            ],
                        },
                    }
                ],
            }

    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _Collector,
    )
    node = ParallelEvidenceNode()
    node.tools = []
    gate_calls = 0

    def _gate(result, rca_update):
        nonlocal gate_calls
        gate_calls += 1
        if gate_calls == 1:
            return {
                "verdict": "retry",
                "failure_codes": ["PRIMARY_CAUSAL_SUPPORT_MISSING"],
                "reasons": ["first attempt missed decisive evidence"],
                "focus_fact_ids": [],
            }
        return {
            "verdict": "pass",
            "failure_codes": [],
            "reasons": [],
            "focus_fact_ids": [],
        }

    monkeypatch.setattr(node, "_minimum_rca_gate", _gate, raising=False)
    monkeypatch.setattr(
        node,
        "_attach_validated_diagnosis",
        lambda result, group, update: result.update(
            {"diagnostic_status": "inconclusive", "rca_analysis": update["rca_analysis"]}
        ),
    )
    monkeypatch.setattr(
        node,
        "_persist_lane_diagnosis_artifact",
        lambda result, update: None,
    )

    output = node.execute({
        "question": "diagnose",
        "run_id": "run-bounded",
        "layer": Layer.ABNORMAL,
        "layer_handoff": _handoff(1),
        "thinking_events": [],
    })

    assert len(output["group_results"]) == 1
    assert len(collector_states) == 2
    assert collector_states[0]["thinking_events"] == []
    assert collector_states[1]["thinking_events"] == []
    retry_context = collector_states[1]["layer_handoff"]["diagnosis_retry"]
    assert retry_context["attempt"] == 2
    assert retry_context["validation_feedback"]["failure_codes"] == [
        "PRIMARY_CAUSAL_SUPPORT_MISSING"
    ]
    assert all(instance.single_react_session for instance in collector_instances)
    assert all(instance.require_diagnosis_submission for instance in collector_instances)
    assert [instance.run_observability_baseline for instance in collector_instances] == [
        True,
        False,
    ]
    assert output["group_results"][0]["diagnosis_state"]["attempt_count"] == 2


def test_parallel_collector_uses_one_full_react_session_without_early_stop(
    monkeypatch,
):
    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.tools = []
    node._early_stop_state = {
        "triggered": False,
        "reason": "",
        "required_levels": ["critical", "important"],
    }
    calls: list[dict] = []

    def _call_llm(question, system_prompt, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(result="agent completed"), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "query_pod_logs",
                "tool_args": {"namespace": "demo", "pod": "api"},
                "structured": {"dimension": "logging", "coverage": "present"},
            }
        ]

    monkeypatch.setattr(node, "_call_llm", _call_llm)
    monkeypatch.setattr(
        node,
        "_is_observability_first_round_gate_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        node,
        "_is_autonomous_observability_enabled",
        lambda: True,
    )

    plan, events, text = node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[{"type": "Pod", "value": "demo/api"}],
        layer_analysis=json.dumps({
            "layer": "ABNORMAL",
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=[{
            "id": "e1",
            "description": "collect scoped logs",
            "level": "critical",
            "tool": "query_pod_logs",
            "command": "query scoped logs",
            "tool_args": {"namespace": "demo", "pod": "api"},
            "purpose": "test",
        }],
        failure_reason="",
    )

    assert plan[0]["id"] == "e1"
    assert len(events) == 1
    assert text == "agent completed"
    assert len(calls) == 1
    assert calls[0]["stop_checker"] is None


def test_parallel_collector_uses_same_tool_agent_for_diagnosis_submission(
    monkeypatch,
):
    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.require_diagnosis_submission = True
    node.tools = []
    calls: list[dict] = []

    def _call_structured_agent(**kwargs):
        calls.append(kwargs)
        submission = DiagnosisSubmission(
            diagnostic_status="diagnosed",
            phenomenon="Pod unavailable",
            root_cause="source-backed startup failure",
            causal_chain=["startup failure", "Pod unavailable"],
            supporting_fact_ids=["fact-causal0001"],
            confidence=0.9,
            confidence_reason="direct source fact",
        )
        return submission, SimpleNamespace(result=submission.model_dump_json()), [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "kubectl_describe",
                "tool_args": {"namespace": "demo", "name": "api"},
                "structured": {"status": "events_found"},
            }
        ]

    monkeypatch.setattr(node, "_call_structured_agent", _call_structured_agent)
    monkeypatch.setattr(
        node,
        "_is_observability_first_round_gate_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        node,
        "_is_autonomous_observability_enabled",
        lambda: True,
    )

    _plan, events, _text = node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[{"type": "Pod", "value": "demo/api"}],
        layer_analysis=json.dumps({
            "layer": "ABNORMAL",
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=[{
            "id": "e1",
            "description": "inspect Pod",
            "level": "critical",
            "tool": "kubectl_describe",
            "command": "describe Pod",
            "tool_args": {"namespace": "demo", "name": "api"},
            "purpose": "find the source failure",
        }],
        failure_reason="",
    )

    assert calls[0]["schema"] is DiagnosisSubmission
    assert calls[0]["use_tools"] is True
    assert len(events) == 1
    assert node._diagnosis_submission["root_cause"] == (
        "source-backed startup failure"
    )


def test_diagnosis_agent_can_choose_read_only_tools_but_not_write_tools():
    node = EvidenceCollectorNode()
    node.require_diagnosis_submission = True
    node.tools = [
        SimpleNamespace(name=name)
        for name in (
            "query_pod_logs",
            "kubectl_events",
            "kubectl_describe",
            "kubectl_apply",
            "kubectl_delete",
            "run_bash_command",
            "execute_prometheus_instant_query",
        )
    ]
    node.workflow_config_override = {
        "evidence": {"observability_mode": "autonomous"}
    }

    blocked = node._blocked_tools_for_preplanned_execution([{
        "id": "e1",
        "tool": "query_pod_logs",
        "acceptable_tools": ["query_pod_logs"],
    }])

    assert "query_pod_logs" not in blocked
    assert "kubectl_events" not in blocked
    assert "kubectl_describe" not in blocked
    assert "kubectl_apply" in blocked
    assert "kubectl_delete" in blocked
    assert "run_bash_command" in blocked
    assert "execute_prometheus_instant_query" in blocked


def test_diagnosis_lane_uses_code_owned_initial_plan_without_planning_llm(
    monkeypatch,
):
    node = EvidenceCollectorNode()
    node.require_diagnosis_submission = True
    node.ai_call = object()
    node.workflow_config_override = {
        "evidence": {
            "observability_mode": "autonomous",
            "observability_first_round_gate": {"enabled": True},
        }
    }
    captured: dict = {}

    def _execute_existing(**kwargs):
        captured.update(kwargs)
        return kwargs["evidence_plan"], [], ""

    monkeypatch.setattr(node, "_execute_existing_evidence_plan", _execute_existing)
    monkeypatch.setattr(
        node,
        "_generate_structured_evidence_plan",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("planning LLM must not run for a diagnosis lane")
        ),
    )

    plan, _events, _text = node._plan_evidence_with_llm(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[{"type": "Pod", "value": "demo/api"}],
        layer_analysis=json.dumps({
            "layer": "ABNORMAL",
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
    )

    assert {item["tool"] for item in plan} == {
        "kubectl_describe",
        "execute_pod_promql",
        "query_pod_logs",
        "query_pod_tracing",
    }
    assert captured["failure_reason"].startswith("代码已根据权威 Pod 身份")


def test_parallel_collector_hands_code_owned_four_dimension_baseline_to_react(
    monkeypatch,
):
    batch_calls: list[dict] = []
    llm_calls: list[dict] = []

    class _BatchAICall:
        def execute_tool_batch(self, **kwargs):
            batch_calls.append(kwargs)
            events = []
            for sequence, request in enumerate(kwargs["tool_requests"], start=1):
                events.extend([{
                    "type": "tool_start",
                    "tool_name": request["tool_name"],
                    "tool_args": request["tool_args"],
                    "tool_sequence": sequence,
                }, {
                    "type": "tool_result",
                    "tool_name": request["tool_name"],
                    "tool_args": request["tool_args"],
                    "tool_sequence": sequence,
                    "status": "success",
                    "semantic_success": True,
                    "result": f"source-backed-{request['tool_name']}",
                    "structured": {
                        "dimension": request["tool_name"],
                        "coverage": "present",
                    },
                }])
            return events

    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.ai_call = _BatchAICall()
    node.tools = [
        SimpleNamespace(name=name)
        for name in EvidenceCollectorNode._PRE_REACT_BASELINE_TOOLS
    ]
    monkeypatch.setattr(
        node,
        "_is_observability_first_round_gate_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        node,
        "_is_autonomous_observability_enabled",
        lambda: True,
    )

    def _call_llm(question, system_prompt, **kwargs):
        llm_calls.append({"question": question, **kwargs})
        return SimpleNamespace(result="agent completed"), []

    monkeypatch.setattr(node, "_call_llm", _call_llm)
    plan = [
        node._build_autonomous_observability_gate_item(
            namespace="demo",
            pod="api",
            tool_name=tool_name,
            target_index=1,
        )
        for tool_name in EvidenceCollectorNode._PRE_REACT_BASELINE_TOOLS
    ]

    _plan, events, text = node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis=json.dumps({
            "layer": "ABNORMAL",
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=plan,
        failure_reason="",
    )

    assert len(batch_calls) == 1
    assert [
        request["tool_name"]
        for request in batch_calls[0]["tool_requests"]
    ] == list(EvidenceCollectorNode._PRE_REACT_BASELINE_TOOLS)
    assert batch_calls[0]["max_workers"] == 4
    assert llm_calls[0]["tool_result_sequence_start"] == 4
    assert "aiops.pre-react-baseline.v2" in llm_calls[0]["question"]
    assert "source-backed-query_pod_logs" in llm_calls[0]["question"]
    assert sum(event["type"] == "tool_result" for event in events) == 4
    assert text == "agent completed"


def test_parallel_collector_skips_react_when_compact_baseline_is_publishable(
    monkeypatch,
):
    entity_id = "k8s.pod:demo/api:uid-api"
    record = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "api",
        "dimension": "metrics",
        "fact_type": "measurement",
        "attribute": "kube_pod_container_status_last_terminated_reason",
        "value": "1",
        "source_system": "prometheus",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["metric-ref"],
        "metadata": {"labels": {"reason": "OOMKilled"}},
        "evidence_role": "causal_candidate",
    }
    record["fact_id"] = _canonical_fact_id(record)
    ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "baseline-metric",
        "scope_entity_ids": [entity_id],
        "records": [record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }

    class _FastAICall:
        def execute_tool_batch(self, **kwargs):
            request = kwargs["tool_requests"][0]
            return [{
                "type": "tool_result",
                "tool_name": request["tool_name"],
                "tool_args": request["tool_args"],
                "status": "success",
                "semantic_success": True,
                "result": "OOMKilled metric",
                "structured": {
                    "status": "query_succeeded",
                    "source_system": "prometheus",
                    "dimension": "metrics",
                    "coverage": "present",
                    "entity": {
                        "kind": "Pod",
                        "namespace": "demo",
                        "pod": "api",
                        "pod_uid": "uid-api",
                    },
                    "fact_ledger": ledger,
                },
            }]

        def call_structured(self, **kwargs):
            assert kwargs["schema"] is EvidenceSlotDiagnosisSubmission
            assert kwargs["node_id"] == "evidence_baseline"
            return EvidenceSlotDiagnosisSubmission(
                diagnostic_status="diagnosed",
                phenomenon="container restarted",
                root_cause="container was OOMKilled",
                causal_chain=["OOM kill", "container restart"],
                supporting_evidence_slots=[1],
                confidence=0.9,
                confidence_reason="direct termination reason",
            ), "{}"

    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.require_diagnosis_submission = True
    node.ai_call = _FastAICall()
    node.tools = [SimpleNamespace(name="execute_pod_promql")]
    monkeypatch.setattr(
        node,
        "_is_observability_first_round_gate_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        node,
        "_is_autonomous_observability_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        node,
        "_call_structured_agent",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("publishable compact baseline must skip ReAct")
        ),
    )

    plan = [node._build_autonomous_observability_gate_item(
        namespace="demo",
        pod="api",
        tool_name="execute_pod_promql",
        target_index=1,
    )]
    _plan, events, _text = node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis=json.dumps({
            "layer": "ABNORMAL",
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=plan,
        failure_reason="",
    )

    assert len(events) == 1
    assert node._diagnosis_submission["supporting_fact_ids"] == [
        record["fact_id"]
    ]


def test_compact_baseline_retries_once_with_validation_feedback():
    event, fact_id = _compact_baseline_event()
    calls: list[dict] = []

    class _RetryAICall:
        def call_structured(self, **kwargs):
            calls.append(kwargs)
            slot = 99 if len(calls) == 1 else 1
            return EvidenceSlotDiagnosisSubmission(
                diagnostic_status="diagnosed",
                phenomenon="容器发生异常终止",
                root_cause="容器进程被运行时终止",
                causal_chain=["进程终止", "容器重启"],
                supporting_evidence_slots=[slot],
                confidence=0.9,
                confidence_reason="直接生命周期事实",
            ), "{}"

    node = EvidenceCollectorNode()
    node.ai_call = _RetryAICall()

    submission = node._try_compact_fact_diagnosis(
        events=[event],
        phase="baseline",
        max_attempts=2,
    )

    assert submission is not None
    assert submission.supporting_fact_ids == [fact_id]
    assert [call["node_id"] for call in calls] == [
        "evidence_baseline",
        "evidence_baseline_retry",
    ]
    retry_payload = json.loads(calls[1]["question"])
    assert "outside catalogue" in retry_payload["validation_feedback"][0]
    assert "所有面向用户的" in calls[0]["system_prompt"]
    assert "必须使用简体中文" in calls[0]["system_prompt"]


def test_compact_baseline_enters_react_only_after_two_failed_attempts(
    monkeypatch,
):
    event, fact_id = _compact_baseline_event()
    compact_calls: list[dict] = []
    react_calls: list[dict] = []

    class _AlwaysInvalidCompactAICall:
        def call_structured(self, **kwargs):
            compact_calls.append(kwargs)
            return EvidenceSlotDiagnosisSubmission(
                diagnostic_status="diagnosed",
                phenomenon="容器发生异常终止",
                root_cause="容器进程被运行时终止",
                causal_chain=["进程终止", "容器重启"],
                supporting_evidence_slots=[99],
                confidence=0.9,
                confidence_reason="直接生命周期事实",
            ), "{}"

    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.require_diagnosis_submission = True
    node.ai_call = _AlwaysInvalidCompactAICall()
    node.tools = []
    monkeypatch.setattr(
        node,
        "_run_pre_react_observability_baseline",
        lambda _plan: [event],
    )

    def _react(**kwargs):
        react_calls.append(kwargs)
        submission = DiagnosisSubmission(
            diagnostic_status="diagnosed",
            phenomenon="容器发生异常终止",
            root_cause="容器进程被运行时终止",
            causal_chain=["进程终止", "容器重启"],
            supporting_fact_ids=[fact_id],
            confidence=0.9,
            confidence_reason="直接生命周期事实",
        )
        return submission, SimpleNamespace(result="agent completed"), []

    monkeypatch.setattr(node, "_call_structured_agent", _react)

    _plan, _events, text = node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis=json.dumps({
            "layer": "ABNORMAL",
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=[],
        failure_reason="",
    )

    assert len(compact_calls) == 2
    assert len(react_calls) == 1
    assert text == "agent completed"
    assert node._diagnosis_submission["supporting_fact_ids"] == [fact_id]
