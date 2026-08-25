import json
from types import SimpleNamespace

from app.core.skills.models import Layer
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


def test_parallel_group_rca_disables_internal_repair():
    node = ParallelEvidenceNode()

    rca = node._build_group_rca(
        "g1",
        "run-1",
        {"entities": [{"kind": "Pod", "namespace": "demo", "name": "api"}]},
    )

    assert rca.disable_internal_repair is True
    assert rca.current_run_id == "run-1-g1"


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


def test_parallel_validation_failure_does_not_recollect_or_overwrite(monkeypatch):
    collector_states: list[dict] = []
    collector_instances: list[object] = []
    rca_calls: list[dict] = []

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

    class _RCA:
        def __init__(self, *args, **kwargs):
            self.current_run_id = ""
            self.disable_internal_repair = False

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            rca_calls.append(state)
            return {
                "rca_analysis": json.dumps({
                    "diagnostic_status": "inconclusive",
                    "root_cause": "not enough evidence",
                    "root_cause_summary": "not enough evidence",
                    "supporting_fact_ids": [],
                    "contradicting_fact_ids": [],
                    "hypotheses": [],
                    "unknowns": [],
                    "confidence": 0.1,
                    "confidence_reason": "test",
                    "claim_validation": {"valid": False, "reasons": []},
                }),
                "rca_attempts": [],
                "claim_validation": {"valid": False, "reasons": []},
            }

    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _Collector,
    )
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.RootCauseAnalyzerNode",
        _RCA,
    )

    node = ParallelEvidenceNode()
    node.tools = []
    node.workflow_config_override = {
        "rca_validation": {"enabled": True}
    }
    gate_calls = 0

    def _gate(result, rca_update):
        nonlocal gate_calls
        gate_calls += 1
        return {
            "verdict": "retry",
            "failure_codes": ["PRIMARY_CAUSAL_SUPPORT_MISSING"],
            "reasons": ["RCA did not bind decisive evidence"],
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
    assert len(collector_states) == 1
    assert len(rca_calls) == 1
    assert gate_calls == 1
    assert collector_states[0]["thinking_events"] == []
    assert all(instance.single_react_session for instance in collector_instances)
    assert [instance.run_observability_baseline for instance in collector_instances] == [
        True,
    ]


def test_parallel_default_skips_gate_and_runs_one_rca_attempt(monkeypatch):
    collector_calls = 0
    rca_calls = 0

    class _Collector:
        current_run_id = "run-default-g1"

        def execute(self, state):
            nonlocal collector_calls
            collector_calls += 1
            return {"evidence_analysis": "{}", "thinking_events": []}

    class _RCA:
        def execute(self, state):
            nonlocal rca_calls
            rca_calls += 1
            return {
                "rca_analysis": json.dumps({
                    "diagnostic_status": "diagnosed",
                    "root_cause": "model-only diagnosis",
                    "confidence": 0.9,
                    "claim_validation": {
                        "enabled": False,
                        "skipped": True,
                        "valid": None,
                    },
                }),
                "rca_attempts": [],
            }

    node = ParallelEvidenceNode()
    monkeypatch.setattr(node, "_build_group_collector", lambda *a, **k: _Collector())
    monkeypatch.setattr(node, "_build_group_rca", lambda *a, **k: _RCA())
    monkeypatch.setattr(
        node,
        "_build_group_result",
        lambda gid, group, state, run_id: {
            "group_id": gid,
            "parent_group_id": gid,
            "presentation_index": 0,
            "entities": group["entities"],
            "entity_evidence_snapshot": {},
            "thinking_events": [],
            "archive_run_id": f"{run_id}-{gid}",
        },
    )
    monkeypatch.setattr(
        node,
        "_minimum_rca_gate",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("gate must not run when validation is disabled")
        ),
    )
    monkeypatch.setattr(
        node,
        "_attach_validated_diagnosis",
        lambda result, group, update: result.update({
            "diagnostic_status": "diagnosed",
            "rca_analysis": update["rca_analysis"],
            "summary": "model-only diagnosis",
        }),
    )
    monkeypatch.setattr(node, "_persist_lane_diagnosis_artifact", lambda *a: None)

    output = node.execute({
        "question": "diagnose",
        "run_id": "run-default",
        "layer": Layer.ABNORMAL,
        "layer_handoff": _handoff(1),
        "thinking_events": [],
    })

    assert collector_calls == 1
    assert rca_calls == 1
    assert len(output["group_results"]) == 1


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


def test_parallel_collector_hands_code_owned_three_signal_baseline_to_react(
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
    assert batch_calls[0]["max_workers"] == 3
    assert llm_calls[0]["tool_result_sequence_start"] == 3
    assert "aiops.pre-react-observability-baseline.v1" in llm_calls[0]["question"]
    assert "source-backed-query_pod_logs" in llm_calls[0]["question"]
    assert sum(event["type"] == "tool_result" for event in events) == 3
    assert text == "agent completed"


def test_parallel_collector_retries_failed_baseline_dimension_once(monkeypatch):
    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.workflow_config_override = {
        "evidence": {
            "observability_mode": "autonomous",
            "observability_first_round_gate": {
                "enabled": True,
                "retry_failed_once": True,
            },
        }
    }
    node.tools = [
        SimpleNamespace(name=name)
        for name in EvidenceCollectorNode._PRE_REACT_BASELINE_TOOLS
    ]
    baseline_events = [
        {
            "type": "tool_result",
            "tool_name": "execute_pod_promql",
            "tool_args": {"namespace": "demo", "pod": "api"},
            "status": "error",
            "semantic_success": False,
            "result": "Input validation error: promql is required",
            "structured": {
                "status": "query_parse_failed",
                "coverage": "error",
                "raw_preview": "'promql' is a required property",
            },
        },
        {
            "type": "tool_result",
            "tool_name": "query_pod_logs",
            "tool_args": {"namespace": "demo", "pod": "api"},
            "status": "success",
            "semantic_success": True,
            "result": "LOG http_status=500 path=/health",
            "structured": {"coverage": "present"},
        },
        {
            "type": "tool_result",
            "tool_name": "query_pod_tracing",
            "tool_args": {"namespace": "demo", "pod": "api"},
            "status": "success",
            "semantic_success": True,
            "result": "TEMPO GET /health status=500",
            "structured": {"coverage": "present"},
        },
    ]
    monkeypatch.setattr(
        node,
        "_run_pre_react_observability_baseline",
        lambda plan: baseline_events,
    )
    calls = []

    def _call_llm(question, system_prompt, **kwargs):
        calls.append({"question": question, **kwargs})
        if len(calls) == 1:
            return SimpleNamespace(result="other dimensions collected"), []
        return SimpleNamespace(result="metrics retry collected"), [{
            "type": "tool_result",
            "tool_name": "execute_pod_promql",
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "promql": 'container_memory_working_set_bytes{namespace="demo",pod="api"}',
                "query_type": "range",
            },
            "status": "success",
            "semantic_success": True,
            "result": "METRIC value=50331648 unit=bytes",
            "structured": {"status": "query_succeeded", "coverage": "present"},
        }]

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
            "abnormal_pods": [{"namespace": "demo", "name": "api"}],
        }),
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=plan,
        failure_reason="",
    )

    assert len(calls) == 2
    assert "action=repair_failed_observability_once" in calls[1]["question"]
    assert "'promql' is a required property" in calls[1]["question"]
    assert calls[1]["tool_result_sequence_start"] == 3
    assert sum(event.get("type") == "tool_result" for event in events) == 4
    assert text == "other dimensions collected\nmetrics retry collected"


def test_parallel_collector_does_not_retry_when_agent_already_recovered_failure(
    monkeypatch,
):
    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.workflow_config_override = {
        "evidence": {
            "observability_mode": "autonomous",
            "observability_first_round_gate": {
                "enabled": True,
                "retry_failed_once": True,
            },
        }
    }
    node.tools = []
    failed = {
        "type": "tool_result",
        "tool_name": "execute_pod_promql",
        "tool_args": {"namespace": "demo", "pod": "api"},
        "status": "error",
        "semantic_success": False,
        "result": "promql is required",
        "structured": {"status": "query_parse_failed", "coverage": "error"},
    }
    monkeypatch.setattr(
        node,
        "_run_pre_react_observability_baseline",
        lambda plan: [failed],
    )
    calls = []

    def _call_llm(question, system_prompt, **kwargs):
        calls.append(question)
        return SimpleNamespace(result="recovered"), [{
            "type": "tool_result",
            "tool_name": "execute_pod_promql",
            "tool_args": {
                "namespace": "demo",
                "pod": "api",
                "promql": "up",
            },
            "status": "success",
            "semantic_success": True,
            "result": "empty result",
            "structured": {"status": "query_succeeded", "coverage": "empty"},
        }]

    monkeypatch.setattr(node, "_call_llm", _call_llm)
    node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=[],
        failure_reason="",
    )

    assert len(calls) == 1


def test_parallel_collector_does_not_retry_successful_empty_baseline(monkeypatch):
    node = EvidenceCollectorNode()
    node.single_react_session = True
    node.workflow_config_override = {
        "evidence": {
            "observability_mode": "autonomous",
            "observability_first_round_gate": {
                "enabled": True,
                "retry_failed_once": True,
            },
        }
    }
    node.tools = []
    monkeypatch.setattr(
        node,
        "_run_pre_react_observability_baseline",
        lambda plan: [{
            "type": "tool_result",
            "tool_name": "query_pod_logs",
            "tool_args": {"namespace": "demo", "pod": "api"},
            "status": "success",
            "semantic_success": True,
            "result": "no matching logs",
            "structured": {"status": "query_succeeded", "coverage": "empty"},
        }],
    )
    calls = []

    def _call_llm(question, system_prompt, **kwargs):
        calls.append(question)
        return SimpleNamespace(result="empty is a boundary"), []

    monkeypatch.setattr(node, "_call_llm", _call_llm)
    node._execute_existing_evidence_plan(
        question="diagnose",
        layer=Layer.ABNORMAL,
        possible_scenarios=[],
        key_entities=[],
        layer_analysis="{}",
        context_archive_ref="",
        layer_archive_ref={},
        evidence_plan=[],
        failure_reason="",
    )

    assert len(calls) == 1
