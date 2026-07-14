# 异常 Pod 实时可观测性稳定采集设计

## 背景

当前 Robusta 的 evidence 节点由 Qwen 生成 `EvidencePlanOutput`，再按计划调用真实工具。
提示词已经说明 `collect_aiops_case` 是高信息密度入口，但仍把是否调用完全交给模型。
相同的模糊问题“我的集群有什么问题？”在真实重复测试中会出现两种结果：

- 调用 `collect_aiops_case`，获得 Kubernetes、Metrics、Logging、Tracing 和 Topology；
- 只调用 describe、logs、events、YAML 等 kubectl 工具，没有采集多维可观测性数据。

因此，仅依赖提示词无法满足“默认情况下稳定采集真实数据”的交付要求。

## 目标

1. 上游确认异常 Pod 后，evidence 默认对每个唯一异常 Pod 调用
   `collect_aiops_case`。
2. 不根据 OOMKilled、CrashLoopBackOff、ImagePullBackOff、Terminating 等故障类型
   编写特殊分支。
3. 保留 Qwen 的工具执行、缺失维度判断、补充采证和根因分析能力。
4. 弱化 kubectl-only 采证路径，使其成为 coarse case 失败或维度缺失时的降级路径。
5. 关闭当前“计划中 critical/important 项已满足即停止”的 evidence early-stop。
6. evidence 上下文达到 80% 时停止新增采集，防止小模型上下文溢出。
7. 不改变现有 MCP 连接方式，不让 Robusta 依赖 `data` 项目。

## 非目标

- 不把整个 evidence 节点改成硬编码的 MCP 顺序执行器。
- 不移除现有 Kubernetes、Prometheus 或细粒度 AIOps 工具。
- 不要求所有应用必须存在完整 Trace；采集结果可以诚实返回 weak、empty、absent 或
  error。
- 不在本次改造中调整故障发现、RCA 算法、修复执行器或 Case Package 数据结构。

## 方案选择

### 方案一：只强化提示词

改动最少，但同一模糊问题的四次历史测试中有两次退化为 kubectl-only，不能提供
稳定性。

### 方案二：Robusta 直接绕过 Qwen 调用 MCP

稳定性最高，但会改变现有 Agent 工具调用架构，削弱 Qwen 的规划能力，侵入范围过大。

### 方案三：通用计划约束并由 Qwen 执行

系统只负责保证 evidence plan 包含每个异常 Pod 的 coarse 采集项，Qwen 仍通过现有
MCP 工具机制执行计划、阅读结果和决定补证。该方案兼顾稳定性、低侵入和模型能力，
本次采用此方案。

## 架构设计

### 1. 异常目标提取

继续使用 `layer_handoff` 作为 evidence 的目标来源，从以下结构提取 Pod：

- `active_entities`；
- `issue_groups[].entities`；
- `abnormal_groups[].entities`；
- `abnormal_pods`。

目标主键为 `namespace + pod name`，按首次出现顺序去重。提取逻辑只判断实体类型是否
为 Pod，不检查状态、故障类型、标签、名称前缀或命名空间。

### 2. Evidence Plan 通用约束

Qwen 仍先生成 Pydantic `EvidencePlanOutput`。计划标准化阶段对每个异常 Pod 检查是否
已有对应的 `collect_aiops_case`：

- 已存在时保留并提升为 `critical`；
- 不存在时系统追加通用 `critical` 计划项；
- mandatory coarse 项排在普通 kubectl 和细粒度工具之前；
- mandatory 项不受当前普通计划项数量上限截断；
- Qwen 生成的其他计划继续执行现有去重和数量约束。

系统注入项只包含：

```text
tool=collect_aiops_case
tool_args.namespace=<namespace>
tool_args.pod=<pod>
tool_args.scenario=auto
```

不得注入故障类型、预期根因、修复方式或评测标签。

### 3. 工具执行策略

Qwen 使用现有 Agent 和 MCP 连接执行计划，不增加 Robusta 到 MCP 的旁路调用。

执行优先级：

1. 对尚未采集的异常 Pod 执行 `collect_aiops_case`；
2. coarse 结果成功且维度信息足够时，不再重复调用同一 Pod 的 describe、logs、
   events、YAML 或 Prometheus；
3. coarse 返回 error、absent、empty 或明确缺失关键维度时，Qwen按缺失维度选择
   细粒度工具；
4. kubectl 保留为 Kubernetes 状态确认和失败降级工具，不能替代 mandatory coarse
   项的完成状态。

提示词明确要求真实工具结果优先于 Runbook、Pod 名称、模型经验和直接推论。没有对应
工具结果时，模型不得声称已获得 Metrics、Logging、Tracing 或 Topology。

### 4. 停止策略

关闭当前基于“critical/important 已满足”的 evidence early-stop，避免模型仅完成
kubectl 计划后结束。

保留两类合法停止条件：

1. 所有异常 Pod 的 mandatory coarse 项均已有终态结果，且所需降级补证已经完成；
2. evidence 本轮上下文使用率达到 80%。

上下文使用率复用现有 `ContextBudgetEstimator` 和工具 observation 的
`context_usage_ratio`：

- 70%：继续使用已有运行时上下文压缩；
- 80%：记录 `context_budget_stop`，停止新增工具调用；
- 达到 80% 后保留已归档原始结果和压缩摘要，不丢弃已有证据；
- 未执行的 Pod 写入 `uncollected_targets`，最终报告必须标记为“上下文预算达到
  80%，本轮未验证”。

80% 停止属于资源保护，不得把未采集目标计入证据完整度，也不得推断其根因。

### 5. MCP 工具描述

仅增强 `collect_aiops_case` 的 Tool description，不改变输入输出协议：

- 它是已知异常 Pod 的首选实时诊断入口；
- 一次返回 Kubernetes、Prometheus Metrics、集中日志、DeepFlow/Tempo Tracing 和
  Topology 的紧凑摘要；
- 比连续调用多个 kubectl 工具具有更高证据密度；
- 适用于任意异常 Pod，不绑定具体故障类型；
- coarse coverage 缺失或失败时再使用细粒度工具补充。

描述用于提高 Qwen 工具选择概率，真正的稳定性由 evidence plan 通用约束保证。

## 数据流

```text
模糊用户问题
  -> Layer 全局扫描
  -> layer_handoff.abnormal Pods
  -> Qwen 生成 EvidencePlanOutput
  -> 通用计划约束补齐每个 Pod 的 collect_aiops_case
  -> Qwen 通过现有 MCP 连接执行
  -> ObservationProcessor 归档 raw 并返回紧凑 dimension_details
  -> coverage 完整：进入 RCA
  -> coverage 缺失：Qwen 按缺失维度补证
  -> 上下文达到 80%：停止并记录未采集目标
  -> RCA 使用真实证据构建因果链
  -> 最终报告逐项引用原始值和 evidence ref
```

## 错误处理

- MCP 工具不可用：记录 `tool_unavailable`，允许使用细粒度工具降级。
- 单个 Pod 已删除或 NotFound：记录冲突证据，不使用历史结果构造当前根因。
- coarse 返回部分覆盖：只补缺失维度，不重复完整采集。
- Qwen 尝试在 mandatory 项未完成前结束：只要上下文低于 80% 且仍有未尝试目标，
  evidence 节点就携带已完成摘要继续执行剩余 mandatory 计划；连续两轮没有新增
  mandatory 工具结果时停止，记录 `collection_stalled` 和未采集目标，避免无限循环。
- 达到 80%：不重试、不新增工具；报告已采集和未采集边界。
- Langfuse 不可用：不影响诊断执行，只影响验收审计；本地 run archive 和服务日志
  仍作为备选审计来源。

## 低侵入边界

Robusta 预计只修改：

- evidence 提示词；
- evidence plan 标准化和 mandatory 项完成判定；
- tool result 中上下文比例的透传；
- evidence 停止状态和未采集目标记录；
- 对应单元测试和部署配置。

MCPStander 预计只修改：

- `collect_aiops_case` description；
- 工具描述契约测试。

不修改现有 MCP URL、SSE 配置、Case Package 采集器、RCA 节点接口和最终报告结构。

## 验收与测试

### 模块测试

完成 Robusta evidence 模块后统一测试：

1. 一个异常 Pod：Qwen 未规划 coarse 时，系统补入一个 mandatory 项。
2. 多个异常 Pod：每个唯一目标均有 mandatory 项，不因普通计划上限被截断。
3. 已规划 coarse：不重复注入。
4. coarse 成功：删除同目标冗余细粒度计划。
5. coarse 失败或维度缺失：允许细粒度补证。
6. kubectl 计划完成但 mandatory coarse 未完成：不得触发旧 early-stop。
7. 上下文达到 80%：停止采集并记录剩余目标。
8. 未达到 80%：继续采集下一个异常 Pod。

完成 MCP description 后统一运行 MCP 工具契约测试。

### 真实端到端测试

部署后使用完全相同的模糊问题至少重复运行三次：

```text
我的集群有什么问题？
```

每次通过 Langfuse session ID 和本地 run ID 交叉审计：

- evidence plan 是否包含全部已发现异常 Pod；
- Qwen 是否真实调用 `collect_aiops_case`；
- tool args 是否使用正确 namespace 和 pod；
- MCP 返回是否包含真实 `dimension_details` 和 evidence refs；
- 是否按 coverage 决定补证，而不是无目的重复 kubectl；
- Metrics、Logging、Tracing、Topology 是否来自真实工具结果；
- 上下文比例、压缩事件和停止原因是否符合 70%/80% 规则；
- RCA 因果链和最终报告是否引用真实原始值；
- 未采集目标是否被明确披露，没有被误写为已验证。

验收要求三次运行均调用 coarse AIOps 工具；允许某个维度真实 absent/empty，但不允许
退化为未调用工具后由模型自行推断多维结果。

Langfuse 审计入口：

```text
http://10.2.0.54:3001/project/cmn5ux21p0006qw07q05hy9ix/sessions
```

以 session ID 区分每次运行，不使用并发或历史 session 替代目标运行。
