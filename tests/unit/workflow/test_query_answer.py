import json
from types import SimpleNamespace

from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.query_answer import (
    QueryCollectNode,
    QueryConclusionNode,
    parse_query_answer,
)


def test_query_catalog_uses_author_description_and_preserves_explicit_catalog(tmp_path):
    from app.core.aicall.builtin_tools import FetchRunbookTool
    from app.core.runbook.catalog import reference_description

    guide = tmp_path / "resource-guide.md"
    guide.write_text("# Resource guide\n\n> 适用说明：集群 CPU、内存、PromQL 与节点映射\n", encoding="utf-8")
    node = QueryCollectNode()
    node.tools = [FetchRunbookTool(runbook_dirs=[str(tmp_path)])]
    assert "集群 CPU、内存、PromQL 与节点映射" in node._prepare_query_tools()
    node.runbook_catalog = SimpleNamespace(catalog=[SimpleNamespace(link=guide.name, description="显式目录优先")])
    assert "显式目录优先" in node._prepare_query_tools()
    assert "集群 CPU" not in node._prepare_query_tools()
    guide.write_text("# Generic reference\nBody\n", encoding="utf-8")
    assert reference_description(guide) == "Generic reference"
    assert reference_description(tmp_path / "missing.md") == "运维参考手册"


def test_query_write_tools_only_for_explicit_ordinary_operation_contract():
    node = QueryCollectNode()
    node.tools = [SimpleNamespace(name=n) for n in ["run_bash_command", "kubectl_run_image", "kubectl_logs"]]
    seen = []
    def call(*args, **kwargs):
        seen.append(kwargs["blocked_tool_names"])
        return SimpleNamespace(result=json.dumps({"intent":"操作","scope":"xnet","status":"answered","answer":"结果"})), []
    node._call_llm = call
    for task in ["query", "diagnose", "repair", "operate"]:
        node.execute({"question":"当前用户请求", "request_contract":{"task":task}})
    for blocked in seen[:3]:
        assert {"run_bash_command", "kubectl_run_image"} <= blocked
    assert not ({"run_bash_command", "kubectl_run_image"} & seen[3])
    assert "run_bash_command" not in node.READ_TOOLS


def test_direct_query_finishes_structured_answer_without_summary_model():
    graph, nodes = build_diagnosis_workflow(query_mode="direct")
    assert [type(node) for node in nodes] == [QueryCollectNode]
    observation = {"type": "tool_result", "tool_name": "kubectl_logs",
                   "result": "device not found", "raw_ref": "/archive/log.raw.txt"}

    def collect(question, prompt, **kwargs):
        assert "xnet" in question
        assert kwargs.get("expect_json")
        assert kwargs['response_schema'].__name__ == 'QueryAnswer'
        assert not kwargs.get("stop_checker")
        assert '没有后续总结节点' in prompt
        return SimpleNamespace(result=json.dumps({"intent": "查询日志", "scope": "xnet",
            "status": "answered", "answer": "日志包含 device not found，不足以确认设备故障。",
            "evidence_refs": [observation["raw_ref"]]})), [observation]

    nodes[0]._call_llm = collect
    result = graph.invoke({"question": "查 xnet Pod 日志"})
    memory = result["query_session_memory"]["turns"][-1]
    assert memory["question"] == "查 xnet Pod 日志"
    assert memory["observations"][0]["result"] == "device not found"
    assert memory["observations"][0]["raw_ref"] == observation["raw_ref"]
    assert "不足以确认" in result["conclusion"]
    assert "query_result" not in result
    assert result["request_route"] == "query"


def test_clarification_without_tools_is_not_rejected():
    graph, nodes = build_diagnosis_workflow(query_mode="direct")
    for node in nodes:
        node._call_llm = lambda *a, **kw: (SimpleNamespace(result=json.dumps({
            "intent": "查询日志", "scope": "未知", "status": "clarify",
            "answer": "需要查询哪个命名空间和 Pod？"})), [])
    result = graph.invoke({"question": "查询 Pod 日志"})
    assert result["conclusion"] == "需要查询哪个命名空间和 Pod？"
    assert "伪结构化" not in result["conclusion"]


def test_direct_invalid_json_is_partial_without_hidden_summary_retry():
    node = QueryCollectNode()
    calls = []
    def collect(*a, **kw):
        calls.append(kw)
        return SimpleNamespace(result='{"answer":"unfinished'), []
    node._call_llm = collect
    result = node.execute({"question": "查询"})
    assert len(calls) == 1
    assert result['query_answer']['status'] == 'partial'
    assert '{"answer"' not in result['conclusion']
    assert result['query_answer']['missing']


def test_direct_budget_error_returns_structured_incomplete_answer():
    from app.core.aicall.client import StructuredContextBudgetError
    node = QueryCollectNode()
    def fail(*a, **kw):
        raise StructuredContextBudgetError('压缩后仍超过预算')
    node._call_llm = fail
    output = node.execute({'question': '查询'})
    assert output['query_answer']['status'] == 'partial'
    assert '压缩后仍超过预算' in output['conclusion']


def test_direct_partial_result_keeps_memory_and_exact_recent_evidence():
    node = QueryCollectNode()
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result=json.dumps({
        'intent': 'CPU', 'scope': 'xnet', 'status': 'answered', 'answer': '| CPU |\n|---|\n| 1 核 |'})), [
            {'type': 'context_compacted', 'working_summary': '早期历史',
             'retained_messages': [{'type': 'tool', 'content': '近期完整结果'}]},
            {'type': 'tool_result', 'raw_ref': '/raw/cpu', 'result': '1 core'},
            {'type': 'execution_incomplete', 'reason': 'step_limit'},
        ])
    result = node.execute({'question': 'CPU', 'query_session_context': {'turns': [{'answer': '旧历史'}]}})
    assert result['query_answer']['status'] == 'partial'
    assert 'step_limit' in result['conclusion']
    memory = result['query_session_memory']
    assert memory['working_summary'] == '早期历史'
    assert len(memory['turns']) == 1
    assert memory['turns'][0]['recent_interactions'][0]['content'] == '近期完整结果'
    assert memory['turns'][0]['observations'][0]['raw_ref'] == '/raw/cpu'


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
    assert "structured" not in captured["observations"][1]
    assert captured["observations"][1]["result"] == "small"


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


def test_unescaped_log_json_is_recovered_without_rewriting_evidence():
    markdown = '## OOM\n\n```json\n{"message":"memory allocation advanced","allocated_mib":48}\n```\n路径 C:\\tmp'
    data = {"intent": "诊断", "scope": "pod", "status": "answered", "answer": markdown,
            "evidence_refs": ["/archive/one.raw"], "runbooks": [], "missing": []}
    raw = json.dumps(data, ensure_ascii=False)
    bad = raw.replace('\\"message\\"', '"message"').replace('\\"memory allocation advanced\\"', '"memory allocation advanced"')
    parsed, repaired = parse_query_answer(bad)
    assert repaired is True
    assert parsed == data
    parsed, repaired = parse_query_answer(raw)
    assert repaired is False and parsed == data


def test_invalid_json_envelope_never_leaks_into_markdown():
    node = QueryConclusionNode()
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result='{"answer":"unfinished'), [])
    result = node.execute({"question": "诊断", "query_draft": "已观察到 OOMKilled，仍需确认原因。"})
    assert result['query_answer'] is None
    assert '已观察到 OOMKilled' in result['conclusion']
    assert '格式异常' in result['conclusion']
    assert '{"answer"' not in result['conclusion']


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
        "request_route": "query", "query_draft": "日志摘录",
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
