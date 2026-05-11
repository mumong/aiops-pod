# 工作流结构化运行时演进说明（2026-05-09）

本文记录 2026-05-07 至 2026-05-09 期间工作流核心链路的演化结果。目标是给后续审查提供一个以当前代码为准的参考，而不是描述早期 prompt JSON 方案。

当前主线结论：

- 结构化输出的权威来源已经从“prompt 要求 LLM 手写 JSON”迁移到 Pydantic schema。
- 运维诊断 `/ask` 仍然保留 `layer -> evidence -> rca -> conclusion` 四节点诊断链，这是本轮改造的主线。
- `/query` 走 direct query 快路径：`layer(query direct) -> conclusion(render)`。
- 大上下文不再默认跨节点传递，完整内容落盘到 context archive，下游只消费结构化 handoff 和摘要。
- evidence 完整度不再等同于工具调用成功率，而是按 Pydantic evidence plan 的可计量项实际匹配计算。

## 1. 为什么做这轮改造

早期问题集中在 5 类：

1. LLM 在 prompt 里手写 JSON 不稳定。常见问题包括字段类型漂移、JSON 被自然语言包裹、最后一段 JSON 截断、字段缺失。
2. `primary_pod` 语义过强。实际集群可能同时存在 `ImagePullBackOff`、`ErrImagePull`、`Terminating` 等多类异常，但下游容易只围绕单个 primary pod 分析。
3. evidence 证据统计口径不透明。工具执行了很多次，但报告里可能显示 `0/N`，或者相反因为自动证据导致完整度接近 100%。
4. layer 工具结果已经是真实证据，但 evidence 可能重复采集，导致慢且上下文膨胀。
5. 运维诊断和简单查询混在一起时，QUERY 错误容易被误判为故障诊断，诊断链也容易被简单查询拖慢。

本轮改造的原则：

- 结构化输出只能由 Pydantic schema 生成和校验。
- prompt 只描述字段语义和任务约束，不再给大段 JSON 输出模板。
- 真实工具结果通过 `thinking_events`、`tool_result.structured`、`tool_args` 和 context archive 传递。
- 统计口径要能解释：计划了多少、匹配了多少、实际执行了多少、未规划证据多少。

## 2. 当前 Pydantic 合约

核心 schema 位于：

- [app/core/workflow/schemas.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/schemas.py)

关键对象：

| Schema | 使用位置 | 职责 |
|---|---|---|
| `LayerOutput` | layer 结构化提取 | 统一输出 layer、layers、reasoning、abnormal_pods、issue groups 相关字段、query_result |
| `LayerHandoff` | layer 到下游 | 下游真正消费的紧凑结构，承载 abnormal groups、active signals、current abnormal summary |
| `EvidencePlanOutput` | evidence 计划 | 生成 Pydantic evidence_plan，不再依赖 LLM 在主 agent 消息里手写 JSON |
| `EvidencePlanItem` | evidence 计划项 | 表达证据意图、目标范围、可接受工具和是否计入完整度 |
| `EvidenceCollectionOutput` | evidence 输出 | 输出证据计划、证据清单、完整度、工具执行统计 |
| `EvidenceMatchOutput` | 计划和工具结果对齐 | 可选的结构化裁判结果，用于 plan item 与 tool result 对齐 |
| `RCAOutput` | RCA 输出 | 输出根因、因果链、替代原因、限制项 |
| `QueryResult` | `/query` 输出 | 查询结果的可渲染结构化表格 |
| `ContextCompactionSummary` | 上下文压缩 | 将历史 ai_messages/tool_observations 压缩成结构化摘要 |

### 2.1 Pydantic 与 prompt 的关系

当前设计不是“prompt 输出 JSON，Pydantic 做事后校验”，而是：

```text
agent 调工具并输出自然语言分析
  -> call_structured(schema=...)
  -> Pydantic 生成结构化对象
  -> 节点只消费 Pydantic 对象
```

prompt 中仍可以出现字段名、字段语义、约束和禁止事项，但不应该出现“请只输出如下 JSON 模板”这种大段模板。这样可以减少小模型截断、格式漂移和字段拼写错误。

### 2.2 旧行为到新行为对照

| 位置 | 旧行为 | 当前行为 |
|---|---|---|
| layer 输出 | prompt 要求模型手写 JSON，代码再解析 | agent 只负责工具和自然语言分析，`LayerOutput` Pydantic 提取唯一结构化结果 |
| layer 到 evidence | 传递大段 layer 文本和单个 `primary_pod` | 传递 `LayerHandoff`，核心是 `abnormal_groups`、`abnormal_pods`、`current_abnormal_summary` |
| evidence plan | 第一条 assistant 消息必须输出 `evidence_plan JSON` | `EvidencePlanOutput` 结构化生成计划，执行阶段不再手写 plan |
| evidence 匹配 | 主要靠 command/description/tool 文本匹配 | 优先用 `evidence_type`、`target_scope`、`acceptable_tools` 做意图级匹配 |
| 证据完整度 | 容易变成工具成功数或自动证据数 | 明确区分 plan 完整度、环境证据完整度、执行工具数、未规划工具数 |
| RCA | 可从大文本和 LLM 叙述里继续推理 | 基于 `RCAOutput`，主要消费 evidence 结构化事实 |
| conclusion | 可能重写证据统计和置信度 | 以后端结构化统计为准，主要负责渲染 |
| QUERY | 可能进入完整诊断链或被误判成 L1/L3 | direct query 只生成 `QueryResult` 并直接渲染 |

### 2.3 运维诊断数据流总览

```text
kubectl/prometheus/bash tool_result
  -> ObservationProcessor
      -> raw.txt
      -> structured.json
      -> summary.txt
      -> semantic_success
  -> thinking_events
  -> LayerOutput / EvidencePlanOutput / EvidenceCollectionOutput / RCAOutput
  -> WorkflowState
  -> reporter / conclusion
```

核心原则：

- 原始工具输出只落盘，不默认塞给下游。
- `structured.json` 是最稳定的机器可读事实来源。
- `summary.txt` 是给 LLM 的短上下文。
- `semantic_success=false` 不等于无价值，它可能是负向诊断事实，例如 registry timeout；但不能被当作普通成功 rows。

## 3. `/ask` 当前链路

`/ask` 是运维诊断主链，仍走完整诊断链：

```text
question
  -> layer
  -> evidence
  -> rca
  -> conclusion
```

这条链路适用于：

- 我的集群有什么问题？
- 为什么这个 Pod 一直拉不起镜像？
- 为什么 Pod 卡在 Terminating？
- 当前异常的根因是什么？

这条链路的目标不是“快速查一个数”，而是形成可审计的诊断闭环：

```text
当前异常识别
  -> 异常分组
  -> 证据计划
  -> 工具验证
  -> 因果链
  -> 报告
```

### 3.1 layer：定位和结构化 handoff

layer 当前分两段：

```text
AICall agent 调工具
  -> 生成自然语言分析和 thinking_events
  -> LayerOutput Pydantic 提取
  -> LayerHandoff 构建
```

主要变化：

- layer 不再要求模型手写最终 JSON。
- layer 工具结果会被规则提取出 `current_abnormal_summary`，包括 `status_counts`、`selected_rows`。
- 当前异常不再只依赖 `primary_pod`，而是以 `abnormal_pods`、`abnormal_groups`、`issue_groups` 为核心传递。
- `primary_pod` 仍可能存在于兼容字段里，但不再作为后续采证的唯一主线。
- layer 阶段真实工具结果会进入 `thinking_events`，后续 evidence 可以把它们纳入 `layer_verified` 证据。

#### layer 的诊断职责边界

layer 负责判断“当前有哪些异常、属于哪些层”，不负责最终根因结论。

它应该优先完成这些事实：

- 当前非正常资源列表。
- Pod 状态分布，例如 `status_counts={"ImagePullBackOff": 4, "Terminating": 1}`。
- 每类异常对应的异常类型，例如 `ImagePullFailed`、`TerminatingStuck`。
- 每类异常兼容的归因层，例如 L3、L1。
- 明显匹配的 runbook 参考。

它不应该在这一阶段把所有证据链都查完，也不应该只因为 Prometheus 查询失败就把 `/query` 请求漂移成 L1/L3 运维诊断。

#### current_abnormal_summary 是诊断核心输入

`current_abnormal_summary` 来自真实工具结果，不依赖 LLM 自己列举。典型结构：

```json
{
  "source": "kubectl_get_by_kind_in_cluster",
  "status_counts": {
    "ImagePullBackOff": 4,
    "Terminating": 1
  },
  "total_abnormal": 5,
  "selected_rows": [
    "aaa test1-redis-master-0 0/1 ImagePullBackOff ...",
    "aiops-e2e terminating-stuck 0/1 Terminating ..."
  ]
}
```

后续 evidence 必须以它作为覆盖基准。非 `Running/Completed/Succeeded/Ready/Bound/Active` 的状态都应至少最小验证，不能只验证影响最大的异常。

#### abnormal_groups 替代单点 primary_pod 思维

运维诊断里经常同时存在多组异常。例如：

```text
g1: ImagePullBackOff / ErrImagePull, ImagePullFailed, L3
g2: Terminating, TerminatingStuck, L1
```

当前目标是让下游围绕 `abnormal_groups` 和 `abnormal_pods` 工作，而不是围绕唯一 `primary_pod`。

实际策略：

- 影响范围最大的异常组作为主影响面，做完整验证。
- 其他异常组做最小验证，至少验证当前状态和一个关键事件/配置/依赖信号。
- 如果多个异常组互不相关，RCA 和 conclusion 要明确呈现多个问题，而不是强行合并成单一根因。

当前异常组的典型结构：

```json
{
  "group_id": "g1",
  "status_keywords": ["ImagePullBackOff", "ErrImagePull"],
  "pod_abnormal_type": "ImagePullFailed",
  "compatible_layers": ["L3"],
  "primary_entities": [
    {"kind": "Pod", "namespace": "aaa", "name": "test1-redis-master-0"}
  ],
  "is_primary": true,
  "possible_scenarios": []
}
```

#### 运维诊断 layer 输出的消费关系

layer 输出不会直接作为最终报告事实，而是进入 `layer_handoff`：

```text
LayerOutput
  -> LayerHandoff
  -> evidence user message
  -> RCA compact context
  -> conclusion summary
```

这样做的原因：

- `LayerOutput` 可能包含 LLM 整理字段。
- `LayerHandoff` 会合并工具结构化事实，例如 `current_abnormal_summary`。
- 下游只依赖 `LayerHandoff` 这种更稳定的结构。

### 3.2 evidence：Pydantic plan + 意图匹配

evidence 当前不再让主 agent 的第一条消息手写 `evidence_plan JSON`。计划由 `EvidencePlanOutput` Pydantic schema 生成。

#### 运维诊断 evidence 的职责

evidence 只负责“把 layer 给出的异常变成可审计证据”，不是重新做全局巡检。

它的输入重点：

- `layer_handoff.abnormal_groups`
- `layer_handoff.issue_groups`
- `layer_handoff.abnormal_pods`
- `layer_handoff.current_abnormal_summary`
- `layer_handoff.active_signals`
- `layer_handoff.matched_runbooks`

它的输出重点：

- `evidence_plan`
- `evidence_inventory`
- `evidence_facts`
- `evidence_conflicts`
- `missing_evidence`
- `plan_completeness`
- `environment_evidence_completeness`

#### 主异常组和非主异常组的采证强度

当前建议口径：

| 异常组 | 采证强度 | 示例 |
|---|---|---|
| 主影响面异常组 | 完整验证 | ImagePullBackOff 影响 4 个 Redis Pod，需要状态、事件、Pod spec、registry 连通性 |
| 次要异常组 | 最小验证 | Terminating 测试 Pod，需要当前状态和 finalizer/deletionTimestamp |
| 已恢复或 NotFound 对象 | 冲突/负向证据 | 不能当作当前故障正向证据 |

这样可以避免两个极端：

- 只看一个 Pod，漏掉其他当前异常。
- 对所有异常都展开长链路，导致工具调用爆炸。

计划项现在除了旧字段：

- `id`
- `description`
- `level`
- `tool`
- `command`
- `purpose`

新增结构化意图字段：

- `evidence_type`
- `target_scope`
- `acceptable_tools`
- `counts_for_completeness`

典型计划项：

```json
{
  "id": "g1-status",
  "description": "验证镜像拉取异常组当前 Pod 状态",
  "level": "critical",
  "tool": "kubectl_describe",
  "command": "kubectl describe pod <abnormal-pod>",
  "purpose": "确认 ImagePullBackOff / ErrImagePull 当前原因",
  "evidence_type": "pod_status",
  "target_scope": "group:g1",
  "acceptable_tools": ["kubectl_describe", "kubectl_get_by_name"],
  "counts_for_completeness": true
}
```

#### 意图匹配口径

匹配逻辑优先使用结构化字段：

```text
EvidencePlanItem.evidence_type
EvidencePlanItem.acceptable_tools
EvidencePlanItem.target_scope
```

不再优先纠结命令参数完全一致。例如计划是“验证 Pod 状态”，实际用 `kubectl_describe` 或 `kubectl_get_by_name` 都可以，只要工具类别在 `acceptable_tools` 中，并且结果回答了 `pod_status` 这个意图。

旧计划没有 `evidence_type` 时，保留兼容规则，继续基于 command/description/tool/result 做宽松匹配。

#### 证据完整度口径

完整度不是工具调用成功率，也不是固定 100%。

当前核心口径：

```text
plan_completeness = matched_planned_items / measurable_planned_items
environment_evidence_completeness = collected_environment_items / measurable_environment_items
```

新增统计字段：

| 字段 | 含义 |
|---|---|
| `plan_total` | Pydantic evidence plan 中可展示的计划项总数 |
| `plan_collected` | 当前 evidence 节点匹配成功的计划项数量 |
| `plan_completeness` | `plan_collected / plan_total` |
| `environment_evidence_total` | 计入环境证据的总项数，包括部分上游 layer_verified |
| `environment_evidence_collected` | 已采集环境证据数量 |
| `environment_evidence_completeness` | 环境证据完整度 |
| `executed_tool_count` | 实际执行的有效证据工具数量 |
| `matched_tool_count` | 成功匹配计划项的工具/证据数量 |
| `unplanned_tool_count` | 实际执行但未被计划吸收的证据工具数量 |

示例解释：

```text
计划 4 项，匹配 2 项，实际执行工具 3 个，未规划证据 1 个
```

这表示完整度是 50%，不是 100%。多出来的工具结果会展示为未规划证据或补充事实，但不会自动提高计划完整度。

### 3.3 layer_verified：上游证据纳入 evidence

layer 已经执行过的真实环境工具不应该被浪费。当前 evidence 会把 layer 阶段有效工具结果转换为 `layer_verified` 证据：

```text
layer thinking_events
  -> tool_result
  -> EvidenceItem(source="layer_verified")
  -> merge into evidence_inventory
```

约束：

- `fetch_runbook` 和 `read_context_archive` 不算环境证据。
- layer 工具结果必须是当前异常对象相关的真实观察，才应参与证据计算。
- layer_verified 可以补足计划项，也可以作为额外环境证据展示。

### 3.4 RCA：结构化因果收敛

RCA 默认 lite，不再调工具。它消费：

- `layer_handoff`
- `evidence_facts`
- `evidence_conflicts`
- `missing_evidence`
- `evidence_analysis`

RCA 输出由 `RCAOutput` 约束，包含：

- `phenomenon`
- `root_cause`
- `causal_chain`
- `alternative_causes`
- `confidence`
- `limitations`
- `recommended_actions`

RCA 的职责是基于已采集证据做因果链收敛，不应该重新规划工具。

#### 运维诊断 RCA 的输入限制

RCA 不应该把以下内容当作强证据：

- layer 的自然语言推测。
- runbook 本身。
- archive 路径。
- 未匹配到计划项的工具噪音。
- 失败但没有诊断意义的工具结果，例如 `docker: command not found`。

RCA 可以使用：

- `evidence_facts` 中的正向事实。
- `evidence_conflicts` 中的冲突事实。
- `missing_evidence` 中的缺口。
- `layer_handoff.current_abnormal_summary` 中的当前异常分布。
- `tool_result.structured` 中的状态、事件、错误码、Prometheus 结果。

#### 多异常根因表达

如果 layer 识别了多个异常组，RCA 应避免把所有异常硬归成一个根因。

例如：

```text
g1 ImagePullFailed:
  根因：节点访问 docker.io/registry-1.docker.io 超时或连接被重置。

g2 TerminatingStuck:
  根因：Pod 存在未清理 finalizer，删除流程被阻塞。
```

这两者都可以出现在一个报告里，但应区分“主影响面”和“次要异常”。

### 3.5 conclusion：渲染和一致性修正

conclusion 消费结构化结果，尽量不重新推理事实：

- `layer_handoff`
- `evidence_analysis`
- `rca_analysis`
- `query_result`

报告里的证据完整度会以后端结构化统计为准，避免 conclusion LLM 自己改写成不一致数字。

#### 运维诊断 conclusion 的职责

conclusion 负责组织输出，不应重新发明事实。

它应该优先展示：

- 当前异常概览：来自 `current_abnormal_summary`。
- 兼容归因层：来自 `layer_handoff.layers` 和 issue groups。
- 证据链：来自 `evidence_inventory` 和 `evidence_facts`。
- 根因：来自 `RCAOutput.root_cause` 和 `causal_chain`。
- 未采集/冲突证据：来自 `missing_evidence` 和 `evidence_conflicts`。

它不应该：

- 把 evidence 完整度改成自己估计的数字。
- 把 runbook 内容当成环境事实。
- 把没有验证的 possible_scenarios 写成已确认根因。
- 忽略非主异常组。

## 4. `/query` direct 当前链路

`/query` 不走 evidence 和 RCA：

```text
question
  -> layer(query direct)
  -> conclusion(render QueryResult)
```

### 4.1 为什么 query 不能走完整诊断链

QUERY 是取数，不是排障。典型问题：

- 查询集群 CPU 和内存使用率
- 查看每个节点的某个指标
- 获取当前某类资源列表

如果走完整诊断链，会出现：

- Prometheus 查询失败被误判成 L1/L3 故障。
- evidence/RCA 继续展开无关诊断。
- 简单查询变成多分钟 agent loop。

因此 direct query 只做三件事：

```text
识别 QUERY
调用最少必要工具
生成 QueryResult
```

### 4.2 QueryResult 结构

`QueryResult` 是 conclusion 直接渲染的数据源：

```json
{
  "query_target": "查询集群 CPU 和内存使用率",
  "collection_summary": "实际采集 2 项，未采集 0 项",
  "columns": [
    {"key": "node", "label": "节点"},
    {"key": "cpu", "label": "CPU 使用率"},
    {"key": "memory", "label": "内存使用率"}
  ],
  "rows": [
    {"node": "node1", "cpu": "12.3%", "memory": "45.6%"}
  ],
  "notes": ["数据来自 Prometheus。"],
  "missing": [],
  "sources": [
    {"tool": "execute_prometheus_instant_query", "query": "cpu_query"}
  ]
}
```

### 4.3 QueryResult 的兼容归一化

小模型可能输出旧形态字段，例如：

- `notes` 是字符串而不是数组。
- `missing` 是字符串而不是对象数组。
- `sources` 是单个对象而不是数组。
- `columns` 使用 `name/type`，没有 `key/label`。
- `collection_summary` 是 dict。

这些现在由 `QueryResult` Pydantic schema 统一归一化，避免 QUERY 已查到数据却因为字段形态小错误失败。

### 4.4 Prometheus 语义失败

Prometheus 工具的 HTTP 400/500 不再被当作成功数据。

现在 observation processor 会把类似输出：

```json
{"error": "400 Client Error: Bad Request for url: ..."}
```

标记为：

```json
{
  "status": "prometheus_error",
  "semantic_success": false
}
```

后续处理：

- 不能把它当成 rows 的来源。
- 可以作为 `missing` 的原因展示。
- direct query 不允许因此漂移成 L1/L3 诊断。

### 4.5 QUERY early stop

QUERY direct 增加了早停条件：

- Prometheus 返回可用结果，停止。
- Prometheus 返回明确语义失败，例如 `prometheus_error`，停止。

这样避免模型在 400 错误后继续反复改 PromQL、反复调用工具直到 max_steps。

## 5. 上下文和归档演进

### 5.1 tool observation 三件套

每个工具结果会被归档为：

```text
*.raw.txt
*.structured.json
*.summary.txt
```

含义：

| 文件 | 用途 |
|---|---|
| raw | 完整原始结果，供人工审查 |
| structured | 规则提取出的结构化事实，供后续稳定消费 |
| summary | 注入 LLM 的短摘要 |

### 5.2 full_analysis 不再跨节点传播

layer 的完整分析和工具全文可能非常大。当前原则：

- 原文落盘。
- 下游拿 `archive_ref`。
- 默认不读取 archive。
- 下游消费 `layer_handoff`、`evidence_facts`、`rca_analysis` 等紧凑结构。

### 5.3 context compaction

当历史 `ai_messages` 和 `tool_observations` 膨胀时，运行时会用 `ContextCompactionSummary` 压缩为：

```json
{
  "process_summary": [],
  "evidence_plan": [],
  "completed_items": [],
  "open_items": [],
  "key_facts": [],
  "negative_facts": [],
  "conflicts": [],
  "discarded_noise": [],
  "next_focus": []
}
```

压缩目标：

- 保留关键事实和已完成事项。
- 保留冲突和负向事实。
- 丢弃重复思考、无关探索和工具循环噪音。
- 避免上下文超过小模型有效窗口。

## 6. Runbook 行为演进

当前 runbook 的核心变化：

- `/ask` 主链只注入 Pod 异常相关 runbook catalog。
- `/query` direct 可以使用 `private-k8s-query-promql-reference.md`。
- image pull runbook 中，curl timeout / connection reset / i/o timeout 被视为有效网络不可达证据，而不是“工具失败所以无结论”。
- 多异常组时，理论上每个异常组都应匹配明显相关 runbook；主异常组完整验证，非主异常组最小验证。

仍需审查的点：

- TerminatingStuck 等非主异常组是否稳定触发对应 runbook。
- runbook 调用是否应由 Pydantic plan 明确记录 `runbook_id`，而不是事后从文本匹配。

## 7. 当前审查重点

建议后续重点看这些点：

### 7.1 layer 是否过度调工具

应检查：

- layer 是否到 max_steps。
- 是否已经拿到当前异常摘要后仍继续查无关对象。
- QUERY direct 是否及时 early stop。

相关日志：

```text
[AICall] agent 达到递归/步数上限
[layer] early_stop=True/False
tool #N execute_prometheus_instant_query
```

### 7.2 evidence 计划是否覆盖异常组

应检查：

- `abnormal_groups` 是否包含所有当前异常状态。
- 每个非正常状态是否至少有最小验证。
- 计划是否只围绕单个 Pod。
- `evidence_type` 和 `target_scope` 是否合理。

### 7.3 证据完整度是否可解释

应检查：

- `plan_total`
- `plan_collected`
- `environment_evidence_total`
- `environment_evidence_collected`
- `executed_tool_count`
- `matched_tool_count`
- `unplanned_tool_count`

如果完整度很低，不一定是坏事。它可能表示：

- 工具确实没有执行。
- 工具执行了但不满足计划意图。
- 计划覆盖了 Terminating，但实际只查了 ImagePull。
- 工具结果是语义失败，只能作为负向事实或 missing。

### 7.4 QUERY 是否保持简单

应检查：

- `/query` 是否只走 `layer -> conclusion`。
- 是否生成 `QueryResult`。
- Prometheus 400 是否进入 `missing`，而不是 L1/L3。
- conclusion 是否直接 render，而不是二次诊断。

## 8. 相关测试

本轮核心回归测试集中在：

- [tests/unit/workflow/test_structured_schemas.py](/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_structured_schemas.py)
- [tests/unit/workflow/test_evidence_dynamic_stop.py](/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_evidence_dynamic_stop.py)
- [tests/unit/workflow/test_query_direct_mode.py](/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_query_direct_mode.py)
- [tests/unit/workflow/test_fast_paths.py](/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_fast_paths.py)
- [tests/unit/context/test_archive_budget_observation.py](/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/context/test_archive_budget_observation.py)

推荐审查命令：

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_query_direct_mode.py \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py
```

编译检查：

```bash
.venv/bin/python -m py_compile \
  app/core/workflow/schemas.py \
  app/core/context/observation.py \
  app/core/workflow/nodes/layer_classifier.py \
  app/core/workflow/nodes/evidence_collector.py \
  app/core/workflow/nodes/root_cause_analyzer.py \
  app/core/workflow/nodes/conclusion_formatter.py
```

## 9. 当前仍未完全解决的事项

这些不是本轮已完全闭环的结论，后续需要继续观察：

- layer 在 `/ask` 中仍可能做较多工具调用，需要继续根据真实 run 日志调 early stop。
- evidence 仍是 agent 执行工具，不是规则执行器；虽然有动态停止和计划匹配，但仍可能受小模型工具决策影响。
- `primary_pod` 兼容字段仍在部分 schema 和历史文档中存在，后续可以逐步迁移到 `abnormal_groups` 为唯一主线。
- runbook 覆盖率和 evidence 完整度的前端展示需要同步当前结构化统计口径。
- context compaction 的触发阈值需要继续结合 32k/35k 小窗口模型观察。
