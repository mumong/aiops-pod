# Observability First-Round Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对每个异常 Pod 强制真实尝试 Metrics、Logging、Tracing 首轮查询，完成后恢复 Qwen 自主补证。

**Architecture:** 在 `EvidenceCollectorNode` 内把首轮目标从 Pod 粒度提升为 Pod 与通用查询工具的笛卡尔积。先让 Qwen生成参数，缺失维度经一次结构化修复后由无场景特判的基线计划兜底；执行阶段只在所有首轮目标已产生真实 `tool_result` 后解除门控。

**Tech Stack:** Python 3.12、LangGraph/AICall、Pydantic、pytest、Kubernetes、Prometheus、Elasticsearch、DeepFlow/Tempo MCP

---

### Task 1: Gate Contract Tests

**Files:**
- Modify: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] 增加单 Pod 三维计划补齐测试。
- [ ] 增加多 Pod 六个门控目标测试。
- [ ] 增加 empty/absent/error 均视为真实尝试的测试。
- [ ] 增加三维完成前禁止停止、完成后允许自主补证的测试。
- [ ] 运行新增测试并确认因现有 Pod 粒度实现而失败。

### Task 2: Plan Completion And Gate Tracking

**Files:**
- Modify: `app/core/workflow/nodes/evidence_collector.py`

- [ ] 将计划缺失检查改为 `(namespace, pod, tool)` 粒度。
- [ ] 更新结构化修复提示，逐项列出缺失维度。
- [ ] 增加无故障类型特判的三维基线计划兜底。
- [ ] 将 attempted、remaining、stalled 和 context stop 统一改为门控项粒度。
- [ ] 运行 Task 1 测试并确认通过。

### Task 3: Prompt And Runtime Contract

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `deploy/configmap/config.yaml`
- Modify: `tests/unit/workflow/test_fast_paths.py`
- Modify: `tests/unit/workflow/test_reporter_runbooks.py`

- [ ] 明确首轮三维必须执行，空结果也是有效边界。
- [ ] 明确首轮完成后由 Qwen决定深入查询。
- [ ] 增加配置开关 `observability_first_round_gate.enabled`。
- [ ] 运行 Evidence、Prompt、Config 模块测试。

### Task 4: Deployment And Repeated Runtime Audit

**Files:**
- Create: `testreports/observability-first-round-gate-20260721.md`

- [ ] 构建并部署 Robusta。
- [ ] 检查 Pod Ready 和 MCP 三工具可发现。
- [ ] 使用“我的集群有什么问题？”连续运行至少三次。
- [ ] 审计每个异常 Pod 的三维 tool result、coverage、真实原始值、后续自主补证和报告一致性。
- [ ] 记录耗时、工具调用数、LLM 调用数、上下文停止和剩余风险。
