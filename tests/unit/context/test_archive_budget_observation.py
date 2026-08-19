import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.context.archive import ContextArchive, get_archive_root
from app.core.context import budget as budget_module
from app.core.context.budget import (
    ContextBudgetEstimator,
    ModelContextResolver,
    count_tokens,
    serialize_tool_schema,
)
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


def test_context_archive_atomic_json_returns_reloadable_digest(tmp_path):
    archive = ContextArchive(run_id="run-atomic", root=str(tmp_path))

    ref = archive.write_json_atomic("lane/value.json", {"value": "真实证据"})

    path = tmp_path / "run-atomic" / "lane" / "value.json"
    assert ref["path"] == str(path)
    assert ref["bytes"] == path.stat().st_size
    assert len(ref["sha256"]) == 64
    assert json.loads(path.read_text(encoding="utf-8")) == {"value": "真实证据"}
    assert list(path.parent.glob(".*.tmp")) == []


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


def test_hard_input_budget_reserves_output_and_safety_margin():
    limit = budget_module.calculate_hard_input_limit(
        context_window=32000,
        output_reserved=6000,
        safety_margin=2000,
        input_ratio=0.72,
    )

    assert limit == 23040


def test_serialize_tool_schema_preserves_openai_dict_tool_contract():
    serialized = serialize_tool_schema([
        {
            "type": "function",
            "function": {
                "name": "query_pod_logs",
                "description": "query real pod logs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "pod": {"type": "string"},
                    },
                },
            },
        }
    ])

    assert serialized == [
        {
            "name": "query_pod_logs",
            "description": "query real pod logs",
            "args_schema": {
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "pod": {"type": "string"},
                },
            },
        }
    ]


def test_fallback_token_counter_is_conservative_for_dense_cjk():
    text = "中文故障证据" * 100
    counted = count_tokens(
        text,
        model="openai/Qwen3.6-35B-A3B",
    )

    assert counted["accuracy"] == "estimated"
    assert counted["source"] == "heuristic:utf8_bytes/3"
    assert counted["tokens"] >= len(text)


def test_deterministic_token_compaction_preserves_head_tail_and_budget():
    text = (
        "HEAD primary entity k8s.pod:demo/api\n"
        + ("middle-observation " * 4000)
        + "\nTAIL output schema and limitations"
    )

    compacted = budget_module.compact_text_to_token_budget(
        text,
        max_tokens=400,
        model="openai/Qwen3.6-35B-A3B",
        preserve_tail_tokens=80,
    )

    assert count_tokens(compacted, model="openai/Qwen3.6-35B-A3B")["tokens"] <= 400
    assert compacted.startswith("HEAD primary entity")
    assert compacted.endswith("TAIL output schema and limitations")
    assert "deterministic context compaction" in compacted


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


def test_context_budget_log_is_compact_when_token_count_exact(monkeypatch, caplog):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "1000")
    monkeypatch.setenv("AIOPS_TIKTOKEN_ENCODING", "cl100k_base")
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    estimator = ContextBudgetEstimator()
    budget = estimator.estimate(
        node_id="evidence",
        model="openai/test",
        system_prompt="",
        user_message="",
        components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "hello world"},
            {"name": "user_message", "category": "static_input", "content": "hello"},
            {"name": "tool_observations", "category": "dynamic_runtime", "content": "hello world hello"},
            {"name": "scratchpad_reserved", "category": "reserved", "tokens": 10},
            {"name": "output_reserved", "category": "reserved", "tokens": 20},
        ],
    )

    with caplog.at_level(logging.INFO, logger="app.core.context.budget"):
        estimator.log(budget)

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "input_tokens=6" in text
    assert "budget_tokens=36" in text
    assert "token=exact" in text
    assert "[context_budget.top]" in text
    assert "startup_prompt=" not in text


def test_context_budget_log_uses_estimated_values_without_unknown_top(monkeypatch, caplog):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "1000")
    monkeypatch.delenv("AIOPS_TIKTOKEN_ENCODING", raising=False)
    monkeypatch.delenv("AIOPS_TOKENIZER_JSON_PATH", raising=False)
    estimator = ContextBudgetEstimator()
    budget = estimator.estimate(
        node_id="layer",
        model="openai/test",
        system_prompt="",
        user_message="",
        components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "中文测试"},
            {"name": "output_reserved", "category": "reserved", "tokens": 20},
        ],
    )

    with caplog.at_level(logging.INFO, logger="app.core.context.budget"):
        estimator.log(budget)

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "token=estimated" in text
    assert "input_tokens=~" in text
    assert "[context_budget.top]" in text
    assert "unknown(" not in text


def test_fetch_runbook_structured_metadata_includes_requested_runbook_id(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path))

    observation = processor.process(
        run_id="run-rb",
        node_id="layer",
        sequence=1,
        tool_name="fetch_runbook",
        raw_content="<runbook>\n# Pod Terminating Stuck\n</runbook>",
        tool_args={"runbook_id": "pod-terminating-stuck.md"},
    )

    assert observation["structured"]["runbook_id"] == "pod-terminating-stuck.md"
    assert observation["structured"]["runbook_name"] == "pod-terminating-stuck"


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


def test_observation_processor_describe_preserves_pod_diagnostic_sections(tmp_path):
    raw = """
Name:                      rc-terminating-long-grace
Namespace:                 aiops-e2e
Node:                      node1/10.2.0.49
Status:                    Terminating (lasts <invalid>)
Termination Grace Period:  600s
Containers:
  app:
    Image:         busybox:1.36
    Command:
      sh
      -c
      trap 'sleep 600' TERM; sleep 86400
    State:          Running
    Ready:          True
    Restart Count:  0
Conditions:
  Type              Status
  Ready             True
Volumes:
  kube-api-access-z74xs:
    Type:                    Projected
QoS Class:                   BestEffort
Events:
  Type    Reason          Age   From               Message
  Normal  Killing         3m4s  kubelet            Stopping container app
""" + ("noise\n" * 200)
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1600)

    processed = processor.process(
        run_id="run-describe-pod-sections",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content=raw,
    )

    summary = processed["summary"]
    structured = processed["structured"]

    assert "Termination Grace Period:  600s" in summary
    assert "Command:" in summary
    assert "trap 'sleep 600' TERM; sleep 86400" in summary
    assert "Normal  Killing" in summary
    assert structured["lifecycle"]["termination_grace_period"] == "600s"
    assert structured["containers"][0]["name"] == "app"
    assert "trap 'sleep 600' TERM; sleep 86400" in structured["containers"][0]["command"]
    assert any("Killing" in event for event in structured["events"])


def test_observation_processor_extracts_pod_yaml_image_pull_fields(tmp_path):
    raw = """
apiVersion: v1
kind: Pod
metadata:
  name: ham-wcc79
  namespace: xnet
  ownerReferences:
  - kind: DaemonSet
    name: ham
spec:
  serviceAccountName: hwaccel-manager
  nodeName: master
  containers:
  - name: ham
    image: xnet.registry.io:8443/ham/ham:v2.24
    imagePullPolicy: IfNotPresent
  volumes:
  - name: config-volume
    configMap:
      name: ham-config
status:
  phase: Pending
  containerStatuses:
  - name: ham
    state:
      waiting:
        reason: ImagePullBackOff
        message: Back-off pulling image "xnet.registry.io:8443/ham/ham:v2.24"
"""
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)

    processed = processor.process(
        run_id="run-pod-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content=raw,
    )

    structured = processed["structured"]
    assert structured["kind"] == "Pod"
    assert structured["name"] == "ham-wcc79"
    assert structured["namespace"] == "xnet"
    assert structured["serviceAccountName"] == "hwaccel-manager"
    assert structured["imagePullSecrets"] == []
    assert structured["imagePullSecrets_present"] is False
    assert structured["containers"][0]["image"] == "xnet.registry.io:8443/ham/ham:v2.24"
    assert structured["containerStatuses"][0]["waiting"]["reason"] == "ImagePullBackOff"
    assert "imagePullSecrets: <absent>" in processed["summary"]
    assert "serviceAccountName: hwaccel-manager" in processed["summary"]


def test_observation_processor_extracts_terminating_pod_lifecycle_fields(tmp_path):
    raw = """
apiVersion: v1
kind: Pod
metadata:
  name: rc-terminating-prestop
  namespace: aiops-e2e
  deletionTimestamp: "2026-05-18T01:00:00Z"
  deletionGracePeriodSeconds: 600
  finalizers:
  - aiops.e2e/hold
spec:
  nodeName: node1
  terminationGracePeriodSeconds: 600
  containers:
  - name: app
    image: busybox:1.36
    command:
    - sh
    - -c
    args:
    - trap 'sleep 600' TERM; sleep 86400
    lifecycle:
      preStop:
        exec:
          command:
          - sh
          - -c
          - sleep 600
status:
  phase: Running
"""
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=3000)

    processed = processor.process(
        run_id="run-terminating-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content=raw,
    )

    structured = processed["structured"]
    assert structured["deletionTimestamp"] == "2026-05-18T01:00:00Z"
    assert structured["finalizers"] == ["aiops.e2e/hold"]
    assert structured["terminationGracePeriodSeconds"] == 600
    assert structured["containers"][0]["lifecycle"]["preStop"]["exec"]["command"] == ["sh", "-c", "sleep 600"]
    assert "deletionTimestamp: 2026-05-18T01:00:00Z" in processed["summary"]
    assert "finalizers: aiops.e2e/hold" in processed["summary"]
    assert "terminationGracePeriodSeconds: 600" in processed["summary"]
    assert "lifecycle:" in processed["summary"]
    assert "preStop" in processed["summary"]


def test_observation_processor_extracts_secret_yaml_type_and_data_keys(tmp_path):
    raw = """
apiVersion: v1
kind: Secret
metadata:
  name: xnet-bmcs
  namespace: xnet
type: Opaque
data:
  bmc.json: W10=
"""
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-secret-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content=raw,
    )

    structured = processed["structured"]
    assert structured["kind"] == "Secret"
    assert structured["type"] == "Opaque"
    assert structured["data_keys"] == ["bmc.json"]
    assert structured["has_dockerconfigjson"] is False
    assert "type: Opaque" in processed["summary"]
    assert "data_keys: bmc.json" in processed["summary"]
    assert "has_dockerconfigjson: False" in processed["summary"]


def test_observation_processor_secret_table_does_not_treat_none_labels_as_abnormal(tmp_path):
    raw = """NAME                            TYPE     DATA   AGE    LABELS
observability-admission         Opaque   3      215d   <none>
observability-kibana-es-token   Opaque   1      3d21h  <none>
xnet-bmcs                       Opaque   1      214d   <none>
"""
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-secret-table",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_namespace",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 0
    assert "abnormal=0" in processed["summary"]


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


def test_observation_processor_keeps_fetch_runbook_full_by_default(tmp_path):
    raw = "<runbook>\n" + ("诊断步骤：检查 Pod 事件和状态。\n" * 200) + "</runbook>"
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=300)

    processed = processor.process(
        run_id="run-runbook",
        node_id="evidence",
        sequence=1,
        tool_name="fetch_runbook",
        raw_content=raw,
        context_usage_ratio=0.2,
    )

    assert processed["summary"] == raw
    assert processed["processor"] == "runbook+passthrough_full"


def test_observation_processor_compresses_fetch_runbook_under_context_pressure(tmp_path):
    calls = []

    def summarizer(tool, raw, current_summary):
        calls.append((tool, raw, current_summary))
        return "压缩后的 runbook: 只保留诊断步骤和禁用修复动作。"

    raw = "<runbook>\n" + ("诊断步骤：检查 Pod 事件和状态。\n" * 200) + "</runbook>"
    processor = ObservationProcessor(
        archive_root=str(tmp_path),
        max_observation_chars=300,
        summarizer=summarizer,
    )

    processed = processor.process(
        run_id="run-runbook-pressure",
        node_id="evidence",
        sequence=1,
        tool_name="fetch_runbook",
        raw_content=raw,
        context_usage_ratio=0.9,
    )

    assert calls
    assert processed["summary"] == "压缩后的 runbook: 只保留诊断步骤和禁用修复动作。"
    assert processed["processor"] == "runbook+passthrough_full+llm_budget"


def test_observation_processor_context_guard_truncates_runbook_without_summarizer(tmp_path):
    raw = "<runbook>\n" + ("诊断步骤：检查 Pod 事件和状态。\n" * 200) + "</runbook>"
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=300)

    processed = processor.process(
        run_id="run-runbook-pressure-no-ai",
        node_id="evidence",
        sequence=1,
        tool_name="fetch_runbook",
        raw_content=raw,
        context_usage_ratio=0.9,
    )

    assert len(processed["summary"]) <= 300
    assert "完整内容见 raw_ref" in processed["summary"]
    assert processed["processor"] == "runbook+passthrough_full+context_guard_truncate"


def test_table_row_running_not_ready_is_abnormal():
    """observation 表格摘要：0/1 Running 行必须入选异常行；Completed 0/1 不算。"""
    from app.core.context.observation import ObservationProcessor
    proc = ObservationProcessor.__new__(ObservationProcessor)
    header_cols = ["NAMESPACE", "NAME", "READY", "STATUS", "RESTARTS", "AGE"]
    status_indexes = {i for i, c in enumerate(header_cols) if c in {"READY", "STATUS", "REASON", "PHASE"}}
    pure_status_indexes = {i for i, c in enumerate(header_cols) if c in {"STATUS", "REASON", "PHASE"}}
    row_not_ready = "aiops-case-09  workload-x  0/1  Running  0  5m"
    row_healthy = "kube-system  coredns-abc  1/1  Running  0  10d"
    row_completed = "batch  job-xyz  0/1  Completed  0  1h"
    assert proc._table_row_is_abnormal(row_not_ready, status_indexes, pure_status_indexes, set()) is True
    assert proc._table_row_is_abnormal(row_healthy, status_indexes, pure_status_indexes, set()) is False
    assert proc._table_row_is_abnormal(row_completed, status_indexes, pure_status_indexes, set()) is False
