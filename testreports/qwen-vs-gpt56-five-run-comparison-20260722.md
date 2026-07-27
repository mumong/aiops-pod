# Qwen 与 GPT-5.6 五次真实诊断对照评测

## 1. 评测目的

本轮不修改 Robusta、MCP、Runbook、Prompt 或测试 Pod，只替换模型并重复执行同一个模糊问题：

```text
我的集群有什么问题？
```

目标是判断当前系统在真实集群、多异常 Pod、32K 上下文条件下：

1. 是否真实调用 Kubernetes、Prometheus、ES/Filebeat、DeepFlow/Tempo。
2. 是否能覆盖每个异常 Pod 的 Metrics、Logging、Tracing。
3. 是否会根据首轮结果自主补查。
4. 是否能把工具事实稳定传递到 RCA 和最终报告。
5. Qwen 与 GPT-5.6 的质量、稳定性和耗时差异。

评测日期：2026-07-22。

## 2. 固定环境与限制

- Qwen：`openai/Qwen3.6-35B-A3B`
- GPT：`openai/gpt-5.6-sol`
- 上下文窗口：32,000 tokens
- Robusta 入口：`http://10.2.0.48:30800`
- 两组使用相同 Robusta 工作流、MCP 服务和集群。
- GPT 测试完成后已回滚到 Qwen，健康检查确认：

```json
{"status":"healthy","config_loaded":true,"ai_initialized":true,"mode":"AICall(LangGraph)","model":"openai/Qwen3.6-35B-A3B"}
```

本轮集群有 5 个诊断目标：

| Namespace | Pod | 主要状态 |
|---|---|---|
| `aiops-traced-config` | `trace-config-api-84bc7cb976-vgtl8` | CrashLoopBackOff/Error |
| `aiops-traced-oom` | `trace-oom-api-598dcf5996-x6v6n` | CrashLoopBackOff 或 Running+RecentRestart |
| `monitor` | `vm-prometheus-node-exporter-9sg5f` | Pending |
| `monitor` | `vm-prometheus-node-exporter-g9h4b` | Pending |
| `monitor` | `vm-prometheus-node-exporter-tmtwh` | Pending |

CrashLoop Pod 会在短暂 Running、Error、CrashLoopBackOff 之间切换，因此十次运行不是静态快照，但异常对象、工作负载和数据源一致。

## 3. 判定口径

- `query_succeeded` 只表示后端查询完成。
- `coverage=present` 且存在真实 facts/evidence refs，才算正向观测事实。
- `empty`、`absent`、`weak`、`error`、`query_rejected` 不能当作正向根因证据。
- 外层日志中的 `tool success` 不代表查询语义成功。
- 最终 Markdown 不能代替结构化 RCA 成功。
- Pending Pod 没有 Pod IP、应用日志或 Trace 是合理生命周期边界，但不能据此判断具体调度根因。

## 4. 十次运行汇总

| 模型 | 次数 | run_id | 耗时 | LLM | 工具请求 | 唯一三维调用覆盖 | 结构化 RCA |
|---|---:|---|---:|---:|---:|---:|---|
| Qwen | 1 | `b1b19448b1724fc2` | 4.9m | 15 | 17 | 11/15 | 失败降级 |
| Qwen | 2 | `d67a5d552e154dae` | 8.7m | 26 | 37 | 11/15 | 失败降级 |
| Qwen | 3 | `ac9eac1ae0764a27` | 5.2m | 14 | 26 | 15/15 | 上下文溢出 |
| Qwen | 4 | `739536ffeea04ed4` | 9.2m | 27 | 31 | 9/15 | 失败降级 |
| Qwen | 5 | `306fc70a4eee4aeb` | 9.3m | 27 | 40 | 12/15 | 成功，3 hypotheses |
| GPT-5.6 | 1 | `6096236f525241a0` | 13.1m | 12 | 22 | 15/15 | 成功，5 hypotheses |
| GPT-5.6 | 2 | `eb5f191e92c8421f` | 13.5m | 13 | 26 | 15/15 | 成功，5 hypotheses |
| GPT-5.6 | 3 | `34846b161c4a4dcb` | 13.9m | 13 | 30 | 15/15 | 成功，5 hypotheses |
| GPT-5.6 | 4 | `ac84e0a1dabc4c22` | 13.0m | 14 | 28 | 15/15 | 成功，5 hypotheses |
| GPT-5.6 | 5 | `e88e3cff9b4c48a1` | 11.4m | 13 | 19 | 15/15 | 成功，5 hypotheses |

平均值：

| 指标 | Qwen | GPT-5.6 |
|---|---:|---:|
| 平均耗时 | 7.46m | 12.98m |
| 中位耗时 | 8.7m | 13.1m |
| 平均 LLM 调用 | 21.8 | 13.0 |
| 平均工具请求 | 30.2 | 25.0 |
| 唯一 Pod-维度调用覆盖 | 58/75，77.3% | 75/75，100% |
| 可观测性查询语义成功 | 103/114，90.4% | 86/92，93.5% |
| 有 hypotheses 的结构化 RCA | 1/5 | 5/5 |
| 严格端到端通过 | 0/5 | 0/5 |

GPT-5.6 平均耗时比 Qwen 高约 74%，但工具调用更少，结构化 RCA 明显更稳定。

## 5. 真实数据是否被采集

答案是肯定的。两个应用 Pod 在多次运行中取得了真实且具有根因价值的数据。

### 5.1 ConfigError

真实日志包括：

```text
required config PAYMENT_GATEWAY_TOKEN is missing
error_code=CONFIG_MISSING
exit_code=78
```

真实 Prometheus 数据包括：

```text
kube_pod_container_status_restarts_total=2417
kube_pod_container_status_last_terminated_reason{reason="Error"}=1
```

真实 Tracing 数据包括：

```text
GET /checkout?... -> HTTP 500
Tempo span: config.key=PAYMENT_GATEWAY_TOKEN
config.present=false
error.type=CONFIG_MISSING
```

部分运行中 DeepFlow flow 与 Tempo span 使用相同 trace ID，可把“请求 500”与“配置缺失”关联起来。

### 5.2 OOMKilled

真实 Prometheus 数据包括：

```text
kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}=1
kube_pod_container_status_restarts_total=2055
```

真实日志包括：

```json
{"event":"allocate","path":"/allocate?mib=2","alloc_mib":2,"allocated_mib":62}
```

真实 DeepFlow/Tempo 数据包括：

```text
GET /allocate?mib=2 -> HTTP 200
span attributes:
aiops.alloc_mib=2
aiops.allocated_mib.before=60
aiops.allocated_mib.after=62
```

这些事实能证明应用持续执行内存分配，并且 Kubernetes 最近终止原因是 OOMKilled。但若没有 memory limit 和故障前 working set 曲线，仍不能进一步区分 limit 配置过低、内存泄漏、瞬时峰值或节点压力。

### 5.3 Pending node-exporter

真实 Kubernetes 状态为：

```text
0/1 Pending
node=<none>
pod_ip=<none>
restart=0
```

Prometheus、日志和 Trace 返回 empty/absent，符合“尚未形成运行容器”的生命周期，但不是 `FailedScheduling` 的具体原因。没有 Kubernetes Events 时，不能确认是：

- CPU/内存/Pod 数量不足
- taint/toleration
- nodeSelector/affinity
- hostPort
- PVC

## 6. Qwen 表现

### 6.1 优点

1. 速度明显更快。
2. 能使用通用 PromQL、日志和 Trace 工具。
3. 部分运行会根据结果继续查询。
4. 能修正错误 PromQL、缩小时间窗、放宽日志条件。
5. 第 5 次成功构建 OOM、ConfigError 和 Pending 三组 RCA。

### 6.2 主要问题

1. 只有 1/5 次得到带 hypotheses 的结构化 RCA。
2. 前三次出现 `ContextWindowExceededError`。
3. 多次尝试不存在的 `run_bash_command`，外层却记录为 success。
4. 会把 DeepFlow 或 Pod 日志误当 Kubernetes Events 渠道。
5. 会生成没有数据支持的修复值，例如假设当前内存 limit 为 1Gi，再建议改为 2Gi。
6. 会把没有 Node 的 Pending Pod 与 node2 资源压力错误关联。
7. 已采集的日志/Trace 有时在最终报告中被写成“未返回可用原文”或“未执行”。

Qwen 具备自主查询能力，但自主性表现为概率性能力，不是稳定保证。

## 7. GPT-5.6 表现

### 7.1 优点

1. 5/5 次完成 15/15 Pod-维度调用覆盖。
2. 没有调用不存在的工具。
3. 更能区分“候选原因”和“已确认原因”。
4. 对 Pending Pod 保持证据边界，没有虚构 `FailedScheduling`。
5. 5/5 次均生成可解析、带 hypotheses 的结构化 RCA。
6. 第 3、4 次会根据首轮结果执行有目的的补查。

### 7.2 主要问题

1. 平均接近 13 分钟，当前 CPA 路由不适合作为高频在线默认模型。
2. Evidence 计划仍被系统截断为 10 项。
3. 多次 RCA 实际上下文超过 80%，第 4 次达到 98.8%。
4. 第 1、2 次 Trace 查询使用错误类型过滤，触发 ClickHouse `TYPE_MISMATCH`。
5. 最终报告仍会错标数据来源、覆盖数量和置信度。
6. 第 4 次 RCA 已正确得到 ConfigError 和 OOMKilled，但最终报告反而说证据不足。
7. 第 5 次 5 个关键补查结果未进入 Fact Ledger，导致 RCA 和报告共同漏诊。

GPT-5.6 提升了推理和证据纪律，但无法绕过当前工作流的数据交接缺陷。

## 8. 上下文对比

表中为实际输入占 32K 的比例，不含输出预留。

| 模型 | run_id | Evidence | RCA |
|---|---|---:|---:|
| Qwen | `b1b19448b1724fc2` | 75.8% | 101.8% |
| Qwen | `d67a5d552e154dae` | 75.8% | 111.2% |
| Qwen | `ac9eac1ae0764a27` | 79.9% | 106.7% |
| Qwen | `739536ffeea04ed4` | 67.2% | 89.5% |
| Qwen | `306fc70a4eee4aeb` | 62.7% | 90.0% |
| GPT-5.6 | `6096236f525241a0` | 72.4% | 81.0% |
| GPT-5.6 | `eb5f191e92c8421f` | 80.3% | 81.9% |
| GPT-5.6 | `34846b161c4a4dcb` | 88.3% | 80.4% |
| GPT-5.6 | `ac84e0a1dabc4c22` | 95.4% | 98.8% |
| GPT-5.6 | `e88e3cff9b4c48a1` | 70.0% | 72.4% |

Qwen 的 RCA 5/5 超过 80%。GPT-5.6 只有第 5 次 RCA 低于 80%。当前上下文治理对两种模型都不合格。

## 9. 系统级问题

### 9.1 10 项计划上限

当前异常目标是 5 个 Pod，每个至少查询 3 个维度：

```text
5 × 3 = 15
```

但 Evidence 计划只保留 10 项。实际执行的后 5 项会被标成 unplanned，甚至不能进入 Fact Ledger。

这是 GPT 第 5 次漏掉 ConfigError、OOMKilled 和 Tracing 的直接原因之一，不是模型没有查到数据。

### 9.2 成功统计失真

外层会把以下情况记为工具成功：

- `query_rejected`
- invalid tool
- `pod_not_found`
- `missing_pod_scope`
- ClickHouse `TYPE_MISMATCH`

这会产生“工具成功率 100%”但真实语义失败的报告。

### 9.3 empty 被标为 positive

Evidence inventory 会把已经执行的 empty/absent 门控标成 `outcome=positive`。这混淆了：

```text
工具执行完成
```

和：

```text
获得支持根因的正向事实
```

### 9.4 Fact Ledger 丢失补查结果

模型自主补查取得的决定性事实，如果不在截断后的 10 项计划内，可能无法成为 RCA 可引用事实。结果是工具查到了，RCA 却说不存在。

### 9.5 Conclusion 事实回退

部分运行中：

```text
工具事实正确
-> RCA 正确
-> 最终报告错误
```

最终报告会漏掉日志原文、错标 Trace 来源、错误计算覆盖率，或把 `execute_pod_promql/query_pod_logs/query_pod_tracing` 写成 `collect_aiops_case`。

## 10. 当前状态评价

当前系统已经证明：

- 能发现多个异常 Pod。
- 能真实查询 Prometheus、ES/Filebeat、DeepFlow/Tempo。
- 能获得 OOMKilled 和 ConfigError 的决定性真实证据。
- 两种模型都存在结果驱动补查行为。
- 数据并非模拟摘要，原始查询和结构化 facts 可从 ContextArchive 核验。

但当前还不能证明：

- 每个异常 Pod 每次都能完整三维覆盖。
- 所有查询失败都能被准确统计。
- 所有正向事实都能进入 RCA。
- RCA 事实一定能忠实进入最终报告。
- 32K 上下文下可以稳定处理 5 个异常 Pod。

因此当前定位应为：

```text
可用于 AIOps 原型、Sprint 验证和人工复核诊断；
不适合无人值守、自动修复或把最终报告直接当作唯一事实来源。
```

## 11. 模型选择建议

在不改代码的当前状态下：

- 默认继续使用 Qwen：速度更符合在线诊断，且当前需求允许小模型结论不够精准。
- GPT-5.6 更适合作为离线复核、困难 case 二次诊断或评测基准。
- 不建议把 GPT-5.6 直接切为默认模型：平均 13 分钟，且最终报告仍受工作流缺陷影响。
- 无论使用哪种模型，关键结论应以 ContextArchive 中的 structured facts 和 evidence refs 为核验依据。

## 12. 严格结论

| 模型 | 结论 |
|---|---|
| Qwen | 有真实工具使用和自主补查能力，但覆盖、上下文和事实忠实度不稳定 |
| GPT-5.6 | RCA 和证据边界明显更好，但更慢，且仍受计划截断和事实交接问题影响 |
| 当前系统 | 真实数据采集链路成立，端到端稳定诊断尚未成立 |

严格端到端通过率：

```text
Qwen: 0/5
GPT-5.6: 0/5
```

本轮没有修改生产代码。测试结束后已恢复 Qwen。
