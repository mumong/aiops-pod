# Qwen 32K 结构化 RCA 硬上下文预算测试报告

## 1. 目标

验证 Robusta 在 Qwen 32K 上下文下：

1. Evidence 压缩失败时不会继续携带原始大上下文。
2. RCA 重新组装的证据输入具有结构化上限。
3. `call_structured()` 在 provider 调用前执行不可绕过的硬预算检查。
4. 压缩后保留异常 Pod、Fact ID 和真实可观测证据引用。
5. 原始 raw/structured/summary 归档不被删除。

测试日期：2026-07-23。

## 2. 原问题

2026-07-22 的五次 Qwen 对照测试中，三次 RCA 请求明确超过 32K：

| run_id | RCA 输入 tokens | 含输出预留后的窗口占比 | 结果 |
|---|---:|---:|---|
| `b1b19448b1724fc2` | 32,578 | 120.6% | `ContextWindowExceeded` |
| `d67a5d552e154dae` | 35,575 | 129.9% | `ContextWindowExceeded` |
| `ac9eac1ae0764a27` | 34,148 | 125.5% | `ContextWindowExceeded` |

根因不是“完全没有压缩”，而是原压缩只覆盖 Evidence Agent 消息历史，RCA 会重新从 state 拼装大输入；同时预算统计只告警，不阻断请求。

## 3. 实现

### 3.1 通用 provider hard guard

`AICall.call_simple()` 和 `AICall.call_structured()` 统一统计：

- system prompt
- user message
- 可选 Pydantic JSON schema
- provider request envelope
- output reserve
- safety margin

32K 默认硬输入上限为 23,040 tokens。超限时先使用节点级压缩，再执行确定性头尾裁剪；裁剪后仍超限则本地失败，provider 不会被调用。

所有硬门禁预算都禁用 completion-based provider usage probe，避免 `/chat/completions` token 探测先接收到原始超长 prompt。计数优先使用本地 tokenizer；未配置时使用保守的 `UTF-8 bytes/3`。每次请求额外计入 64 tokens provider envelope，native structured 调用直接复用含 safety margin 的最终预算。

模型窗口无法解析且 hard guard 开启时 fail closed，并先写入：

```text
budget/<node>_pre_guard.json
hard_guard.error=context_window_unavailable
```

### 3.2 LangGraph Agent 每轮 hard guard

工具型 Agent 使用 `wrap_model_call` 在每一次 provider 调用前重新统计真实 `ModelRequest`：

- system prompt
- LangGraph message history
- AI tool call arguments
- tool schemas
- response-format schema
- output reserve
- safety margin

超限时，provider-bound messages 被替换为单条确定性证据摘要。摘要保留用户目标、工具名、有界参数、关键工具结果、语义状态和 archive refs。该过程不调用 LLM，因此不会因为 Qwen 压缩失败而继续发送原始大上下文。

### 3.3 RCA 证据感知构建

- `layer_handoff` 上限：7,000 字符。
- RCA 主 context 上限：52,000 字符。
- 所有异常 Pod 先进入 `abnormal_pod_entity_index`。
- canonical Fact Ledger 中 direct diagnostic facts 优先于 coverage facts。
- 质量合同、补充工具输出使用共享预算。
- 所有 legacy case 先进入不可截断的
  `supplementary_identity_index`，保留 case ID 和 primary Pod
  kind/namespace/name/uid。
- `supplementary_limit=10` 只限制可选事实、结构化上下文或 raw 详情；
  第 11 个及以后的 case 仍以 identity-only 形式保留。
- 完整最小身份索引无法装入预算时本地明确失败，不静默丢失 case。

### 3.4 Evidence 确定性兜底

- LLM compactor 返回 `None`、无效结构或无证据合同内容时，使用 deterministic fallback。
- 摘要保留 evidence plan、工具名、`semantic_success`、错误/结果预览和 archive refs。
- 无 refs 的长 tool result 仍会裁剪，并标记 `refs unavailable`。
- deterministic summary 受 `summary_max_tokens` 总限制。
- `max_compactions_per_call` 使用计数器，可配置二次压缩。
- `max_compactions_per_call: 0` 会保持为 0，不再被配置默认值覆盖。
- AI tool-call arguments 被纳入运行时预算。
- 空内容但包含 tool calls 的 AIMessage 同样进入 provider-bound 历史压缩。
- 压缩器 payload 有事件数和 token 总上限。
- LLM 摘要不能成为证据事实来源；工具名、状态、错误、结果预览和 archive refs 均由 source events 确定性重建。

## 4. 真实归档重放

命令：

```bash
PYTHONPATH=. .venv/bin/python scripts/replay_rca_context_budget.py \
  --archive-root /tmp/model-comparison-20260722/archives \
  --output /tmp/structured-context-replay-final.json
```

结果：

| run_id | 历史记录输入 | 当前重建输入 | 硬上限 | Pod 保留 | refs 保留 |
|---|---:|---:|---:|---:|---:|
| `b1b19448b1724fc2` | 32,578 | 11,495 | 23,040 | 5/5 | 8/8 |
| `d67a5d552e154dae` | 35,575 | 11,828 | 23,040 | 5/5 | 7/7 |
| `ac9eac1ae0764a27` | 34,148 | 9,544 | 23,040 | 5/5 | 6/6 |

三次重放全部通过。第三个归档在首次重放时曾暴露“长 handoff 丢失第 5 个 Pod”的问题，增加独立实体索引后恢复为 5/5。

历史归档生成时还没有 canonical Fact Ledger，因此 `fact_id_check_applicable=false`。当前 Fact ID 保留通过合成的多实体 canonical ledger 测试验证。

## 5. 自动化验证

已验证的关键测试包括：

```text
tests/unit/context/test_archive_budget_observation.py
tests/unit/aicall/test_event_loop_safety.py
tests/unit/aicall/test_observation_processing.py
tests/unit/test_service_think_stream.py
tests/unit/workflow/test_fact_contract.py
tests/unit/workflow/test_context_handoff.py
```

关键行为：

- provider 实际收到的 plain、structured 和 LangGraph input 不超过硬上限。
- 原始超长 prompt 不会被发送给 completion-based usage probe。
- 模型窗口未知时 provider 调用次数为 0，并归档明确错误。
- LangGraph Agent 每轮真实 provider-bound messages 受硬预算约束。
- 空文本 tool-call AIMessage 的历史参数会在第二次真实 `create_agent` provider 请求前压缩。
- schema-valid LLM 压缩结果不能通过自由文本字段注入伪造证据。
- system prompt + schema 自身超限时 provider 调用次数为 0。
- deterministic compaction 在 LLM 压缩失败时生效。
- 无 archive refs 的长 tool result 仍被压缩。
- context 再次增长时真实 helper 可以二次压缩。
- 多异常 Pod 和 direct Fact ID 不因预算裁剪丢失。

测试结果：

```text
上下文与证据集中测试：640 passed, 1 warning
RCA/Fact Ledger 集中测试：177 passed, 1 warning
全量单元测试：1000 passed, 23 warnings
历史真实归档重放：3/3 passed
历史归档完整性：1002 个文件 SHA256 前后一致
目标级独立审查：ACCEPT
```

## 6. 数据保留与消费边界

模型上下文缩短不等于删除真实数据：

- `tools/*.raw.txt`：原始工具结果。
- `tools/*.structured.json`：结构化查询结果。
- `tools/*.summary.txt`：回注模型的摘要。
- `node_inputs/`、`node_outputs/`、`handoff/`：节点输入、输出和阶段交接。
- `budget/*_pre_guard.json`：硬门禁前预算。
- `budget/<node>.json`：硬门禁后预算及策略。

Agent 默认消费有界 Fact Ledger、实体索引和摘要；需要细节时根据 ref 读取归档，而不是把全部 raw 数据一次性放入 32K prompt。

## 7. 剩余限制

1. 本次真实验证是历史 archive 离线重放，没有重新部署并执行新的在线 Qwen run。
2. 当前环境无法连接 `10.2.0.54:4000`，因此尚未执行新的在线 Qwen 部署诊断。
3. 未配置 Qwen 原生 tokenizer 时，所有 hard guard 使用保守的 `UTF-8 bytes/3` 本地估算，并保留 2,000 tokens 安全余量；硬门禁不调用 completion-based provider probe。
4. 历史 archive 没有 canonical Fact ID，无法用这三次旧数据直接验证 Fact ID；已由当前合同测试覆盖。
