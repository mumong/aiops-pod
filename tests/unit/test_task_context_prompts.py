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
    # 2026-10-20: layer/evidence/RCA prompts add symptom-vs-cause and verification rules.
    "DiagnosisStageNode-False-False": "bbfd23e7d67310cbe0f2a0da523af9b074a5adfc4b2828b2670e4ee85709128b",
    "DiagnosisStageNode-False-True": "afa453e2211da333a5b776a76dcbd515fade45cd40f9747650463dfa00d7c21e",
    "DiagnosisStageNode-True-False": "72ade31dcc51babc4138ef0d4a34e3727ceff6746de17d970a13c45d21d5b278",
    "DiagnosisStageNode-True-True": "bbe8b057e94061f05d473e87a1cc916054dbb9f1d8652b921a41ce5af96ec9eb",
    "DiagnosisEvidenceNode-False-False": "f41a60eb6dddfdb06a2ab5707aaef1e61ced1a38647bc530bc7d702f665c28f1",
    "DiagnosisEvidenceNode-False-True": "e35bbbf5ffebf17c95481acb5159bb04d19d823a852463cb53f6bbed17487a8e",
    "DiagnosisEvidenceNode-True-False": "930d6f88b2eb098e9a48d3d2678cb439e14da7a69fb02f85718d3d54ce0bac69",
    "DiagnosisEvidenceNode-True-True": "3339cd6b5646c1817e2ce4a56894e5ed661bbe8a5377c6a4f291b1ad32a30f2d",
    "DiagnosisRootCauseNode-False-False": "c4cc0d6c3af4543ee4377ad74b1b8a59189be9b5b03551993a8dc8d9a3f9b58c",
    "DiagnosisRootCauseNode-False-True": "c4cc0d6c3af4543ee4377ad74b1b8a59189be9b5b03551993a8dc8d9a3f9b58c",
    "DiagnosisRootCauseNode-True-False": "41f4c718d43810bf9376ab84a19dfc6658b38bb80d2d84795931cee5acff1bac",
    "DiagnosisRootCauseNode-True-True": "41f4c718d43810bf9376ab84a19dfc6658b38bb80d2d84795931cee5acff1bac",
    "focused-query-False": "870561bee4aa85c3c0371116af3e58b6cad46c7fba6ad7acd0e4245c4065be13",
    "focused-query-True": "870561bee4aa85c3c0371116af3e58b6cad46c7fba6ad7acd0e4245c4065be13",
    "focused-explain-False": "107d2504391ad261c5e65510f7c964998dc5f00e0242bcf944b3947d9aa45c8a",
    "focused-explain-True": "107d2504391ad261c5e65510f7c964998dc5f00e0242bcf944b3947d9aa45c8a",
    # Metric guidance intentionally updated in query/deep; focused stays unchanged.
    "query-False-query": "f064ba3c9205cf59a68f6940a729e185a851cb93ee3dbd6ff08d6cf9c95984b3",
    "query-False-operate": "9b3288b3646341099bba09e852e6c08dfd35931d0ea343d42085412d3a44f942",
    "query-True-query": "24660dd2f3e8f9cf74cb38f2429cc21deb75f74e3f1cfb66e27430bd65970780",
    "query-True-operate": "32368977428776d29476f0d6b99e7b90262a5c3a5fc12e7ce18214dd5f4d97e2",
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
