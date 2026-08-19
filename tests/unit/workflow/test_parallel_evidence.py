"""多异常并发 evidence 扇出 + conclusion 确定性拼接回归测试。"""
import json
from types import SimpleNamespace

import pytest

from app.core.skills.models import Layer
from app.core.workflow.nodes.parallel_evidence import (
    ParallelEvidenceNode,
    extract_abnormal_groups,
)
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.graph import build_diagnosis_workflow, _make_layer_router
from app.core.workflow.fact_contract import _canonical_fact_id


def _handoff(n_groups):
    return {
        "layer": "ABNORMAL",
        "issue_groups": [
            {
                "group_id": f"g{i}",
                "status_keywords": ["CrashLoopBackOff"],
                "pod_abnormal_type": "OOMKilled" if i % 2 else "ConfigError",
                "entities": [{"kind": "Pod", "namespace": f"ns-{i}", "name": f"pod-{i}"}],
                "possible_scenarios": [],
            }
            for i in range(1, n_groups + 1)
        ],
    }


def test_extract_abnormal_groups_from_issue_groups_and_pod_fallback():
    assert len(extract_abnormal_groups(_handoff(3))) == 3
    # 无 issue_groups 时按 abnormal_pods 逐个成组
    fb = extract_abnormal_groups({
        "abnormal_pods": [
            {"namespace": "a", "name": "p1", "status": "Pending"},
            {"namespace": "b", "name": "p2", "status": "Error"},
        ]
    })
    assert len(fb) == 2
    assert fb[0]["entities"][0]["name"] == "p1"


def test_layer_router_fans_out_only_above_threshold():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        parallel_enabled=True, parallel_threshold=2,
    )
    # 2 组 ≤ 阈值 → 走原 evidence
    assert router({"layer": Layer.ABNORMAL, "layer_handoff": _handoff(2)}) == "evidence"
    # 3 组 > 阈值 → 并发
    assert router({"layer": Layer.ABNORMAL, "layer_handoff": _handoff(3)}) == "parallel_evidence"
    # HEALTHY 不受影响
    assert router({"layer": Layer.HEALTHY, "layer_handoff": _handoff(5)}) == "conclusion"


def test_layer_router_defaults_every_abnormal_pod_to_the_lane_contract():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        parallel_enabled=True,
    )

    assert router({
        "layer": Layer.ABNORMAL,
        "layer_handoff": _handoff(1),
    }) == "parallel_evidence"


def test_layer_router_preserves_explicit_target_inventory_when_layer_is_healthy():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        parallel_enabled=True,
    )
    handoff = _handoff(1)
    handoff["explicit_pod_targets"] = [{
        "namespace": "ns-1",
        "name": "pod-1",
    }]

    assert router({
        "layer": Layer.HEALTHY,
        "layer_handoff": handoff,
    }) == "parallel_evidence"


def test_layer_router_counts_atomic_pod_lanes_not_coarse_issue_groups():
    router = _make_layer_router(
        ["layer", "evidence", "rca", "conclusion"],
        parallel_enabled=True,
        parallel_threshold=2,
    )
    handoff = _handoff(2)
    handoff["issue_groups"][0]["entities"].append({
        "kind": "Pod",
        "namespace": "ns-extra",
        "name": "pod-extra",
    })

    assert router({
        "layer": Layer.ABNORMAL,
        "layer_handoff": handoff,
    }) == "parallel_evidence"


class _FakeCollector:
    """替身：模拟每组 evidence 采集，返回带真实 fact 的 thinking_events + 摘要。"""
    instances = []

    def __init__(self, *a, **k):
        _FakeCollector.instances.append(self)
        self.current_run_id = ""

    def set_event_queue(self, q): pass

    def execute(self, state):
        # 从 scoped handoff 拿到本组实体，回一份该组独有的真实数据
        h = state["layer_handoff"]
        ns = h["abnormal_pods"][0]["namespace"]
        return {
            "evidence_analysis": json.dumps({
                "plan_completeness": 1.0,
                "collection_summary": f"{ns} 采集完成",
                "llm_analysis": f"{ns} 的根因是内存超限 OOMKilled，退出码137",
            }),
            "thinking_events": [{
                "type": "tool_result", "status": "success",
                "tool_name": "execute_pod_promql",
                "tool_args": {"namespace": ns, "pod": "pod", "purpose": "内存"},
                "structured": {
                    "dimension": "metrics", "coverage": "present",
                    "facts": [{"name": "container_memory_working_set_bytes",
                               "value": "99999", "unit": "bytes", "dimension": "metrics"}],
                },
            }],
        }


def test_parallel_evidence_fans_out_per_group(monkeypatch):
    _FakeCollector.instances = []
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _FakeCollector,
    )
    node = ParallelEvidenceNode()
    node.workflow_config_override = {"evidence": {"parallel": {"max_concurrency": 3}}}
    node.ai_call = object()
    node.tools = []
    state = {
        "question": "集群有哪些异常？", "run_id": "run1",
        "layer": Layer.ABNORMAL, "layer_handoff": _handoff(3),
        "thinking_events": [],
    }
    new_state = node.execute(state)
    gr = new_state["group_results"]
    # 3 组各自独立采集
    assert len(gr) == 3
    assert len(_FakeCollector.instances) == 3
    # 每组独立归档 run_id
    assert {r["archive_run_id"] for r in gr} == {"run1-g1", "run1-g2", "run1-g3"}
    # 每组摘要含该组真实根因
    assert all("OOMKilled" in r["summary"] for r in gr)


def test_conclusion_multi_group_deterministic_assembly_preserves_all_groups():
    """conclusion 多组模式：代码拼接正式 RCA 与真实数据，一组都不能丢。"""
    calls = []

    class _AI:
        def call_simple(self, system_prompt, question, max_tokens=None):
            calls.append(question)
            return "## 📊 集群多异常诊断概览\n（LLM 写的结论）"

    node = ConclusionFormatterNode()
    node.ai_call = _AI()
    group_results = [
        {
            "group_id": f"g{i}", "pod_abnormal_type": "OOMKilled",
            "status_keywords": ["CrashLoopBackOff"],
            "entities": [{"namespace": f"ns-{i}", "name": f"pod-{i}"}],
            "summary": f"ns-{i} 根因内存超限",
            "collection_summary": "采集完成",
            "thinking_events": [{
                "type": "tool_result", "status": "success",
                "tool_name": "execute_pod_promql",
                "tool_args": {"namespace": f"ns-{i}", "pod": f"pod-{i}", "purpose": "内存"},
                "structured": {
                    "dimension": "metrics", "coverage": "present",
                    "facts": [{"name": "mem", "value": f"{i}0000", "unit": "bytes",
                               "dimension": "metrics"}],
                },
            }],
            "archive_run_id": f"run1-g{i}", "error": None,
        }
        for i in range(1, 4)
    ]
    state = {
        "question": "集群有哪些异常？", "layer": Layer.ABNORMAL,
        "group_results": group_results, "thinking_events": [],
    }
    result = node.execute(state)
    report = result["conclusion"]
    # 多组结论不得由另一个 LLM 重判或覆盖正式组级 RCA
    assert calls == []
    # 三组真实 metric 值都被代码确定性拼接进报告（一组不丢）
    assert "10000" in report and "20000" in report and "30000" in report
    # 各组归档引用都在
    for i in range(1, 4):
        assert f"run1-g{i}" in report
    assert "集群多异常诊断" in report


def test_conclusion_multi_group_fallback_when_llm_unavailable():
    node = ConclusionFormatterNode()  # 无 ai_call
    group_results = [{
        "group_id": "g1", "pod_abnormal_type": "OOMKilled",
        "status_keywords": ["CrashLoopBackOff"],
        "entities": [{"namespace": "ns-1", "name": "pod-1"}],
        "summary": "ns-1 根因内存超限", "thinking_events": [],
        "archive_run_id": "run1-g1", "error": None,
    }]
    result = node.execute({
        "question": "?", "layer": Layer.ABNORMAL,
        "group_results": group_results, "thinking_events": [],
    })
    assert "确定性汇总" in result["conclusion"]
    assert "ns-1 根因内存超限" in result["conclusion"]


def test_parallel_report_uses_only_validated_selected_rca():
    node = ConclusionFormatterNode()
    group = {
        "group_id": "g1",
        "entities": [{"namespace": "demo", "name": "api"}],
        "diagnostic_status": "diagnosed",
        "rca_analysis": json.dumps({
            "diagnostic_status": "inconclusive",
            "root_cause": "Current facts are insufficient",
            "confidence": 0.2,
            "supporting_fact_ids": [],
            "claim_validation": {
                "valid": False,
                "reasons": ["invalid fact ownership"],
            },
        }),
        "entity_summaries": [{
            "namespace": "demo",
            "name": "api",
            "diagnostic_status": "diagnosed",
            "root_cause": "unsupported model root",
            "confidence": 0.99,
            "supporting_fact_ids": ["fact-foreign123"],
        }],
        "dimension_evidence_by_entity": {
            "demo/api": {
                "logging": {
                    "status": "present",
                    "facts": [{
                        "fact_id": "fact-real1234",
                        "source_system": "elasticsearch",
                        "value": "real symptom",
                    }],
                },
            },
        },
        "thinking_events": [],
    }

    report = node.execute({
        "question": "What is wrong?",
        "layer": Layer.ABNORMAL,
        "group_results": [group],
        "thinking_events": [],
    })["conclusion"]

    assert "证据不足" in report
    assert "invalid fact ownership" in report
    assert "unsupported model root" not in report
    assert "real symptom" in report


def test_group_state_key_entities_are_dicts_for_evidence_planner():
    """回归：evidence planner 对 key_entities 调 .get('type')，必须传 dict 不能传 str
    （11.0.97 实测 bug：传 str 导致每组采集器崩溃 'str' object has no attribute get）。"""
    node = ParallelEvidenceNode()
    handoff = _handoff(1)
    group = extract_abnormal_groups(handoff)[0]
    scoped = node._build_group_state(
        question="q", state={"run_id": "r"}, handoff=handoff, group=group, gid="g1",
    )
    assert scoped["key_entities"], "key_entities 不应为空"
    for e in scoped["key_entities"]:
        assert isinstance(e, dict), f"key_entities 项必须是 dict，实际 {type(e)}"
        assert "type" in e and "value" in e
    # 复现 evidence planner 的取值不崩溃
    rendered = [f"{e.get('type', '')}: {e.get('value', '')}" for e in scoped["key_entities"]]
    assert all("/" in r for r in rendered)


def test_group_state_replaces_multi_target_question_with_single_lane_scope():
    node = ParallelEvidenceNode()
    handoff = _handoff(2)
    group = extract_abnormal_groups(handoff)[0]
    scoped = node._build_group_state(
        question="诊断 demo/pod-1 other/pod-2",
        state={"run_id": "r"},
        handoff=handoff,
        group=group,
        gid="g1",
    )

    target = group["entities"][0]
    target_label = f"{target['namespace']}/{target['name']}"
    assert target_label in scoped["question"]
    assert "other/pod-2" not in scoped["question"]
    assert "不查询其他 Pod" in scoped["question"]


def test_group_result_legacy_fallback_prefers_full_content_over_500_char_preview():
    group = _handoff(1)["issue_groups"][0]
    decisive = "dependency unavailable -> HTTP 503 -> Ready=False"
    result = ParallelEvidenceNode._build_group_result(
        "g1",
        group,
        {
            "evidence_analysis": json.dumps({"collection_summary": "采集完成"}),
            "thinking_events": [{
                "type": "ai_message",
                "content": "x" * 500,
                "full_content": "x" * 700 + decisive,
            }],
        },
        "run1",
    )

    assert decisive in result["summary"]
    assert result["legacy_text_fallback"] is True


def test_parallel_result_contains_four_dimensions_for_every_entity(monkeypatch):
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _FakeCollector,
    )
    node = ParallelEvidenceNode()
    node.workflow_config_override = {"evidence": {"parallel": {"max_concurrency": 2}}}
    node.tools = []
    result = node.execute({
        "question": "诊断",
        "run_id": "run-dimensions",
        "layer": Layer.ABNORMAL,
        "layer_handoff": _handoff(3),
        "thinking_events": [],
    })

    for group_result in result["group_results"]:
        entity = group_result["entities"][0]
        key = f"{entity['namespace']}/{entity['name']}"
        assert set(group_result["dimension_evidence_by_entity"][key]) >= {
            "kubernetes", "metrics", "logging", "tracing",
        }


def test_formal_group_rca_keeps_merged_entity_roots_separate(monkeypatch):
    fact_ids = {}

    class _MergedCollector(_FakeCollector):
        def execute(self, state):
            entities = state["layer_handoff"]["issue_groups"][0]["entities"]
            events = []
            tool_data = []
            messages = {
                "aiops-case-06": "exit 2 runtime process exiting",
                "aiops-case-10": "liveness HTTP 500 kubelet restart exit 137",
            }
            for entity in entities:
                message = messages[entity["namespace"]]
                entity_id = f"k8s.pod:{entity['namespace']}/{entity['name']}:uid"
                record = {
                    "entity_id": entity_id,
                    "entity_kind": "Pod", "namespace": entity["namespace"],
                    "entity_name": entity["name"], "dimension": "logging",
                    "fact_type": "log", "attribute": "log.message",
                    "value": message, "source_system": "elasticsearch",
                    "directness": "direct", "confidence": "high",
                    "strength": "strong",
                    "evidence_refs": [f"ref-{entity['namespace']}"],
                }
                fact_id = _canonical_fact_id(record)
                fact_ids[entity["namespace"]] = fact_id
                record["fact_id"] = fact_id
                ledger = {
                    "contract_version": "aiops.fact-ledger.v1",
                    "case_id": f"logs-{entity['namespace']}",
                    "scope_entity_ids": [entity_id],
                    "records": [record],
                    "record_count": 1,
                    "truncated": False,
                    "source": "mcp_canonical",
                    "legacy_contract": False,
                }
                tool_data.append({
                    "tool": "query_pod_logs",
                    "status": "success",
                    "fact_ledger": ledger,
                })
                events.append({
                    "type": "tool_result", "status": "success", "semantic_success": True,
                    "tool_name": "query_pod_logs",
                    "tool_args": {
                        "namespace": entity["namespace"], "pod": entity["name"],
                        "purpose": "根因日志",
                    },
                    "structured": {
                        "status": "query_succeeded", "dimension": "logging",
                        "coverage": "present", "source_system": "elasticsearch",
                        "entity": {
                            "namespace": entity["namespace"], "pod": entity["name"],
                            "pod_uid": f"uid-{fact_id}", "pod_ip": "172.16.1.9",
                        },
                        "fact_ledger": ledger,
                    },
                })
            return {
                "evidence_analysis": json.dumps({
                    "collection_summary": "采集完成",
                    "tool_data": tool_data,
                }),
                "thinking_events": events,
            }

    formal_rca_inputs = []

    class _FormalRCA:
        def __init__(self, *args, **kwargs):
            pass

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            formal_rca_inputs.append(state)
            entity = state["layer_handoff"]["issue_groups"][0]["entities"][0]
            fact_id = fact_ids[entity["namespace"]]
            root = (
                "runtime process exited with code 2"
                if entity["namespace"] == "aiops-case-06"
                else "liveness probe returned HTTP 500"
            )
            return {
                "root_cause": root,
                "causal_chain": {},
                "rca_analysis": json.dumps({
                    "diagnostic_status": "diagnosed",
                    "phenomenon": "one runtime symptom",
                    "root_cause": root,
                    "root_cause_summary": root,
                    "supporting_fact_ids": [fact_id],
                    "contradicting_fact_ids": [],
                    "unknowns": [],
                    "hypotheses": [],
                    "confidence": 0.88,
                    "confidence_reason": "validated per-entity fact references",
                    "claim_validation": {
                        "valid": True,
                        "valid_supporting_fact_ids": [fact_id],
                        "invalid_fact_ids": [],
                    },
                }),
                "thinking_events": state.get("thinking_events", []),
            }

    handoff = {
        "layer": "ABNORMAL",
        "issue_groups": [{
            "group_id": "g1", "status_keywords": ["CrashLoopBackOff", "RecentRestart"],
            "pod_abnormal_type": "RuntimeFailure",
            "entities": [
                {"kind": "Pod", "namespace": "aiops-case-06", "name": "crash"},
                {"kind": "Pod", "namespace": "aiops-case-10", "name": "probe"},
            ],
        }],
    }
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _MergedCollector,
    )
    import app.core.workflow.nodes.parallel_evidence as parallel_module
    monkeypatch.setattr(parallel_module, "RootCauseAnalyzerNode", _FormalRCA, raising=False)
    node = ParallelEvidenceNode()
    node.ai_call = object()
    node.tools = []
    result = node.execute({
        "question": "诊断", "run_id": "run-merged", "layer": Layer.ABNORMAL,
        "layer_handoff": handoff, "thinking_events": [],
    })

    summaries = {
        f"{item['namespace']}/{item['name']}": item
        for group_result in result["group_results"]
        for item in group_result["entity_summaries"]
    }
    assert summaries["aiops-case-06/crash"]["supporting_fact_ids"] == [
        fact_ids["aiops-case-06"]
    ]
    assert summaries["aiops-case-10/probe"]["supporting_fact_ids"] == [
        fact_ids["aiops-case-10"]
    ]
    assert "OOM" not in summaries["aiops-case-10/probe"]["root_cause"]
    assert len(formal_rca_inputs) == 2
    assert all(
        group_result["diagnostic_status"] == "diagnosed"
        for group_result in result["group_results"]
    )
    assert all(
        json.loads(group_result["rca_analysis"])["claim_validation"]["valid"] is True
        for group_result in result["group_results"]
    )


def test_multi_entity_issue_group_executes_one_collector_and_rca_per_pod(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    collector_scopes = []
    rca_scopes = []

    class _AtomicCollector:
        def __init__(self, *args, **kwargs):
            self.current_run_id = ""

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            entity = state["layer_handoff"]["issue_groups"][0]["entities"][0]
            collector_scopes.append((entity["namespace"], entity["name"]))
            entity_id = f"k8s.pod:{entity['namespace']}/{entity['name']}:uid"
            record = {
                "entity_id": entity_id,
                "entity_kind": "Pod",
                "namespace": entity["namespace"],
                "entity_name": entity["name"],
                "dimension": "kubernetes",
                "fact_type": "event",
                "attribute": "event.message",
                "value": f"source-backed failure for {entity['name']}",
                "source_system": "kubernetes",
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
                "evidence_refs": [f"kubernetes://events/{entity['name']}"],
            }
            record["fact_id"] = _canonical_fact_id(record)
            ledger = {
                "contract_version": "aiops.fact-ledger.v1",
                "case_id": f"lifecycle-{entity['name']}",
                "scope_entity_ids": [entity_id],
                "records": [record],
                "record_count": 1,
                "truncated": False,
                "source": "mcp_canonical",
                "legacy_contract": False,
            }
            return {
                "evidence_analysis": json.dumps({
                    "collection_summary": "collected",
                    "plan_completeness": 1.0,
                    "tool_data": [{
                        "tool": "kubectl_events",
                        "status": "success",
                        "fact_ledger": ledger,
                    }],
                }),
                "thinking_events": [],
            }

    class _AtomicRCA:
        def __init__(self, *args, **kwargs):
            pass

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            entity = state["layer_handoff"]["issue_groups"][0]["entities"][0]
            rca_scopes.append((entity["namespace"], entity["name"]))
            analysis = json.loads(state["evidence_analysis"])
            fact_id = analysis["tool_data"][0]["fact_ledger"]["records"][0]["fact_id"]
            return {"rca_analysis": json.dumps({
                "diagnostic_status": "diagnosed",
                "phenomenon": "abnormal Pod",
                "root_cause": f"root for {entity['name']}",
                "root_cause_summary": f"root for {entity['name']}",
                "supporting_fact_ids": [fact_id],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "hypotheses": [],
                "confidence": 0.9,
                "confidence_reason": "source-backed",
                "claim_validation": {
                    "valid": True,
                    "valid_supporting_fact_ids": [fact_id],
                    "invalid_fact_ids": [],
                },
            })}

    handoff = {
        "layer": "ABNORMAL",
        "issue_groups": [{
            "group_id": "g-container-creating",
            "status_keywords": ["ContainerCreating"],
            "pod_abnormal_type": "PreRuntimeFailure",
            "entities": [
                {"kind": "Pod", "namespace": "case-03", "name": "failed-mount"},
                {"kind": "Pod", "namespace": "case-05", "name": "sandbox"},
            ],
        }],
    }
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _AtomicCollector,
    )
    import app.core.workflow.nodes.parallel_evidence as parallel_module
    monkeypatch.setattr(parallel_module, "RootCauseAnalyzerNode", _AtomicRCA)

    node = ParallelEvidenceNode()
    node.ai_call = object()
    node.tools = []
    result = node.execute({
        "question": "诊断",
        "run_id": "run-atomic",
        "layer": Layer.ABNORMAL,
        "layer_handoff": handoff,
        "thinking_events": [],
    })

    expected = {("case-03", "failed-mount"), ("case-05", "sandbox")}
    assert set(collector_scopes) == expected
    assert set(rca_scopes) == expected
    assert len(result["group_results"]) == 2
    assert all(len(item["entities"]) == 1 for item in result["group_results"])
    assert {
        item["parent_group_id"] for item in result["group_results"]
    } == {"g-container-creating"}
    assert all(
        item["entity_summaries"][0]["diagnostic_status"] == "diagnosed"
        for item in result["group_results"]
    )
    from app.core.workflow.lane_diagnosis_artifact import (
        LaneDiagnosisArtifactWriter,
    )
    for item in result["group_results"]:
        artifact = item["lane_diagnosis_artifact"]
        assert artifact["contract_version"] == (
            "aiops.lane-diagnosis-artifact.v2"
        )
        reloaded = LaneDiagnosisArtifactWriter(
            item["archive_run_id"]
        ).reload_and_verify(artifact)
        assert reloaded["snapshot"]["contract_version"] == (
            "aiops.entity-evidence-snapshot.v1"
        )
        assert item["lane_diagnosis_artifact_ref"] == artifact["artifact_ref"]


def test_multi_group_report_renders_readable_four_dimension_entity_card():
    class _AI:
        def call_simple(self, **kwargs):
            return "# 多异常诊断结论\n\n已按实体完成分析。"

    node = ConclusionFormatterNode()
    node.ai_call = _AI()
    dimensions = {
        "kubernetes": {
            "dimension": "kubernetes", "status": "present", "source_systems": ["kubernetes"],
            "query_count": 2, "present_query_count": 2, "empty_query_count": 0,
            "facts": [{"fact_id": "fact-k8s", "source_system": "kubernetes",
                       "value": "Ready=False; readiness probe HTTP 503", "evidence_refs": []}],
            "limitations": [],
        },
        "metrics": {
            "dimension": "metrics", "status": "present", "source_systems": ["prometheus"],
            "query_count": 1, "present_query_count": 1, "empty_query_count": 0,
            "facts": [{"fact_id": "fact-metric", "source_system": "prometheus",
                       "value": "kube_pod_container_status_ready = 0", "evidence_refs": ["metric-ref"]}],
            "limitations": [],
        },
        "logging": {
            "dimension": "logging", "status": "present", "source_systems": ["elasticsearch"],
            "query_count": 2, "present_query_count": 1, "empty_query_count": 1,
            "facts": [{"fact_id": "fact-log", "source_system": "elasticsearch",
                       "value": "dependency unavailable -> HTTP 503", "evidence_refs": ["log-ref"]}],
            "limitations": ["另有 1 次补充查询未命中，但不覆盖已采集真实事实"],
        },
        "tracing": {
            "dimension": "tracing", "status": "present", "source_systems": ["deepflow", "tempo"],
            "query_count": 1, "present_query_count": 1, "empty_query_count": 0,
            "facts": [{"fact_id": "fact-trace", "source_system": "deepflow",
                       "value": "GET /work -> HTTP 503 trace_id=abc", "evidence_refs": ["trace-ref"]}],
            "limitations": [],
        },
    }
    group_results = [{
        "group_id": "g7", "pod_abnormal_type": "NotReadyProbeFailed",
        "status_keywords": ["NotReady"],
        "entities": [{"kind": "Pod", "namespace": "aiops-case-09", "name": "workload"}],
        "entity_summaries": [{
            "namespace": "aiops-case-09", "name": "workload",
            "status": "Running / Ready=False", "phenomenon": "readiness probe HTTP 503",
            "root_cause": "dependency unavailable",
            "causal_chain": ["dependency unavailable", "HTTP 503", "Ready=False"],
            "confidence": 0.96,
            "supporting_fact_ids": ["fact-log", "fact-trace"],
            "contradicting_fact_ids": [], "unknowns": [],
        }],
        "dimension_evidence_by_entity": {"aiops-case-09/workload": dimensions},
        "rca_analysis": json.dumps({
            "diagnostic_status": "diagnosed",
            "root_cause": "dependency unavailable",
            "root_cause_summary": "dependency unavailable",
            "supporting_fact_ids": ["fact-log", "fact-trace"],
            "contradicting_fact_ids": [],
            "confidence": 0.96,
            "claim_validation": {
                "valid": True,
                "valid_supporting_fact_ids": ["fact-log", "fact-trace"],
                "invalid_fact_ids": [],
                "reasons": [],
            },
        }),
        "summary": "legacy summary must not be authoritative",
        "collection_summary": "采集完成", "completeness": 1.0,
        "thinking_events": [{
            "type": "tool_result", "status": "success", "tool_name": "query_pod_logs",
            "node": "evidence", "tool_args": {"namespace": "aiops-case-09", "pod": "workload"},
            "structured": {"dimension": "logging", "coverage": "present", "facts": [{
                "name": "log.message", "dimension": "logging",
                "value": "dependency unavailable", "source_system": "elasticsearch",
            }]},
        }],
        "archive_run_id": "run-g7", "error": None,
    }]

    report = node.execute({
        "question": "检查异常", "layer": Layer.ABNORMAL,
        "group_results": group_results, "thinking_events": [],
    })["conclusion"]

    assert "## 异常组 g7 · aiops-case-09/workload" in report
    assert "**根因**：dependency unavailable" in report
    assert "| Kubernetes | present |" in report
    assert "| Metrics | present |" in report
    assert "| Logging | present |" in report
    assert "| Tracing | present |" in report
    assert "GET /work -> HTTP 503 trace_id=abc" in report
    assert "补充查询未命中" in report
    assert "<details>" in report and "逐工具原始证据" in report
    assert "run-g7" in report


def test_multi_group_entity_card_ranks_all_rca_referenced_facts_before_context():
    node = ConclusionFormatterNode()
    dimensions = {
        dimension: {
            "dimension": dimension,
            "status": "absent",
            "source_systems": [],
            "query_count": 0,
            "present_query_count": 0,
            "empty_query_count": 0,
            "facts": [],
            "limitations": [],
        }
        for dimension in ("kubernetes", "metrics", "logging", "tracing")
    }
    dimensions["metrics"] = {
        **dimensions["metrics"],
        "status": "present",
        "source_systems": ["prometheus"],
        "query_count": 1,
        "present_query_count": 1,
        "facts": [
            {
                "fact_id": "fact-context-restarts",
                "source_system": "prometheus",
                "dimension": "metrics",
                "attribute": "kube_pod_container_status_restarts_total",
                "value": "10",
                "display_value": "kube_pod_container_status_restarts_total=10 count（持平）",
                "directness": "direct",
                "confidence": "high",
                "strength": "context",
                "evidence_refs": ["metric://restarts"],
            },
            {
                "fact_id": "fact-decisive-reason",
                "source_system": "prometheus",
                "dimension": "metrics",
                "attribute": "kube_pod_container_status_last_terminated_reason",
                "value": "1",
                "display_value": (
                    "kube_pod_container_status_last_terminated_reason=1 unitless"
                    "（reason=OOMKilled，持平）"
                ),
                "metadata": {"labels": {"reason": "OOMKilled"}},
                "directness": "direct",
                "confidence": "high",
                "strength": "strong",
                "evidence_refs": ["metric://reason"],
            },
        ],
    }
    group = {
        "group_id": "g1",
        "entities": [{"kind": "Pod", "namespace": "aiops-case-08", "name": "workload"}],
        "entity_summaries": [{
            "namespace": "aiops-case-08",
            "name": "workload",
            "status": "CrashLoopBackOff",
            "phenomenon": "container repeatedly terminated",
            "root_cause": "memory limit exceeded",
            "causal_chain": ["memory pressure", "OOMKilled", "restart backoff"],
            "confidence": 0.95,
            "supporting_fact_ids": ["fact-decisive-reason"],
            "contradicting_fact_ids": [],
            "unknowns": [],
        }],
        "dimension_evidence_by_entity": {"aiops-case-08/workload": dimensions},
        "archive_run_id": "run-g1",
        "thinking_events": [],
    }

    report = node.execute({
        "question": "检查异常",
        "layer": Layer.ABNORMAL,
        "group_results": [group],
        "thinking_events": [],
    })["conclusion"]

    decisive_index = report.index("reason=OOMKilled")
    context_index = report.index("restarts_total=10")
    assert decisive_index < context_index
    assert "fact-decisive-reason" in report


def test_multi_group_entity_card_labels_negative_observation_after_causal_facts():
    facts = [
        {
            "fact_id": "fact-node-lost-zero",
            "source_system": "prometheus",
            "dimension": "metrics",
            "attribute": "kube_pod_status_reason",
            "value": "0",
            "display_value": "kube_pod_status_reason=0（reason=NodeLost）",
            "evidence_role": "negative_observation",
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
        },
        {
            "fact_id": "fact-restarts",
            "source_system": "prometheus",
            "dimension": "metrics",
            "attribute": "kube_pod_container_status_restarts_total",
            "value": "10",
            "display_value": "kube_pod_container_status_restarts_total=10",
            "evidence_role": "symptom",
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
        },
        {
            "fact_id": "fact-liveness-http-500",
            "source_system": "kubernetes",
            "dimension": "kubernetes",
            "attribute": "event.message",
            "value": "Liveness probe failed: HTTP 500",
            "display_value": "event.message=Liveness probe failed: HTTP 500",
            "evidence_role": "causal_candidate",
            "directness": "direct",
            "confidence": "high",
            "strength": "strong",
        },
    ]
    ordered = ConclusionFormatterNode._select_multi_group_display_facts(
        facts,
        {"supporting_fact_ids": [], "contradicting_fact_ids": []},
    )

    assert [item["fact_id"] for item in ordered] == [
        "fact-liveness-http-500",
        "fact-restarts",
        "fact-node-lost-zero",
    ]

    dimensions = {
        name: {
            "dimension": name,
            "status": "present" if name == "metrics" else "absent",
            "facts": facts if name == "metrics" else [],
            "limitations": [],
        }
        for name in ("kubernetes", "metrics", "logging", "tracing")
    }
    report = ConclusionFormatterNode._render_multi_group_entity_cards([{
        "group_id": "g1",
        "entity_summaries": [{
            "namespace": "demo",
            "name": "workload",
            "root_cause": "证据不足",
            "supporting_fact_ids": [],
            "contradicting_fact_ids": [],
        }],
        "dimension_evidence_by_entity": {"demo/workload": dimensions},
    }])

    assert "负向观测/排除" in report
    assert report.index("HTTP 500") < report.index("restarts_total=10")
    assert report.index("restarts_total=10") < report.index("reason=NodeLost")


def test_single_entity_group_uses_formal_top_level_rca_as_authority():
    node = ParallelEvidenceNode()
    group = {
        "group_id": "g1",
        "status_keywords": ["CrashLoopBackOff"],
        "entities": [{"kind": "Pod", "namespace": "aiops-case-08", "name": "workload"}],
    }
    result = {
        "group_id": "g1",
        "summary": "collector interpretation",
        "dimension_evidence_by_entity": {
            "aiops-case-08/workload": {
                "kubernetes": {"facts": [{
                    "fact_id": "fact-primary-evidence",
                    "entity_id": "k8s.pod:aiops-case-08/workload:uid",
                    "value": "Reason=OOMKilled",
                }]},
            },
        },
    }
    rca_update = {
        "rca_analysis": json.dumps({
            "diagnostic_status": "diagnosed",
            "phenomenon": "container restart loop",
            "root_cause": "validated memory limit exhaustion",
            "root_cause_summary": "validated memory limit exhaustion",
            "supporting_fact_ids": ["fact-primary-evidence"],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "hypotheses": [{
                "hypothesis_id": "h-alternative",
                "entity_id": "k8s.pod:aiops-case-08/workload:uid",
                "summary": "alternative hypothesis must not replace selected root",
                "supporting_fact_ids": ["fact-primary-evidence"],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.6,
            }],
            "confidence": 0.95,
            "confidence_reason": "formal validation selected the top-level conclusion",
            "claim_validation": {"valid": True},
        }),
    }

    node._attach_validated_diagnosis(result, group, rca_update)

    summary = result["entity_summaries"][0]
    assert summary["root_cause"] == "validated memory limit exhaustion"
    assert summary["confidence"] == 0.95


def test_group_result_uses_same_canonical_kubernetes_fact_registry_as_rca():
    """Report projection must not mint a second ID for an RCA-backed fact."""
    entity_id = "k8s.pod:aiops-case-10/workload:uid-c10"
    group = {
        "group_id": "g10",
        "status_keywords": ["CrashLoopBackOff", "Unhealthy"],
        "pod_abnormal_type": "RuntimeFailure",
        "entities": [{
            "kind": "Pod",
            "namespace": "aiops-case-10",
            "name": "workload",
        }],
    }
    canonical_record = {
        "entity_id": entity_id,
        "entity_kind": "Pod",
        "namespace": "aiops-case-10",
        "entity_name": "workload",
        "dimension": "kubernetes",
        "fact_type": "event",
        "attribute": "event.message",
        "value": "Liveness probe failed: HTTP probe returned statuscode: 500",
        "source_system": "kubernetes",
        "directness": "direct",
        "confidence": "high",
        "strength": "strong",
        "evidence_refs": ["kubernetes://event/liveness-failure"],
    }
    fact_id = _canonical_fact_id(canonical_record)
    canonical_record["fact_id"] = fact_id
    canonical_ledger = {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": "canonical-kubernetes-lifecycle",
        "scope_entity_ids": [entity_id],
        "records": [canonical_record],
        "record_count": 1,
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }
    group_state = {
        "evidence_analysis": json.dumps({
            "collection_summary": "Kubernetes lifecycle collected",
            "plan_completeness": 1.0,
            "tool_data": [{
                "tool": "kubectl_events",
                "status": "success",
                "fact_ledger": canonical_ledger,
            }],
        }),
        # Audit event intentionally has no embedded ledger. The old report
        # projector hashes this message into a new fact-k8s-* identifier.
        "thinking_events": [{
            "type": "tool_result",
            "status": "success",
            "semantic_success": True,
            "tool_name": "kubectl_events",
            "tool_args": {
                "namespace": "aiops-case-10",
                "resource_name": "workload",
            },
            "structured": {
                "status": "events_found",
                "selected_events": [
                    "Liveness probe failed: HTTP probe returned statuscode: 500"
                ],
            },
        }],
    }

    result = ParallelEvidenceNode._build_group_result(
        "g10", group, group_state, "run-authoritative",
    )
    facts = result["dimension_evidence_by_entity"][
        "aiops-case-10/workload"
    ]["kubernetes"]["facts"]

    assert [fact["fact_id"] for fact in facts] == [fact_id]

    ParallelEvidenceNode()._attach_validated_diagnosis(
        result,
        group,
        {"rca_analysis": json.dumps({
            "diagnostic_status": "diagnosed",
            "phenomenon": "container repeatedly restarted",
            "root_cause": "liveness endpoint returned HTTP 500",
            "root_cause_summary": "liveness endpoint returned HTTP 500",
            "supporting_fact_ids": [fact_id],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "hypotheses": [],
            "confidence": 0.94,
            "confidence_reason": "canonical Kubernetes event",
            "claim_validation": {
                "valid": True,
                "valid_supporting_fact_ids": [fact_id],
                "invalid_fact_ids": [],
            },
        })},
    )

    summary = result["entity_summaries"][0]
    assert summary["diagnostic_status"] == "diagnosed"
    assert summary["supporting_fact_ids"] == [fact_id]


def test_parallel_middle_worker_exception_persists_error_lane_in_order(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    class _MiddleFailingCollector:
        def __init__(self, *args, **kwargs):
            self.current_run_id = ""

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            group_id = state["layer_handoff"]["issue_groups"][0]["group_id"]
            if group_id == "g2":
                raise RuntimeError("middle lane exploded")
            return {
                "evidence_analysis": json.dumps({
                    "collection_summary": "collected",
                    "plan_completeness": 1.0,
                }),
                "thinking_events": [],
            }

    class _InconclusiveRCA:
        def __init__(self, *args, **kwargs):
            pass

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            return {
                "rca_analysis": json.dumps({
                    "diagnostic_status": "inconclusive",
                    "supporting_fact_ids": [],
                    "contradicting_fact_ids": [],
                    "unknowns": ["no causal facts"],
                    "claim_validation": {"valid": False},
                }),
            }

    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _MiddleFailingCollector,
    )
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.RootCauseAnalyzerNode",
        _InconclusiveRCA,
    )
    node = ParallelEvidenceNode()
    node.tools = []

    result = node.execute({
        "question": "diagnose all lanes",
        "run_id": "run-terminal",
        "layer": Layer.ABNORMAL,
        "layer_handoff": _handoff(3),
        "thinking_events": [],
    })

    assert [item["group_id"] for item in result["group_results"]] == [
        "g1",
        "g2",
        "g3",
    ]
    assert len(result["group_results"]) == 3
    failed = result["group_results"][1]
    assert failed["terminal_status"] == "error"
    assert failed["terminal_error"]["stage"] == "evidence_collection"
    assert failed["terminal_error"]["message"] == "middle lane exploded"
    assert failed["lane_diagnosis_artifact_ref"]

    from app.core.workflow.lane_diagnosis_artifact import (
        LaneDiagnosisArtifactWriter,
    )

    reloaded = LaneDiagnosisArtifactWriter(
        failed["archive_run_id"]
    ).reload_and_verify(failed["lane_diagnosis_artifact"])
    assert reloaded["terminal_error"] == failed["terminal_error"]
    assert [artifact["group_id"] for artifact in result["authoritative_lane_artifacts"]] == [
        "g1",
        "g2",
        "g3",
    ]


def test_parallel_error_artifact_persistence_failure_is_not_claimed_successful(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    class _FailingCollector:
        def __init__(self, *args, **kwargs):
            pass

        def set_event_queue(self, queue):
            self.queue = queue

        def execute(self, state):
            raise RuntimeError("lane execution failed")

    def _fail_persistence(*args, **kwargs):
        raise OSError("archive unavailable")

    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.EvidenceCollectorNode",
        _FailingCollector,
    )
    monkeypatch.setattr(
        "app.core.workflow.nodes.parallel_evidence.LaneDiagnosisArtifactWriter.persist",
        _fail_persistence,
    )
    node = ParallelEvidenceNode()
    node.tools = []

    result = node.execute({
        "question": "diagnose",
        "run_id": "run-persist-failure",
        "layer": Layer.ABNORMAL,
        "layer_handoff": _handoff(1),
        "thinking_events": [],
    })

    failed = result["group_results"][0]
    assert failed["terminal_status"] == "error"
    assert failed["artifact_persistence_error"] == "archive unavailable"
    assert "lane_diagnosis_artifact" not in failed
    assert "lane_diagnosis_artifact_ref" not in failed
    assert result["authoritative_lane_artifacts"] == []
    assert any("archive unavailable" in message for message in result["errors"])
