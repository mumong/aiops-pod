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
    """conclusion 多组模式：LLM 写结论 + 代码拼接各组真实数据，一组都不能丢。"""
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
    # LLM 只调一次（读所有组摘要）
    assert len(calls) == 1
    # 三组真实 metric 值都被代码确定性拼接进报告（一组不丢）
    assert "10000" in report and "20000" in report and "30000" in report
    # 各组归档引用都在
    for i in range(1, 4):
        assert f"run1-g{i}" in report
    # LLM 结论也在
    assert "集群多异常诊断概览" in report


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
    assert "确定性回退模板" in result["conclusion"]
    assert "ns-1 根因内存超限" in result["conclusion"]


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


def test_structured_group_diagnosis_keeps_merged_entity_roots_separate(monkeypatch):
    class _MergedCollector(_FakeCollector):
        def execute(self, state):
            entities = state["layer_handoff"]["issue_groups"][0]["entities"]
            events = []
            for entity, fact_id, message in (
                (entities[0], "fact-c06", "exit 2 runtime process exiting"),
                (entities[1], "fact-c10", "liveness HTTP 500 kubelet restart exit 137"),
            ):
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
                        "fact_ledger": {
                            "records": [{
                                "fact_id": fact_id,
                                "entity_id": f"k8s.pod:{entity['namespace']}/{entity['name']}:uid",
                                "entity_kind": "Pod", "namespace": entity["namespace"],
                                "entity_name": entity["name"], "dimension": "logging",
                                "fact_type": "log", "attribute": "log.message",
                                "value": message, "source_system": "elasticsearch",
                                "evidence_refs": [f"ref-{fact_id}"],
                            }],
                        },
                    },
                })
            return {
                "evidence_analysis": json.dumps({"collection_summary": "采集完成"}),
                "thinking_events": events,
            }

    class _StructuredAI:
        def call_structured(self, **kwargs):
            schema = kwargs["schema"]
            return schema.model_validate({
                "entities": [
                    {
                        "namespace": "aiops-case-06", "name": "crash",
                        "status": "CrashLoopBackOff", "phenomenon": "exit 2",
                        "root_cause": "runtime process exited",
                        "causal_chain": ["runtime error", "exit 2", "restart"],
                        "confidence": 0.9, "supporting_fact_ids": ["fact-c06"],
                    },
                    {
                        "namespace": "aiops-case-10", "name": "probe",
                        "status": "RecentRestart", "phenomenon": "liveness HTTP 500",
                        "root_cause": "liveness probe failure",
                        "causal_chain": ["HTTP 500", "kubelet restart"],
                        "confidence": 0.9, "supporting_fact_ids": ["fact-c10"],
                    },
                ],
            }), "structured"

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
    node = ParallelEvidenceNode()
    node.ai_call = _StructuredAI()
    node.tools = []
    result = node.execute({
        "question": "诊断", "run_id": "run-merged", "layer": Layer.ABNORMAL,
        "layer_handoff": handoff, "thinking_events": [],
    })

    summaries = {
        f"{item['namespace']}/{item['name']}": item
        for item in result["group_results"][0]["entity_summaries"]
    }
    assert summaries["aiops-case-06/crash"]["supporting_fact_ids"] == ["fact-c06"]
    assert summaries["aiops-case-10/probe"]["supporting_fact_ids"] == ["fact-c10"]
    assert "OOM" not in summaries["aiops-case-10/probe"]["root_cause"]


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
