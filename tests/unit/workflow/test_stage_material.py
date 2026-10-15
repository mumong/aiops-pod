from copy import deepcopy

from app.core.workflow.stage_material import branch_state, stage_material


def source():
    targets = [
        {
            "target_id": name,
            "entity": {"kind": "Pod", "namespace": "ns", "name": name, "uid": "uid-" + name},
            "issue": "需要核实的线索",
            "status": "investigate",
            "evidence_refs": ["/archive/lifecycle"],
        }
        for name in ("a", "b")
    ]
    return {
        "question": "检查Pod",
        "query_draft": "全局很长的定位分析",
        "diagnosis_handoff": {
            "contract_version": "location-handoff.v1",
            "targets": targets,
            "coverage": "complete",
        },
        "thinking_events": [
            {
                "type": "tool_result",
                "tool_name": "query_pod_lifecycle",
                "result": "normal-pod-detail" * 10000,
            }
        ],
        "diagnosis_events_start": 1,
    }


def test_branch_receives_only_own_identity_and_handles_not_parent_history():
    state = source()
    before = deepcopy(state)
    group = {
        "group_id": "g1",
        "target_id": "a",
        "question": "检查a",
        "entities": [state["diagnosis_handoff"]["targets"][0]["entity"]],
    }
    local = branch_state(state, group)
    assert len(local["diagnosis_handoff"]["targets"]) == 1
    assert local["diagnosis_handoff"]["targets"][0]["target_id"] == "a"
    assert not local["thinking_events"]
    assert "query_draft" not in local
    local["diagnosis_handoff"]["targets"][0]["issue"] = "changed"
    assert state == before


def test_evidence_discards_parent_lifecycle_and_location_prose():
    material = stage_material(source(), "evidence")
    assert material["observations"] == []
    assert material["analysis_draft"] == ""
    assert "lifecycle_core" not in material["protected_handoff"]
    assert "parallel_results" not in material


def test_rca_keeps_own_tool_evidence_and_analysis_but_not_global_history():
    state = source()
    state["query_draft"] = "本组证据分析"
    state["thinking_events"].append(
        {
            "type": "tool_result",
            "tool_name": "kubectl_logs",
            "status": "success",
            "result": "actual error",
            "raw_ref": "/archive/log",
        }
    )
    material = stage_material(state, "rca")
    assert len(material["observations"]) == 1
    assert material["observations"][0]["result"] == "actual error"
    assert material["analysis_draft"] == "本组证据分析"
    assert "normal-pod-detail" not in str(material)


def test_compaction_cannot_reinflate_stage_protection():
    from app.core.context.handoff import protected_handoff

    material = stage_material(source(), "evidence")
    material["observations"] = [{"raw_ref": "/raw/huge", "result": "x" * 100000}]
    material["parallel_results"] = [{"group_id": "other", "material": {"analysis_draft": "huge"}}]
    protected = protected_handoff(material)
    assert set(protected) == {"context_policy", "diagnosis_handoff"}


def test_evidence_core_survives_only_into_own_rca(monkeypatch):
    import json
    from types import SimpleNamespace

    from app.core.context.handoff import protected_handoff
    from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisEvidenceNode

    node = DiagnosisEvidenceNode()
    node.ai_call = SimpleNamespace()
    core = {
        "key_facts": [
            {"statement": "原始错误", "observed_at": "", "evidence_refs": ["/archive/error"]}
        ],
        "unresolved": ["配置来源待核实"],
        "runbook_refs": ["runbook/ref"],
    }

    def call(text, prompt, **kwargs):
        assert kwargs["response_schema"].__name__ == "EvidenceStageOutput"
        return SimpleNamespace(result=json.dumps({"analysis": "普通分析", **core})), []

    node._call_llm = call
    state = source()
    state.update(node.execute(state))
    material = stage_material(state, "rca")
    assert protected_handoff(material)["evidence_handoff"] == core
    assert material["analysis_draft"] == "普通分析"
    assert "evidence_handoff" not in stage_material(state, "evidence")["protected_handoff"]


def test_real_rca_node_publishes_report_and_index_to_archive(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    from app.core.workflow.nodes.autonomous_diagnosis import DiagnosisRootCauseNode

    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    node = DiagnosisRootCauseNode()
    node.current_run_id = "rca-delivery"
    node.ai_call = SimpleNamespace()
    state = source()
    state["diagnosis_handoff"]["targets"] = state["diagnosis_handoff"]["targets"][:1]
    state["thinking_events"].append(
        {
            "type": "tool_result",
            "tool_name": "kubectl_logs",
            "raw_ref": "/archive/error",
            "result": "原始错误",
            "status": "success",
        }
    )

    def call(text, prompt, **kwargs):
        assert "normal-pod-detail" not in text
        assert kwargs["response_schema"].__name__ == "DiagnosisCaseOutput"
        return SimpleNamespace(
            result=json.dumps(
                {
                    "outcome": "inconclusive",
                    "summary": "证据不足",
                    "certainty": "unknown",
                    "unresolved": ["尚未确认原因"],
                    "report": "未确认根因，需补充证据。",
                }
            )
        ), []

    node._call_llm = call
    result = node.execute(state)
    case = result["diagnosis_case_result"]
    assert case["target"]["target_id"] == "a"
    assert case["report"] == result["rca_analysis"]
    assert json.loads((tmp_path / "rca-delivery/cases/result.json").read_text()) == case
    index = json.loads((tmp_path / "rca-delivery/cases/evidence-index.json").read_text())
    assert index["observations"] == [
        {"tool_name": "kubectl_logs", "raw_ref": "/archive/error", "status": "success"}
    ]
    assert case["evidence_index_ref"].endswith("/cases/evidence-index.json")


def test_actual_compactor_keeps_selected_core_and_not_lifecycle(monkeypatch):
    import asyncio
    import json

    from app.core.aicall.working_context import compact_working_material

    state = source()
    core = {
        "key_facts": [{"statement": "关键原始错误", "evidence_refs": ["/raw/log"]}],
        "unresolved": ["原因未定"],
        "runbook_refs": [],
    }
    state["diagnosis_evidence_handoff"] = core
    material = stage_material(state, "rca")
    material["analysis_draft"] = "可压缩分析" * 10000

    async def summarize(*args, **kwargs):
        return "压缩后的普通分析"

    monkeypatch.setattr("app.core.aicall.working_context.summarize_history", summarize)
    compact = asyncio.run(compact_working_material(object(), material, lambda **kw: None))
    assert compact["protected_handoff"]["evidence_handoff"] == core
    assert "lifecycle_core" not in compact["protected_handoff"]
    assert len(json.dumps(compact, ensure_ascii=False)) < 3000
