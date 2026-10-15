from types import SimpleNamespace

from app.core.context.observation import ObservationProcessor
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.focused import FocusedResult, FocusedTaskNode
from app.core.workflow.nodes.request_router import RequestContract, RequestRouterNode


def test_focused_no_diagnostic_prompt_and_no_writes():
    node = FocusedTaskNode()
    node.tools = [SimpleNamespace(name=name) for name in
                  ["kubectl_get_by_kind_in_namespace", "kubectl_run_image", "run_bash_command"]]
    captured = {}

    def call(question, prompt, **kwargs):
        captured.update(kwargs)
        captured["prompt"] = prompt
        return SimpleNamespace(result="xnet 中当前未观察到 Pod 状态异常。"), [
                {"type": "tool_result", "status": "success", "raw_ref": "/raw/1"}]

    node._call_llm = call
    node.ai_call = SimpleNamespace(call_structured=lambda **kw: (
        FocusedResult(answer="xnet 中当前未观察到 Pod 状态异常。", evidence_refs=["/raw/1"]), ""))
    output = node.execute({"question": "xnet 有异常 Pod 吗？", "request_contract": {"task": "inspect"}})
    assert "kubectl_run_image" in captured["blocked_tool_names"]
    assert "run_bash_command" in captured["blocked_tool_names"]
    assert not node.should_inject_runbook_catalog()
    assert captured["skip_remediation_policy"]
    assert "xnet" in output["conclusion"]
    assert "abnormal_groups" not in output


def test_fabricated_reference_cannot_publish_environment_answer():
    node = FocusedTaskNode()
    node._call_llm = lambda *args, **kwargs: (SimpleNamespace(result="CPU 为 1%"), [])
    node.ai_call = SimpleNamespace(call_structured=lambda **kw: (
        FocusedResult(answer="CPU 为 1%", evidence_refs=["fake"]), ""))
    output = node.execute({"question": "CPU 多少", "request_contract": {"task": "query"}})
    assert "1%" not in output["conclusion"]
    assert output["focused_result"]["missing"]


def test_not_found_is_valid_negative_observation_not_positive_health():
    node = FocusedTaskNode()
    node._call_llm = lambda *args, **kwargs: (SimpleNamespace(result="目标不存在"), [
        {"type": "tool_result", "raw_ref": "/raw/notfound", "status": "success",
         "semantic_success": False, "result": "Error from server (NotFound)"}])
    node.ai_call = SimpleNamespace(call_structured=lambda **kw: (
        FocusedResult(answer="目标不存在", evidence_refs=["/raw/notfound"]), ""))
    output = node.execute({"question": "test-nginx 存在吗？", "request_contract": {"task": "inspect"}})
    assert output["conclusion"] == "目标不存在"


def test_auto_graph_model_selects_lightweight_scoped_request():
    graph, nodes = build_diagnosis_workflow(query_mode="auto")
    visited = []
    for node in nodes:
        if node.node_id == "request_router":
            node.ai_call = SimpleNamespace(call_structured=lambda **kw: (
                RequestContract(route="focused", task="inspect", scope="namespace", namespaces=["xnet"]), ""))
        elif node.node_id in {"query_collect", "conclusion"}:
            def focused(state):
                visited.append("lightweight")
                return {"conclusion": "xnet 正常"}
            node.execute = focused
        else:
            def unexpected(state):
                raise AssertionError("scoped task entered legacy diagnostic node")
            node.execute = unexpected
    result = graph.invoke({"question": "xnet 有异常吗？"})
    assert visited == ["lightweight"]
    assert result["conclusion"] == "xnet 正常"


def test_focused_executor_emits_final_without_enabling_remediation(monkeypatch, tmp_path):
    monkeypatch.setattr(RequestRouterNode, "execute", lambda self, state: {
        "request_route": "focused", "request_contract": {"task": "query"}})
    from app.core.workflow.nodes.query_answer import QueryCollectNode
    monkeypatch.setattr(QueryCollectNode, "execute", lambda self, state: {
        "query_draft": "CPU 查询结果",
        "conclusion": "CPU 查询结果", "conclusion_formatted": "CPU 查询结果"})

    def forbidden(*args, **kwargs):
        raise AssertionError("read-only focused result reached remediation processing")

    monkeypatch.setattr("app.core.workflow.executor.extract_remediation_plan", forbidden)
    service = SimpleNamespace(merged_catalog=None, workflow_config={"remediation": {"enabled": True}})
    executor = WorkflowExecutor(service)
    executor.REPORTS_DIR = str(tmp_path)
    events = list(executor.execute_stream("xnet CPU 是多少？", workflow_overrides={"query_mode": "auto"}))
    finals = [event for event in events if event.get("type") == "final"]
    assert len(finals) == 1
    assert "CPU 查询结果" in finals[0]["answer"]
    assert "根因置信度" not in finals[0]["answer"]
    assert "evidence_completeness" not in finals[0]["metrics"]
    assert finals[0]["request_route"] == "focused"
    assert not [event for event in events if event.get("type") == "error"]


def test_focused_table_preserves_healthy_rows_and_discloses_omission(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=600)
    raw = "NAMESPACE  NAME  READY  STATUS  RESTARTS  AGE\nxnet  healthy  1/1  Running  0  1d\nother  broken  0/1  Pending  0  1d\n"
    result = processor.process(run_id="focused-test", node_id="focused", sequence=1,
                               tool_name="kubectl_get_by_kind_in_cluster", raw_content=raw)
    assert "healthy" in result["summary"]
    assert result["raw_ref"] in result["summary"]
    assert result["structured"]["omitted_rows"] == 0
    assert len(result["structured"]["all_rows"]) == 2
    raw += "\n".join(f"xnet  healthy-{i}  1/1  Running  0  1d" for i in range(30))
    result = processor.process(run_id="focused-test", node_id="focused", sequence=2,
                               tool_name="kubectl_get_by_kind_in_cluster", raw_content=raw)
    assert result["structured"]["omitted_rows"] > 0
    assert "未展示不代表不存在" in result["summary"]
