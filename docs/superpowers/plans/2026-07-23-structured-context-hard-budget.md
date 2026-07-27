# Structured Context Hard Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 32K Qwen 实现覆盖 RCA 和 structured output 的硬上下文预算门禁，并为 Evidence 压缩失败提供确定性兜底。

**Architecture:** RCA 先按实体和 Fact Ledger 优先级构造 bounded context；`AICall.call_structured()` 再统一计算 system/user/schema/output/safety 预算并执行不可绕过的确定性裁剪。Evidence 运行时压缩继续保留 LLM 摘要，但失败时用事件元数据生成确定性摘要。

**Tech Stack:** Python 3.12、LangChain/OpenAI-compatible API、Pydantic、pytest、ContextArchive。

---

### Task 1: 上下文预算与确定性裁剪原语

**Files:**
- Modify: `app/core/context/budget.py`
- Test: `tests/unit/context/test_archive_budget_observation.py`

- [ ] 编写失败测试：结构化输入预算应计入 schema、输出预留和安全余量。
- [ ] 编写失败测试：长文本裁剪后 token 数不超过目标，并保留头部、尾部和压缩标记。
- [ ] 运行该测试模块，确认新增测试因能力缺失而失败。
- [ ] 实现预算计算和确定性文本裁剪原语。
- [ ] 运行该测试模块，确认通过。

### Task 2: `call_structured` 硬预算门禁

**Files:**
- Modify: `app/core/aicall/client.py`
- Modify: `app/core/service.py`
- Modify: `deploy/configmap/config.yaml`
- Test: `tests/unit/aicall/test_event_loop_safety.py`
- Test: `tests/unit/test_service_think_stream.py`

- [ ] 编写失败测试：32K 模型收到超长 RCA 输入时，模型实际收到的消息低于硬预算。
- [ ] 编写失败测试：guard 前后预算写入 archive，并带有裁剪元数据。
- [ ] 编写失败测试：无法容纳 system/schema 时本地失败，不调用 provider。
- [ ] 运行 AICall 和 service 配置测试，确认新增测试失败。
- [ ] 在 `call_structured()` 接入硬门禁，并支持可选的节点级 compactor。
- [ ] 增加通用配置解析和部署默认值。
- [ ] 运行 AICall 和 service 配置测试，确认通过。

### Task 3: RCA 证据感知压缩

**Files:**
- Modify: `app/core/workflow/nodes/root_cause_analyzer.py`
- Modify: `app/core/workflow/fact_contract.py`
- Test: `tests/unit/workflow/test_context_handoff.py`
- Test: `tests/unit/workflow/test_fact_contract.py`

- [ ] 编写失败测试：超长 layer handoff、五个 Pod、多份三维证据生成的 RCA context 保持 bounded。
- [ ] 编写失败测试：每个 Pod 至少保留实体身份，direct facts 优先于 coverage facts。
- [ ] 编写失败测试：补充工具上下文使用共享上限，不能按工具线性膨胀。
- [ ] 运行 workflow 测试模块，确认新增测试失败。
- [ ] 实现 RCA section budgets、精简 handoff 和 bounded supplementary evidence。
- [ ] 修正 Fact Ledger 截断优先级，但不改变事实校验规则。
- [ ] 将 RCA compactor 传入通用 structured guard。
- [ ] 运行 workflow 测试模块，确认通过。

### Task 4: Evidence 确定性压缩兜底与重复压缩

**Files:**
- Modify: `app/core/aicall/client.py`
- Test: `tests/unit/aicall/test_observation_processing.py`

- [ ] 编写失败测试：LLM compactor 返回 `None` 时仍压缩 thinking/tool messages。
- [ ] 编写失败测试：`max_compactions_per_call=2` 时上下文再次增长可以二次压缩。
- [ ] 运行 observation 测试模块，确认新增测试失败。
- [ ] 实现 bounded compaction payload、确定性 fallback 和压缩计数。
- [ ] 运行 observation 测试模块，确认通过。

### Task 5: 集中回归与真实归档重放

**Files:**
- Create: `scripts/replay_rca_context_budget.py`
- Create: `testreports/structured-context-hard-budget-20260723.md`
- Modify: `docs/上下文管理设计与实现.md`

- [ ] 使用 `/tmp/model-comparison-20260722/archives` 中三个真实超限 run 重放 RCA context。
- [ ] 验证每个重放结果低于 32K，且保留异常 Pod、ConfigError/OOMKilled 关键事实和 Fact ID。
- [ ] 集中运行 context、AICall、workflow 相关测试模块。
- [ ] 如部署条件可用，重新部署并使用 Qwen 执行一次“我的集群有什么问题？”。
- [ ] 记录预算前后、结构化 RCA 结果、剩余风险和运行命令。
- [ ] 更新上下文管理文档。

### Task 6: 独立审查

**Files:**
- Review only

- [ ] 检查是否存在故障类型、namespace、Pod 名称特判。
- [ ] 检查所有模型请求是否可能绕过 structured hard guard。
- [ ] 检查裁剪后 Fact ID 和实体范围是否仍可通过 RCA claim validation。
- [ ] 检查原始 archive 是否保持完整。
- [ ] 独立 reviewer 给出 ACCEPT 或 REWORK。

### Task 7: Live 返工：Tokenizer 漂移、流中断恢复和报告一致性

**Files:**
- Modify: `app/core/aicall/client.py`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Modify only if the failing report test proves it is required: `app/core/workflow/nodes/root_cause_analyzer.py`
- Test: `tests/unit/aicall/test_event_loop_safety.py`
- Test: `tests/unit/workflow/test_fast_paths.py`
- Test: `tests/unit/workflow/test_reporter_runbooks.py`
- Record: `agent-loop/tasks/T007/attempts/A016/`

- [ ] 编写失败测试：当本地 token 计数为 estimated 时，hard guard 必须在公开上限 `23040` 内再保留固定 estimator drift reserve；exact tokenizer 不应重复扣减该 reserve。
- [ ] 运行新增 hard guard 测试，确认当前实现因为仍裁剪到 `23040` 而失败。
- [ ] 实现通用 drift reserve，归档同时记录 `max_input_tokens`、`effective_input_target`、`estimator_drift_reserve` 和 token accuracy；不得按模型名称、故障类型、namespace 或 Pod 名称分支。
- [ ] 编写失败测试：OpenAI `APIError` 子类返回 `unexpected EOF`、`empty_stream` 或 `closed before first payload` 时只重试一次并切换 non-streaming；普通 4xx/5xx、超时和上下文错误不得重试。
- [ ] 运行流中断测试，确认 `InternalServerError: empty_stream` 当前不会被恢复。
- [ ] 实现严格白名单流中断判断，保留一次重试上限。
- [ ] 编写失败测试：当 Fact Ledger/机器附录已提供 `coverage=present` 的日志、指标、Trace、Kubernetes 和拓扑事实时，确定性报告不得输出“未返回可用”或“未提供该维度”，也不得暴露 `... 截断，原始 N 字符`。
- [ ] 编写失败测试：两个独立异常实体必须渲染为两条实体隔离的因果链，不能合并为一个跨实体 trigger/mechanism/manifestation 链。
- [ ] 实现基于结构化 coverage、事实和实体 ID 的通用报告一致性处理；不得增加 OOM、ConfigError 或测试 Pod 特判。
- [ ] 集中运行 AICall、workflow 和完整单元测试。
- [ ] 构建隔离 probe 镜像，不修改生产 Qwen、共享 `aiops-config` 或测试 Pod。
- [ ] 重新运行“我的集群现在有什么问题？”，归档 provider token、八项真实查询、两条因果链、最终报告、部署前后快照和完整测试日志。
- [ ] 独立 reviewer 按 T007 contract 给出 `ACCEPT` 或精确 `REWORK`。
