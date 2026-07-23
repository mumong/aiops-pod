# 结构化调用硬上下文预算设计

## 1. 背景

当前系统已经具备三类上下文治理能力：

- 单个工具结果通过 `ObservationProcessor` 生成 bounded summary。
- Evidence Agent 达到阈值后，调用小模型生成 `ContextCompactionSummary`。
- Layer 和 Conclusion 的部分长文本通过 `_compact_context()` 压缩。

真实五次 Qwen 诊断仍出现三次 RCA `ContextWindowExceededError`。根因不是压缩未配置，而是当前机制没有形成端到端硬约束：

1. Evidence 运行时压缩只处理当前 Agent 消息历史，不约束下游重新组装的 RCA 输入。
2. RCA 使用 `call_structured()`，不会进入 Evidence Agent 的运行时压缩路径。
3. 压缩器本身仍可能收到超过 32K 的输入；压缩调用失败后当前逻辑保持原上下文继续运行。
4. `ContextBudgetEstimator` 只记录预算，不阻止超限调用。
5. RCA 上下文包含过长 `layer_handoff`、Fact Ledger、质量合同和多份补充工具表示，整体没有统一上限。

## 2. 目标

实现不依赖模型成功与否的上下文安全边界：

- 任意 `call_structured()` 发起模型请求前，输入必须低于模型窗口和输出预留共同决定的硬预算。
- RCA 在进入底层硬裁剪前，优先保留实体、直接证据、Fact ID、三维可观测事实、冲突和缺失证据。
- Evidence LLM 压缩失败时执行确定性压缩，不能继续携带原始超限历史。
- 保留原始工具数据和完整归档，不因模型上下文裁剪删除审计数据。
- 不增加 OOMKilled、ConfigError 等故障类型特判。

## 3. 非目标

- 不改变 Agent 的工具自主选择机制。
- 不修改 Metrics、Logging、Tracing MCP 查询语义。
- 不改变 Fact Ledger 的事实引用校验规则。
- 不通过提升模型上下文窗口掩盖当前问题。
- 不把原始数据重新塞进最终 Prompt。

## 4. 方案选择

### 方案 A：只降低 Evidence `trigger_ratio`

不能解决。RCA 会从 Workflow State 重新构建输入，仍可能超过 32K。

### 方案 B：只在 RCA 对完整字符串做头尾截断

可以避免 API 报错，但可能丢失中间 Pod 的 Fact ID 和根因证据，诊断质量不可控。

### 方案 C：证据感知压缩 + 通用硬预算门禁

采用本方案：

1. RCA 使用确定性的结构化预算分配生成紧凑上下文。
2. `call_structured()` 计算包含 system prompt、user message、Pydantic schema、输出预留和安全余量的预算。
3. 仍超限时执行通用确定性头尾裁剪，作为最后一道不可绕过的保险。
4. Evidence LLM 压缩失败时执行确定性事件压缩。

该方案同时保证诊断价值和调用稳定性。

## 5. 设计

### 5.1 通用结构化调用硬门禁

在 `AICall.call_structured()` 进入 native structured output 或 JSON fallback 前执行预检：

```text
resolve model context window
  -> count system/user/schema tokens
  -> reserve output tokens
  -> reserve safety margin
  -> calculate maximum input tokens
  -> input over budget?
       no  -> invoke model
       yes -> deterministic compact
             -> recount
             -> still over budget?
                  yes -> stricter hard truncate or local failure
                  no  -> invoke model
```

默认计算：

```text
max_input_tokens =
  min(
    context_window * hard_guard_input_ratio,
    context_window - output_reserved - safety_margin
  )
```

32K 模型默认：

```text
input ratio       = 0.72
max input         = 23,040 tokens
output reserved   = 6,000 tokens
safety margin     = 2,000 tokens
```

预算统计必须包含 `schema.model_json_schema()`，避免 function-calling schema 成为未统计开销。

通用裁剪采用头部与尾部保留：

- 头部保留任务、实体和主要证据入口。
- 尾部保留最终约束、缺失证据和输出要求。
- 中间插入明确的 deterministic compaction 标记。
- 裁剪后重新计数，直到满足硬预算。

### 5.2 RCA 证据感知压缩

RCA 不依赖 LLM 再次总结，而是按固定优先级构建 Prompt：

1. 精简 `layer_handoff`
   - 保留层级、异常 Pod、状态、实体、异常组和 runbook。
   - 限制超长 `primary_problem/reasoning`。
   - 去除重复的 `abnormal_groups/issue_groups` 表示和归档路径。
2. Fact Ledger
   - 保留合法完整 FactRecord，不能截断序列化后的单条记录。
   - 多 Pod 按 ledger 轮询分配空间，避免第一个 Pod 占满预算。
   - 优先 direct、high/medium confidence、critical/strong/supporting facts。
   - coverage 和 related-context 事实排在诊断事实之后。
3. 质量合同
   - 保留 source coverage、diagnostic sufficiency 和 unresolved questions。
4. 补充工具证据
   - 每条只保留工具名、实体、维度、coverage、关键事实、错误和 evidence refs。
   - 整个补充区共享上限，不允许每个工具单独占用 10K/12K。
5. 冲突与缺失
   - 始终保留 bounded 表示，防止模型把缺证据误判为已确认根因。

RCA 主上下文目标上限为约 54,000 字符。底层 token 门禁仍是最终权威，因为中文、JSON 和具体 tokenizer 的字符/token 比例并不固定。

### 5.3 Evidence 压缩失败兜底

运行时压缩仍优先尝试 `ContextCompactionSummary`，但输入先做 deterministic bound。

如果模型压缩失败：

- 从 `thinking_events` 生成确定性摘要。
- 保留 evidence plan、工具名、语义状态、短结果、归档引用。
- 长 AI 消息替换为占位。
- 长 ToolMessage 替换为引用占位。
- `tool_observation_contents` 只保留确定性摘要。

`max_compactions_per_call` 必须真正生效，避免压缩一次后继续执行大量工具再次增长。

### 5.4 归档与可观测性

每次结构化调用至少保留：

- guard 前预算。
- guard 后最终预算。
- 是否触发硬裁剪。
- 原始/最终字符数。
- 原始/最终估算 token 数。
- 使用的 context window、output reserve 和 safety margin。

原始 Evidence、工具 raw/structured/summary 文件保持不变。

## 6. 配置

沿用 `workflow.context_compaction`，增加：

```yaml
hard_guard_enabled: true
hard_guard_input_ratio: 0.72
hard_guard_safety_tokens: 2000
hard_guard_preserve_tail_tokens: 1200
```

这些配置是通用上下文参数，不包含故障类型或 Pod 名称。

## 7. 错误处理

- 无法解析模型上下文窗口：记录 warning，保持兼容，不执行不可靠硬裁剪。
- system prompt + schema 本身超过输入预算：本地抛出明确错误，不发送必然失败的请求。
- 自定义压缩后仍超限：执行通用确定性裁剪。
- 确定性裁剪后仍超限：本地失败并进入节点现有低置信度 fallback。
- 所有失败不得删除 archive 原始数据。

## 8. 验收标准

1. 32K 模型、RCA 原始输入大于 32K 时，发送给模型的最终输入不超过硬预算。
2. RCA 压缩后仍包含每个异常 Pod 的实体 ID 和可用 Fact ID。
3. ConfigError 的关键日志原文和 OOMKilled 的终止原因等 direct facts 优先于 coverage facts。
4. Evidence LLM 压缩失败时仍会缩短 Agent 历史。
5. `max_compactions_per_call` 能执行多次且不会无限压缩。
6. 现有 structured output、Fact Ledger 校验和 Context Archive 测试不回归。
7. 使用历史真实超限归档重放时，RCA Prompt 满足 32K 预算。

