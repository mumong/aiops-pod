# Model-Driven Observability Tool Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 evidence planner 在用户未显式提到可观测性维度时，也优先评估实时多维证据工具，同时保留 Qwen 自主选择工具和目标 Pod 的能力。

**Architecture:** 只修改 Robusta evidence prompt 与通用 guidance。上游确认异常 Pod 后，guidance 向模型提供候选目标和实时证据优先语义，但不生成计划、不插入工具、不识别故障类型；现有 Pydantic plan、工具执行和 coverage 补证流程保持不变。

**Tech Stack:** Python、Prompt templates、Pydantic evidence plan、pytest、Qwen3.6-35B-A3B、Kubernetes。

---

### Task 1: 为通用实时证据 guidance 建立失败测试

**Files:**
- Modify: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] **Step 1: 修改现有单 Pod 多维测试，覆盖宽泛问题和多个异常 Pod**

将现有 `test_evidence_user_prompt_ends_with_coarse_case_guidance_for_multidimensional_pod_request`
替换为两个测试：

```python
def test_evidence_user_prompt_prioritizes_live_observability_for_broad_multi_pod_question():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="我的集群现在有什么问题？",
        layer="L2",
        layer_handoff=json.dumps(
            {
                "active_entities": [
                    {"type": "Pod", "namespace": "ns-a", "name": "pod-a"},
                    {"type": "Pod", "namespace": "ns-b", "name": "pod-b"},
                ],
                "issue_groups": [],
            },
            ensure_ascii=False,
        ),
    )

    guidance = message.rsplit("# 实时可观测性证据优先", 1)[1]
    assert "ns-a/pod-a" in guidance
    assert "ns-b/pod-b" in guidance
    assert "`collect_aiops_case`" in guidance
    assert "高信息密度" in guidance
    assert "自主选择" in guidance
    assert "用户同时要求 metrics" not in guidance
    assert "必须调用 `collect_aiops_case`" not in guidance


def test_evidence_user_prompt_keeps_live_observability_guidance_generic():
    message = EvidenceCollectorNode._build_evidence_user_message(
        question="请分析这个异常。",
        layer="L3",
        layer_handoff=json.dumps(
            {
                "issue_groups": [
                    {
                        "group_id": "g1",
                        "entities": [
                            {"kind": "Pod", "namespace": "generic-ns", "name": "generic-pod"}
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
    )

    guidance = message.rsplit("# 实时可观测性证据优先", 1)[1]
    assert "generic-ns/generic-pod" in guidance
    assert "OOMKilled" not in guidance
    assert "ImagePullBackOff" not in guidance
    assert "CrashLoopBackOff" not in guidance
    assert "固定调用次数" not in guidance
```

- [ ] **Step 2: 增加 evidence 系统提示的语义契约测试**

在同一测试文件中导入 `EVIDENCE_COLLECTOR_PROMPT`，新增：

```python
def test_evidence_system_prompt_prioritizes_live_observability_independent_of_user_wording():
    assert "用户是否显式提到" in EVIDENCE_COLLECTOR_PROMPT
    assert "实时可观测性证据" in EVIDENCE_COLLECTOR_PROMPT
    assert "由模型自主选择" in EVIDENCE_COLLECTOR_PROMPT
    assert "若单一 kubectl 事实已足够回答问题" not in EVIDENCE_COLLECTOR_PROMPT
```

- [ ] **Step 3: 运行目标测试确认失败**

Run:

```bash
.venv/bin/pytest -q \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_user_prompt_prioritizes_live_observability_for_broad_multi_pod_question \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_user_prompt_keeps_live_observability_guidance_generic \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_system_prompt_prioritizes_live_observability_independent_of_user_wording
```

Expected: FAIL，因为当前 guidance 要求四类关键词且只接受一个 Pod，系统提示仍允许用单一 kubectl 事实直接跳过 coarse 工具。

### Task 2: 实现模型驱动的通用证据优先语义

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`

- [ ] **Step 1: 收敛 evidence 系统提示**

将 `EVIDENCE_COLLECTOR_PROMPT` 中的 coarse 工具规则改为：

```text
- 实时环境工具结果是诊断事实的首选来源；Runbook、Pod 名称、标签和模型经验只用于提出待验证假设，不能替代真实证据。
- 用户是否显式提到 metrics、logging、tracing、topology，不应决定是否使用可观测性工具。当上游已经确认异常 Pod，模型应优先评估 `collect_aiops_case` 这类高信息密度入口能否用更少调用获得 Kubernetes、Metrics、Logging、Tracing 和 Topology 的真实证据，并由模型自主选择合适目标。
- `collect_aiops_case` 成功且 `dimension_details` 足以支撑诊断时，不要重复规划同目标的 describe、logs、events 或 Prometheus；coverage 缺失、冲突或 error 时，再按缺失维度使用细粒度工具补证。
- 这是一项证据优先级，不是代码强制编排。模型仍根据问题范围、目标数量、采集成本和预期证据价值自主决定工具组合。
```

保留现有 case package 标签隔离、evidence refs、topology 强弱和缺失维度回退规则。

- [ ] **Step 2: 将动态 guidance 改为与用户措辞无关**

把 `_build_multidimensional_case_plan_guidance()` 改为：

```python
@classmethod
def _build_live_observability_plan_guidance(
    cls,
    question: str,
    handoff: Dict[str, Any],
) -> str:
    targets = cls._collect_handoff_pod_targets(handoff)
    if not targets:
        return ""
    rendered_targets = ", ".join(f"{namespace}/{pod}" for namespace, pod in targets)
    return (
        "# 实时可观测性证据优先\n"
        f"- 上游已确认的异常 Pod 候选：{rendered_targets}。\n"
        "- 诊断应优先依赖当前环境工具返回的真实证据，而不是 Runbook、名称、标签或模型经验推断。\n"
        "- `collect_aiops_case` 是 Pod 级高信息密度候选入口，可一次返回 Kubernetes、"
        "Metrics、Logging、Tracing 和 Topology；请根据诊断价值、问题范围和采集成本自主选择合适目标及工具组合。\n"
        "- coarse 结果足够时避免重复采集；coverage 缺失、冲突或 error 时，再使用细粒度工具补证。\n"
        "- 这是证据优先级提示，不是强制调用或固定调用次数；仍由 Qwen 自主生成 evidence_plan。"
    )
```

Pod 目标提取继续复用当前 `active_entities` 和 `issue_groups` 数据，不读取状态、不匹配
namespace、Pod 名或故障标签。

- [ ] **Step 3: 运行目标测试确认通过**

Run:

```bash
.venv/bin/pytest -q \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_user_prompt_prioritizes_live_observability_for_broad_multi_pod_question \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_user_prompt_keeps_live_observability_guidance_generic \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_system_prompt_prioritizes_live_observability_independent_of_user_wording
```

Expected: `3 passed`。

### Task 3: 模块回归与真实模型验证

**Files:**
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`
- Runtime verification only: Robusta deployment and context archives

- [ ] **Step 1: 运行 evidence 模块测试**

Run:

```bash
.venv/bin/pytest -q tests/unit/workflow/test_evidence_dynamic_stop.py
```

Expected: 全部通过。

- [ ] **Step 2: 部署当前 Robusta 代码**

沿用仓库现有部署方式更新 `aiops-copilot`，确认新 Pod Ready 且 MCP 工具列表包含
`collect_aiops_case`。

- [ ] **Step 3: 重复运行宽泛问题**

连续运行三次：

```text
我的集群现在有什么问题？
```

每次记录 run ID、evidence plan、实际工具和 `aiops_observability_status`。

- [ ] **Step 4: 审计模型行为**

验收重点：

- Qwen 在没有四维关键词时能够自主考虑并调用 `collect_aiops_case`；
- 对多个异常 Pod 能自主选择有诊断价值的目标，不依赖状态特判；
- coarse 工具成功后没有无意义重复采集；
- 最终报告引用真实 Prometheus、Logging、DeepFlow/Tempo 和 topology；
- 若某次模型仍跳过，报告必须如实标记 `not_collected`，并保留该次结果用于评估模型随机性。

本方案不以三次全部调用作为代码正确性的硬门槛，因为工具选择仍由模型决定；以调用率和
报告证据质量相较修改前明显改善作为模型行为评估结果。
