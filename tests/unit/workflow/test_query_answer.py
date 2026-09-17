import json
from types import SimpleNamespace

from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.query_answer import QueryCollectNode, QueryConclusionNode
from app.core.workflow.executor import WorkflowExecutor


def test_direct_query_uses_two_agents_and_passes_logs_without_metric_schema():
    graph, nodes = build_diagnosis_workflow(query_mode="direct")
    assert [type(node) for node in nodes] == [QueryCollectNode, QueryConclusionNode]
    captured = {}
    observation = {"type": "tool_result", "tool_name": "kubectl_logs",
                   "result": "device not found", "raw_ref": "/archive/log.raw.txt"}

    def collect(question, prompt, **kwargs):
        assert "xnet" in question
        assert not kwargs.get("expect_json")
        assert not kwargs.get("stop_checker")
        return SimpleNamespace(result="可能没有设备"), [observation]

    def conclude(question, prompt, **kwargs):
        captured.update(json.loads(question))
        assert kwargs["force_no_tools"]
        assert kwargs["skip_remediation_policy"]
        return SimpleNamespace(result="日志包含 device not found，不足以确认设备故障。"), []

    nodes[0]._call_llm = collect
    nodes[1]._call_llm = conclude
    result = graph.invoke({"question": "查 xnet Pod 日志"})
    assert captured["question"] == "查 xnet Pod 日志"
    assert captured["observations"][0]["result"] == "device not found"
    assert captured["observations"][0]["raw_ref"] == observation["raw_ref"]
    assert "不足以确认" in result["conclusion"]
    assert "query_result" not in result
    assert result["request_route"] == "query"


def test_clarification_without_tools_is_not_rejected():
    graph, nodes = build_diagnosis_workflow(query_mode="direct")
    for node in nodes:
        node._call_llm = lambda *a, **kw: (SimpleNamespace(result="需要查询哪个命名空间和 Pod？"), [])
    result = graph.invoke({"question": "查询 Pod 日志"})
    assert result["conclusion"] == "需要查询哪个命名空间和 Pod？"
    assert "伪结构化" not in result["conclusion"]


def test_conclusion_consumes_latest_working_context_not_old_raw_history():
    node = QueryConclusionNode()
    captured = {}
    def call(question, *args, **kwargs):
        captured.update(json.loads(question))
        return SimpleNamespace(result='ok'), []
    node._call_llm = call
    node.execute({'question': 'CPU', 'thinking_events': [
        {'type': 'tool_result', 'result': 'old huge raw'},
        {'type': 'context_compacted', 'working_summary': 'CPU metrics found',
         'retained_messages': [{'type': 'tool', 'content': 'recent exact fact'}]},
        {'type': 'tool_result', 'result': 'CPU 14%', 'raw_ref': '/cpu.raw'},
    ]})
    assert captured['working_summary'] == 'CPU metrics found'
    assert captured['recent_interactions'][0]['content'] == 'recent exact fact'
    assert len(captured['observations']) == 1
    assert captured['observations'][0]['result'] == 'CPU 14%'


def test_raw_mode_is_request_client_configuration(monkeypatch):
    monkeypatch.setenv("AIOPS_QUERY_RAW_TOOL_OUTPUT", "true")
    node = QueryCollectNode()
    node.ai_call = SimpleNamespace()
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result="ok"), [])
    node.execute({"question": "查询"})
    assert node.ai_call.query_raw_passthrough is True
    assert node.ai_call.query_tool_timeout == 60


def test_conclusion_does_not_reexpand_targeted_summary():
    node = QueryConclusionNode()
    captured = {}
    def call(question, *args, **kwargs):
        captured.update(json.loads(question))
        return SimpleNamespace(result="ok"), []
    node._call_llm = call
    node.execute({"question": "CPU", "thinking_events": [
        {"type": "tool_result", "result": "bounded summary", "structured": {"all_rows": ["large"]},
         "structured_ref": "/archive/full.json", "observation_processor": "table+query_targeted_summary"},
        {"type": "tool_result", "result": "small", "structured": {"value": 1}},
    ]})
    assert "structured" not in captured["observations"][0]
    assert captured["observations"][0]["structured_ref"] == "/archive/full.json"
    assert captured["observations"][1]["structured"] == {"value": 1}


def test_budget_failure_skips_conclusion_model_and_preserves_refs():
    node = QueryConclusionNode()
    def forbidden(*a, **kw):
        from app.core.aicall.client import StructuredContextBudgetError
        raise StructuredContextBudgetError("压缩后仍超过预算")
    node._call_llm = forbidden
    output = node.execute({"question": "查询", "thinking_events": [
        {"type": "tool_result", "raw_ref": "/archive/a.raw"},
        {"type": "execution_incomplete", "reason": "原文直传输入超过模型预算"},
    ]})
    assert output["query_answer"]["status"] == "partial"
    assert output["query_answer"]["evidence_refs"] == ["/archive/a.raw"]


def test_incomplete_execution_cannot_be_presented_as_completed():
    node = QueryConclusionNode()
    answer = {"intent": "查询", "scope": "集群", "status": "answered", "answer": "部分数据"}
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result=json.dumps(answer)), [])
    output = node.execute({"question": "查询", "thinking_events": [
        {"type": "execution_incomplete", "reason": "step_limit"}]})
    assert output["query_answer"]["status"] == "partial"
    assert "step_limit" in output["conclusion"]


def test_structured_answer_preserves_frontend_markdown():
    node = QueryConclusionNode()
    answer = {"intent": "解释 Pod", "scope": "知识解释", "status": "answered",
              "answer": "Pod 是 Kubernetes 调度单位。", "missing": [], "runbooks": [], "evidence_refs": []}
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result=json.dumps(answer)), [])
    result = node.execute({"question": "什么是 Pod？"})
    assert result["conclusion"] == answer["answer"]
    assert result["query_answer"] == answer


def test_all_installed_runbooks_available_without_mutating_shared_tool(tmp_path):
    from app.core.aicall.builtin_tools import FetchRunbookTool
    (tmp_path / "custom-guide.md").write_text("custom")
    tool = FetchRunbookTool(runbook_dirs=[str(tmp_path)], allowed_runbook_ids=["old-only"])
    node = QueryCollectNode()
    node.tools = [tool]
    catalog = node._prepare_query_tools()
    assert "custom-guide.md" in catalog
    assert "custom-guide" in node.tools[0].allowed_runbook_ids
    assert tool.allowed_runbook_ids == ["old-only"]
    assert "必须按照" not in node.tools[0].description
    assert {"kubernetes_jq_query", "query_pod_tracing", "read_context_archive"} <= node.READ_TOOLS
    assert "run_bash_command" not in node.READ_TOOLS


def test_query_executor_preserves_answer_without_diagnostic_score_or_remediation(monkeypatch, tmp_path):
    monkeypatch.setattr(QueryCollectNode, "execute", lambda self, state: {
        "request_route": "query", "query_draft": "日志摘录"})
    monkeypatch.setattr(QueryConclusionNode, "execute", lambda self, state: {
        "conclusion": "日志查询完成", "conclusion_formatted": "日志查询完成"})

    def forbidden(*args, **kwargs):
        raise AssertionError("Query must not trigger remediation extraction")

    monkeypatch.setattr("app.core.workflow.executor.extract_remediation_plan", forbidden)
    service = SimpleNamespace(merged_catalog=None, workflow_config={"remediation": {"enabled": True}})
    executor = WorkflowExecutor(service)
    executor.REPORTS_DIR = str(tmp_path)
    events = list(executor.execute_stream("查询日志", workflow_overrides={"query_mode": "direct"}))
    final = next(event for event in events if event.get("type") == "final")
    assert "日志查询完成" in final["answer"]
    assert final["request_route"] == "query"
    assert final["metrics"]["diagnosis_metrics_applicable"] is False
    assert "evidence_completeness" not in final["metrics"]
