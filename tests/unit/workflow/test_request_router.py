from types import SimpleNamespace
import json

import pytest

from app.core.workflow.nodes.request_router import RequestContract, RequestRouterNode
from app.core.workflow.nodes.layer_classifier import LayerClassifierNode


def test_observed_entities_are_never_promoted_to_user_explicit_targets():
    observed = [{"type": "pod", "namespace": "aiops-case-08", "name": "workload"}]
    assert LayerClassifierNode._extract_explicit_pod_targets("xnet 中有异常吗？", observed) == []
    assert LayerClassifierNode._extract_explicit_pod_targets("集群有什么问题？", observed) == []
    assert LayerClassifierNode._extract_explicit_pod_targets("检查 xnet/nginx", observed) == [("xnet", "nginx")]


@pytest.mark.parametrize("update", [
    {"scope": "namespace", "namespaces": ["xnet"]},
    {"scope": "pod", "pod_names": ["test-nginx"]},
    {"task": "query", "requested_outputs": ["CPU", "memory"]},
    {"task": "explain"},
    {"scope": "unspecified"},
])
def test_schema_does_not_override_model_route_or_scope(update):
    values = dict(route="full_diagnosis", task="inspect", scope="cluster")
    values.update(update)
    contract = RequestContract(**values)
    assert contract.route == "full_diagnosis"
    assert contract.scope == values['scope']


def test_explicit_cluster_inspection_keeps_diagnostic_route():
    contract = RequestContract(route="full_diagnosis", task="inspect", scope="cluster")
    assert contract.route == "full_diagnosis"


def test_router_uses_original_question_and_no_cluster_tools():
    question = "xnet 命名空间全部 Pod 的 CPU 和内存是多少？"
    calls = []

    def classify(**kwargs):
        calls.append(kwargs)
        return RequestContract(route="focused", task="query", scope="namespace",
                               namespaces=["xnet"], requested_outputs=["CPU", "memory"]), ""

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


def test_ambiguous_request_returns_clarification():
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=lambda **kwargs: (
        RequestContract(route="clarify", task="unsupported", scope="unspecified",
                        clarification="需要检查哪个 Pod？"), ""))
    result = node.execute({"question": "看看这个"})
    assert result["conclusion"] == "需要检查哪个 Pod？"
    assert result['query_session_memory']['turns'][-1]['question'] == '看看这个'


@pytest.mark.parametrize('question', ['这个异常的pod是什么根因？', '刚刚回复里的那个workload啊'])
def test_router_receives_answer_discovered_targets_even_after_clarification(question):
    answer = 'aiops-case-08 下两个 Pod：driver Running；workload-abc CrashLoopBackOff。'
    turns = [
        {'question': 'aiops-case-08下几个pod？', 'answer': answer,
         'scope': 'aiops-case-08', 'observed_at': '2026-09-18T02:18:14Z',
         'request_contract': {'pod_names': []}, 'observations': ['bulky raw results']},
        {'question': '那个异常pod？', 'answer': '需要哪个Pod？', 'scope': 'unspecified'},
    ]
    def classify(**kwargs):
        material = json.loads(kwargs['question'])
        assert material['question'] == question
        assert material['history'][0]['answer'] == answer
        assert material['history'][0]['observed_at'] == turns[0]['observed_at']
        assert material['history'][1]['answer'] == '需要哪个Pod？'
        assert 'observations' not in material['history'][0]
        return RequestContract(route='full_diagnosis', task='diagnose', scope='pod',
                               namespaces=['aiops-case-08'], pod_names=['workload-abc']), ''
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=classify)
    result = node.execute({'question': question, 'query_session_context': {'turns': turns}})
    assert result['request_contract']['pod_names'] == ['workload-abc']
