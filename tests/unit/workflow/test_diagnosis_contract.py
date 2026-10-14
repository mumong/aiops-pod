import asyncio
import copy
import json
from types import SimpleNamespace

import pytest

from app.core.workflow.diagnosis_contract import DiagnosisHandoff, reconcile_handoff, scoped_handoff
from app.core.workflow.nodes.autonomous_parallel import plan_groups
from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisStageNode, DiagnosisEvidenceNode, DiagnosisRootCauseNode
from app.core.workflow.working_material import build_working_material
from app.core.context.handoff import protected_handoff, handoff_from_messages
from app.core.remediation.records import diagnosis_payload
from app.core.remediation.group_context import scoped_diagnosis


def packet(count=4, kind="Pod"):
    return DiagnosisHandoff.model_validate({"summary": "待调查对象", "coverage": "partial", "targets": [
        {"target_id": f"t{i}", "entity": {"kind": kind, "namespace": "demo", "name": f"object-{i}"},
         "issue": "现场现象", "facts": [{"fact_id": "f1", "summary": f"原始错误 {i}",
          "observed_at": "2026-10-12T06:47:00Z", "evidence_refs": [f"/raw/{i}"]}],
         "next_questions": ["核实原因"]} for i in range(count)]}).model_dump()


@pytest.mark.parametrize("count", [0, 1, 4, 7])
def test_grouping_is_lossless_without_second_model_call(count):
    node = SimpleNamespace(ai_call=SimpleNamespace(call_structured=lambda **kw: pytest.fail("no second LLM")))
    result = plan_groups(node, {"diagnosis_handoff": packet(count)})
    assert [g["target_id"] for g in result["autonomous_groups"]] == [f"t{i}" for i in range(count)]


@pytest.mark.parametrize('kind', ['Pod', 'pod', 'POD', ' pod '])
def test_location_kind_spelling_does_not_lose_four_parallel_groups(kind):
    from app.core.workflow.diagnosis_contract import LocationOutput
    raw = {'analysis': '发现四个待查对象', 'handoff': {'targets': [
        {'target_id': f't{i}', 'entity': {'kind': kind, 'namespace': 'demo', 'name': f'p{i}'},
         'issue': '需要调查的现场线索'} for i in range(4)]}}
    handoff = LocationOutput.model_validate(raw).handoff.model_dump()
    groups = plan_groups(SimpleNamespace(), {'diagnosis_handoff': handoff})['autonomous_groups']
    assert len(groups) == 4
    assert [g['target_id'] for g in groups] == [f't{i}' for i in range(4)]
    assert all(g['entities'][0]['kind'] == 'Pod' for g in groups)
    for group in groups:
        assert len(scoped_handoff(handoff, group['target_id'])['targets']) == 1


def test_kind_normalization_does_not_convert_other_resources_or_hide_duplicates():
    from app.core.workflow.diagnosis_contract import DiagnosisEntity, LocationHandoff
    assert DiagnosisEntity(kind='Service', name='p').kind == 'Service'
    assert DiagnosisEntity(kind='PodMonitor', name='p').kind == 'PodMonitor'
    with pytest.raises(ValueError, match='duplicate target identity'):
        LocationHandoff.model_validate({'targets': [
            {'target_id': str(i), 'entity': {'kind': kind, 'namespace': 'demo', 'name': 'p'},
             'issue': '异常'} for i, kind in enumerate(['Pod', 'pod'])]})


def test_general_entities_and_agent_dispositions():
    data = packet()
    data["targets"][1].update(status="excluded", status_reason="模型已核实正常")
    groups = plan_groups(SimpleNamespace(), {"diagnosis_handoff": data})["autonomous_groups"]
    assert len(groups) == 3
    general = packet(kind="Service")
    assert not plan_groups(SimpleNamespace(), {"diagnosis_handoff": general})["autonomous_groups"]
    assert len(general["targets"]) == 4  # serial path retains all targets


def test_omitted_targets_and_facts_are_preserved_with_explicit_gap():
    old = packet()
    new = copy.deepcopy(old)
    new["targets"].pop()
    new["targets"][0]["facts"] = []
    result, issues = reconcile_handoff(new, old)
    assert len(result["targets"]) == 4 and result["coverage"] == "partial"
    assert result["targets"][0]["facts"] == old["targets"][0]["facts"]
    assert "t3" in issues[0]
    assert len(new["targets"]) == 3  # caller input not mutated


@pytest.mark.parametrize("change", ["duplicate", "entity", "unknown_ref", "unexplained_exclusion"])
def test_invalid_contracts_fail_explicitly(change):
    old = packet()
    new = copy.deepcopy(old)
    target = new["targets"][0]
    if change == "duplicate": new["targets"].append(copy.deepcopy(target))
    if change == "entity": target["entity"]["name"] = "another"
    if change == "unknown_ref": target["findings"] = [{"summary": "推测", "certainty": "hypothesis", "fact_ids": ["missing"]}]
    if change == "unexplained_exclusion": target["status"] = "excluded"
    with pytest.raises(ValueError): reconcile_handoff(new, old)


def test_fact_rewording_preserves_original_and_versions_current_references():
    old = packet(1)
    new = copy.deepcopy(old)
    new["targets"][0]["facts"][0]["summary"] = "新的表述，代码不判定它是否更正确"
    new["targets"][0]["findings"] = [{"summary": "解释", "certainty": "hypothesis", "fact_ids": ["f1"]}]
    result, issues = reconcile_handoff(new, old)
    assert not issues
    target = result["targets"][0]
    assert old["targets"][0]["facts"][0] in target["facts"]
    assert target["facts"][0]["previous_fact_id"] == "f1"
    assert target["findings"][0]["fact_ids"] == ["f1.v2"]


def test_uid_can_be_enriched_but_replacement_cannot_rewrite_identity():
    old = packet(1)
    new = copy.deepcopy(old)
    new["targets"][0]["entity"]["uid"] = "uid-1"
    enriched, _ = reconcile_handoff(new, old)
    new["targets"][0]["entity"]["uid"] = "uid-2"
    with pytest.raises(ValueError): reconcile_handoff(new, enriched)


def test_scope_compaction_fanin_and_repair_keep_exact_contract(monkeypatch):
    from app.core.aicall import working_context
    old = packet()
    target = scoped_handoff(old, "t3")
    material = build_working_material({"question": "调查", "diagnosis_handoff": target})
    async def summarize(*args, **kwargs): return "故意不包含任何对象的摘要"
    monkeypatch.setattr(working_context, "summarize_history", summarize)
    for _ in range(3):
        material = asyncio.run(working_context.compact_working_material(None, material, window=54000))
        assert material["protected_handoff"]["diagnosis_handoff"] == target
    assert handoff_from_messages([{"role": "user", "content": json.dumps(material)}])["diagnosis_handoff"] == target
    lane = {"group_id": "g4", "target": {"entities": [target["targets"][0]["entity"]]}, "material": material}
    assert protected_handoff({"parallel_results": [lane]})["groups"][0]["diagnosis_handoff"] == target
    payload = diagnosis_payload({"diagnosis_handoff": old, "autonomous_group_results": [lane]}, evidence_chars=0)
    scoped = scoped_diagnosis({"payload": payload}, "g4")["payload"]["diagnosis_handoff"]
    assert scoped == target and len(scoped["targets"]) == 1


@pytest.mark.parametrize("node_class", [DiagnosisStageNode, DiagnosisEvidenceNode, DiagnosisRootCauseNode])
def test_stage_emits_and_archives_contract(node_class):
    from app.core.workflow.diagnosis_contract import LocationOutput
    node = node_class()
    node.ai_call = SimpleNamespace()
    seen = {}
    def call(text, prompt, **kw):
        seen.update(kw)
        if node_class is DiagnosisRootCauseNode:
            return SimpleNamespace(result=json.dumps({'outcome': 'inconclusive', 'summary': '原因待核实',
                'certainty': 'unknown', 'report': '本组诊断报告'})), []
        targets = [{k: t[k] for k in ('target_id', 'entity', 'issue', 'status', 'status_reason')} for t in packet()['targets']]
        return SimpleNamespace(result=json.dumps({'analysis': '定位文字', 'handoff': {'targets': targets}})
                               if node_class is DiagnosisStageNode else json.dumps({'analysis': '取证文字'})), []
    node._call_llm = call
    result = node.execute({"question": "查询现场异常", "diagnosis_handoff": scoped_handoff(packet(), 't0')})
    if node_class is DiagnosisStageNode:
        assert seen["response_schema"] is LocationOutput
        assert len(result["diagnosis_handoff"]["targets"]) == 4
        assert result['query_draft'] == '定位文字'
    elif node_class is DiagnosisRootCauseNode:
        assert seen['response_schema'].__name__ == 'DiagnosisCaseOutput'
        assert result['diagnosis_case_result']['execution_status'] == 'completed'
        assert result['query_draft'] == '本组诊断报告'
    else:
        assert seen['response_schema'].__name__ == 'EvidenceStageOutput'
        assert 'diagnosis_handoff' not in result
        assert result['query_draft'] == '取证文字'
    assert not result["thinking_events"]


def test_invalid_output_retains_previous_and_marks_incomplete():
    node = DiagnosisStageNode()
    node.ai_call = SimpleNamespace()
    node._call_llm = lambda *a, **kw: (SimpleNamespace(result="不是 JSON"), [])
    result = node.execute({"question": "q", "diagnosis_handoff": packet()})
    assert result["diagnosis_handoff"]["coverage"] == 'partial'
    assert result['query_draft'] == '不是 JSON'
    assert result["thinking_events"][-1]["type"] == "execution_incomplete"


def test_tool_free_zero_step_stage_uses_native_schema(monkeypatch):
    from app.core.aicall.client import AICall
    ai = AICall(model="openai/test", api_key="test")
    seen = []
    def structured(*args, **kwargs):
        seen.append(kwargs)
        return DiagnosisHandoff.model_validate(packet(1)), ""
    monkeypatch.setattr(ai, "call_structured", structured)
    result, events = ai.call("sys", "question", tools=[], max_steps=0,
                             response_schema=DiagnosisHandoff, node_id="rca")
    assert len(seen) == 1 and json.loads(result.result)["targets"][0]["target_id"] == "t0"
    assert not events


def test_four_parallel_lanes_keep_target_contracts_isolated(monkeypatch):
    from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode
    old = packet()
    state = {"question": "调查全部对象", "diagnosis_handoff": old}
    state.update(plan_groups(SimpleNamespace(), state))
    node = AutonomousParallelNode(SimpleNamespace(_build_request_scoped_ai_call=lambda: SimpleNamespace()))
    node.current_run_id = ""
    node.ai_call = None
    def call(self, text, prompt, **kwargs):
        material = json.loads(text)
        contract = material["protected_handoff"]["diagnosis_handoff"]
        assert len(contract["targets"]) == 1
        expected = next(g for g in state['autonomous_groups'] if g['group_id'] == material['group_id'])
        assert contract["targets"][0]["target_id"] == expected['target_id']
        if self.node_id == 'rca':
            return SimpleNamespace(result=json.dumps({'outcome': 'inconclusive', 'summary': '原因待核实',
                'certainty': 'unknown', 'report': '本组诊断报告'})), []
        return SimpleNamespace(result=json.dumps({'analysis': '本组取证结果'})), []
    monkeypatch.setattr(DiagnosisEvidenceNode, "_call_llm", call)
    monkeypatch.setattr(DiagnosisRootCauseNode, "_call_llm", call)
    result = node.execute(state)
    assert len(result["autonomous_group_results"]) == 4
    for lane in result["autonomous_group_results"]:
        assert lane["status"] == "completed"
        assert lane['case_result']['target']['target_id'] == lane['target']['target_id']
        assert 'material' not in lane
    assert old == packet()  # parallel updates did not mutate parent


def test_failed_lane_start_retains_its_original_contract(monkeypatch):
    from app.core.workflow.nodes.autonomous_parallel import AutonomousParallelNode
    state = {"diagnosis_handoff": packet(2)}
    state.update(plan_groups(SimpleNamespace(), state))
    node = AutonomousParallelNode()
    node.current_run_id, node.ai_call = "", None
    def fail(*args): raise RuntimeError("provider unavailable")
    monkeypatch.setattr(node, "_run_lane", fail)
    result = node.execute(state)
    for lane in result["autonomous_group_results"]:
        assert lane["status"] == "partial"
        assert lane["material"]["protected_handoff"]["diagnosis_handoff"]["targets"][0]["target_id"] == lane["target"]["target_id"]
