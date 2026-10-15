import json
from types import SimpleNamespace

import pytest

from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.remediation import RemediationNode
from app.core.workflow.nodes.request_router import RequestContract


@pytest.mark.parametrize('feedback', ['明确可以这样处理', '直接移除', '确认使用刚才说明的配置'])
def test_revision_feedback_is_delivered_with_previous_plan_and_scope(feedback):
    from app.core.prompts import POD_REMEDIATION_PROMPT
    node = RemediationNode()
    node.ai_call = SimpleNamespace()
    node._prepare_query_tools = lambda: ''
    context = {'diagnosis': {'payload': {'group_id': 'g4', 'groups': [
        {'target': {'group_id': 'g4', 'entities': [{'kind': 'Pod', 'namespace': 'demo', 'name': 'p'}]}}]}},
        'previous_plan': {'payload': {'draft': {'actions': [], 'missing': ['确认操作选择']}}}}
    def collect(question, prompt, **kwargs):
        material = json.loads(question)
        assert material['question'] == feedback
        assert material['current_repair_group']['group_id'] == 'g4'
        assert material['repair_context'] == context
        assert '最新人工反馈是高价值规划输入' in prompt
        assert '旧方案的拒绝理由不是不可修改的规则' in prompt
        assert '不解释成“同意继续等待确认”' in prompt
        assert '存在多个会改变操作的解释时' in prompt
        assert '其反馈不证明资源当前状态' in prompt
        assert '不自动批准执行，不覆盖执行层安全限制' in prompt
        return SimpleNamespace(result=json.dumps({'intent': '修订', 'scope': 'demo/p',
            'status': 'answered', 'answer': '待审查', 'targets': [], 'actions': []})), []
    node._call_llm = collect
    node.execute({'question': feedback, 'repair_context': context})
    assert 'finalizer' not in POD_REMEDIATION_PROMPT


def test_repair_route_uses_recent_context_and_only_read_tools():
    graph, nodes = build_diagnosis_workflow(query_mode="auto")
    router = next(n for n in nodes if n.node_id == "request_router")
    repair = next(n for n in nodes if n.node_id == "remediation")
    history = {"turns": [{"question": "Pod 哪个异常", "answer": "ns/demo OOMKilled"}]}
    def classify(**kw):
        assert "ns/demo OOMKilled" in kw["question"]
        return RequestContract(route="remediation", task="repair", scope="pod",
                               namespaces=["ns"], pod_names=["demo"]), ""
    router.ai_call = SimpleNamespace(call_structured=classify)
    repair.ai_call = SimpleNamespace()
    repair.tools = [SimpleNamespace(name="run_bash_command"), SimpleNamespace(name="fetch_runbook")]
    repair._prepare_query_tools = lambda: "pod-oomkilled.md"
    def collect(question, prompt, **kw):
        assert repair.ai_call.query_session_context == history
        assert "run_bash_command" in kw["blocked_tool_names"]
        assert "fetch_runbook" not in kw["blocked_tool_names"]
        assert "Runbook" in prompt and "pod-oomkilled.md" in prompt
        return SimpleNamespace(result=json.dumps({"intent": "修复", "scope": "ns/demo",
            "status": "answered", "answer": "尚未执行，需审阅。", "targets": [], "actions": []})), [
                {"type": "tool_result", "tool_name": "fetch_runbook", "result": "oom guidance",
                 "raw_ref": "/archive/runbook.txt"}]
    repair._call_llm = collect
    result = graph.invoke({"question": "帮我修复刚刚的问题", "query_session_context": history})
    assert result["request_route"] == "remediation"
    assert result["remediation_draft"]["actions"] == []
    assert result["conclusion"] == "尚未执行，需审阅。"
    assert result["query_session_memory"]["turns"][-1]["observations"][0]["tool_name"] == "fetch_runbook"


def test_invalid_repair_json_is_not_an_executable_plan():
    node = RemediationNode()
    node.ai_call = SimpleNamespace()
    node._prepare_query_tools = lambda: ""
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result="kubectl delete namespace ns"), [])
    result = node.execute({"question": "修复"})
    assert result["remediation_draft"]["actions"] == []
    assert result["query_answer"]["status"] == "partial"
    assert result['remediation_draft']['planning_error']['code'] == 'planning_incomplete'


def test_disconnected_planner_is_failed_not_no_action():
    node = RemediationNode()
    node.ai_call = SimpleNamespace()
    node._prepare_query_tools = lambda: ""
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result='Agent 执行异常'), [
        {'type': 'execution_incomplete', 'reason': 'stream disconnected before completion: stream closed before response.completed'}])
    result = node.execute({'question': '修复'})
    plan = result['remediation_draft']
    assert not plan['actions']
    assert plan['planning_error']['code'] == 'model_connection_interrupted'
    assert '模型服务连接中断' in plan['answer']
    from app.core.remediation.pod_executor import PodRepairExecutor
    events = list(PodRepairExecutor(runner=lambda args: pytest.fail('must not execute')).run('test', plan))
    assert events[-1]['status'] == 'failed'


def test_repair_schema_does_not_prescribe_agent_operations():
    from app.core.workflow.nodes.remediation import RepairDraft
    values = {"intent": "fix", "scope": "ns/demo", "status": "answered", "answer": "review",
              "targets": [{"namespace": "ns", "pod": "demo", "pod_uid": "uid", "group_id": "g1"}],
              "actions": [{"id": "a1", "group_id": "g1", "description": "check", "risk": "low",
                           "execute_command": "kubectl get pod/demo -n ns",
                           "verify_command": "kubectl get pod/demo -n ns", "rollback_advice": "none"}]}
    assert RepairDraft.model_validate(values).actions[0].execute_command.startswith("kubectl get")


def test_deep_conclusion_never_emits_executable_repair_plan():
    from app.core.workflow.nodes.query_answer import QueryConclusionNode
    from tests.unit.remediation.test_pod_executor import fixture
    draft, _, _, _ = fixture()
    draft.update(intent='diagnose', scope='demo/api-1', status='answered', answer='OOMKilled; review required')
    draft['actions'][0]['rollback_advice'] = 'Restore previous resource limit after review'
    calls = []
    node = QueryConclusionNode()
    def conclude(question, prompt, **kw):
        calls.append(kw)
        assert kw['force_no_tools'] is True
        assert 'RepairDraft' not in prompt
        return SimpleNamespace(result=json.dumps(draft)), []
    node._call_llm = conclude
    result = node.execute({'question':'诊断 demo/api-1',
                           'request_contract':{'route':'full_diagnosis'}})
    assert len(calls) == 1
    assert result['conclusion'] == draft['answer']
    assert not result.get('remediation_draft')


@pytest.mark.parametrize('mode', ['review', 'auto'])
def test_workflow_passes_configured_pod_mode_owner_and_policy(monkeypatch, tmp_path, mode):
    from app.core.remediation.pod_executor import PodRepairExecutor
    from app.core.workflow.executor import WorkflowExecutor
    from app.core.workflow.nodes.query_answer import QueryCollectNode
    draft = {'targets': [], 'actions': []}
    monkeypatch.setattr(QueryCollectNode, 'execute', lambda self, state: {
        'request_route': 'remediation', 'request_contract': {'namespaces': ['demo']},
        'remediation_draft': draft, 'conclusion': 'report', 'conclusion_formatted': 'report'})
    def run(self, run_id, actual, **kw):
        assert actual == draft and kw['mode'] == mode
        assert kw['owner'] == 'alice' and kw['timeout'] == 42
        assert kw['request_contract']['namespaces'] == ['demo']
        assert 'patch' in kw['policy'].denied_operations
        yield {'type':'remediation_finished', 'run_id':run_id, 'status':'skipped'}
    monkeypatch.setattr(PodRepairExecutor, 'run', run)
    service = SimpleNamespace(merged_catalog=None, workflow_config={'remediation':{
        'enabled':True,'executor':'pod','mode':mode,'approval_timeout_seconds':42,'denied_operations':['patch']}})
    executor = WorkflowExecutor(service)
    executor.REPORTS_DIR = str(tmp_path)
    import threading
    cancel = threading.Event()
    events = list(executor.execute_stream('diagnose', cancel_event=cancel, workflow_overrides={
        'query_mode':'direct','_remediation_owner':'alice'}))
    assert any(e['type']=='remediation_finished' for e in events)
    assert not cancel.is_set(), 'normal workflow completion must not cancel subsequent job execution'


def test_group_scope_is_explicit_in_repair_material():
    node = RemediationNode()
    node.ai_call = SimpleNamespace()
    node._prepare_query_tools = lambda: ''
    def collect(question, prompt, **kw):
        material = json.loads(question)
        assert material['current_repair_group'] == {'group_id': 'g2', 'targets': [{'entities': [{'name': 'p2'}]}]}
        assert '不为其他组生成 targets/actions' in prompt
        return SimpleNamespace(result=json.dumps({'intent':'repair', 'scope':'p2', 'status':'answered',
                                                  'answer':'needs input', 'targets':[], 'actions':[]})), []
    node._call_llm = collect
    node.execute({'question':'fix all three', 'repair_context': {'diagnosis': {'payload': {
        'group_id':'g2', 'groups':[{'target':{'entities':[{'name':'p2'}]}}]}}}})
