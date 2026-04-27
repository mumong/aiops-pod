import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.context.archive import ContextArchive, get_archive_root
from app.core.context.budget import ContextBudgetEstimator, ModelContextResolver, count_tokens
from app.core.context.observation import ObservationProcessor


def test_context_archive_writes_raw_structured_and_summary(tmp_path):
    archive = ContextArchive(run_id="run-1", root=str(tmp_path))

    refs = archive.write_tool_artifact(
        node_id="layer",
        sequence=1,
        tool_name="kubectl_describe",
        raw="Name: pod-a\nStatus: Failed\n",
        structured={"status": "Failed"},
        summary="Pod pod-a Failed",
    )

    assert refs["raw_ref"].endswith("001-layer-kubectl_describe.raw.txt")
    assert refs["structured_ref"].endswith("001-layer-kubectl_describe.structured.json")
    assert refs["summary_ref"].endswith("001-layer-kubectl_describe.summary.txt")
    assert (tmp_path / "run-1" / "tools" / "001-layer-kubectl_describe.raw.txt").read_text() == "Name: pod-a\nStatus: Failed\n"
    assert json.loads((tmp_path / "run-1" / "tools" / "001-layer-kubectl_describe.structured.json").read_text()) == {"status": "Failed"}


def test_context_archive_writes_node_handoff_and_io(tmp_path):
    archive = ContextArchive(run_id="run-io", root=str(tmp_path))

    refs = archive.write_node_artifacts(
        node_id="evidence",
        input_payload={"question": "q", "layer_handoff": {"layer": "L3"}},
        output_payload={"evidence_facts": [{"id": "e1"}]},
        handoff_payload={"to": "rca", "summary": "evidence ready"},
    )

    assert refs["input_ref"].endswith("node_inputs/evidence.input.json")
    assert refs["output_ref"].endswith("node_outputs/evidence.output.json")
    assert refs["handoff_ref"].endswith("handoff/evidence-to-rca.json")
    assert json.loads((tmp_path / "run-io" / "node_inputs" / "evidence.input.json").read_text())["question"] == "q"
    assert json.loads((tmp_path / "run-io" / "handoff" / "evidence-to-rca.json").read_text())["summary"] == "evidence ready"


def test_archive_root_prefers_reports_subdir_when_default_parent_is_not_writable(tmp_path, monkeypatch):
    default_root = tmp_path / "aiops" / "context_archives"
    reports_root = tmp_path / "aiops" / "reports"
    reports_root.mkdir(parents=True)

    monkeypatch.delenv("AIOPS_CONTEXT_ARCHIVE_ROOT", raising=False)
    monkeypatch.setattr("app.core.context.archive.DEFAULT_ARCHIVE_ROOT", str(default_root))
    monkeypatch.setattr("app.core.context.archive.REPORTS_ARCHIVE_ROOT", str(reports_root / "context_archives"))
    monkeypatch.setattr("app.core.context.archive.os.access", lambda path, mode: str(path) == str(reports_root))

    assert get_archive_root() == str(reports_root / "context_archives")


def test_context_budget_estimator_reports_required_categories(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32768")
    estimator = ContextBudgetEstimator()

    budget = estimator.estimate(
        node_id="evidence",
        model="openai/Qwen3-32B",
        system_prompt="系统提示 " * 100,
        user_message="用户问题 " * 50,
        tool_count=15,
        handoff={"layer": "L3", "active_entities": [{"type": "Pod", "name": "pod-a"}]},
        tool_traces=[{"result": "tool output " * 20}],
    )

    assert budget["context_window"] == 32768
    for key in [
        "startup_prompt",
        "user",
        "tool_schema",
        "handoff",
        "tool_traces",
        "scratchpad_reserved",
        "output_reserved",
        "estimated_total",
        "usage_ratio",
    ]:
        assert key in budget
    assert budget["estimated_total"] > 0


def test_model_context_resolver_prefers_env_exact(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "49152")

    resolved = ModelContextResolver().resolve("openai/Qwen3-32B-AWQ")

    assert resolved["context_window"] == 49152
    assert resolved["source"] == "env:MODEL_CONTEXT_WINDOW"
    assert resolved["accuracy"] == "exact"


def test_model_context_resolver_reads_openai_compatible_metadata(monkeypatch):
    monkeypatch.delenv("MODEL_CONTEXT_WINDOW", raising=False)
    ModelContextResolver._metadata_cache.clear()

    class _Response:
        status_code = 200

        def json(self):
            return {
                "data": [
                    {
                        "id": "Qwen3-32B-AWQ",
                        "max_model_len": 32768,
                    }
                ]
            }

    calls = []

    def _fake_get(url, timeout=0, headers=None):
        calls.append(url)
        return _Response()

    monkeypatch.setattr("app.core.context.budget.requests.get", _fake_get)

    resolved = ModelContextResolver().resolve(
        "openai/Qwen3-32B-AWQ",
        api_base="http://llm.example/v1",
        api_key="sk-test",
    )

    assert resolved["context_window"] == 32768
    assert resolved["source"].startswith("metadata:")
    assert resolved["accuracy"] == "exact"
    assert calls
    assert calls[0].endswith("/models/Qwen3-32B-AWQ")


def test_count_tokens_uses_explicit_tiktoken_encoding_exact(monkeypatch):
    monkeypatch.setenv("AIOPS_TIKTOKEN_ENCODING", "cl100k_base")
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)

    counted = count_tokens("hello world", model="openai/test")

    assert counted["tokens"] == 2
    assert counted["accuracy"] == "exact"
    assert counted["source"] == "tiktoken:cl100k_base"


def test_context_budget_estimator_marks_actual_and_reserved_tokens(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "1000")
    monkeypatch.setenv("AIOPS_TIKTOKEN_ENCODING", "cl100k_base")
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    estimator = ContextBudgetEstimator()

    budget = estimator.estimate(
        node_id="evidence",
        model="openai/test",
        system_prompt="hello world",
        user_message="hello",
        components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "hello world"},
            {"name": "user_message", "category": "static_input", "content": "hello"},
            {"name": "scratchpad_reserved", "category": "reserved", "tokens": 10},
            {"name": "output_reserved", "category": "reserved", "tokens": 20},
        ],
    )

    assert budget["token_count_accuracy"] == "exact"
    assert budget["actual_context_tokens"] == 3
    assert budget["reserved_tokens"] == 30
    assert budget["estimated_total"] == 33


def test_context_budget_estimator_reports_component_percentages(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "1000")
    estimator = ContextBudgetEstimator()

    budget = estimator.estimate(
        node_id="evidence",
        model="openai/test",
        system_prompt="",
        user_message="",
        components=[
            {"name": "runbook_catalog", "category": "static_input", "content": "a" * 300},
            {"name": "node_system_prompt", "category": "static_input", "content": "b" * 300},
            {"name": "tool_observations", "category": "dynamic_runtime", "tokens": 50},
            {"name": "output_reserved", "category": "reserved", "tokens": 100},
        ],
    )

    components = {c["name"]: c for c in budget["components"]}
    assert components["runbook_catalog"]["tokens"] == 100
    assert components["runbook_catalog"]["window_ratio"] == 0.1
    assert components["tool_observations"]["category"] == "dynamic_runtime"
    assert budget["static_context_tokens"] == 200
    assert budget["dynamic_context_tokens"] == 50
    assert budget["reserved_tokens"] == 100


def test_observation_processor_extracts_kubectl_events_empty_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=500)

    processed = processor.process(
        run_id="run-2",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_events",
        raw_content="No events found in default namespace.",
    )

    assert processed["processed"] is True
    assert processed["structured"]["status"] == "no_events_found"
    assert "没有找到事件" in processed["summary"]
    assert "raw_ref" in processed


def test_observation_processor_summarizes_large_kubectl_describe(tmp_path):
    raw = """
Name:             app-1
Namespace:        aiops-e2e
Node:             node2/10.2.0.50
Status:           Running
Containers:
  app:
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    42
Events:
  Type     Reason   Age   From     Message
  Warning  BackOff  1m    kubelet  Back-off restarting failed container app
""" + ("noise\n" * 1000)
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=800)

    processed = processor.process(
        run_id="run-3",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content=raw,
    )

    assert len(processed["summary"]) <= 800
    assert "CrashLoopBackOff" in processed["summary"]
    assert "Exit Code:    42" in processed["summary"]
    assert processed["structured"]["name"] == "app-1"
    assert processed["structured"]["namespace"] == "aiops-e2e"


def test_observation_processor_generic_large_output_is_bounded_and_archived(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=300)

    processed = processor.process(
        run_id="run-4",
        node_id="layer",
        sequence=1,
        tool_name="unknown_heavy_tool",
        raw_content="line\n" * 1000,
    )

    assert len(processed["summary"]) <= 360
    assert processed["processor"] == "generic"
    assert processed["raw_chars"] == 5000
    assert (tmp_path / "run-4" / "tools" / "001-layer-unknown_heavy_tool.raw.txt").exists()


def test_observation_processor_ai_mode_forces_llm_summary_for_small_output(tmp_path):
    calls = []

    def summarizer(tool, raw, current_summary):
        calls.append((tool, raw, current_summary))
        return "AI summary: pod-a OOMKilled"

    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=500,
        summarizer=summarizer,
        summary_mode="ai",
    )

    processed = processor.process(
        run_id="run-ai",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n",
    )

    assert calls
    assert processed["summary"] == "AI summary: pod-a OOMKilled"
    assert processed["processor"] == "k8s_describe+llm"
