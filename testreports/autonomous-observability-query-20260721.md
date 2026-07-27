# 自主可观测性查询与 Runbook 真实运行审计

## 1. 审计范围

- 审计日期：2026-07-21
- 用户输入：`我的集群有什么问题？`
- Robusta 运行 ID：`52c9c7f41b944bff`
- Robusta 镜像：`xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.74-autonomous-20260721-a004`
- MCP 镜像：`xnet.registry.io:8443/xnet-cloud/mcp-server-manager:7.0.23-autonomous-20260721-a006`
- 模型：`openai/Qwen3.6-35B-A3B`
- 模型上下文：32K

本次审计重点回答：

1. Runbook 是否已经针对不同 Pod 异常提供不同的诊断和可观测性查询知识。
2. Qwen 是否真实调用了 Prometheus、Elasticsearch、DeepFlow/Tempo 工具。
3. MCP 返回的数据是否来自当前集群，是否能够改变或支撑根因判断。
4. 最终报告是否如实引用了实际执行的数据，是否存在过度推断。

## 2. 部署与配置验证

集群中 `aiops-copilot` 和 `mcp-server-manager` Pod 均为 Ready。

Robusta 启动日志确认：

```text
加载自定义 runbook catalog: 11 个 runbooks
aiops-observability-query: 3 个工具
- execute_pod_promql
- query_pod_logs
- query_pod_tracing
```

执行以下配置一致性检查：

```bash
kubectl diff -f deploy/configmap/runbooks.yaml
```

结果退出码为 `0`，说明本地 Runbook 配置与集群当前 ConfigMap 一致。

## 3. Runbook 是否按不同 case 调整

结论：**已经调整，并且不同场景的观测重点不同；Runbook 是查询知识，不是 Python 中的故障类型路由。**

### 3.1 OOMKilled

OOMKilled Runbook 要求：

- Kubernetes 必须确认 `terminated.reason=OOMKilled`、`exitCode=137` 和 memory limit。
- Metrics 推荐查询 working set/RSS、limit、restart 和 terminated reason。
- Logging 推荐查询 memory、heap、GC、allocate、cache 等原文。
- Tracing 只在应用有流量和埋点时使用，用于回答“什么请求驱动了故障前负载”。

建议工具：

```text
execute_pod_promql
query_pod_logs
query_pod_tracing
```

### 3.2 ConfigError

ConfigError Runbook 要求：

- Logging 优先级最高，应查找 required、missing、config、secret、key、token 等决定性原文。
- Metrics 主要用于确认 restart/waiting/ready 状态和排除冲突根因，不能替代日志。
- Tracing 只在应用曾启动、有 Pod IP 或日志已经给出 trace ID 时查询，用于验证业务影响。

### 3.3 ImagePullBackOff

ImagePullBackOff Runbook 要求：

- Kubernetes Events 是主证据，应读取 registry 返回的 manifest、认证、DNS、TLS 或 timeout 原文。
- Metrics 只确认 waiting reason 和异常持续性。
- 主容器未启动时，应用日志和 Trace 为空是正常边界，不应为了凑齐三维执行无意义查询。

这说明当前设计不是“所有 case 固定查询同一组数据”，而是：

```text
Runbook 提供候选问题和查询建议
  -> Qwen 根据真实状态选择查询维度和参数
  -> MCP 校验实体范围、执行查询并返回结构化事实
```

## 4. 通用 MCP 工具边界

三个工具本身不识别 OOMKilled、ConfigError 或 ImagePullBackOff。

### 4.1 execute_pod_promql

- PromQL 由 Qwen 生成。
- 每个 vector selector 必须包含精确的 `namespace="<namespace>"` 和 `pod="<pod>"`。
- MCP 负责作用域校验、时间窗限制、Prometheus 请求、样本截断和事实生成。
- MCP 不根据故障类型替 Qwen 选择指标。

### 4.2 query_pod_logs

- 关键词、级别、容器、trace ID 和时间窗由 Qwen 选择。
- 优先使用 Pod UID 查询，必要时才按 Pod name + time 回退。
- MCP 生成安全的 Elasticsearch DSL，并限制返回记录数和序列化大小。

### 4.3 query_pod_tracing

- 方向、协议、状态码、时延、peer、resource、service 和 trace ID 由 Qwen 选择。
- DeepFlow 查询始终保留目标 Pod IP 约束。
- Tempo span 与 DeepFlow flow 分开返回。
- 只有完整 trace ID 一致时，工具才输出 `basis=exact_trace_id` 的关联结果。

## 5. 真实运行过程

### 5.1 Layer：发现异常并初选 Runbook

全局 Pod 扫描发现 67 个 Pod，其中：

```text
Running: 63
CrashLoopBackOff: 2
```

两个异常 Pod：

```text
aiops-traced-config/trace-config-api-84bc7cb976-vgtl8
aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n
```

Layer 阶段真实工具调用：

```text
#1 kubectl_get_by_kind_in_cluster(kind="Pod")
#2 fetch_runbook(runbook_id="pod-oomkilled.md")
#3 fetch_runbook(runbook_id="pod-crashloop-runtime.md")
```

注意：本轮 Layer 阶段尚未读取容器终态和日志，因此只把两个 Pod 识别为宽泛的 CrashLoopBackOff 候选。

### 5.2 Evidence：真实采证

Evidence 阶段真实执行 12 次工具：

```text
#1  kubectl_describe          ConfigError Pod
#2  kubectl_describe          OOM Pod
#3  kubectl_previous_logs     ConfigError Pod
#4  kubectl_previous_logs     OOM Pod
#5  kubectl_get_yaml          OOM Pod
#6  kubectl_events            ConfigError Pod
#7  kubectl_events            OOM Pod
#8  run_bash_command          OOM Pod resources
#9  run_bash_command          ConfigError Pod resources
#10 execute_pod_promql        OOM Pod
#11 query_pod_logs            ConfigError Pod
#12 execute_pod_promql        ConfigError Pod
```

Qwen 在第 4 轮自主选择了三个可观测性查询：

```text
execute_pod_promql(OOM)
query_pod_logs(ConfigError)
execute_pod_promql(ConfigError)
```

本轮没有调用 `query_pod_tracing`。

### 5.3 RCA 与报告

RCA 根据真实证据把两个相同的 CrashLoopBackOff 状态拆分为：

```text
ConfigError:
required config PAYMENT_GATEWAY_TOKEN is missing
Exit Code: 78

OOMKilled:
Reason: OOMKilled
Exit Code: 137
memory limit: 80Mi
```

最终核心 Runbook 被归一化为：

```text
pod-config-error
pod-oomkilled
```

但需要区分：

- `pod-config-error` 最终被报告为核心 Runbook。
- 本次真实 `fetch_runbook` 日志中没有出现 `fetch_runbook("pod-config-error.md")`。
- 因此“最终分类选中了 ConfigError Runbook”成立，但“本轮实际读取了 ConfigError Runbook 正文”不成立。

## 6. 三维真实数据

### 6.1 Prometheus

OOM Pod 查询：

```promql
container_memory_working_set_bytes{
  namespace="aiops-traced-oom",
  pod="trace-oom-api-598dcf5996-x6v6n"
}
```

真实结果：

```text
application_container:
first=23855104 bytes
max=55435264 bytes
sample_count=2

pod_aggregate:
max=78876672 bytes
sample_count=21

configured memory limit:
80Mi = 83886080 bytes
```

判断：

- Kubernetes 的 `OOMKilled + exitCode 137` 是主证据。
- Pod aggregate 最大值约 75.2MiB，接近 80Mi limit，支持“故障前存在内存压力”。
- application container 的直接序列只有 2 个样本，不能单独证明内存泄漏。

ConfigError Pod 查询了同一个内存指标，用于排除 OOM：

```text
application_container:
value=3784704 bytes
sample_count=1
trend_evaluable=false

configured memory limit:
96Mi
```

这个查询有排除意义，但强度有限。ConfigError Runbook 更推荐 waiting/restart/terminated reason，而不是默认把内存作为主要指标。

### 6.2 Logging

Qwen 实际执行的 ES 查询包含：

```text
keywords:
- config_missing
- PAYMENT_GATEWAY_TOKEN
- fatal_configuration_error

levels:
- error
- fatal
```

工具调用成功，但结果：

```text
status=query_succeeded
coverage=empty
backend_total=0
```

独立冒烟时移除 `levels` 过滤，使用同一 Pod UID 和关键词，真实返回：

```text
coverage=present
backend_total=115
uid_query_hits=100
```

决定性 ES 原文：

```json
{
  "event": "config_missing",
  "level": "error",
  "message": "required config PAYMENT_GATEWAY_TOKEN is missing",
  "error_code": "CONFIG_MISSING",
  "missing_config": "PAYMENT_GATEWAY_TOKEN",
  "http_status": 500,
  "path": "/checkout?order_id=order-346098",
  "trace_id": "57d8bfa75fe27c63f8da544b8ce93d60"
}
```

根因是 Filebeat 文档中的顶层 `log.level/level/severity` 字段为空，而业务 `level=error` 位于 JSON message 字符串内部。Qwen 增加顶层 level 过滤后，把真实日志过滤掉了。

因此：

- ES/Filebeat 数据真实存在。
- MCP 查询功能正常。
- 本轮 `coverage=empty` 是 Qwen 查询参数过严。
- Qwen 没有根据 empty 结果进行第二次放宽过滤的补证。

### 6.3 Tracing

Agent 本轮没有调用 Tracing。为了区分“工具故障”和“模型未调用”，使用日志中的完整 trace ID 做了独立冒烟。

ConfigError trace：

```text
trace_id=57d8bfa75fe27c63f8da544b8ce93d60
DeepFlow:
  src_ip=172.16.104.56
  dst_ip=172.16.104.2
  GET /checkout?order_id=order-346098
  response_code=500
  duration_us=6539

Tempo:
  service=aiops-traced-config-api
  span=GET /checkout
  http.response.status_code=500
  error.type=CONFIG_MISSING
  config.key=PAYMENT_GATEWAY_TOKEN
  config.present=false

correlation:
  basis=exact_trace_id
  flow_count=2
  span_count=1
```

OOM trace：

```text
trace_id=6e73437350f6856b06437fe312da5582
DeepFlow:
  src_ip=172.16.104.8
  dst_ip=172.16.104.13
  GET /allocate?mib=2&step=156101
  response_code=200
  duration_us=11123

Tempo:
  service=aiops-traced-oom-api
  span=GET /allocate
  aiops.allocated_mib.before=60
  aiops.alloc_mib=2
  aiops.allocated_mib.after=62

correlation:
  basis=exact_trace_id
  flow_count=2
  span_count=1
```

结论：

- DeepFlow 和 Tempo 后端均可用。
- Tracing 数据与两个故障都直接相关，不是无关 flow。
- ConfigError Trace 能证明 `/checkout` 请求因缺失配置返回 500。
- OOM Trace 能证明调用方持续请求 `/allocate`，每次推动应用内存从 60MiB 增长到 62MiB。
- 本次 Agent 报告缺少 Tracing，原因是模型没有继续调用，而不是数据不存在。

## 7. 上下文与耗时

运行耗时：

```text
Layer:      23.7s
Evidence:  107.8s
RCA:        47.3s
Conclusion: 65.5s
Total:      4.1m
```

Evidence 最大实际输入：

```text
20066 tokens
62.71% of 32K
```

Conclusion 初始预估：

```text
29915 tokens > 21760 budget
```

系统执行 LLM 压缩：

```text
36621 chars -> 2498 chars
```

压缩后最终报告生成输入：

```text
10367 tokens
32.40% of 32K
```

## 8. 最终报告审计

### 8.1 正确部分

- 正确发现两个当前异常 Pod，没有把历史事件当成当前故障。
- 正确区分 ConfigError 和 OOMKilled。
- 引用了 `PAYMENT_GATEWAY_TOKEN is missing`、exit code 78、OOMKilled、exit code 137 和 memory limit 80Mi。
- OOM 因果链基本成立：

```text
持续分配内存
  -> 接近 80Mi limit
  -> OOMKilled / exitCode 137
  -> CrashLoopBackOff
```

- ConfigError 因果链基本成立：

```text
PAYMENT_GATEWAY_TOKEN 缺失
  -> 应用主动 exit 78
  -> Kubernetes 重启并 BackOff
  -> CrashLoopBackOff
```

### 8.2 不准确或过强部分

1. 报告把 ES Logging 写成 `present`，但本轮真实 ES 查询是 `coverage=empty`。
2. 报告写“两个 Pod 彼此无调用依赖”，但本轮没有执行 Trace/DeepFlow，不能从 K8s owner/node 边证明不存在调用依赖。
3. 报告中的拓扑主要由 Pod owner 和 node 信息推导，不是本轮 DeepFlow 查询结果。
4. ConfigError 的 `3.78MiB` direct series 只有一个样本，适合作为辅助排除，不应表述为“彻底排除”的唯一依据。
5. OOM 的 78.8MB/75.2MiB 峰值来自 `pod_aggregate`，工具将其标为 `related_context`；最强证据仍是 OOMKilled 终态和 exit code 137。
6. 附录仍写“由 collect_aiops_case 确定性注入”，但本轮实际模式是三个通用 query 工具，属于遗留文案。
7. 报告建议的 Deployment 名称错误。真实 Deployment 是：

```text
trace-config-api
trace-oom-api
```

报告中使用了 namespace 名作为 Deployment 名：

```text
aiops-traced-config
aiops-traced-oom
```

相关修复命令不能直接执行。

## 9. 验收结论

| 验证项 | 结果 | 说明 |
|---|---|---|
| 不同 case 使用不同 Runbook 知识 | 通过 | OOM、ConfigError、ImagePull 已有不同的观测维度、查询建议和停止条件 |
| Runbook 引导使用通用观测工具 | 通过 | 配置中明确给出 Metrics、Logging、Tracing 的选择依据和参数建议 |
| Qwen 自主选择 PromQL/日志过滤 | 通过 | 本轮 PromQL、关键词、时间窗均由模型选择，MCP 无故障类型路由 |
| 每个异常 Pod 至少有实时观测查询 | 通过 | 两个 Pod 都执行了 Prometheus 查询 |
| ES/Filebeat 真实数据可查询 | 通过 | 放宽错误的 level 过滤后返回 115 条匹配文档 |
| DeepFlow/Tempo 工具可用 | 通过 | 两个 case 均返回 exact trace ID 关联的 flow + span |
| Agent 本轮完整使用三维数据 | 未通过 | Agent 未调用 `query_pod_tracing`，ES 查询为空后也未二次补证 |
| 最终报告严格反映真实 coverage | 部分通过 | 主要根因正确，但 Logging、Topology 和附录描述存在不一致 |
| Runbook 实际 fetch 与最终核心列表一致 | 部分通过 | ConfigError 被最终选中，但本轮没有真实 fetch 其 Runbook 正文 |

总体结论：

**Runbook 的分场景设计和三个通用 MCP 工具已经可用，真实后端数据质量也足以形成 Metrics、Logging、Tracing 的强关联证据。当前主要短板不在采集能力，而在小模型的查询策略稳定性和最终报告约束：它可能在已有两维证据足够判断根因时停止，遗漏仍有价值的 Trace；也可能使用过严过滤造成假 empty。**

因此本次可以认定：

- “Runbook 针对不同 case 提供不同处理和观测建议”已实现。
- “Qwen 会真实使用可观测性工具”已验证。
- “每次诊断都稳定完成 Metrics、Logging、Tracing 三维关联”尚未验证通过。

## 10. 可复核位置

运行归档：

```text
/tmp/aiops/reports/context_archives/52c9c7f41b944bff
```

关键文件：

```text
node_outputs/layer.output.json
node_outputs/evidence.output.json
node_outputs/rca.output.json
node_outputs/conclusion.output.json
tools/010-evidence-execute_pod_promql.*
tools/011-evidence-query_pod_logs.*
tools/012-evidence-execute_pod_promql.*
tools/002-evidence-kubectl_previous_logs.*
tools/004-evidence-kubectl_previous_logs.*
```

## 11. 模块回归结果

Robusta Runbook、Evidence、上下文交接和 fast path 相关测试：

```text
335 passed, 1 warning
```

MCP 通用 Metrics、Logging、Tracing 工具的 schema、作用域校验、查询构造、结果压缩和错误边界测试：

```text
65 passed, 2 subtests passed
```

MCP 项目自身虚拟环境包含运行依赖但未安装 pytest。本次未修改依赖，使用同版本 Python 3.10 的现有 pytest 入口，并通过 `PYTHONPATH` 复用 MCP 项目自身 site-packages 完成测试。
