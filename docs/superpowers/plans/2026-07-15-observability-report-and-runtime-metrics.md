# Observability Report And Runtime Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正真实运行统计、支持粗粒度 case 后按需细粒度补采，并优化面向人的结构化诊断报告。

**Architecture:** 以最终 `thinking_events` 作为调用统计唯一事实源；Evidence 在 mandatory case 完成后执行一次 post-case reconciliation，由模型决定是否调用细粒度证据工具；Conclusion 保留现有章节并通过 prompt 与确定性后处理增强真实数据和拓扑总结。

**Tech Stack:** Python、LangGraph/LangChain、Pydantic、pytest、Kubernetes、MCP

---

### Task 1: 真实运行统计

**Files:**
- Modify: `app/core/workflow/metrics.py`
- Modify: `app/core/workflow/reporter.py`
- Modify: `app/core/workflow/nodes/base.py`
- Modify: `app/core/workflow/executor.py`
- Test: `tests/unit/workflow/test_executor_timing.py`
- Test: `tests/unit/workflow/test_reporter_runbooks.py`

- [ ] 添加失败测试：多个 `ai_usage` 事件必须计为多次真实模型请求。
- [ ] 添加失败测试：工具次数区分 started/succeeded/failed，耗时由 start/result 时间差计算。
- [ ] 运行统计测试，确认失败原因是当前按 Agent loop 计数及 0ms 工具耗时。
- [ ] 实现 `WorkflowMetrics.rebuild_runtime_counts(thinking_events)`，按 `tool_call_id` 去重。
- [ ] 移除 `_call_llm` 中根据 `tool_call_count` 写入 0ms 工具调用的逻辑。
- [ ] 在最终状态形成后统一重建统计，日志和报告都使用同一结果。
- [ ] 运行统计模块测试。

### Task 2: Case 后按需细粒度补采

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`
- Test: `tests/unit/workflow/test_context_handoff.py`

- [ ] 添加失败测试：mandatory case 成功后不能在 post-case reconciliation 之前立即停止。
- [ ] 添加失败测试：case 存在 missing/error/conflict 或关键字段不足时允许 `get_aiops_case_evidence`。
- [ ] 添加失败测试：case 已包含足够决定性证据时允许模型停止，不强制细粒度展开。
- [ ] 调整 early-stop 状态，增加 `post_case_reconciliation` 完成标记。
- [ ] 调整执行循环，在全部 case 返回后给模型一次携带 case 摘要的补采决策机会。
- [ ] 更新 Evidence prompt：细粒度调用依据是“能否回答关键诊断问题”，而非 coverage 是否为 present。
- [ ] 运行 Evidence 模块测试。

### Task 3: 完整度与最终报告

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Test: `tests/unit/workflow/test_fast_paths.py`

- [ ] 添加失败测试：最终报告不再注入“采集统计”。
- [ ] 添加失败测试：目标 case 100% 但决定性证据不足时，诊断概览不得无条件显示 100%。
- [ ] 添加失败测试：拓扑原始边后必须存在人可读的调用入口、工作负载归属和责任边界总结。
- [ ] 删除“采集统计”的确定性注入。
- [ ] 扩展 Conclusion prompt，要求按 Pod 展示关键 Metrics、Logging、DeepFlow、Tempo 和 K8s 原始字段。
- [ ] 增强拓扑后处理，根据原始 calls/selects/owned_by 边生成受约束的中文总结。
- [ ] 运行 Conclusion 模块测试。

### Task 4: 集成验证与部署

**Files:**
- Verify: `deploy/k8s-simple.yaml`
- Verify: `deploy/configmap/config.yaml`
- Verify: `scripts/`

- [ ] 运行相关模块测试：

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_executor_timing.py \
  tests/unit/workflow/test_reporter_runbooks.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_fast_paths.py
```

- [ ] 使用现有部署脚本构建并滚动更新 Robusta。
- [ ] 使用模糊问题“我的集群现在有什么问题？”执行真实诊断。
- [ ] 审计新 run 的 `thinking_events`、工具归档、统计块和最终报告。
- [ ] 验证 case 后在有必要时调用细粒度工具，没有必要时明确停止。
- [ ] 验证最终报告无“采集统计”，可观测性数据更详细且拓扑有中文总结。
