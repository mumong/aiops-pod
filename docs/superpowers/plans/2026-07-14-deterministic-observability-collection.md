# 异常 Pod 实时可观测性稳定采集 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变 Robusta 现有 Agent/MCP 架构的前提下，使 evidence 对每个已发现异常 Pod 稳定调用 `collect_aiops_case`，并在上下文达到 80% 时停止新增采集。

**Architecture:** Qwen 继续生成和执行 Pydantic evidence plan；Robusta 在计划标准化后补齐通用 mandatory coarse 项，并用真实 tool result 审核完成状态。现有 observation token 估算负责 70% 压缩和 80% 停止，MCPStander 仅增强工具描述，不改变协议。

**Tech Stack:** Python 3.10、Pydantic、LangChain `create_agent`、MCP SSE、pytest、Kubernetes、Langfuse。

---

## 文件结构

Robusta：

- `app/core/workflow/nodes/evidence_collector.py`：异常 Pod 提取、mandatory plan、
  完成状态、停止策略和剩余目标执行。
- `app/core/aicall/client.py`：把 observation 的 `context_usage_ratio` 写入
  `tool_result` 事件，并支持多轮执行时连续归档序号。
- `app/core/prompts.py`：将实时多维采证从“候选”提升为异常 Pod 的 mandatory 事实入口。
- `deploy/configmap/config.yaml`：关闭旧 evidence early-stop，保留上下文压缩配置。
- `tests/unit/workflow/test_evidence_dynamic_stop.py`：计划和停止契约。
- `tests/unit/aicall/test_observation_processing.py`：上下文比例事件透传。

MCPStander：

- `servers/holmes_tools/aiops_case.py`：增强 `collect_aiops_case` description。
- `tests/test_aiops_observability_contract.py`：固定工具描述契约。

不创建新的调度模块，不修改 Case Package collector、RCA 接口或 MCP URL。

### Task 1: Mandatory Coarse Plan Contract

**Files:**

- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] **Step 1: 添加一组失败测试**

在 `tests/unit/workflow/test_evidence_dynamic_stop.py` 增加以下行为测试：

```python
def test_evidence_injects_mandatory_case_for_every_unique_abnormal_pod():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "active_entities": [
            {"type": "Pod", "namespace": "ns-a", "name": "pod-a"},
        ],
        "issue_groups": [
            {
                "entities": [
                    {"kind": "Pod", "namespace": "ns-b", "name": "pod-b"},
                    {"kind": "Pod", "namespace": "ns-a", "name": "pod-a"},
                ]
            }
        ],
        "abnormal_pods": [
            {"namespace": "ns-c", "name": "pod-c"},
        ],
    }

    result = node._ensure_mandatory_aiops_case_plan(
        [{"id": "events", "level": "critical", "tool": "kubectl_events"}],
        handoff,
    )

    coarse = [item for item in result if item["tool"] == "collect_aiops_case"]
    assert [(item["tool_args"]["namespace"], item["tool_args"]["pod"]) for item in coarse] == [
        ("ns-a", "pod-a"),
        ("ns-b", "pod-b"),
        ("ns-c", "pod-c"),
    ]
    assert all(item["level"] == "critical" for item in coarse)
    assert all(item["tool_args"]["scenario"] == "auto" for item in coarse)


def test_evidence_does_not_inject_case_when_tool_is_unavailable():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="kubectl_describe")]

    result = node._ensure_mandatory_aiops_case_plan(
        [],
        {"abnormal_pods": [{"namespace": "ns", "name": "pod"}]},
    )

    assert result == []


def test_evidence_keeps_all_mandatory_cases_beyond_regular_plan_limit():
    node = EvidenceCollectorNode()
    node.tools = [SimpleNamespace(name="collect_aiops_case")]
    handoff = {
        "abnormal_pods": [
            {"namespace": "ns", "name": f"pod-{index}"}
            for index in range(12)
        ]
    }

    result = node._ensure_mandatory_aiops_case_plan([], handoff)

    assert len(result) == 12
    assert all(item["source"] == "mandatory_live_observability" for item in result)
```

- [ ] **Step 2: 集中运行新增测试，确认 RED**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest tests/unit/workflow/test_evidence_dynamic_stop.py \
  -k 'mandatory_case_for_every or tool_is_unavailable or beyond_regular_plan_limit' -q
```

预期：失败，提示 `_ensure_mandatory_aiops_case_plan` 不存在，或只注入一个目标。

- [ ] **Step 3: 实现通用目标提取和 mandatory plan**

在 `EvidenceCollectorNode` 中扩展 `_collect_handoff_pod_targets()`，明确读取
`active_entities`、`issue_groups[].entities`、`abnormal_groups[].entities` 和
`abnormal_pods`，返回按首次出现顺序去重的 `(namespace, pod)`。

新增实例方法：

```python
def _ensure_mandatory_aiops_case_plan(
    self,
    evidence_plan: List[Dict[str, Any]],
    layer_handoff: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    plan = list(evidence_plan or [])
    tool_names = {
        str(getattr(tool, "name", "") or "")
        for tool in (getattr(self, "tools", []) or [])
    }
    if "collect_aiops_case" not in tool_names:
        return plan

    targets = self._collect_handoff_pod_targets(layer_handoff or {})
    existing = {
        target
        for item in plan
        if self._normalize_plan_text(item.get("tool")) == "collect_aiops_case"
        if (target := self._extract_plan_pod_target(item))
    }
    mandatory = []
    for index, (namespace, pod) in enumerate(targets, start=1):
        if (namespace.lower(), pod.lower()) in existing:
            continue
        mandatory.append({
            "id": f"aiops-case-{index}",
            "description": f"实时采集异常 Pod {namespace}/{pod} 的多维可观测性 case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "command": f"collect_aiops_case namespace={namespace} pod={pod}",
            "tool_args": {
                "namespace": namespace,
                "pod": pod,
                "scenario": "auto",
            },
            "purpose": "采集 Kubernetes、Metrics、Logging、Tracing 和 Topology 真实证据",
            "acceptable_tools": ["collect_aiops_case"],
            "source": "mandatory_live_observability",
        })
    return mandatory + plan
```

在 `_plan_evidence_with_llm()` 的 existing plan 和新生成 plan 两条路径中，在
`_normalize_evidence_plan()` 后调用该方法。已有同目标 coarse 项要提升为
`critical` 并标记 mandatory，不能重复添加。

- [ ] **Step 4: 运行 evidence 模块测试，确认 GREEN**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest tests/unit/workflow/test_evidence_dynamic_stop.py -q
```

预期：该测试文件全部通过。

- [ ] **Step 5: 提交 Task 1**

```bash
git add app/core/workflow/nodes/evidence_collector.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py
git commit -m "feat: require live case collection for abnormal pods"
```

### Task 2: Context Budget Stop And Completion Audit

**Files:**

- Modify: `app/core/aicall/client.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/aicall/test_observation_processing.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] **Step 1: 添加上下文比例透传和停止契约失败测试**

在 `tests/unit/aicall/test_observation_processing.py` 增加断言：生成的
`tool_result` event 包含 processor 返回的 `context_usage_ratio=0.81`。

在 `tests/unit/workflow/test_evidence_dynamic_stop.py` 增加：

```python
def test_evidence_does_not_stop_after_kubectl_when_mandatory_case_is_pending():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod"},
            "source": "mandatory_live_observability",
        },
        {
            "id": "describe",
            "level": "critical",
            "tool": "kubectl_describe",
            "tool_args": {"namespace": "ns", "name": "pod"},
        },
    ]
    events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "kubectl_describe",
        "semantic_success": True,
        "tool_args": {"namespace": "ns", "name": "pod"},
        "result": "CrashLoopBackOff",
    }]

    assert node._should_stop_collection_early(events) is False


def test_evidence_stops_at_eighty_percent_context_and_records_remaining_targets():
    node = EvidenceCollectorNode()
    node._active_evidence_plan = [
        {
            "id": "case-a",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-a"},
            "source": "mandatory_live_observability",
        },
        {
            "id": "case-b",
            "level": "critical",
            "tool": "collect_aiops_case",
            "tool_args": {"namespace": "ns", "pod": "pod-b"},
            "source": "mandatory_live_observability",
        },
    ]
    events = [{
        "type": "tool_result",
        "status": "success",
        "tool_name": "collect_aiops_case",
        "tool_args": {"namespace": "ns", "pod": "pod-a"},
        "context_usage_ratio": 0.81,
        "structured": {"status": "case_collected"},
    }]

    assert node._should_stop_collection_early(events) is True
    assert node._early_stop_state["reason"] == "context_budget_stop"
    assert node._early_stop_state["uncollected_targets"] == ["ns/pod-b"]
```

- [ ] **Step 2: 集中运行新增测试，确认 RED**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  -k 'context_usage_ratio or mandatory_case_is_pending or eighty_percent_context' -q
```

预期：失败，因为 `tool_result` 尚未保存上下文比例，旧 early-stop 仍只按计划等级判断。

- [ ] **Step 3: 透传 observation 上下文比例**

在 `AICall.call()` 构造 `evt` 时加入：

```python
"context_usage_ratio": observation.get("context_usage_ratio"),
```

同时给 `AICall.call()` 增加可选参数：

```python
tool_result_sequence_start: int = 0
```

并将初始化改为：

```python
tool_result_sequence = max(0, int(tool_result_sequence_start or 0))
```

该参数只用于 evidence 有界继续执行时避免覆盖同一 run 的既有 tool archive。

- [ ] **Step 4: 实现 mandatory 完成状态和 80% 停止**

在 `EvidenceCollectorNode` 增加以下辅助方法：

```python
@classmethod
def _mandatory_case_targets(
    cls,
    evidence_plan: List[Dict[str, Any]],
) -> List[tuple[str, str]]:
    return [
        target
        for item in evidence_plan
        if item.get("source") == "mandatory_live_observability"
        if (target := cls._extract_plan_pod_target(item))
    ]


@classmethod
def _attempted_mandatory_case_targets(
    cls,
    thinking_events: List[Dict[str, Any]],
) -> set[tuple[str, str]]:
    return {
        target
        for event in thinking_events
        if event.get("type") == "tool_result"
        if str(event.get("tool_name") or "") == "collect_aiops_case"
        if (target := cls._extract_tool_event_pod_target(event))
    }


@classmethod
def _extract_tool_event_pod_target(
    cls,
    event: Dict[str, Any],
) -> Optional[tuple[str, str]]:
    args = event.get("tool_args") if isinstance(event.get("tool_args"), dict) else {}
    namespace = str(args.get("namespace") or "").strip().lower()
    pod = str(args.get("pod") or args.get("pod_name") or "").strip().lower()
    structured = event.get("structured") if isinstance(event.get("structured"), dict) else {}
    primary = (
        structured.get("primary_entity")
        if isinstance(structured.get("primary_entity"), dict)
        else {}
    )
    namespace = namespace or str(primary.get("namespace") or "").strip().lower()
    pod = pod or str(primary.get("name") or "").strip().lower()
    return (namespace, pod) if namespace and pod else None
```

修改 `_should_stop_collection_early()`：

1. 任一 tool result 的 `context_usage_ratio >= 0.8` 时立即停止，reason 为
   `context_budget_stop`，记录 `uncollected_targets`。
2. mandatory 目标存在时，只有所有目标均返回 `status=case_collected` 才允许按
   coarse 完成停止。
3. kubectl 或普通 critical 计划完成不能触发停止。
4. 没有 mandatory 目标时保留原有普通 evidence 行为，避免影响 QUERY/HEALTHY。

将 `deploy/configmap/config.yaml` 中：

```yaml
evidence:
  early_stop:
    enabled: false
```

旧配置关闭后，`_execute_existing_evidence_plan()` 仍显式传入新的 mandatory/budget
stop checker；配置开关只控制旧的 critical/important completeness early-stop。

- [ ] **Step 5: 实现未尝试目标的有界继续执行**

在 `_execute_existing_evidence_plan()` 中累计所有 round 的 events。每轮结束后：

```python
remaining = self._remaining_unattempted_mandatory_items(
    evidence_plan,
    all_thinking_events,
)
```

如果 `remaining` 非空且未达到 80%，则使用剩余 mandatory plan 再执行一轮；下一轮
user message 注入已完成目标和紧凑结果摘要，并传：

```python
tool_result_sequence_start=len([
    event for event in all_thinking_events
    if event.get("type") == "tool_result"
])
```

每轮比较 mandatory result 数量：有新增时把无进展计数清零，没有新增时加一。连续
两轮没有新增 mandatory result 时停止，设置：

```python
{
    "triggered": True,
    "reason": "collection_stalled",
    "uncollected_targets": [...],
}
```

不得重试已经返回 `case_error`、NotFound 或其他终态错误的目标；这些目标进入
`failed_targets`，由已有细粒度计划或最终报告处理。

- [ ] **Step 6: 运行 Robusta 两个模块测试，确认 GREEN**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py -q
```

预期：两个测试文件全部通过。

- [ ] **Step 7: 提交 Task 2**

```bash
git add app/core/aicall/client.py \
  app/core/workflow/nodes/evidence_collector.py \
  deploy/configmap/config.yaml \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py
git commit -m "feat: stop evidence collection at context budget"
```

### Task 3: Prompt And MCP Tool Selection Metadata

**Files:**

- Modify: `app/core/prompts.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/holmes_tools/aiops_case.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`
- Test: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_contract.py`

- [ ] **Step 1: 添加 prompt 和 MCP description 失败测试**

Robusta 测试要求 evidence prompt 包含：

```text
每个已确认异常 Pod 都必须优先执行 collect_aiops_case
kubectl 只能作为缺失维度补证或工具失败降级
达到 80% 上下文预算后停止新增采集
```

同时删除当前测试中以下旧断言：

```python
assert "必须调用 `collect_aiops_case`" not in guidance
assert "自主选择" in guidance
```

MCPStander 契约测试：

```python
def test_collect_aiops_case_description_marks_preferred_live_entrypoint(self):
    collect = next(tool for tool in aiops_case.TOOLS if tool.name == "collect_aiops_case")
    description = collect.description.lower()
    for term in (
        "preferred",
        "prometheus",
        "logging",
        "deepflow",
        "tempo",
        "topology",
        "abnormal pod",
    ):
        self.assertIn(term, description)
```

- [ ] **Step 2: 分别运行契约测试，确认 RED**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest tests/unit/workflow/test_evidence_dynamic_stop.py \
  -k 'live_observability or system_prompt_prioritizes' -q

cd /root/huhu/agent/combine-aiops-mcp/mcpstander
.venv/bin/python -m pytest tests/test_aiops_observability_contract.py -q
```

预期：现有“候选、自主选择”措辞和简短 MCP description 导致失败。

- [ ] **Step 3: 强化 Robusta evidence prompt**

修改 `EVIDENCE_COLLECTOR_PROMPT` 和
`_build_live_observability_plan_guidance()`：

- 每个已确认异常 Pod 的 mandatory coarse 项必须先执行；
- 真实 Metrics、Logging、Tracing 和 Topology 优先于模型推论；
- coarse 完整时不重复 kubectl；
- coarse error/absent/缺失维度时才回退细粒度工具；
- 80% 上下文预算后停止，并披露未采集目标；
- 不写任何 OOM、ImagePull、Terminating 特定注入逻辑。

- [ ] **Step 4: 增强 MCP Tool description**

将 description 改为完整但紧凑的英文工具选择说明：

```python
description=(
    "Preferred live diagnostic entrypoint for every known abnormal Kubernetes Pod. "
    "Collects a compact evidence-first case with Kubernetes state, Prometheus metrics, "
    "centralized logging, DeepFlow network tracing, Tempo application spans, and topology. "
    "Use this before multiple kubectl-only calls; use fine-grained tools only when coverage "
    "is absent, incomplete, or the collection returns an error."
)
```

- [ ] **Step 5: 运行 Robusta prompt 与 MCP 契约测试，确认 GREEN**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest tests/unit/workflow/test_evidence_dynamic_stop.py -q

cd /root/huhu/agent/combine-aiops-mcp/mcpstander
.venv/bin/python -m pytest tests/test_aiops_observability_contract.py -q
```

预期：两个测试文件全部通过。

- [ ] **Step 6: 分仓库提交 Task 3**

Robusta：

```bash
git add app/core/prompts.py tests/unit/workflow/test_evidence_dynamic_stop.py
git commit -m "feat: prioritize mandatory live observability evidence"
```

MCPStander：

```bash
git add servers/holmes_tools/aiops_case.py \
  tests/test_aiops_observability_contract.py
git commit -m "docs: clarify preferred aiops case tool usage"
```

### Task 4: Grouped Regression And Deployment

**Files:**

- Verify only: Robusta and MCPStander changed modules
- Runtime: Kubernetes deployments `aiops-copilot` and `mcp-server-manager`

- [ ] **Step 1: 运行 Robusta 分组回归**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_fast_paths.py -q
```

预期：全部通过，无 early-stop、handoff 或 observation 回归。

- [ ] **Step 2: 运行 MCPStander 分组回归**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
.venv/bin/python -m pytest \
  tests/test_aiops_case_tool.py \
  tests/test_aiops_observability_contract.py \
  tests/test_aiops_observability_collectors.py -q
```

预期：全部通过，description 改动不影响工具协议和真实 collector。

- [ ] **Step 3: 构建并部署 MCPStander**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
make build-push
make deploy
kubectl rollout status deployment/mcp-server-manager -n mcp --timeout=120s
kubectl logs -n mcp deployment/mcp-server-manager --tail=120
```

确认 coarse AIOps MCP 服务启动，且 `collect_aiops_case` 仍出现在工具列表。

- [ ] **Step 4: 构建并部署 Robusta**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make build
make push
make deploy
kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s
curl -s http://10.2.0.48:30800/health
curl -s http://10.2.0.48:30800/api/v1/mcp/status
```

确认服务健康，AIOps coarse MCP server enabled，Qwen 模型配置保持不变。

### Task 5: Repeated Vague-Question Acceptance With Langfuse Audit

**Files:**

- Runtime archives: `/tmp/aiops/reports/context_archives/<run_id>/`
- Audit UI: `http://10.2.0.54:3001/project/cmn5ux21p0006qw07q05hy9ix/sessions`

- [ ] **Step 1: 确认测试前异常 Pod 集合**

```bash
kubectl get pods -A | rg 'CrashLoopBackOff|ImagePullBackOff|ErrImagePull|Terminating|Pending|Error'
```

保存本轮所有异常 Pod 的 `namespace/name`，作为 mandatory target 基线。

- [ ] **Step 2: 使用相同模糊问题连续运行三次**

每次单独保存 SSE 输出：

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？" \
  | tee /tmp/aiops-vague-observability-run-1.txt
```

将文件序号依次改为 `2`、`3`，等待上一轮完成后再启动下一轮，禁止并发。

- [ ] **Step 3: 对每个 run/session 审计真实工具调用**

从 SSE 输出提取 run ID，再检查对应 archive 和 Langfuse session：

```bash
rg -n 'run_id|collect_aiops_case|context_budget_stop|collection_stalled' \
  /tmp/aiops-vague-observability-run-*.txt

find /tmp/aiops/reports/context_archives/<run_id> -maxdepth 3 -type f | sort
```

每次必须确认：

- evidence plan 含测试前发现的全部异常 Pod；
- 每个已尝试目标有真实 `collect_aiops_case` tool call 和正确参数；
- 未达到 80% 时不存在未尝试目标；
- 达到 80% 时停止新增调用并列出 `uncollected_targets`；
- tool result 的 `dimension_details` 包含真实值或诚实的 absent/empty/error；
- kubectl 只用于 coarse 缺失维度、错误降级或必要状态确认；
- Langfuse 中 tool call 顺序与本地 archive 一致。

- [ ] **Step 4: 审计 RCA 和最终报告**

每个报告必须：

- 区分 Prometheus、Logging、DeepFlow、Tempo 和 Kubernetes 数据来源；
- 引用具体指标值、日志原文、trace/flow ID、拓扑边和 evidence ref；
- 使用真实 topology 的 relationship/directness/confidence；
- 只对已采集目标构建因果链；
- 不把 absent/weak 维度写成强证据；
- 不把上下文预算未采集的 Pod 写成已验证。

- [ ] **Step 5: 最终差异和状态检查**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
git status --short
git diff --check

cd /root/huhu/agent/combine-aiops-mcp/mcpstander
git status --short
git diff --check
```

只报告本次修改和既有脏文件，不清理、不回退用户已有改动。
