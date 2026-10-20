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
    "DiagnosisStageNode-False-False": "a8b15358198f5ca36541634c13f8775766e573aa2cca726c7e34f8f6e4dc0613",
    "DiagnosisStageNode-False-True": "523efee88c76a8fd0f66355b4ed8f36b7971df116294416122ae3f3eb44c367e",
    "DiagnosisStageNode-True-False": "faa8d2662bd71bcf9ee8659f136f58b9692906fdc6c0113d192c0405ec2bf32e",
    "DiagnosisStageNode-True-True": "f9ad6e891ba5b9a8b97af25d45c045a8f17c8b11bbca48d3b61c612bf4584499",
    "DiagnosisEvidenceNode-False-False": "a13e66910024ca8025bb49bc76aae97de677bf2bf5b751c467457d0ddc879bd9",
    "DiagnosisEvidenceNode-False-True": "1e2b33a11984a6ca7b0bddbe2bccae56e6168771723357efad90b09e0d1845bb",
    "DiagnosisEvidenceNode-True-False": "876472c7d50b825567d8780f33ae6f500185417c940f69cc880a5b728c5d9334",
    "DiagnosisEvidenceNode-True-True": "7574d60f0976c92a5550374ee59ea406129ad844652e5ed4b75fe43dfe6c016f",
    "DiagnosisRootCauseNode-False-False": "9c98032d2c7558644199bd635b16b1aec5b5f35f1321da0ce721fa430860d81c",
    "DiagnosisRootCauseNode-False-True": "9c98032d2c7558644199bd635b16b1aec5b5f35f1321da0ce721fa430860d81c",
    "DiagnosisRootCauseNode-True-False": "164f18202c03cf4c508b5d447ae3607f356f14a38a6d3466090176142eaf239d",
    "DiagnosisRootCauseNode-True-True": "164f18202c03cf4c508b5d447ae3607f356f14a38a6d3466090176142eaf239d",
    "focused-query-False": "870561bee4aa85c3c0371116af3e58b6cad46c7fba6ad7acd0e4245c4065be13",
    "focused-query-True": "870561bee4aa85c3c0371116af3e58b6cad46c7fba6ad7acd0e4245c4065be13",
    "focused-explain-False": "107d2504391ad261c5e65510f7c964998dc5f00e0242bcf944b3947d9aa45c8a",
    "focused-explain-True": "107d2504391ad261c5e65510f7c964998dc5f00e0242bcf944b3947d9aa45c8a",
    # Metric guidance intentionally updated in query/deep; focused stays unchanged.
    "query-False-query": "1a5ebdcae1afc765dcae60a642c9a650a9417d72c4e090331a79859173a91d4f",
    "query-False-operate": "ab76765b021fca92bcd36a5aa7dfc29550879b0b6db780c88f7569cd7b222848",
    "query-True-query": "e5075d66a4e7159c68c3207c1474189d5715bead9aaaa5bf2e68357c6b520b08",
    "query-True-operate": "a041d4bb3073ce5958531f805a3d8f468c70f5ef7c230447a60ff72ef3522fdf",
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
