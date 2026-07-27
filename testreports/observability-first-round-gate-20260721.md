# Qwen 通用可观测性工具五次重复评测

## 1. 评测目标

验证 `openai/Qwen3.6-35B-A3B` 在不切换模型、不修改代码的前提下，面对模糊问题：

```text
我的集群有什么问题？
```

是否能够：

1. 发现当前所有异常 Pod。
2. 对每个异常 Pod 完成 Metrics、Logging、Tracing 首轮真实查询。
3. 根据通用工具返回，自主选择更具体的查询或补充工具。
4. 在查询错误、空结果或证据不足时继续研究。
5. 将真实证据传递给 RCA，并形成可信的最终报告。

## 2. 固定环境

- 评测日期：2026-07-21
- Robusta 模型：`openai/Qwen3.6-35B-A3B`
- 模型上下文：32,000 tokens
- Robusta 镜像：`11.0.74-observability-gate-20260721-a001`
- 首轮门控：开启
- 当前异常对象：
  - `aiops-traced-config/trace-config-api-84bc7cb976-vgtl8`
  - `aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n`

每个异常 Pod 的首轮最低采集要求为：

```text
execute_pod_promql
query_pod_logs
query_pod_tracing
```

`present/empty/absent/weak/error` 都代表工具被真实执行，但只有返回有效事实时才算有效证据。

## 3. 五次运行结果

| 次数 | run_id | 三维门控 | Evidence 工具 | 计划外补证 | 自主行为 | RCA 预算 | RCA 结果 |
|---|---|---:|---:|---:|---|---:|---|
| 1 | `6b9752c981fc4941` | 6/6 | 10 | 0 | 全部为首轮计划，未继续查询 | 33,588 / 32,000 | 失败 |
| 2 | `3f0774299f2c4179` | 6/6 | 10 | 0 | 自主选择内存时序 PromQL，但无结果驱动补证 | 33,056 / 32,000 | 失败 |
| 3 | `7c877661420a4aca` | 6/6 | 18 | 8 | ES 日志为空后改查 previous logs，并补 YAML/describe | 29,721 / 32,000 | 成功 |
| 4 | `e7b7f3e955e14dff` | 6/6 | 10 | 2 | PromQL 参数错误后补齐时间窗并重试成功 | 34,350 / 32,000 | 失败 |
| 5 | `8a05e3576e62498e` | 6/6 | 12 | 2 | 基于首轮结果追加容器内存 PromQL，但结果为空 | 34,142 / 32,000 | 失败 |

汇总：

- 三维首轮门控完成率：**5/5，100%**
- 出现模型自主扩展查询：**4/5**
- 出现计划外补证：**3/5**
- 出现明确的二次可观测性查询：**2/5**
- 工具报错后自主修正并成功：**1 次，成功 1 次**
- RCA 技术上完成：**1/5，20%**
- RCA 因 32K 上下文溢出失败：**4/5，80%**
- 严格端到端 PASS：**0/5**
- `detail_retrieval` 证据详情读取：**0/5**

## 4. 关键能力证据

### 4.1 Qwen 能自主选择故障相关 PromQL

第 2 次运行没有只使用通用生命周期指标。Qwen 为两个 Pod 自主选择：

```promql
container_memory_working_set_bytes{
  namespace="...",
  pod="..."
}
```

并使用 range query 对齐故障时间窗。

它正确使用 OOM Pod 的内存增长趋势作为正向证据，也使用 ConfigError Pod 的低内存作为排除 OOM 的负向证据。

这证明 Qwen 能根据初始假设选择通用 Metrics 工具的查询内容，但该行为并非每次稳定出现。

### 4.2 Qwen 能跨工具补证

第 3 次运行中，ConfigError Pod 的宽范围 ES 查询一度返回：

```text
coverage=empty
```

Qwen 没有直接结束，而是继续使用：

```text
kubectl_previous_logs
kubectl_get_yaml
kubectl_describe
kubectl_events
```

最终从 previous logs 得到决定性原文：

```text
required config PAYMENT_GATEWAY_TOKEN is missing
fatal_configuration_error
exit_code=78
```

随后它又使用 `config_missing`、`PAYMENT_GATEWAY_TOKEN`、`level=error` 形成更精确的日志查询，并尝试检查 Pod 引用的 ConfigMap。

这一轮共执行 18 个 Evidence 工具，其中 8 个属于计划外补证。这是“模型根据证据缺口继续研究”的有效样本。

### 4.3 Qwen 能读取工具错误并修正参数

第 4 次运行中，首次 range PromQL 缺少 `start/end`，MCP 返回：

```text
status=query_rejected
coverage=error
error.code=invalid_time_range
error.message=range queries require start and end
```

Qwen 随后补充：

```text
start=2026-07-21T08:59:14Z
end=2026-07-21T09:59:14Z
step=30s
```

再次调用同一通用工具并成功获取真实 Prometheus 数据。

这次行为可以确认：

- 查询不是 MCP 按 OOM 类型写死的固定执行链。
- Qwen 能理解结构化错误。
- Qwen 能修改工具参数并重新执行。

### 4.4 Qwen 会主动追加查询，但不一定选对指标

第 5 次运行完成首轮基线后，又为两个 Pod 查询：

```promql
container_memory_usage_bytes{
  namespace="...",
  pod="...",
  container="business-api"
}
```

两次结果均为 `coverage=empty`。Qwen接受了空结果，没有继续尝试当前环境实际更有效的 `container_memory_working_set_bytes`。

这说明它具备追加查询的意愿，但对 Prometheus 指标命名和查询迭代的稳定性仍不足。

## 5. 真实推理质量

### 正确部分

五次运行都能稳定识别两条核心事实：

```text
ConfigError Pod:
Last State Reason=Error
Exit Code=78
required config PAYMENT_GATEWAY_TOKEN is missing

OOM Pod:
Last State Reason=OOMKilled
Exit Code=137
/allocate?mib=2
Prometheus 内存增长
DeepFlow/Tempo 存在对应调用
```

第 3 次 RCA 成功构建了两条因果链：

```text
配置缺失
-> 应用配置校验失败
-> Exit Code 78
-> Kubernetes 重启
-> CrashLoopBackOff

/allocate 持续分配内存
-> working set 增长
-> 超过 cgroup memory limit
-> OOMKilled / Exit Code 137
-> 高频重启
```

### 不稳定或错误部分

1. 第 1、2、4、5 次 RCA 实际已失败，但部分最终报告仍从 Evidence 文本重新组织出高置信结论。最终报告不能替代失败的结构化 RCA。
2. 部分运行把“应用缺少配置”过度收窄为“ConfigMap `traced-config-app` 缺少键”。现有证据能确认配置缺失，但未始终确认配置来源一定是该 ConfigMap，也可能是 Secret 或环境变量注入。
3. 第 2 次把日志中的 trace ID 当作 Tracing 查询已确认的 trace ID，来源引用不准确。
4. 第 3 次结构化 RCA 的 `supporting_fact_ids` 存在跨 Pod 串用：Config 假设引用了 OOM Pod 的门控指标，OOM 假设又引用了 Config Pod 的 describe/previous logs。因果结论基本正确，但机器可核验证据引用不合格。
5. 第 4 次 PromQL 重试已成功，但覆盖统计仍保留首次 `metrics(error)`，后一次成功没有覆盖前一次失败。
6. 第 5 次额外内存 PromQL 返回 `coverage=empty`、`evidence_refs=[]`，最终报告却写成“内存使用接近 Limit”，属于没有数据支撑的指标结论。
7. 个别报告声称 Prometheus 已证明内存“达到 limit”，但查询只包含 working set，没有同时查询 limit；更准确的表述应是“观察到接近 limit 的高位，并由 OOMKilled/137 确认发生了 cgroup OOM”。

五次运行的 `detail_retrieval.requested` 均为 `0`。模型虽然会继续调用通用查询或 Kubernetes 工具，但没有使用 evidence ref 再读取归档中的更详细原始证据。

## 6. 上下文分析

| run_id | Evidence 实际上下文 | Evidence 含预留 | RCA 实际上下文 | RCA 含预留 |
|---|---:|---:|---:|---:|
| `6b9752c981fc4941` | 19,263 | 29,359 | 27,588 | 33,588 |
| `3f0774299f2c4179` | 19,768 | 29,864 | 27,056 | 33,056 |
| `7c877661420a4aca` | 15,236 | 25,332 | 23,721 | 29,721 |
| `e7b7f3e955e14dff` | 18,054 | 28,150 | 28,350 | 34,350 |
| `8a05e3576e62498e` | 20,688 | 30,784 | 28,142 | 34,142 |

第 3 次之所以技术上完成 RCA，不是因为 Qwen 突然更强，而是该轮 RCA 输入控制在 23,721 tokens，加 6,000 输出预留后仍低于 32K。

当前主要失败原因是 Evidence 到 RCA 的交接内容过大，而不是 Qwen完全无法理解真实证据。

但上下文不是唯一问题。即使第 3 次没有溢出，仍出现跨 Pod 证据 ID 串用和配置来源过度推断，因此不能把该轮判为严格成功。

## 7. 最终结论

**Qwen具备使用通用工具自主研究问题的能力，但目前不具备稳定、可重复的端到端保证。**

按照“自主规划、结果驱动补证、引用准确、RCA 成功、最终报告一致”五项同时满足的严格标准，本轮结果为：

```text
严格 PASS: 0/5
严格 FAIL: 5/5
```

可以确认的能力：

- 能根据异常假设选择 PromQL。
- 能同时使用 Kubernetes、Prometheus、ES、DeepFlow/Tempo。
- 能在日志为空时切换到其他证据来源。
- 能读取 MCP 参数错误并修正后重试。
- 能在部分轮次中构建方向正确的因果链。

不能确认的稳定能力：

- 不能保证每次都会做结果驱动的二次查询。
- 不能保证每次都选到当前环境存在的 Prometheus 指标。
- 不能保证最终引用的来源完全准确。
- 不能保证 Evidence 中正确的事实在最终报告中仍被忠实表达。
- 在两个异常 Pod、三维数据同时进入 32K 上下文时，不能稳定完成 RCA。

因此，当前合理定位是：

```text
工程门控保证最低真实数据
+ Qwen负责概率性的自主选查询、补证和解释
+ 结构化压缩保证 RCA 能在 32K 内完成
```

不能把系统定位为“只给通用工具，Qwen 每次都能完全自主研究清楚”。更准确的说法是：

> Qwen 已证明具备自主查询和自我修正能力；在首轮门控和上下文治理的工程约束下，可以形成有价值的真实诊断，但当前端到端稳定性仍受 32K 上下文、跨实体证据引用和最终报告一致性限制。

## 8. 本轮变更边界

本轮仅执行真实重复测试和审计：

- 未修改 Robusta 代码。
- 未修改 MCP 工具。
- 未修改提示词。
- 未切换到其他模型。
- 未改变集群异常测试环境。
