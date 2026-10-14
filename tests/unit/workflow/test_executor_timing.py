import json
import os
import sys
import time
import types
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.service import HolmesService
from app.core.skills.models import EvidenceItem, EvidenceLevel
from app.core.workflow.executor import WorkflowExecutor, _missing_structured_actions_reason
from app.core.workflow.metrics import WorkflowMetrics
from app.core.workflow.nodes.autonomous_parallel import LaneQueue


def _install_fake_langfuse(monkeypatch):
    calls = {"sessions": []}

    @contextmanager
    def _propagate_attributes(**kwargs):
        calls["sessions"].append(kwargs.get("session_id"))
        yield

    fake_langfuse = types.ModuleType("langfuse")
    fake_langfuse.propagate_attributes = _propagate_attributes
    monkeypatch.setitem(sys.modules, "langfuse", fake_langfuse)
    return calls


class _DummyNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.node_name = node_id
        self._event_queue = None

    def set_event_queue(self, q):
        self._event_queue = q


class _DummyWorkflow:
    def __init__(self, nodes):
        self._nodes = {node.node_id: node for node in nodes}

    def _run_node(self, node_id, sleep_seconds, state_update):
        node = self._nodes[node_id]
        event_queue = node._event_queue

        event_queue.put((
            "node_lifecycle",
            {
                "phase": "start",
                "node": node.node_id,
                "node_name": node.node_name,
                "ts": time.time(),
            },
        ))
        time.sleep(sleep_seconds)
        event_queue.put((
            "node_lifecycle",
            {
                "phase": "end",
                "node": node.node_id,
                "node_name": node.node_name,
                "ts": time.time(),
                "success": True,
                "state_update": state_update,
            },
        ))
        return state_update

    def stream(self, initial_state):
        yield {"rca": self._run_node("rca", 0.02, {
            "root_cause": "simulated-rca",
            "rca_analysis": "{}",
        })}
        yield {"conclusion": self._run_node("conclusion", 0.03, {
            "conclusion": "simulated conclusion",
            "conclusion_formatted": "simulated conclusion",
        })}


class _DummyHolmesService:
    merged_catalog = None
    workflow_config = {"nodes": {"layer": False, "evidence": False, "rca": True, "conclusion": True}}


def test_executor_join_helper_never_joins_current_thread():
    import threading

    alive = WorkflowExecutor._join_worker_if_needed(
        threading.current_thread(),
        timeout=5,
    )

    assert alive is True


def test_executor_join_helper_keeps_bounded_join_for_other_worker(monkeypatch):
    class _Worker:
        def __init__(self):
            self.alive = True
            self.join_calls = []

        def is_alive(self):
            return self.alive

        def join(self, *, timeout):
            self.join_calls.append(timeout)
            self.alive = False

    worker = _Worker()
    monkeypatch.setattr(
        "app.core.workflow.executor.threading.current_thread",
        lambda: object(),
    )

    alive = WorkflowExecutor._join_worker_if_needed(
        worker,
        timeout=5,
    )

    assert alive is False
    assert worker.join_calls == [5]


def test_executor_preserves_setup_error_before_worker_creation(monkeypatch):
    class _FailingNode(_DummyNode):
        def set_event_queue(self, q):
            if q is not None:
                raise RuntimeError("event queue setup failed")
            super().set_event_queue(q)

    node = _FailingNode("rca")
    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _DummyWorkflow([node]),
            [node],
        ),
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("setup failure"))

    error_event = next(event for event in events if event.get("type") == "error")
    assert error_event["error"] == "event queue setup failed"


def test_executor_sse_sanitizes_llm_disconnect_and_retains_log(monkeypatch, caplog):
    import httpx
    from openai import APIError
    message = 'stream disconnected before completion: stream closed before response.completed'

    class FailingNode(_DummyNode):
        def set_event_queue(self, queue):
            if queue is not None:
                raise APIError(message, request=httpx.Request('POST', 'https://model.invalid'), body=None)

    node = FailingNode('conclusion')
    monkeypatch.setattr('app.core.workflow.executor.build_diagnosis_workflow',
        lambda *args, **kwargs: (_DummyWorkflow([node]), [node]))
    events = list(WorkflowExecutor(holmes_service=_DummyHolmesService()).execute_stream('test'))
    error = next(event for event in events if event['type'] == 'error')
    assert 'LLM API 服务连接中断' in error['error']
    assert 'stream disconnected' not in error['error']
    assert message in caplog.text


def test_executor_tracks_non_streaming_final_node_duration(monkeypatch):
    nodes = [_DummyNode("rca"), _DummyNode("conclusion")]

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _DummyWorkflow(nodes),
            nodes,
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("timing test"))
    final_event = next(event for event in events if event.get("type") == "final")
    node_metrics = final_event["metrics"]["nodes"]

    assert 15 <= node_metrics["rca"]["duration_ms"] <= 40
    assert node_metrics["conclusion"]["duration_ms"] >= 25
    assert node_metrics["conclusion"]["duration_ms"] > node_metrics["rca"]["duration_ms"]


def test_executor_appends_deterministic_timing_and_runbook_trace(monkeypatch):
    nodes = [_DummyNode("rca"), _DummyNode("conclusion")]

    class _RunbookWorkflow(_DummyWorkflow):
        def stream(self, initial_state):
            yield {"rca": self._run_node("rca", 0.02, {
                "root_cause": "simulated-rca",
                "rca_analysis": "{}",
                "thinking_events": [
                    {
                        "type": "tool_start",
                        "tool_name": "fetch_runbook",
                        "tool_call_id": "call-runbook",
                        "tool_args": {"runbook_id": "pod-oomkilled"},
                    },
                    {
                        "type": "tool_result",
                        "tool_name": "fetch_runbook",
                        "tool_call_id": "call-runbook",
                        "status": "success",
                        "result_preview": "# Pod OOMKilled 诊断手册\n检查内存限制。",
                    },
                ],
            })}
            yield {"conclusion": self._run_node("conclusion", 0.03, {
                "conclusion": "simulated conclusion",
                "conclusion_formatted": "simulated conclusion",
            })}

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _RunbookWorkflow(nodes),
            nodes,
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )
    monkeypatch.setattr("app.core.workflow.metrics.METRICS_ENABLED", False)

    events = list(WorkflowExecutor(
        holmes_service=_DummyHolmesService(),
    ).execute_stream("timing and runbook trace"))
    final_event = next(event for event in events if event.get("type") == "final")
    answer = final_event["answer"]

    assert answer.startswith("simulated conclusion")
    assert "## 📊 性能统计" in answer
    assert "├─ 总耗时:" in answer
    assert "📋 Runbook 参考" in answer
    assert "- pod-oomkilled" in answer
    assert "未归属 lane" not in answer
    assert "LLM 调用" not in answer
    assert "工具调用" not in answer
    assert "## 📈 质量指标" not in answer


def test_executor_propagates_langfuse_session_at_workflow_boundary(monkeypatch):
    langfuse_calls = _install_fake_langfuse(monkeypatch)
    nodes = [_DummyNode("rca"), _DummyNode("conclusion")]

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _DummyWorkflow(nodes),
            nodes,
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("timing test", run_id="workflow-session-1"))

    assert any(event.get("type") == "run_start" for event in events)
    assert langfuse_calls["sessions"] == ["workflow-session-1"]


def test_executor_assigns_same_run_id_to_all_four_nodes_without_ai_call(monkeypatch):
    nodes = [_DummyNode("layer"), _DummyNode("evidence"), _DummyNode("rca"), _DummyNode("conclusion")]

    class _NoopWorkflow:
        def stream(self, initial_state):
            return iter([])

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _NoopWorkflow(),
            nodes,
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    list(executor.execute_stream("timing test", run_id="workflow-session-4"))

    assert [getattr(node, "current_run_id", None) for node in nodes] == [
        "workflow-session-4",
        "workflow-session-4",
        "workflow-session-4",
        "workflow-session-4",
    ]


def test_executor_assigns_same_run_id_and_ai_call_to_all_four_nodes(monkeypatch):
    nodes = [_DummyNode("layer"), _DummyNode("evidence"), _DummyNode("rca"), _DummyNode("conclusion")]

    class _NoopWorkflow:
        def stream(self, initial_state):
            return iter([])

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _NoopWorkflow(),
            nodes,
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    executor.ai_call = object()
    executor.mcp_tools = ["tool-a"]
    list(executor.execute_stream("timing test", run_id="workflow-session-5"))

    assert [getattr(node, "current_run_id", None) for node in nodes] == [
        "workflow-session-5",
        "workflow-session-5",
        "workflow-session-5",
        "workflow-session-5",
    ]
    assert all(getattr(node, "ai_call", None) is executor.ai_call for node in nodes)
    assert all(getattr(node, "tools", None) == ["tool-a"] for node in nodes)


def test_executor_langfuse_session_scope_preserves_original_exception(monkeypatch):
    _install_fake_langfuse(monkeypatch)
    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())

    with pytest.raises(ValueError, match="workflow failed"):
        with executor._langfuse_session_scope("workflow-session-error"):
            raise ValueError("workflow failed")


def test_executor_evidence_snapshot_is_json_serializable():
    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    snapshot = executor._extract_state_snapshot(
        {
            "evidence_completeness": 0.5,
            "evidence_analysis": '{"plan_total":2,"plan_collected":1}',
            "evidence_items": [
                EvidenceItem(
                    id="e1",
                    description="pod yaml",
                    level=EvidenceLevel.CRITICAL,
                    collected=True,
                    value="ok",
                    source="thinking_match",
                ),
                EvidenceItem(
                    id="e2",
                    description="pod events",
                    level=EvidenceLevel.IMPORTANT,
                    collected=False,
                    source="planned",
                ),
            ],
        },
        "evidence",
    )

    assert snapshot["evidence_count"] == 2
    assert snapshot["collected_count"] == 1
    assert snapshot["evidence_items"][0]["id"] == "e1"
    assert snapshot["evidence_items"][0]["level"] == "critical"
    assert snapshot["evidence_items"][1]["collected"] is False
    json.dumps(snapshot, ensure_ascii=False)


class _ParallelLifecycleWorkflow:
    def __init__(self, node):
        self._node = node

    def stream(self, initial_state):
        event_queue = self._node._event_queue
        now = time.time()
        event_queue.put((
            "node_lifecycle",
            {
                "phase": "start",
                "node": "parallel_evidence",
                "node_name": "parallel-evidence-name",
                "ts": now,
            },
        ))
        scoped_queue = LaneQueue(
            event_queue,
            group_id="g3",
            entities=[{"kind": "Pod", "namespace": "ns", "name": "pod"}],
        )
        scoped_queue.put((
            "thinking",
            {
                "type": "ai_message",
                "node": "rca",
                "content": "lane analysis",
            },
        ))
        state_update = {
            "autonomous_group_results": [{
                "group_id": "g3",
                "target": {"group_id": "g3"},
                "status": "completed",
                "error": None,
                "run_id": "lane-g3",
            }],
        }
        event_queue.put((
            "node_lifecycle",
            {
                "phase": "end",
                "node": "parallel_evidence",
                "node_name": "parallel-evidence-name",
                "ts": now + 0.01,
                "success": True,
                "state_update": state_update,
            },
        ))
        yield {"parallel_evidence": state_update}


def test_executor_archives_parallel_group_state_only_after_lifecycle_end(monkeypatch):
    node = _DummyNode("parallel_evidence")
    archives = []
    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _ParallelLifecycleWorkflow(node),
            [node],
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_archive_node_transition",
        lambda self, run_id, node_name, state, snapshot, handoff: archives.append({
            "node": node_name,
            "state": dict(state),
            "snapshot": snapshot,
        }),
    )

    events = list(WorkflowExecutor(
        holmes_service=_DummyHolmesService(),
    ).execute_stream("parallel lifecycle"))

    thinking = next(event for event in events if event.get("type") == "thinking")
    assert thinking["node"] == "parallel_evidence"
    assert thinking["lane_stage"] == "rca"
    assert [archive["node"] for archive in archives] == ["parallel_evidence"]
    assert [group["group_id"] for group in archives[0]["snapshot"]["groups"]] == ["g3"]
    assert archives[0]["state"]["autonomous_group_results"][0]["group_id"] == "g3"


def test_executor_parallel_snapshot_without_group_results_is_empty():
    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())

    assert executor._extract_state_snapshot({}, "parallel_evidence") == {}


def test_executor_evidence_handoff_summary_uses_structured_plan_counts():
    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    state = {
        "evidence_analysis": json.dumps({
            "plan_total": 2,
            "plan_collected": 2,
        }),
        "evidence_items": [
            EvidenceItem(
                id=f"item-{index}",
                description="evidence",
                level=EvidenceLevel.IMPORTANT,
                collected=True,
                source="layer_verified" if index >= 2 else "thinking_match",
            )
            for index in range(5)
        ],
    }

    summary = executor._format_handoff_summary("evidence", state)

    assert summary.startswith("evidence_items=2/2\n")


class _SlowNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.node_name = f"{node_id}-name"
        self._event_queue = None

    def set_event_queue(self, q):
        self._event_queue = q


class _SlowWorkflow:
    def __init__(self, node):
        self._node = node

    def stream(self, initial_state):
        self._node._event_queue.put((
            "node_lifecycle",
            {
                "phase": "start",
                "node": self._node.node_id,
                "node_name": self._node.node_name,
                "ts": time.time(),
            },
        ))
        time.sleep(0.45)
        self._node._event_queue.put((
            "node_lifecycle",
            {
                "phase": "end",
                "node": self._node.node_id,
                "node_name": self._node.node_name,
                "ts": time.time(),
                "success": True,
                "state_update": {
                    "conclusion": "done",
                    "conclusion_formatted": "done",
                },
            },
        ))
        yield {"conclusion": {"conclusion": "done"}}


def test_executor_emits_heartbeat_when_workflow_is_idle(monkeypatch):
    node = _SlowNode("conclusion")

    monkeypatch.setenv("WORKFLOW_STREAM_HEARTBEAT_SECONDS", "0.02")
    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda holmes_service, metrics, runbook_catalog, node_config, query_mode="full", **_kw: (
            _SlowWorkflow(node),
            [node],
        ),
    )
    monkeypatch.setattr(
        WorkflowExecutor,
        "_save_report",
        lambda self, layer, question, full_answer: None,
    )

    executor = WorkflowExecutor(holmes_service=_DummyHolmesService())
    events = list(executor.execute_stream("heartbeat test"))

    heartbeat = next(event for event in events if event.get("type") == "heartbeat")
    assert heartbeat["node"] == "conclusion"
    assert heartbeat["node_name"] == "汇总总结"


def test_workflow_to_text_renders_heartbeat_lines():
    class _Executor:
        def execute_stream(self, question, cancel_event=None, workflow_overrides=None):
            yield {"type": "run_start", "run_id": "hbtest"}
            yield {"type": "node_start", "node": "conclusion", "node_name": "汇总总结"}
            yield {"type": "heartbeat", "node": "conclusion", "node_name": "汇总总结"}
            yield {"type": "final", "answer": "done", "metrics": {}, "elapsed_seconds": 1.0}

    service = HolmesService()
    output = "".join(service._workflow_to_text(_Executor(), "heartbeat test"))

    assert "仍在处理" in output
    assert "汇总总结" in output


def test_metrics_rebuilds_real_llm_and_tool_counts_from_thinking_events():
    metrics = WorkflowMetrics(run_id="runtime-facts")
    events = [
        {
            "type": "ai_usage",
            "node": "layer",
            "timestamp": 1.0,
            "usage": {"input_tokens": 100, "output_tokens": 10},
        },
        {
            "type": "tool_start",
            "node": "layer",
            "timestamp": 2.0,
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "tool_call_id": "tool-1",
        },
        {
            "type": "tool_result",
            "node": "layer",
            "timestamp": 2.25,
            "tool_name": "kubectl_get_by_kind_in_cluster",
            "tool_call_id": "tool-1",
            "status": "success",
        },
        {
            "type": "ai_usage",
            "node": "layer",
            "timestamp": 3.0,
            "usage": {"input_tokens": 200, "output_tokens": 20},
        },
        {
            "type": "tool_start",
            "node": "layer",
            "timestamp": 4.0,
            "tool_name": "kubectl_get_by_name",
            "tool_call_id": "tool-2",
        },
    ]

    metrics.rebuild_runtime_counts(events)

    assert metrics.total_llm_calls == 2
    assert metrics.total_tool_calls == 2
    assert metrics.successful_tool_calls == 1
    assert metrics.failed_tool_calls == 1
    assert metrics.total_tool_duration_ms == pytest.approx(250.0)
    assert metrics.tool_call_details == [
        {
            "tool": "kubectl_get_by_kind_in_cluster",
            "tool_call_id": "tool-1",
            "duration_ms": pytest.approx(250.0),
            "success": True,
            "node": "layer",
        },
        {
            "tool": "kubectl_get_by_name",
            "tool_call_id": "tool-2",
            "duration_ms": 0.0,
            "success": False,
            "node": "layer",
        },
    ]


def test_metrics_runtime_rebuild_deduplicates_replayed_events():
    metrics = WorkflowMetrics(run_id="runtime-replay")
    usage = {
        "type": "ai_usage",
        "node": "evidence",
        "timestamp": 1.0,
        "iteration": 2,
        "usage": {"input_tokens": 100, "output_tokens": 10},
    }
    start = {
        "type": "tool_start",
        "node": "evidence",
        "timestamp": 2.0,
        "tool_name": "collect_aiops_case",
        "tool_call_id": "tool-case",
    }
    result = {
        "type": "tool_result",
        "node": "evidence",
        "timestamp": 3.0,
        "tool_name": "collect_aiops_case",
        "tool_call_id": "tool-case",
        "status": "success",
    }

    metrics.rebuild_runtime_counts([usage, usage, start, start, result, result])

    assert metrics.total_llm_calls == 1
    assert metrics.total_tool_calls == 1
    assert metrics.successful_tool_calls == 1
    assert metrics.failed_tool_calls == 0
    assert metrics.total_tool_duration_ms == pytest.approx(1000.0)


def test_metrics_runtime_rebuild_pairs_anonymous_start_and_result_as_one_call():
    metrics = WorkflowMetrics(run_id="runtime-anonymous")
    events = [
        {
            "type": "tool_start",
            "node": "evidence",
            "timestamp": 2.0,
            "tool_name": "collect_aiops_case",
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "timestamp": 2.4,
            "tool_name": "collect_aiops_case",
            "status": "success",
        },
    ]

    metrics.rebuild_runtime_counts(events)

    assert metrics.total_tool_calls == 1
    assert metrics.successful_tool_calls == 1
    assert metrics.failed_tool_calls == 0
    assert metrics.total_tool_duration_ms == pytest.approx(400.0)


def test_metrics_stats_block_has_balanced_code_fence():
    metrics = WorkflowMetrics(run_id="stats-fence")
    metrics.end_time = metrics.start_time + 1

    result = metrics.format_stats_block()

    assert result.count("```") % 2 == 0
    assert "```text" in result


def test_metrics_stats_block_shows_parallel_lane_wall_times():
    metrics = WorkflowMetrics(run_id="lane-times")
    metrics.end_time = metrics.start_time + 12
    parallel = metrics.start_node(
        "parallel_evidence",
        "并发证据采集",
        start_ts=metrics.start_time + 1,
    )
    parallel.finish(end_ts=metrics.start_time + 11)
    metrics.lane_timings = [{
        "group_id": "g1",
        "entities": [{"namespace": "demo", "name": "oom-pod"}],
        "total_duration_ms": 9000,
        "evidence_duration_ms": 6000,
        "rca_duration_ms": 2500,
    }]

    stats = metrics.format_stats_block()

    assert "并发证据采集: 10.0s" in stats
    assert "g1 demo/oom-pod: 9.0s (Evidence 6.0s, RCA 2.5s)" in stats
    assert "LLM 调用" not in stats
    assert "工具调用" not in stats


def test_rollout_status_verification_is_not_treated_as_write_advice():
    report = """
## 验证步骤
`kubectl rollout status deployment/api -n demo --timeout=60s`
"""
    plan = SimpleNamespace(remediation_available=False, actions=[])

    assert _missing_structured_actions_reason(report, plan) is None


def test_bare_write_command_name_in_caution_is_not_treated_as_actionable_advice():
    report = """
## ⚠️ 注意事项
- 执行 `kubectl set env` 和 `kubectl set resources` 会触发 Deployment 滚动更新。
"""
    plan = SimpleNamespace(remediation_available=False, actions=[])

    assert _missing_structured_actions_reason(report, plan) is None












def test_metrics_separates_parallel_tool_cumulative_and_wall_time():
    metrics = WorkflowMetrics(run_id="parallel-tools")
    events = [
        {
            "type": "tool_start",
            "node": "evidence",
            "timestamp": 10.0,
            "tool_name": "collect_aiops_case",
            "tool_call_id": "case-a",
        },
        {
            "type": "tool_start",
            "node": "evidence",
            "timestamp": 10.0,
            "tool_name": "collect_aiops_case",
            "tool_call_id": "case-b",
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "timestamp": 20.0,
            "tool_name": "collect_aiops_case",
            "tool_call_id": "case-a",
            "status": "success",
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "timestamp": 20.0,
            "tool_name": "collect_aiops_case",
            "tool_call_id": "case-b",
            "status": "success",
        },
    ]

    metrics.rebuild_runtime_counts(events)

    assert metrics.total_tool_duration_ms == pytest.approx(20000.0)
    assert metrics.tool_wall_duration_ms == pytest.approx(10000.0)
    stats = metrics.format_stats_block()
    assert "累计耗时" not in stats
    assert "并行关键路径" not in stats


def test_metrics_reports_requests_executions_dedup_and_unfinished_separately():
    metrics = WorkflowMetrics(run_id="tool-real-counts")
    events = [
        {
            "type": "tool_start",
            "node": "layer",
            "timestamp": 1.0,
            "tool_name": "kubectl_get_by_name",
            "tool_call_id": "first",
        },
        {
            "type": "tool_result",
            "node": "layer",
            "timestamp": 2.0,
            "tool_name": "kubectl_get_by_name",
            "tool_call_id": "first",
            "status": "success",
        },
        {
            "type": "tool_start",
            "node": "layer",
            "timestamp": 3.0,
            "tool_name": "kubectl_get_by_name",
            "tool_call_id": "dedup",
        },
        {
            "type": "tool_result",
            "node": "layer",
            "timestamp": 3.01,
            "tool_name": "kubectl_get_by_name",
            "tool_call_id": "dedup",
            "status": "success",
            "deduplicated": True,
            "original_tool_call_id": "first",
        },
        {
            "type": "tool_start",
            "node": "layer",
            "timestamp": 4.0,
            "tool_name": "kubectl_get_by_name",
            "tool_call_id": "unfinished",
        },
    ]

    metrics.rebuild_runtime_counts(events)

    assert metrics.total_tool_calls == 3
    assert metrics.executed_tool_calls == 1
    assert metrics.deduplicated_tool_calls == 1
    assert metrics.successful_tool_calls == 2
    assert metrics.failed_tool_calls == 1
    assert metrics.total_tool_duration_ms == pytest.approx(1000.0)
    stats = metrics.format_stats_block()
    assert "请求 3" not in stats
    assert "实际执行 1" not in stats
    assert "去重 1" not in stats
    assert "失败/未完成 1" not in stats


def test_metrics_uses_provider_model_duration_instead_of_agent_wall_time():
    metrics = WorkflowMetrics(run_id="model-duration")
    metrics.record_llm_call(
        "conclusion",
        250.0,
        request_count=1,
        source="direct",
    )
    events = [
        {
            "type": "ai_usage",
            "node": "layer",
            "timestamp": 2.0,
            "iteration": 1,
            "model_duration_ms": 600.0,
            "usage": {"input_tokens": 100, "output_tokens": 10},
        },
        {
            "type": "tool_start",
            "node": "layer",
            "timestamp": 2.0,
            "tool_name": "collect_aiops_case",
            "tool_call_id": "case-a",
        },
        {
            "type": "tool_result",
            "node": "layer",
            "timestamp": 12.0,
            "tool_name": "collect_aiops_case",
            "tool_call_id": "case-a",
            "status": "success",
        },
        {
            "type": "ai_usage",
            "node": "layer",
            "timestamp": 13.0,
            "iteration": 2,
            "model_duration_ms": 900.0,
            "usage": {"input_tokens": 200, "output_tokens": 20},
        },
    ]

    metrics.rebuild_runtime_counts(events)

    assert metrics.total_llm_calls == 3
    assert metrics.total_llm_duration_ms == pytest.approx(1750.0)
    assert metrics.nodes["conclusion"].llm_duration_ms == pytest.approx(250.0)
    assert metrics.nodes["layer"].llm_duration_ms == pytest.approx(1500.0)
