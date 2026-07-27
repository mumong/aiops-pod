# 可观测性首轮门控设计

## 1. 目标

在 Robusta 现有四节点工作流和三个通用可观测性 MCP 工具基础上，增加一个低侵入
首轮门控：

- 对每个已确认异常 Pod，至少真实尝试一次 Metrics、Logging、Tracing 查询。
- 工具返回 `present`、`empty`、`absent`、`weak` 或 `error` 都视为已尝试，原样保留。
- 三维首轮完成后解除门控，由 Qwen 根据真实返回决定是否继续细化查询或调用其他
  Kubernetes 工具。
- 不按 OOMKilled、ConfigError、ImagePullBackOff 等故障类型写死工具链。

## 2. 门控边界

门控只保证“查询被真实执行”，不保证每个维度都有数据，也不把空结果改写成成功证据。

首轮状态使用以下键追踪：

```text
(namespace, pod, execute_pod_promql)
(namespace, pod, query_pod_logs)
(namespace, pod, query_pod_tracing)
```

例如两个异常 Pod 会形成六个首轮目标。只有六个工具调用都产生非去重
`tool_result` 后，首轮门控才完成。

## 3. 计划生成

Qwen 首先根据 Pod 生命周期、Runbook 和待验证假设，自主生成三维查询参数：

- Metrics：自主选择精确 Pod scope 的 PromQL、查询类型和时间窗。
- Logging：自主选择关键词、容器、级别、trace ID 和时间窗。
- Tracing：自主选择方向、状态码、资源、service、trace ID 和时间窗。

系统校验 `异常 Pod × 三维工具` 是否齐全。缺少时执行一次结构化计划修复，明确列出
缺失的 Pod 和维度。

如果 Qwen 修复后仍遗漏，系统补入通用基线计划：

- Metrics 查询 Pod 生命周期、等待原因、终止原因和重启状态，不包含故障类型判断。
- Logging 查询目标 Pod 最近时间窗，不预设错误关键词。
- Tracing 查询目标 Pod 最近时间窗的双向 DeepFlow/Tempo 数据，不预设协议或状态码。

基线计划只保证真实数据入口存在。Qwen仍可在后续使用更具体的 purpose 和参数继续
查询。

## 4. 执行状态机

```text
生成 Evidence Plan
  -> 补齐异常 Pod × Metrics/Logging/Tracing 首轮计划
  -> 执行真实工具
  -> 检查首轮缺失的 Pod/维度
      -> 有缺失：只提示执行剩余门控项
      -> 全完成：解除门控，允许 Qwen 自主补证
  -> 上下文达到 80%：停止新增查询并记录未完成门控项
  -> RCA / Conclusion
```

首轮完成后提供一次有界自主补证机会。Qwen可以：

- 使用日志中的 trace ID 精确查询 Trace。
- 将 instant PromQL 改成 range PromQL。
- 根据 `empty/error` 修正时间窗或参数。
- 查询 YAML、ConfigMap、Secret、Node 等必要 Kubernetes 事实。
- 判断现有证据已经充分并停止。

## 5. 真实性与稳定性

- 门控依据真实 `tool_result`，不依据模型文字声称。
- 工具错误也保留为真实负向结果，不伪造数据。
- MCP继续负责 Pod scope、安全校验、结果裁剪和 evidence refs。
- 报告 coverage 从结构化工具结果生成，不能由模型把 `not_executed` 写成 `absent`。
- 80% 上下文预算保护继续生效，但未完成的 Pod/维度必须进入
  `uncollected_targets`。

## 6. 验收

自动化测试验证：

1. 一个异常 Pod 的计划必含三个通用查询工具。
2. 两个异常 Pod 会生成六个唯一门控目标。
3. `empty/absent/error` 仍记为已尝试。
4. 只执行 Metrics 时不能提前结束。
5. 三维完成后允许 Qwen继续调用更具体的第二次查询。
6. 上下文达到 80% 时停止并准确报告尚未尝试的 Pod/维度。

真实运行验证使用模糊问题：

```text
我的集群有什么问题？
```

连续运行至少三次，检查每个异常 Pod 都出现 Metrics、Logging、Tracing
`tool_result`，并确认至少一次运行中 Qwen根据首轮结果进行了计划外的深入补证。
