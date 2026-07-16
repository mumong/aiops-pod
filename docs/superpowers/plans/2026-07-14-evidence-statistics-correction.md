# AIOps Evidence Statistics Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正 AIOps evidence 统计，使多 Pod 实时 case 覆盖、补充证据完成度和工具调用数使用一致且可解释的口径。

**Architecture:** 在 evidence plan 归一化边界按目标 Pod 去重，统计阶段直接基于 mandatory case 目标与成功 case 结果计算覆盖。提示词只负责 Runbook 二次选择和报告表达，不承担数字纠错。

**Tech Stack:** Python、pytest、LangGraph、MCP、Kubernetes

---

### Task 1: Plan 目标归一化与去重

**Files:**
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] 添加失败测试：`target_scope=namespace/pod` 能被解析。
- [ ] 添加失败测试：同 Pod 的系统 mandatory 项和 Qwen coarse 项只保留一项。
- [ ] 扩展 `_extract_plan_pod_target` 并修正 `_ensure_mandatory_aiops_case_plan`。
- [ ] 运行 evidence 动态停止测试模块。

### Task 2: Pod 覆盖统计

**Files:**
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] 添加失败测试：两个 mandatory Pod 成功采集时覆盖为 `2/2`。
- [ ] 在 evidence analysis 中加入 `observability_target_total`、`observability_target_collected` 和 `observability_target_completeness`。
- [ ] 更新 `collection_summary`，优先展示 Pod 可观测性覆盖。
- [ ] 运行 evidence 动态停止测试模块。

### Task 3: 提示词表达约束

**Files:**
- Modify: `app/core/prompts.py`
- Test: `tests/unit/workflow/test_fast_paths.py`

- [ ] 添加失败测试：要求真实 case 后补充更具体 Runbook，且禁止重复。
- [ ] 添加失败测试：明确 `calls` 不是控制关系，正文使用完整 evidence ref。
- [ ] 更新 Evidence、RCA 和 Conclusion 提示词。
- [ ] 运行 fast paths 测试模块。

### Task 4: 集成与真实回归

- [ ] 运行 workflow 单元测试。
- [ ] 构建并推送新镜像。
- [ ] 滚动更新 Deployment。
- [ ] 连续运行三次“我的集群有什么问题？”。
- [ ] 审计 Runbook、case 覆盖、根因正文、拓扑和附录。
