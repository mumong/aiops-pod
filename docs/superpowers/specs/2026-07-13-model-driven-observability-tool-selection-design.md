# 模型驱动的可观测性工具选择设计

## 背景

Robusta 的 evidence 节点已经能够通过 `collect_aiops_case` 一次性获取异常 Pod 的
Kubernetes、Prometheus、Logging、DeepFlow、Tempo 和轻量拓扑数据。真实运行
`2fd3b7b391444441` 证明该工具返回的数据可以形成完整证据链：

- Kubernetes：`Last terminated state: business-api=Error exit=78`
- Prometheus：内存 `max=3.8Mi`、`limit=96.0Mi`
- Logging：`required config PAYMENT_GATEWAY_TOKEN is missing`
- DeepFlow：`GET /checkout`、HTTP 500、耗时和 trace ID
- Tempo：相同 trace ID 下的 `CONFIG_MISSING` Span 属性
- Topology：调用方 Pod、Service、Pod、ReplicaSet 和 Deployment 关系

但宽泛集群诊断经常不选择该工具。当前 Pod 生命周期内的运行归档统计如下：

| 提问类型 | 运行数 | 调用 `collect_aiops_case` | 调用率 |
|---|---:|---:|---:|
| 明确要求多维可观测性 | 14 | 12 | 85.7% |
| “我的集群现在有什么问题？” | 20 | 7 | 35.0% |
| 其他明确 Pod 诊断 | 4 | 3 | 75.0% |

## 根因机制

问题不是 MCP 服务不可用，也不是 Prometheus 或 DeepFlow 查询失败，而是工具选择在
evidence plan 阶段已经被锁定。

### 1. 多维提示只在狭窄条件下生效

动态提示目前要求用户问题同时包含 metrics、logging、tracing、topology 的关键词，
并且上游只识别出一个 Pod。宽泛集群诊断通常不包含这些关键词，并且经常发现多个
异常 Pod，因此不会获得 `collect_aiops_case` 的额外语义提示。

### 2. 基础提示把 coarse 工具描述为可选项

基础 evidence prompt 明确允许模型在 kubectl 事实足够时跳过
`collect_aiops_case`。与此同时，prompt 和 runbook 对 describe、previous logs、
events 的诊断步骤描述得更具体。Qwen 在生成结构化计划时更容易选择这些熟悉且目标
明确的工具。

### 3. Pydantic 计划生成与执行分离

evidence 节点先让模型只生成 `EvidencePlanOutput`，此时不执行工具。生成后，系统只
执行这个既有计划。若计划中没有 `collect_aiops_case`，执行阶段不会重新评估是否需要
多维可观测性数据。

### 4. 计划归一化不会补充 coarse 工具

计划归一化只负责参数规范化、去重和截断，并明确不自动补全 evidence plan。因此，
第一次计划选择 kubectl 后，不存在系统层面的第二次机会。

### 5. Early-stop 放大第一次选择

当计划中的 critical 和 important kubectl 项都执行成功后，evidence 节点立即停止。
即使此时仍没有 Prometheus、DeepFlow 或 topology，系统也会认为“当前计划已经完整”，
因为完整度是相对于模型生成的计划计算，而不是相对于可观测性维度计算。

### 6. 多 Pod 覆盖目标使模型偏向 kubectl

宽泛集群问题可能同时发现多个异常 Pod。现有 prompt 强调覆盖每个异常组，而
`collect_aiops_case` 是单 Pod 工具。模型容易选择 describe/logs/events 逐个覆盖，
而不是自主选择代表 Pod 构建高密度 case，再对其他 Pod 做轻量验证。

## 设计原则

本次采用模型驱动方案，不增加 OOM、CrashLoopBackOff、ImagePullBackOff 等状态特判，
不由工作流代码强制插入工具。

只强化三个通用原则：

1. 诊断结论优先建立在当前环境的真实工具证据上，而不是 runbook、Pod 名称或模型推断。
2. 当异常 Pod 已知时，`collect_aiops_case` 是高信息密度的候选入口，模型应主动比较
   它与多个细粒度工具的证据价值和成本。
3. coarse 结果完整时停止重复采集；存在缺失、冲突或错误时，再使用细粒度工具补证。

## 提示词调整

### Evidence 系统提示

将当前“只有用户明确要求四个维度时优先”的表述改为通用证据优先级：

- 用户不需要显式说出 metrics、logging、tracing、topology。
- 只要诊断目标包含已确认的异常 Pod，模型就应考虑实时多维 case 是否能显著提高
  根因定位质量。
- 模型保留跳过 coarse 工具的权利，但应基于问题范围和证据充分性判断，而不是因为
  kubectl 工具更熟悉。
- Runbook 只提供检查思路，不能替代真实环境证据。

### 动态 guidance

动态 guidance 不再检查四类关键词，也不再要求目标只能有一个 Pod。它只做两件事：

- 将上游已经确认的异常 Pod 作为可选采集目标提供给模型。
- 提醒模型自主选择最有诊断价值的 Pod 使用 coarse 工具，并对其他目标保持必要的
  最小覆盖。

该 guidance 不生成 evidence plan、不插入工具、不规定调用数量，也不包含故障类型
分支。

### 报告约束

保持现有事实边界：

- 只有实际调用 coarse 工具后，才能报告 Prometheus、DeepFlow、Tempo 和结构化拓扑。
- 未采集时不得用 Kubernetes 状态冒充 Metrics。
- 未生成结构化 topology 时，不得把模型自行推导的关系写成 case topology。

## 不做的事情

- 不按异常状态硬编码工具选择。
- 不根据 namespace、Pod 名或测试标签触发工具。
- 不在 `_normalize_evidence_plan` 中自动追加 `collect_aiops_case`。
- 不修改 MCP 数据采集逻辑。
- 不要求每次诊断都调用所有可观测性工具。
- 不取消模型对成本、范围和证据充分性的判断。

## 验证

### 单元验证

验证以下通用行为：

1. 宽泛集群问题且上游存在异常 Pod 时，会得到简短的实时证据优先 guidance。
2. 多 Pod 输入不会因为目标数大于一而完全失去 guidance。
3. guidance 不包含强制调用、固定调用次数或具体异常类型。
4. 显式 Pod 问题继续保留模型自主选择权。

### 真实模型验证

使用相同的 Qwen 模型重复运行两组问题：

```text
我的集群现在有什么问题？
```

```text
请诊断 <namespace>/<pod> 当前为什么异常。
```

检查：

- evidence plan 是否能自主选择 `collect_aiops_case`；
- 工具返回是否包含真实 Prometheus、Logging、DeepFlow/Tempo 和 topology；
- 最终报告是否引用具体数值、日志原文、flow、trace ID 和拓扑边；
- 若模型跳过 coarse 工具，报告是否诚实标记未采集，而不是自行补造多维数据。

验证重点是提高模型在普通自然语言诊断中的工具理解和选择稳定性，不追求通过代码保证
100% 调用率。
