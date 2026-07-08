import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.aicall.client import AICall
from app.core.context.observation import ObservationProcessor
from langchain_core.messages import AIMessage, ToolMessage


def test_aicall_process_tool_observation_returns_bounded_summary(tmp_path):
    ai = AICall(model="openai/test", api_key="sk-test")
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=500)

    processed = ai._process_tool_observation(
        processor=processor,
        run_id="run-a",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        tool_content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n" + ("noise\n" * 1000),
    )

    assert processed["processed"] is True
    assert len(processed["summary"]) <= 500
    assert "OOMKilled" in processed["summary"]
    assert processed["raw_ref"].endswith(".raw.txt")


def test_aicall_mutates_tool_message_to_bounded_observation(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n" + ("noise\n" * 1000),
        tool_call_id="tc-1",
        name="kubectl_describe",
    )

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"tools": {"messages": [msg]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "d", "args_schema": None})()
    result, events = ai.call(
        "sys",
        "q",
        tools=[tool],
        node_id="evidence",
        run_id="run-b",
        max_steps=2,
    )

    assert len(msg.content) < 3000
    assert "OOMKilled" in msg.content
    assert "raw_ref" in result.tool_calls[0]
    assert events[0]["observation_processed"] is True


def test_aicall_writes_final_budget_with_dynamic_context(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "8192")

    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n",
        tool_call_id="tc-1",
        name="kubectl_describe",
    )

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"tools": {"messages": [msg]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "describe pods", "args_schema": None})()
    ai.call(
        "system prompt",
        "user prompt",
        tools=[tool],
        node_id="evidence",
        run_id="run-dynamic",
        max_steps=2,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "system prompt"},
            {"name": "user_message", "category": "static_input", "content": "user prompt"},
        ],
    )

    budget = json.loads((tmp_path / "run-dynamic" / "budget" / "evidence.json").read_text())
    names = {c["name"] for c in budget["components"]}
    assert "tool_observations" in names
    assert "final_output" in names
    assert budget["dynamic_context_tokens"] > 0


def test_aicall_compacts_evidence_runtime_context_when_small_window_is_hot(monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    ai = AICall(model="openai/Qwen3-32B-AWQ", api_key="sk-test")
    ai._compact_context_with_lite_llm = lambda payload, **kwargs: {
        "process_summary": [
            "先输出 evidence_plan",
            "随后连续调用多个 run_bash_command 检查 registry 网络",
            "最后发现存在重复节点信息查询，应抓大放小",
        ],
        "evidence_plan": [{"id": "e1", "description": "检查 docker.io 连通性"}],
        "completed_items": [{"id": "e1", "outcome": "negative", "fact": "curl registry 超时"}],
        "open_items": [{"id": "e2", "reason": "镜像存在性未能独立验证"}],
        "key_facts": ["Pod test1-redis-master-0 为 ImagePullBackOff"],
        "negative_facts": ["curl registry-1.docker.io timed out"],
        "conflicts": [],
        "discarded_noise": ["重复 node capacity 查询"],
        "next_focus": ["不要继续查询 Node capacity，优先总结网络不可达证据"],
    }
    static_components = [
        {"name": "node_system_prompt", "category": "static_input", "content": "s" * 4000},
        {"name": "user_message", "category": "static_input", "content": "u" * 4000},
        {"name": "tool_schema", "category": "static_input", "content": "t" * 4000},
    ]
    plan_text = json.dumps({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "检查 docker.io 连通性",
                "level": "important",
                "tool": "run_bash_command",
                "command": "curl https://registry-1.docker.io/v2/",
                "purpose": "验证镜像仓库连通性",
            }
        ],
        "collection_strategy": "先确认镜像拉取失败。",
    }, ensure_ascii=False)
    thinking_events = [
        {
            "type": "ai_message",
            "node": "evidence",
            "full_content": plan_text,
            "content": plan_text[:500],
        },
        {
            "type": "ai_message",
            "node": "evidence",
            "full_content": "第一轮分析" + ("循环思考" * 3000),
            "content": "第一轮分析",
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "tool_name": "run_bash_command",
            "result": '{"success": false, "stderr": "curl: (28) timed out"}',
            "result_preview": "curl timed out",
            "semantic_success": False,
        },
        {
            "type": "tool_result",
            "node": "evidence",
            "tool_name": "run_bash_command",
            "result": '{"success": true, "stdout": "node capacity noise"}' * 1000,
            "result_preview": "node capacity noise",
            "semantic_success": True,
            "raw_ref": "/archive/tools/node.raw.txt",
            "structured_ref": "/archive/tools/node.structured.json",
            "summary_ref": "/archive/tools/node.summary.txt",
        },
    ]

    compacted = ai._maybe_compact_runtime_context(
        node_id="evidence",
        run_id="run-compact",
        static_context_components=static_components,
        thinking_events=thinking_events,
        tool_observation_contents=[
            '{"success": false, "stderr": "curl: (28) timed out"}',
            '{"success": true, "stdout": "node capacity noise"}' * 1000,
        ],
    )

    assert compacted is True
    assert thinking_events[0]["type"] == "context_summary"
    assert len([ev for ev in thinking_events if ev.get("type") == "ai_message"]) == 2
    assert len([ev for ev in thinking_events if ev.get("type") == "tool_result"]) == 2
    assert any("evidence_plan" in (ev.get("full_content") or "") for ev in thinking_events)
    assert any("timed out" in (ev.get("result") or "") for ev in thinking_events if ev.get("type") == "tool_result")
    assert any(
        "[compacted: see raw_ref/structured_ref/summary_ref]" in (ev.get("result") or "")
        for ev in thinking_events
        if ev.get("type") == "tool_result"
    )
    summary = thinking_events[0]["full_content"]
    assert "process_summary" in summary
    assert "curl registry 超时" in summary
    assert "重复 node capacity 查询" in summary
    assert all("循环思考循环思考循环思考" not in json.dumps(ev, ensure_ascii=False) for ev in thinking_events)


def test_aicall_compaction_rewrites_non_plan_ai_messages_in_agent_context(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "32000")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    ai = AICall(model="openai/Qwen3-32B-AWQ", api_key="sk-test")
    ai.context_compaction_config = {
        "enabled": True,
        "nodes": ["evidence"],
        "max_context_window": 35000,
        "trigger_ratio": 0.01,
        "summary_max_tokens": 500,
    }
    ai._compact_context_with_lite_llm = lambda payload, **kwargs: {
        "process_summary": ["先输出计划，随后执行 describe。"],
        "evidence_plan": [{"id": "e1", "description": "describe pod"}],
        "completed_items": [{"id": "e1", "outcome": "positive"}],
        "open_items": [],
        "key_facts": ["Pod 异常"],
        "negative_facts": [],
        "conflicts": [],
        "discarded_noise": ["长思考已压缩"],
        "next_focus": ["停止重复 describe"],
    }

    plan_message = AIMessage(content=json.dumps({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "describe pod",
                "level": "critical",
                "tool": "kubectl_describe",
                "command": "kubectl describe pod p -n n",
                "purpose": "确认状态",
            }
        ],
        "collection_strategy": "先 describe。",
    }, ensure_ascii=False))
    noisy_message = AIMessage(content="后续长思考" + ("循环分析" * 2000))
    tool_message = ToolMessage(
        content=json.dumps({"success": True, "stdout": "registry probe\n" + ("network noise\n" * 500)}, ensure_ascii=False),
        tool_call_id="tc-1",
        name="run_bash_command",
    )

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"agent": {"messages": [plan_message]}})
            yield ("updates", {"agent": {"messages": [noisy_message]}})
            yield ("updates", {"tools": {"messages": [tool_message]}})

    monkeypatch.setattr("langchain.agents.create_agent", lambda **kwargs: _Agent())
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "run_bash_command", "description": "run readonly shell", "args_schema": None})()
    _, events = ai.call(
        "s" * 2000,
        "u" * 2000,
        tools=[tool],
        node_id="evidence",
        run_id="run-compact-agent-context",
        max_steps=3,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "s" * 2000},
            {"name": "user_message", "category": "static_input", "content": "u" * 2000},
            {"name": "tool_schema", "category": "static_input", "content": "t" * 2000},
        ],
    )

    assert "evidence_plan" in plan_message.content
    assert noisy_message.content.startswith("[compacted ai_message:")
    assert tool_message.content.startswith("[compacted tool_result:")
    assert events[0]["type"] == "context_summary"
    assert any(ev.get("type") == "tool_result" for ev in events)


def test_aicall_passes_ai_summary_mode_to_observation_processor(tmp_path, monkeypatch):
    ai = AICall(
        model="openai/test",
        api_key="sk-test",
        observation_summary_mode="ai",
        observation_summary_max_chars=500,
    )
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    msg = ToolMessage(
        content="Name: pod-a\nNamespace: default\nReason: OOMKilled\n",
        tool_call_id="tc-1",
        name="kubectl_describe",
    )

    def fake_summary(tool_name, raw, current_summary):
        return "AI forced summary"

    ai._summarize_tool_observation = fake_summary

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"tools": {"messages": [msg]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_describe", "description": "describe pods", "args_schema": None})()
    result, events = ai.call(
        "system prompt",
        "user prompt",
        tools=[tool],
        node_id="evidence",
        run_id="run-ai-mode",
        max_steps=2,
    )

    assert msg.content == "AI forced summary"
    assert result.tool_calls[0]["summary_chars"] == len("AI forced summary")
    assert events[0]["observation_processor"] == "k8s_describe+llm"


def test_aicall_returns_compact_yaml_summary_under_context_threshold(tmp_path, monkeypatch):
    ai = AICall(
        model="openai/test",
        api_key="sk-test",
        observation_summary_mode="rule",
        observation_summary_max_chars=500,
    )
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "20000")

    raw_yaml = "kind: Pod\nmetadata:\n  name: ham-wcc79\nspec:\n  imagePullSecrets:\n  - name: xnet-bmcs\n" + ("noise: value\n" * 50)
    msg = ToolMessage(content=raw_yaml, tool_call_id="tc-yaml", name="kubectl_get_yaml")

    def fake_summary(tool_name, raw, current_summary):
        raise AssertionError("yaml should not be summarized below threshold")

    ai._summarize_tool_observation = fake_summary

    processed = ai._process_tool_observation(
        processor=ai._build_observation_processor(),
        run_id="run-full-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        tool_content=msg.content,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "system"},
            {"name": "user_message", "category": "static_input", "content": "user"},
        ],
        prior_tool_observations=[],
    )

    assert processed["summary"] != raw_yaml
    assert "imagePullSecrets: xnet-bmcs" in processed["summary"]
    assert processed["processor"] == "k8s_yaml"
    assert processed["structured"]["kind"] == "Pod"
    assert processed["structured"]["imagePullSecrets"] == ["xnet-bmcs"]


def test_observation_processor_includes_pod_lifecycle_structured_facts_in_yaml_summary(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw_yaml = """
apiVersion: v1
kind: Pod
metadata:
  name: terminating-stuck
  namespace: aiops-e2e
  creationTimestamp: "2026-04-29T06:54:19Z"
  deletionTimestamp: "2026-04-29T06:56:00Z"
  deletionGracePeriodSeconds: 0
  finalizers:
  - aiops.e2e/hold
  labels:
    pod_abnormal_type: TerminatingStuck
  annotations:
    aiops.e2e/runbook: pod-terminating-stuck.md
    kubectl.kubernetes.io/last-applied-configuration: "very noisy"
spec:
  nodeName: node1
  terminationGracePeriodSeconds: 30
  restartPolicy: Always
  containers:
  - name: app
    image: busybox:1.36
status:
  phase: Running
  conditions:
  - type: Ready
    status: "False"
    reason: ContainersNotReady
  containerStatuses:
  - name: app
    ready: false
    restartCount: 0
    state:
      terminated:
        exitCode: 137
        reason: Error
        startedAt: "2026-04-29T06:54:19Z"
        finishedAt: "2026-04-29T06:56:30Z"
"""

    processed = processor.process(
        run_id="run-pod-lifecycle",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content=raw_yaml,
    )

    structured = processed["structured"]
    summary = processed["summary"]

    assert structured["deletionTimestamp"] == "2026-04-29T06:56:00Z"
    assert structured["deletionGracePeriodSeconds"] == 0
    assert structured["finalizers"] == ["aiops.e2e/hold"]
    assert structured["labels"]["pod_abnormal_type"] == "TerminatingStuck"
    assert structured["diagnostic_annotations"] == {"aiops.e2e/runbook": "pod-terminating-stuck.md"}
    assert structured["terminationGracePeriodSeconds"] == 30
    assert structured["restartPolicy"] == "Always"
    assert structured["conditions"][0]["type"] == "Ready"
    assert "deletionTimestamp: 2026-04-29T06:56:00Z" in summary
    assert "finalizers: aiops.e2e/hold" in summary
    assert "deletionGracePeriodSeconds: 0" in summary
    assert "aiops.e2e/runbook=pod-terminating-stuck.md" in summary
    assert "conditions:" in summary


def test_aicall_summarizes_yaml_tool_when_context_threshold_exceeded(tmp_path, monkeypatch):
    ai = AICall(
        model="openai/test",
        api_key="sk-test",
        observation_summary_mode="rule",
        observation_summary_max_chars=500,
    )
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    monkeypatch.setenv("MODEL_CONTEXT_WINDOW", "300")

    raw = "kind: Pod\nmetadata:\n  name: ham-wcc79\n" + ("noise: value\n" * 300)

    def fake_summary(tool_name, raw_content, current_summary):
        return json.dumps({
            "summary": "Pod ham-wcc79 yaml compressed because context budget is high",
            "key_facts": ["imagePullSecrets should be checked"],
            "conflicts": [],
            "missing": [],
        }, ensure_ascii=False)

    ai._summarize_tool_observation = fake_summary

    processed = ai._process_tool_observation(
        processor=ai._build_observation_processor(),
        run_id="run-compress-yaml",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        tool_content=raw,
        static_context_components=[
            {"name": "node_system_prompt", "category": "static_input", "content": "system" * 100},
            {"name": "user_message", "category": "static_input", "content": "user" * 100},
        ],
        prior_tool_observations=[],
    )

    assert "compressed because context budget is high" in processed["summary"]
    assert processed["processor"] == "k8s_yaml+llm"
    assert processed["structured"]["kind"] == "Pod"


def test_aicall_deduplicates_replayed_agent_updates(tmp_path, monkeypatch):
    ai = AICall(model="openai/test", api_key="sk-test")
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))

    first_ai = AIMessage(
        content="<think>planning</think>",
        tool_calls=[{
            "name": "kubectl_run_image",
            "args": {"image": "busybox:1.36", "command": "nslookup xnet.registry.io"},
            "id": "call-1",
            "type": "tool_call",
        }],
    )
    tool_msg = ToolMessage(
        content=json.dumps({
            "success": False,
            "stdout": "pod \"curl-test\" deleted\n",
            "stderr": "error: timed out waiting for the condition\n",
            "returncode": 1,
        }, ensure_ascii=False),
        tool_call_id="call-1",
        name="kubectl_run_image",
    )
    final_ai = AIMessage(content="最终结论")

    class _CompletedFuture:
        def result(self, timeout=None):
            return None

    class _Executor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn):
            fn()
            return _CompletedFuture()

    class _Agent:
        async def astream(self, *args, **kwargs):
            yield ("updates", {"agent": {"messages": [first_ai]}})
            yield ("updates", {"tools": {"messages": [tool_msg]}})
            yield ("updates", {"agent": {"messages": [first_ai]}})
            yield ("updates", {"tools": {"messages": [tool_msg]}})
            yield ("updates", {"agent": {"messages": [final_ai]}})

    def _create_agent(**kwargs):
        return _Agent()

    monkeypatch.setattr("langchain.agents.create_agent", _create_agent)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda max_workers=1: _Executor())

    tool = type("T", (), {"name": "kubectl_run_image", "description": "run image", "args_schema": None})()
    result, events = ai.call(
        "system prompt",
        "user prompt",
        tools=[tool],
        node_id="evidence",
        run_id="run-dedupe",
        max_steps=2,
    )

    tool_start_events = [e for e in events if e["type"] == "tool_start"]
    tool_result_events = [e for e in events if e["type"] == "tool_result"]

    assert result.tool_call_count == 1
    assert len(result.tool_calls) == 1
    assert len(tool_start_events) == 1
    assert len(tool_result_events) == 1
    assert tool_start_events[0]["tool_name"] == "kubectl_run_image"
    assert tool_start_events[0]["tool_args"] == {"image": "busybox:1.36", "command": "nslookup xnet.registry.io"}


def test_observation_processor_extracts_kubectl_run_image_failure(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=500)

    processed = processor.process(
        run_id="run-kri",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_run_image",
        raw_content=json.dumps({
            "success": False,
            "stdout": "pod \"curl-test\" deleted\n",
            "stderr": "error: timed out waiting for the condition\n",
            "returncode": 1,
        }, ensure_ascii=False),
    )

    assert processed["processor"] == "k8s_run_image+passthrough_full"
    assert processed["structured"]["status"] == "run_image_result"
    assert processed["structured"]["success"] is False
    assert processed["structured"]["signals"] == ["timeout"]
    assert "timed out waiting for the condition" in processed["summary"]
    assert processed["semantic_success"] is False


def test_observation_processor_keeps_secret_table_image_pull_facts(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)
    raw = """NAME        TYPE                             DATA   AGE
xnet-bmcs   Opaque                           1      215d
pull-good   kubernetes.io/dockerconfigjson   1      1d
other       Opaque                           1      1d
"""

    processed = processor.process(
        run_id="run-secret-table",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_namespace",
        raw_content=raw,
    )

    assert processed["processor"] == "k8s_secret_table"
    assert processed["structured"]["resource_kind"] == "Secret"
    assert processed["structured"]["docker_secret_count"] == 1
    assert "pull-good" in processed["summary"]
    assert "xnet-bmcs" in processed["summary"]


def test_observation_processor_marks_failed_yaml_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-yaml-failed",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_yaml",
        raw_content='Command failed (exit 1):\nkubectl get -o yaml configmap registry-config -n kube-system\nError from server (NotFound): configmaps "registry-config" not found',
    )

    assert processed["structured"]["status"] == "command_failed"
    assert processed["semantic_success"] is False
    assert "NotFound" in processed["summary"]


def test_observation_processor_marks_failed_describe_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-describe-failed",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content='Command failed (exit 1):\nkubectl describe pod memhog -n aiops-e2e\nError from server (NotFound): pods "memhog" not found',
    )

    assert processed["structured"]["status"] == "command_failed"
    assert processed["semantic_success"] is False
    assert "NotFound" in processed["summary"]


def test_observation_processor_preserves_describe_event_not_found_as_diagnostic_evidence(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = """Name:             volume-mount-failed
Namespace:        aiops-e2e
Status:           Pending
Containers:
  app:
    State:          Waiting
      Reason:       ContainerCreating
Events:
  Type     Reason       Age                  From               Message
  ----     ------       ----                 ----               -------
  Warning  FailedMount  68s (x45 over 76m)   kubelet            MountVolume.SetUp failed for volume "missing-config" : configmap "definitely-missing-configmap" not found
"""

    processed = processor.process(
        run_id="run-describe-diagnostic-notfound",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_describe",
        raw_content=raw,
    )

    assert processed["processor"] == "k8s_describe"
    assert processed["structured"]["status"] != "command_failed"
    assert "关键诊断行" in processed["summary"]
    assert 'configmap "definitely-missing-configmap" not found' in processed["summary"]
    assert any("MountVolume.SetUp failed" in line for line in processed["structured"]["key_events"])


def test_observation_processor_preserves_kubectl_events_not_found_as_diagnostic_evidence(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = """LAST SEEN             TYPE      REASON        OBJECT                    MESSAGE
15m (x20 over 74m)    Warning   FailedMount   Pod/volume-mount-failed   Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-4nj8h]: timed out waiting for the condition
68s (x45 over 76m)    Warning   FailedMount   Pod/volume-mount-failed   MountVolume.SetUp failed for volume "missing-config" : configmap "definitely-missing-configmap" not found
"""

    processed = processor.process(
        run_id="run-events-diagnostic-notfound",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_events",
        raw_content=raw,
    )

    assert processed["processor"] == "k8s_events"
    assert processed["structured"]["status"] == "events_found"
    assert "关键诊断行" in processed["summary"]
    assert 'configmap "definitely-missing-configmap" not found' in processed["summary"]
    assert any("MountVolume.SetUp failed" in line for line in processed["structured"]["key_events"])


def test_observation_processor_logs_not_found_line_is_not_tool_failure(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-log-app-notfound",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_previous_logs",
        raw_content="ERROR failed to load config: /etc/app/config.yaml not found\n",
    )

    assert processed["processor"] == "k8s_logs"
    assert processed["structured"]["status"] == "logs_summarized"
    assert processed["semantic_success"] is True
    assert "config.yaml not found" in processed["summary"]


def test_observation_processor_marks_invalid_tool_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-invalid-tool",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_logs",
        raw_content="Error: kubectl_logs is not a valid tool, try one of [kubectl_describe, kubectl_get_yaml].",
    )

    assert processed["processor"] == "invalid_tool"
    assert processed["structured"]["status"] == "invalid_tool"
    assert processed["semantic_success"] is False
    assert "not a valid tool" in processed["summary"]


def test_observation_processor_marks_medium_empty_output_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-empty-medium",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_name",
        raw_content="No resources found in aiops-e2e namespace.",
    )

    assert processed["processor"] == "generic_empty"
    assert processed["structured"]["status"] == "empty"
    assert processed["semantic_success"] is False


def test_observation_processor_marks_medium_command_failure_as_negative(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-failed-medium",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_name",
        raw_content='Command failed (exit 1):\nkubectl get customresource -n aiops-e2e\nerror: the server doesn\'t have a resource type "customresource"',
    )

    assert processed["processor"] == "generic_failure"
    assert processed["structured"]["status"] == "command_failed"
    assert processed["semantic_success"] is False


def test_observation_processor_does_not_mark_runbook_diagnostic_text_as_failure(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)
    raw = """<runbook>
# Pod ImagePullFailed / ImagePullBackOff

重点关注 Events 部分:
- `Failed to pull image "xxx"`: 具体镜像地址
- `manifest unknown/not found`: 镜像或 tag 不存在
- `i/o timeout`: 节点到镜像仓库访问失败
</runbook>
Note: the above runbook is for DIAGNOSTIC REFERENCE ONLY.
"""

    processed = processor.process(
        run_id="run-runbook-diagnostic-text",
        node_id="evidence",
        sequence=1,
        tool_name="fetch_runbook",
        raw_content=raw,
    )

    assert processed["processor"] == "runbook+passthrough_full"
    assert processed["structured"]["status"] == "runbook_loaded"
    assert processed["semantic_success"] is True
    assert "Failed to pull image" in processed["summary"]


def test_observation_processor_summarizes_aiops_case_without_label_leakage(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = json.dumps({
        "ok": True,
        "case_id": "oom-aiops-temp-aiops-oom-business",
        "abnormal_type": "oomkilled",
        "scenario": "oomkilled",
        "primary_entity": {
            "kind": "Pod",
            "namespace": "aiops-temp",
            "name": "aiops-oom-business",
        },
        "coverage": {
            "kubernetes": "observed",
            "metrics": "observed",
            "logging": "observed",
            "tracing": "weak_context",
            "topology": "observed",
        },
        "signals_summary": [
            {
                "signal_id": "sig_status_oom",
                "dimension": "kubernetes",
                "strength": "critical",
                "observed": True,
                "evidence_refs": ["k8s.describe"],
            },
            {
                "signal_id": "sig_logs_memory_growth",
                "dimension": "logging",
                "strength": "important",
                "observed": True,
                "evidence_refs": ["log.memory_growth"],
            },
        ],
        "timeline_summary": [
            {
                "timestamp": "2026-07-06T10:00:00Z",
                "dimension": "kubernetes",
                "summary": "container lastState terminated reason=OOMKilled exitCode=137",
                "evidence_refs": ["k8s.describe"],
            }
        ],
        "topology_summary": {
            "entity_count": 4,
            "edge_count": 3,
            "entity_kinds": {"Pod": 1, "Container": 1, "Node": 1, "Service": 1},
            "relations": {"runs_on": 1, "contains": 1, "selects": 1},
            "directness": {"direct": 2, "related_context": 1},
            "confidence": {"high": 2, "weak": 1},
        },
        "evidence_inventory": [
            {"ref": "evidence/k8s_describe.txt", "exists": True, "records": 80},
            {"ref": "evidence/logs.jsonl", "exists": True, "records": 20},
        ],
        "evidence_refs": ["k8s.describe", "log.memory_growth", "metric.memory_limit"],
        "recommended_refs_by_dimension": {
            "k8s": ["k8s.describe"],
            "metrics": ["metric.memory_limit"],
            "tracing": ["deepflow.node_context"],
        },
        "package_ref": "/cases/oom-aiops-temp-aiops-oom-business",
        "root_cause": "OOMKilled label only for evaluator",
        "expected_remediation": "increase memory limit",
        "labels": {"root_cause": "oom"},
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-case",
        node_id="evidence",
        sequence=1,
        tool_name="collect_aiops_case",
        raw_content=raw,
    )

    assert processed["processor"] == "aiops_case"
    assert processed["semantic_success"] is True
    assert processed["structured"]["status"] == "case_collected"
    assert processed["structured"]["case_id"] == "oom-aiops-temp-aiops-oom-business"
    assert processed["structured"]["coverage"]["metrics"] == "observed"
    assert processed["structured"]["evidence_refs"] == [
        "k8s.describe",
        "log.memory_growth",
        "metric.memory_limit",
    ]
    assert processed["structured"]["recommended_refs_by_dimension"]["metrics"] == ["metric.memory_limit"]
    assert processed["structured"]["topology_summary"]["directness"]["related_context"] == 1
    assert processed["structured"]["topology_summary"]["confidence"]["weak"] == 1
    assert "collect_aiops_case 摘要" in processed["summary"]
    assert "aiops-temp/aiops-oom-business" in processed["summary"]
    assert "tracing=weak_context" in processed["summary"]
    assert "recommended_refs_by_dimension" in processed["summary"]
    assert "directness={'direct': 2, 'related_context': 1}" in processed["summary"]
    assert "k8s.describe" in processed["summary"]
    assert "root_cause" not in processed["summary"]
    assert "expected_remediation" not in processed["summary"]


def test_observation_processor_preserves_aiops_evidence_strength_fields(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = json.dumps({
        "ok": True,
        "case_id": "oom-aiops-temp-aiops-oom-business",
        "ref": "deepflow.node_context",
        "truncated": False,
        "record": {
            "evidence_id": "deepflow.node_context",
            "timestamp": "2026-07-08T05:00:00Z",
            "source_system": "deepflow",
            "dimension": "tracing",
            "summary": "node-level related flow only",
            "severity": "info",
            "confidence": "weak",
            "directness": "related_context",
            "trace_correlation": {"pod_ip": "10.244.0.10", "trace_ids": []},
            "payload": {"large": "not selected"},
        },
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-case-evidence",
        node_id="evidence",
        sequence=1,
        tool_name="get_aiops_case_evidence",
        raw_content=raw,
    )

    record = processed["structured"]["record"]
    assert record["confidence"] == "weak"
    assert record["directness"] == "related_context"
    assert record["trace_correlation"]["pod_ip"] == "10.244.0.10"
    assert "payload" not in record
    assert "labels" not in processed["structured"]


def test_observation_processor_does_not_inline_aiops_case_evaluator_file_content(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1200)
    raw = json.dumps({
        "ok": True,
        "case_id": "oom-aiops-temp-aiops-oom-business",
        "ref": "labels.yaml",
        "truncated": False,
        "content": (
            "root_cause: OOMKilled\n"
            "expected_remediation: increase memory limit\n"
            "labels:\n"
            "  pod_abnormal_type: OOMKilled\n"
        ),
    }, ensure_ascii=False)

    processed = processor.process(
        run_id="run-aiops-case-label-file",
        node_id="evidence",
        sequence=1,
        tool_name="get_aiops_case_evidence",
        raw_content=raw,
    )

    assert processed["processor"] == "aiops_case"
    assert processed["semantic_success"] is True
    assert processed["structured"]["status"] == "case_evidence_loaded"
    assert processed["structured"]["ref"] == "labels.yaml"
    assert processed["structured"]["content_chars"] > 0
    assert "labels.yaml" in processed["summary"]
    assert "content_chars=" in processed["summary"]
    assert "root_cause" not in processed["summary"]
    assert "expected_remediation" not in processed["summary"]
    assert "pod_abnormal_type" not in processed["summary"]
    assert "content" not in processed["structured"]


def test_observation_processor_summarizes_kubectl_logs(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=1000)

    processed = processor.process(
        run_id="run-logs",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_previous_logs",
        raw_content="\n".join([
            "2026-04-30T01:00:00Z INFO startup ok",
            "2026-04-30T01:00:01Z ERROR failed to load config key DB_URL",
            "2026-04-30T01:00:02Z Traceback most recent call last",
        ]),
    )

    assert processed["processor"] == "k8s_logs"
    assert processed["structured"]["status"] == "logs_summarized"
    assert processed["structured"]["signal_count"] == 2
    assert "failed to load config" in processed["summary"]
    assert processed["semantic_success"] is True


def test_observation_processor_table_marks_terminating_and_image_pull_as_abnormal(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE     NAME                    READY   STATUS             RESTARTS   AGE
aaa           test1-redis-master-0    0/1     ImagePullBackOff   0          24h
aaa           test1-redis-slave-0     0/1     ErrImagePull       0          24h
aiops-e2e     terminating-stuck       0/1     Terminating        0          7d18h
aiops         aiops-copilot-abc       1/1     Running            0          15h
"""

    processed = processor.process(
        run_id="run-table-terminating",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["status"] == "table_summarized"
    assert processed["structured"]["abnormal_count"] == 3
    assert processed["structured"]["status_counts"]["ImagePullBackOff"] == 1
    assert processed["structured"]["status_counts"]["ErrImagePull"] == 1
    assert processed["structured"]["status_counts"]["Terminating"] == 1
    assert any("terminating-stuck" in row for row in processed["structured"]["selected_rows"])


def test_observation_processor_table_filters_running_and_completed_from_status_column(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAMESPACE     NAME                                      READY   STATUS             RESTARTS       AGE
xnet          observability-kepler-8fhp6                1/1     Running            10 (24h ago)   9d
xnet          observability-kibana-65d7c45f6d-7zc9l     0/1     Completed          0              12d
aaa           test1-redis-master-0                      0/1     ImagePullBackOff   0              24h
aiops-e2e     terminating-stuck                         0/1     Terminating        0              7d18h
"""

    processed = processor.process(
        run_id="run-table-status-filter",
        node_id="layer",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 2
    selected_rows = processed["structured"]["selected_rows"]
    assert any("test1-redis-master-0" in row for row in selected_rows)
    assert any("terminating-stuck" in row for row in selected_rows)
    assert all("observability-kepler-8fhp6" not in row for row in selected_rows)
    assert all("observability-kibana-65d7c45f6d-7zc9l" not in row for row in selected_rows)


def test_observation_processor_table_treats_ready_bound_and_active_as_normal(tmp_path):
    processor = ObservationProcessor(archive_root=str(tmp_path), max_observation_chars=2000)
    raw = """NAME        STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP
master      Ready    control-plane   223d   v1.26.8   10.2.0.48     <none>
node1       Ready    <none>          223d   v1.26.8   10.2.0.49     <none>
"""

    processed = processor.process(
        run_id="run-table-ready-normal",
        node_id="evidence",
        sequence=1,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=raw,
    )

    assert processed["structured"]["abnormal_count"] == 0
    assert "# 样例行" in processed["summary"]
    assert "# 异常行" not in processed["summary"]

    pvc_raw = """NAME        STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-0      Bound    pvc-1    8Gi        RWO            nfs-storage    20d
data-1      Bound    pvc-2    8Gi        RWO            nfs-storage    20d
"""
    pvc_processed = processor.process(
        run_id="run-table-bound-normal",
        node_id="evidence",
        sequence=2,
        tool_name="kubectl_get_by_kind_in_namespace",
        raw_content=pvc_raw,
    )

    assert pvc_processed["structured"]["abnormal_count"] == 0
    assert "# 样例行" in pvc_processed["summary"]

    namespace_raw = """NAME      STATUS   AGE
default   Active   223d
kube      Active   223d
"""
    namespace_processed = processor.process(
        run_id="run-table-active-normal",
        node_id="evidence",
        sequence=3,
        tool_name="kubectl_get_by_kind_in_cluster",
        raw_content=namespace_raw,
    )

    assert namespace_processed["structured"]["abnormal_count"] == 0
    assert "# 样例行" in namespace_processed["summary"]
