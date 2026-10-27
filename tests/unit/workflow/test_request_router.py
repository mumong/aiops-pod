import json
from types import SimpleNamespace

import pytest

from app.core.workflow.nodes.request_router import RequestContract, RequestRouterNode


def test_ordinary_operation_contract_keeps_focused_route_and_session_scope():
    from app.core.prompts import REQUEST_ROUTER_PROMPT

    contract = RequestContract(
        route="focused",
        task="operate",
        scope="namespace",
        namespaces=["xnet"],
        requested_outputs=["创建 nginx 测试 Pod"],
    )
    assert contract.route == "focused"
    assert contract.task == "operate"
    assert contract.pod_names == []
    assert "卸载 Helm Release" in REQUEST_ROUTER_PROMPT
    assert (
        "“卸载 xx”“删除 xx”“重启 xx”这类已经说明对象和动作的指令是执行请求"
        in REQUEST_ROUTER_PROMPT
    )
    assert "不再次发起修复" in REQUEST_ROUTER_PROMPT


@pytest.mark.parametrize(
    "update",
    [
        {"scope": "namespace", "namespaces": ["xnet"]},
        {"scope": "pod", "pod_names": ["test-nginx"]},
        {"task": "query", "requested_outputs": ["CPU", "memory"]},
        {"task": "explain"},
        {"scope": "unspecified"},
    ],
)
def test_schema_does_not_override_model_route_or_scope(update):
    values = dict(route="full_diagnosis", task="inspect", scope="cluster")
    values.update(update)
    contract = RequestContract(**values)
    assert contract.route == "full_diagnosis"
    assert contract.scope == values["scope"]


def test_explicit_cluster_inspection_keeps_diagnostic_route():
    contract = RequestContract(route="full_diagnosis", task="inspect", scope="cluster")
    assert contract.route == "full_diagnosis"


def test_router_uses_original_question_and_no_cluster_tools():
    question = "xnet 命名空间全部 Pod 的 CPU 和内存是多少？"
    calls = []

    def classify(**kwargs):
        calls.append(kwargs)
        return RequestContract(
            route="focused",
            task="query",
            scope="namespace",
            namespaces=["xnet"],
            requested_outputs=["CPU", "memory"],
        ), ""

    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=classify)
    result = node.execute({"question": question})
    assert calls[0]["question"] == question
    assert "tools" not in calls[0]
    assert result["request_route"] == "focused"
    assert result["request_contract"]["time_range"] is None
    assert not node.should_inject_runbook_catalog()


def test_classification_failure_never_falls_back_to_cluster_scan():
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=lambda **kwargs: (None, "invalid"))
    result = node.execute({"question": "xnet 的 CPU？"})
    assert result["request_route"] == "stop"
    assert result["errors"]
    assert result["request_contract"] is None
    assert result["request_error"]["code"] == "route_format"
    assert "格式异常" in result["conclusion"]


def test_model_500_is_not_misreported_as_lost_history_or_ambiguous_question():
    import httpx
    from openai import InternalServerError

    response = httpx.Response(500, request=httpx.Request("POST", "http://model.invalid"))
    failure = InternalServerError("private provider detail", response=response, body={})
    node = RequestRouterNode()

    def fail(**kwargs):
        assert kwargs["raise_on_error"] is True
        assert "xnet" in kwargs["question"]
        raise failure

    node.ai_call = SimpleNamespace(call_structured=fail)
    result = node.execute(
        {
            "question": "其中哪个CPU最高",
            "query_session_context": {
                "turns": [{"question": "xnet有哪些pod", "answer": "pod-a, pod-b"}]
            },
        }
    )
    assert result["request_route"] == "stop"
    assert result["request_error"]["http_status"] == 500
    assert result["request_error"]["history_loaded"] is True
    assert "HTTP 500" in result["conclusion"]
    assert "private provider detail" not in str(result)
    assert "query_session_memory" not in result


def test_timeout_and_connection_failures_have_distinct_presentation():
    import httpx
    from openai import APIConnectionError, APITimeoutError

    from app.core.workflow.nodes.request_router import router_failure

    request = httpx.Request("POST", "http://model.invalid")
    assert router_failure(APITimeoutError(request))["code"] == "model_timeout"
    assert router_failure(APIConnectionError(request=request))["code"] == "model_connection"


def test_native_structured_can_propagate_original_provider_failure(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "54000")
    from contextlib import nullcontext

    import httpx
    from openai import InternalServerError

    from app.core.aicall.client import AICall

    failure = InternalServerError(
        "provider failure",
        response=httpx.Response(500, request=httpx.Request("POST", "http://model.invalid")),
        body={},
    )

    class Model:
        def bind(self, **kw):
            return self

        def with_structured_output(self, *a, **kw):
            return self

        def invoke(self, *a, **kw):
            raise failure

    client = AICall(model="openai/test", api_key="test")
    monkeypatch.setattr(client, "_create_chat_model", lambda **kw: Model())
    monkeypatch.setattr(client, "_bind_session_metadata", lambda model, *a, **kw: model)
    monkeypatch.setattr(client, "_build_langchain_config", lambda *a, **kw: None)
    monkeypatch.setattr(client, "_langfuse_session_scope", lambda *a: nullcontext())
    with pytest.raises(InternalServerError):
        client.call_structured("route", "question", RequestContract, raise_on_error=True)
    assert client.call_structured("route", "question", RequestContract) == (None, "")


def test_router_error_reaches_sse_snapshot_and_final_without_query(monkeypatch, tmp_path):
    import httpx
    from openai import InternalServerError

    from app.core.workflow.executor import WorkflowExecutor

    failure = InternalServerError(
        "private",
        response=httpx.Response(500, request=httpx.Request("POST", "http://model.invalid")),
        body={},
    )

    def classify(**kw):
        raise failure

    service = SimpleNamespace(merged_catalog=None, workflow_config={})
    executor = WorkflowExecutor(service)
    executor.ai_call = SimpleNamespace(call_structured=classify)
    executor.mcp_tools = []
    executor.REPORTS_DIR = str(tmp_path)
    events = list(
        executor.execute_stream("哪个CPU最高", workflow_overrides={"query_mode": "auto"})
    )
    snapshot = next(e["state_snapshot"] for e in events if e.get("type") == "node_complete")
    assert snapshot["request_error"]["http_status"] == 500
    final = next(e for e in events if e.get("type") == "final")
    assert final["status"] == "error"
    assert final["request_error"]["code"] == "model_service"
    assert [e["node"] for e in events if e.get("type") == "node_start"] == ["request_router"]


def test_ambiguous_request_returns_clarification():
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(
        call_structured=lambda **kwargs: (
            RequestContract(
                route="clarify",
                task="unsupported",
                scope="unspecified",
                clarification="需要检查哪个 Pod？",
            ),
            "",
        )
    )
    result = node.execute({"question": "看看这个"})
    assert result["conclusion"] == "需要检查哪个 Pod？"
    assert result["query_session_memory"]["turns"][-1]["question"] == "看看这个"


@pytest.mark.parametrize("question", ["这个异常的pod是什么根因？", "刚刚回复里的那个workload啊"])
def test_router_receives_answer_discovered_targets_even_after_clarification(question):
    answer = "aiops-case-08 下两个 Pod：driver Running；workload-abc CrashLoopBackOff。"
    turns = [
        {
            "question": "aiops-case-08下几个pod？",
            "answer": answer,
            "scope": "aiops-case-08",
            "observed_at": "2026-09-18T02:18:14Z",
            "request_contract": {"pod_names": []},
            "observations": ["bulky raw results"],
        },
        {"question": "那个异常pod？", "answer": "需要哪个Pod？", "scope": "unspecified"},
    ]

    def classify(**kwargs):
        material = json.loads(kwargs["question"])
        assert material["question"] == question
        assert material["history"][0]["answer"] == answer
        assert material["history"][0]["observed_at"] == turns[0]["observed_at"]
        assert material["history"][1]["answer"] == "需要哪个Pod？"
        assert "observations" not in material["history"][0]
        return RequestContract(
            route="full_diagnosis",
            task="diagnose",
            scope="pod",
            namespaces=["aiops-case-08"],
            pod_names=["workload-abc"],
        ), ""

    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=classify)
    result = node.execute({"question": question, "query_session_context": {"turns": turns}})
    assert result["request_contract"]["pod_names"] == ["workload-abc"]


def _repair_router():
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(
        call_structured=lambda **kw: (
            RequestContract(
                route="remediation", task="repair", scope="namespace", namespaces=["aiops-case-09"]
            ),
            "",
        )
    )
    return node


def test_repair_plan_without_a_diagnosis_diagnoses_first():
    # Live 2026-10-19 (A2A run 5b804cc9): "诊断并修复 …" in a fresh session went to
    # single-agent planning and waited for an inline approval API/A2A callers never see.
    result = _repair_router().execute(
        {"question": "诊断并修复 aiops-case-09", "repair_auto_plan": True}
    )
    assert result["request_route"] == "full_diagnosis"
    contract = result["request_contract"]
    assert contract["task"] == "diagnose" and contract["namespaces"] == ["aiops-case-09"]


def test_repair_plan_with_a_diagnosis_or_without_the_flag_keeps_remediation():
    with_diagnosis = {
        "question": "修复刚刚的问题",
        "repair_auto_plan": True,
        "repair_context": {"diagnosis": {"run_id": "d"}},
    }
    assert _repair_router().execute(with_diagnosis)["request_route"] == "remediation"
    assert _repair_router().execute({"question": "修复"})["request_route"] == "remediation"


def test_repair_on_request_reroutes_only_a_repair_and_marks_it():
    # Live 2026-10-26 (A2A run d52a2280): an A2A host sent "帮我修复 …" without metadata;
    # it went to single-agent planning and its inline approval timed out after 600 s.
    # repair=on_request (always sent by the adapter) diagnoses first and marks the request
    # so the executor starts the per-group batch whose approvals A2A callers can answer.
    result = _repair_router().execute(
        {"question": "帮我修复 aiops-case-10 的异常 Pod", "repair_on_request": True}
    )
    assert result["request_route"] == "full_diagnosis"
    assert result["repair_requested"] is True
    with_diagnosis = {
        "question": "修复刚刚的问题",
        "repair_on_request": True,
        "repair_context": {"diagnosis": {"run_id": "d"}},
    }
    kept = _repair_router().execute(with_diagnosis)
    assert kept["request_route"] == "remediation" and not kept.get("repair_requested")


def test_repair_on_request_leaves_a_plain_diagnosis_unmarked():
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(
        call_structured=lambda **kw: (
            RequestContract(route="full_diagnosis", task="diagnose", scope="cluster"),
            "",
        )
    )
    result = node.execute({"question": "集群有什么问题", "repair_on_request": True})
    assert result["request_route"] == "full_diagnosis" and not result.get("repair_requested")


def test_unsupported_request_stops_with_a_clear_reason_not_a_format_error():
    """Live 02cf7ca2a72948c6: "执行 rm /tmp/x" on the host → the model answered
    route=unsupported (a refusal), the schema rejected it and the person saw
    "输出格式异常，请重试" instead of "不在支持范围"."""
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(
        call_structured=lambda **kwargs: (
            RequestContract(
                route="unsupported",
                task="unsupported",
                scope="unspecified",
                clarification="主机上的文件删除不在支持范围",
            ),
            "",
        )
    )
    result = node.execute({"question": "帮我执行命令 rm /tmp/x"})
    assert result["request_route"] == "stop"
    assert result["request_error"]["code"] == "unsupported_request"
    assert "不在支持范围" in result["conclusion"] and "未执行任何命令" in result["conclusion"]
    assert "格式异常" not in result["conclusion"]
    assert result["request_contract"]["route"] == "unsupported"


def test_router_prompt_routes_in_pod_commands_to_the_executor():
    """Live 2026-10-20 (feb539aad5ea4c69): "在 <ns> 的 <pod> Pod 里执行 rm ..." was refused
    as a host operation, so the blacklist never saw it. In-Pod commands are cluster
    execution; the rules decide, not the router."""
    from app.core.prompts import QUERY_COLLECT_PROMPT, REQUEST_ROUTER_PROMPT

    assert "等同 kubectl exec" in REQUEST_ROUTER_PROMPT
    assert "路由不提前拒绝" in REQUEST_ROUTER_PROMPT
    assert "kubectl_run_image 只在用户要求新起临时 Pod 时使用" in QUERY_COLLECT_PROMPT
