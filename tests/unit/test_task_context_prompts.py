"""Complete messages captured before autonomous task-text extraction."""

import copy
import hashlib
import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.workflow.nodes import autonomous_diagnosis as diagnosis
from app.core.workflow.nodes import autonomous_parallel as parallel
from app.core.workflow.nodes import focused, query_answer


QUESTION = '原问题 {literal}\n`Pod` "中文"'
TIME = "2026-09-24T01:02:03+00:00"


class CaptureCall(BaseException):
    """Stop before any model or output recovery can run."""


class Tool(SimpleNamespace):
    def model_copy(self, *, update):
        return Tool(**{**vars(self), **update})


def _tools():
    return [
        Tool(
            name="fetch_runbook",
            description="original runbook",
            runbook_dirs=[],
            allowed_runbook_ids=["z{literal}", "中文\n`id`"],
        ),
        Tool(
            name="execute_prometheus_instant_query",
            description="original metric AIOps boundary: legacy rule",
        ),
        Tool(name="run_bash_command", description="original write"),
        SimpleNamespace(name="opaque", description="no clone API"),
    ]


def _capture(node, state, catalog):
    original = _tools()
    node.tools = original[:]
    before = copy.deepcopy([vars(tool) for tool in original])
    node.runbook_catalog = SimpleNamespace(
        catalog=[
            SimpleNamespace(link="z{id}", description="中文\n`内容`"),
            SimpleNamespace(link="a.md", description="first"),
        ]
        if catalog
        else []
    )
    node.ai_call = SimpleNamespace()
    node._archive_node_input = lambda value: None
    captured = {}

    def call(question, prompt, **kwargs):
        captured.update(question=question, prompt=prompt)
        captured["kwargs"] = {
            key: sorted(value)
            if isinstance(value, set)
            else value.__name__
            if isinstance(value, type)
            else value
            for key, value in kwargs.items()
        }
        raise CaptureCall

    node._call_llm = call
    fixed_clock = SimpleNamespace(now=lambda tz: datetime.fromisoformat(TIME))
    with (
        patch.object(focused, "datetime", fixed_clock),
        patch.object(query_answer, "datetime", fixed_clock),
        pytest.raises(CaptureCall),
    ):
        node.execute(state)
    assert [vars(tool) for tool in original] == before
    captured["tools"] = [vars(tool) for tool in node.tools]
    return captured


def _autonomous(stage, lane, catalog):
    state = {
        "question": QUESTION,
        "original_question": "父任务 {parent}",
        "request_time_utc": TIME,
        "request_contract": {"route": "full_diagnosis", "task": "diagnose"},
    }
    if lane:
        state["diagnosis_target"] = {
            "group_id": "g{1}",
            "entities": [{"namespace": "空间", "name": "pod{id}"}],
        }
    return _capture(getattr(diagnosis, stage)(), state, catalog)


def _focused(task, catalog):
    return _capture(
        focused.FocusedTaskNode(),
        {
            "question": QUESTION,
            "request_contract": {"task": task, "literal": "{json}"},
        },
        catalog,
    )


def _query(original, task):
    return _capture(
        query_answer.QueryCollectNode(),
        {
            "question": QUESTION,
            "original_question": "父问题 {original}" if original else "",
            "request_contract": {"task": task, "literal": "{json}"},
        },
        True,
    )


CASES = {
    **{
        f"{stage}-{lane}-{catalog}": lambda s=stage, l=lane, c=catalog: _autonomous(s, l, c)
        for stage in ("DiagnosisStageNode", "DiagnosisEvidenceNode", "DiagnosisRootCauseNode")
        for lane in (False, True)
        for catalog in (False, True)
    },
    **{
        f"focused-{task}-{catalog}": lambda t=task, c=catalog: _focused(t, c)
        for task in ("query", "explain")
        for catalog in (False, True)
    },
    **{
        f"query-{original}-{task}": lambda o=original, t=task: _query(o, t)
        for original in (False, True)
        for task in ("query", "operate")
    },
}

EXPECTED_DIGESTS = {
    # Handoff fields + optional shared Runbook guidance; tool contracts unchanged.
    "DiagnosisStageNode-False-False": "f531b82e593a7752f61d7433bf2a657ba1e06de22d1e7c8f56661fd3cdd78aa1",
    "DiagnosisStageNode-False-True": "9ed76ac98bc290656dd8394c568e6dffe5a7c6d7cd2d07c4f47000310584fe17",
    "DiagnosisStageNode-True-False": "e8aafba85501e5e0f30b93a7cdb3ddacda7b6ebdaa12c881e8d55313ba5a0ed4",
    "DiagnosisStageNode-True-True": "7b74f880e4c07c31c898e04c1b311fe101a80f3532f27b3e08a38ff7e9702fac",
    "DiagnosisEvidenceNode-False-False": "820d9ecfdb48a58c174a8d63a4a36a31959f84300f05c31f8e80aa15ff0521dd",
    "DiagnosisEvidenceNode-False-True": "f05fdb03db2f73fc5ff4934ce879d71683fd892b29b8f1c6ae951d3295ac2541",
    "DiagnosisEvidenceNode-True-False": "a0d0625fb60c58aab4baf477d7c55f3c8cc891d3adfee1d89614fb57b4bc117c",
    "DiagnosisEvidenceNode-True-True": "5e4eec9e87ccb1015ecf63e47189369a82ef68770d6251406df44b9d9101f149",
    "DiagnosisRootCauseNode-False-False": "3e0b6f272b9b43ccec75e42fac99cfb73e362de7752acbcdfc9185dea02fe027",
    "DiagnosisRootCauseNode-False-True": "3e0b6f272b9b43ccec75e42fac99cfb73e362de7752acbcdfc9185dea02fe027",
    "DiagnosisRootCauseNode-True-False": "3964aa9b58220a83fce176dc5b81b4858f104f0989680d678501eb336c3ea0e7",
    "DiagnosisRootCauseNode-True-True": "3964aa9b58220a83fce176dc5b81b4858f104f0989680d678501eb336c3ea0e7",
    "focused-query-False": "870561bee4aa85c3c0371116af3e58b6cad46c7fba6ad7acd0e4245c4065be13",
    "focused-query-True": "870561bee4aa85c3c0371116af3e58b6cad46c7fba6ad7acd0e4245c4065be13",
    "focused-explain-False": "107d2504391ad261c5e65510f7c964998dc5f00e0242bcf944b3947d9aa45c8a",
    "focused-explain-True": "107d2504391ad261c5e65510f7c964998dc5f00e0242bcf944b3947d9aa45c8a",
    # Metric guidance intentionally updated in query/deep; focused stays unchanged.
    "query-False-query": "91655d35862d829761f7f1edc1f3d163bb1a83d1b1bc6e1091c1a3a059e1c967",
    "query-False-operate": "bdc102f83401599602fc55716b19d3c90cfd292463956f6d2736207928305d77",
    "query-True-query": "6cc32df21cc97aaed6dd5bcbb1dcbcde3dcb3eaead3500c112e31e949a4940d2",
    "query-True-operate": "1702de940192615c3c7f056da46c8dee5e8efff8446c4b73eae326a324d5fe6e",
}


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


@pytest.mark.parametrize("case", CASES)
def test_task_context_message_bytes(case):
    assert _digest(CASES[case]()) == EXPECTED_DIGESTS[case]


def test_parallel_lane_question_and_fanin_contract(monkeypatch):
    node = parallel.AutonomousParallelNode(
        SimpleNamespace(_build_request_scoped_ai_call=lambda: SimpleNamespace())
    )
    node.current_run_id = "parent"
    group = {
        "group_id": "g1",
        "question": QUESTION,
        "entities": [{"namespace": "中文{ns}", "name": "pod{1}"}],
    }
    seen = []

    def execute(self, state):
        seen.append(copy.deepcopy(state))
        return {"query_draft": "stage result"}

    monkeypatch.setattr(diagnosis.DiagnosisEvidenceNode, "execute", execute)
    monkeypatch.setattr(diagnosis.DiagnosisRootCauseNode, "execute", execute)
    monkeypatch.setattr(parallel, "build_working_material", lambda state: state)
    state = {
        "question": "parent question",
        "original_question": "authoritative parent",
        "request_contract": {"scope": "namespace"},
        "query_draft": "location",
        "thinking_events": [],
    }
    before = copy.deepcopy(state)
    result, events = node._run_lane(group, state)
    assert state == before
    assert len(seen) == 2
    for local in seen:
        assert local["question"] == '本分支只诊断 中文{ns}/pod{1}：原问题 {literal}\n`Pod` "中文"'
        assert local["original_question"] == "authoritative parent"
        assert local["request_contract"] == {
            "scope": "pod",
            "namespaces": ["中文{ns}"],
            "pod_names": ["pod{1}"],
        }
    assert result["status"] == "completed"
    assert events == []
    node.current_run_id = ""
    assert node.execute({})["query_draft"] == (
        "各 Pod 分支已结束；请按 parallel_results 中的各组证据和限制汇总，不把分支完成等同于根因确认。"
    )


def test_query_runbook_ids_stay_dynamic_and_original_tools_unchanged(monkeypatch):
    monkeypatch.setattr(query_answer, "reference_description", lambda path: "运维参考手册")
    node = query_answer.QueryCollectNode()
    tool = _tools()[0]
    tool.runbook_dirs = ["virtual-directory"]
    node.tools = [tool]
    node.runbook_catalog = SimpleNamespace(catalog=[])
    paths = [
        SimpleNamespace(stem="z{id}", name="z{id}.md"),
        SimpleNamespace(stem="a", name="a.md"),
    ]
    monkeypatch.setattr(
        query_answer, "Path", lambda directory: SimpleNamespace(glob=lambda pattern: paths)
    )
    assert node._prepare_query_tools() == "- a.md: 运维参考手册\n- z{id}.md: 运维参考手册"
    assert node.tools[0].allowed_runbook_ids == ["a", "z{id}"]
    assert tool.allowed_runbook_ids == ["z{literal}", "中文\n`id`"]
    assert tool.description == "original runbook"
    assert node.tools[0].description == (
        "读取指定 Runbook 全文作为参考。按原问题选取相关知识，不要求执行全部步骤；手册不是环境事实。"
    )
