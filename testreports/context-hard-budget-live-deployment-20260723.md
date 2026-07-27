# Qwen 32K 上下文硬预算线上部署测试

测试日期：2026-07-23

## 1. 测试目标

验证结构化上下文硬预算实现已经进入真实 Kubernetes
`aiops-copilot` Pod，并验证以下三类 provider 调用路径：

1. `call_simple()`
2. `call_structured()`
3. LangGraph Agent 每轮 `ModelRequest`

同时尝试使用真实问题“我的集群现在有什么问题？”运行完整诊断。

## 2. 部署信息

部署镜像：

```text
xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.74-context-hard-budget-20260723-a001
```

镜像 digest：

```text
sha256:c98955b456b76ef82531baa7cf41e885cda3d4196570caf20c514cfc38dc1266
```

Deployment：

```text
namespace=aiops
name=aiops-copilot
revision=83
ready=1/1
```

部署前回退文件：

```text
/tmp/aiops-copilot-before-context-hard-budget-20260723.yaml
/tmp/aiops-config-before-context-hard-budget-20260723.yaml
```

本次只更新 Deployment 镜像，没有修改 Secret 和现有 ConfigMap。

## 3. 容器冒烟测试

新镜像内成功导入：

- `AICall`
- `RootCauseAnalyzerNode`
- context budget 模块

32K 配置计算结果：

```text
context_window=32000
hard_input_limit=23040
output_reserved=6000
safety_margin=2000
```

## 4. Provider 路径运行时测试

测试在真实部署 Pod 内执行。Provider 使用捕获 handler，确保能够观测
门禁后的实际输入，同时不依赖当前不可用的 Qwen 网关。

### 4.1 `call_simple()`

```text
original_input_tokens=168084
final_input_tokens=23040
max_input_tokens=23040
strategy=deterministic_head_tail
```

验证结果：

- provider 捕获到的是压缩后内容。
- case/entity identity 保留。
- 尾部关键证据保留。
- 原始 504,039 字符没有进入 provider。

### 4.2 `call_structured()`

```text
original_input_tokens=168960
final_input_tokens=23040
max_input_tokens=23040
strategy=deterministic_head_tail
```

验证结果：

- Pydantic `RCAOutput` schema 已计入预算。
- case/entity identity 保留。
- 尾部关键证据保留。
- native structured provider 捕获到的是压缩后内容。

### 4.3 LangGraph Agent

构造了 12 个 case、12 组 tool call 参数和 ToolMessage 结果：

```text
original_input_tokens=249957
final_input_tokens=10188
max_input_tokens=23040
original_messages=25
final_messages=1
strategy=deterministic_agent_summary
```

压缩后仍保留：

- `query_pod_logs` 工具名称。
- `PAYMENT_GATEWAY_TOKEN is missing` 决定性错误。
- `/archive/case-0.raw` 原始归档引用。
- 第 12 个 case 的 identity。

对应在线预算归档：

```text
/tmp/aiops/reports/context_archives/runtime-agent-hard-guard-probe/
  budget/runtime_agent_probe_agent_guard_001.json
```

## 5. 真实 `/ask` 运行

请求：

```text
我的集群现在有什么问题？
```

运行 ID：

```text
7df0007f5d4b479d
```

真实 layer provider-bound 预算：

```text
actual_context_tokens=4185
max_input_tokens=23040
hard_guard.triggered=false
output_reserved=6000
safety_tokens=2000
provider_request_overhead=64
```

预算归档：

```text
/tmp/aiops/reports/context_archives/7df0007f5d4b479d/
  budget/layer.json
  budget/layer_agent_guard_001.json
```

这证明新 LangGraph provider 门禁已经进入真实 `/ask` 路径。

## 6. 当前外部阻断

模型配置：

```text
LLM_API_BASE=http://10.2.0.54:4000/v1
LLM_MODEL=openai/Qwen3.6-35B-A3B
```

2026-07-23 13:57:05、13:57:25、13:57:45 连续检查结果：

```text
10.2.0.54:4000 connection refused
```

从宿主机和 `aiops-copilot` Pod 内访问均失败。主机可以 ping 通，
Langfuse `10.2.0.54:3001` 健康，但推理网关 4000 端口没有监听。

因此真实 `/ask` 在 layer 的第一次模型调用处结束：

```text
LLM 服务不可用，无法完成问题定位:
Agent 执行异常: Connection error.
```

本次不能据此评价：

- Qwen 的自主工具选择；
- metrics/logging/tracing 实际采集过程；
- Evidence 压缩触发效果；
- RCA 和最终报告质量。

这些步骤必须在 CPA/Qwen 网关恢复后继续。

## 7. 当前结论

线上部署和上下文硬门禁本身验证通过：

- 新镜像成功滚动部署。
- 三类 provider 路径均在调用前压缩。
- 最终 provider-bound input 不超过 23,040 tokens。
- 实体、关键错误和 archive refs 在压力测试中保留。
- 真实 `/ask` 已生成在线 hard-guard 预算归档。

完整 Agent 诊断效果验证仍被外部模型网关不可用阻断。

## 8. 回退

快速回退到部署前镜像：

```bash
kubectl -n aiops set image deployment/aiops-copilot \
  aiops-copilot=xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.74-observability-gate-20260721-a001

kubectl -n aiops rollout status deployment/aiops-copilot --timeout=300s
```

也可以使用部署前完整 YAML：

```bash
kubectl apply -f /tmp/aiops-copilot-before-context-hard-budget-20260723.yaml
```

## 9. 可用模型上的完整真实运行

由于本地 Qwen 网关仍不可用，使用隔离的 GPT probe Deployment 完成了
同一套代码、同一套 MCP、同一 32K 配置下的完整真实诊断。该 probe
不修改生产 Qwen Deployment。

请求：

```text
我的集群现在有什么问题？
```

运行 ID：

```text
7b766f6f1a7a4be2
```

总耗时：

```text
13m 12.3s
```

真实异常实体：

```text
aiops-traced-config/trace-config-api-55647d7bb5-vw456
aiops-traced-oom/trace-oom-api-7c75757475-vgvxs
```

### 9.1 旧压缩机制为什么仍会超过 32K

旧机制是 Evidence Agent 的运行时历史摘要，不是端到端 provider
请求硬约束：

1. 只在 Evidence 工具结果返回后按阈值触发。
2. 只压缩当前 Agent 的消息历史。
3. RCA 会从 `WorkflowState.evidence_analysis` 重新拼装新输入。
4. 旧预算估算只记录日志，不阻止超限请求发送。
5. system prompt、tool schema、structured schema、历史消息和输出预留
   共同占用 32K，而不是只有工具结果占用 32K。

历史 Qwen 运行的 RCA 输入分别达到：

```text
32578 tokens
35575 tokens
34148 tokens
```

因此出现过 Evidence 压缩日志，不代表下游 RCA 请求一定安全。

### 9.2 本次真实运行的强制压缩

Evidence 运行时摘要在估算使用率 71% 时触发：

```text
runtime context compacted | node=evidence usage=71% window=32000
```

更关键的是 LangGraph 每轮 provider 请求前的硬门禁真实触发两次：

```text
request 3:
original_input_tokens=26252
final_input_tokens=16616
max_input_tokens=23040
messages=15 -> 1
strategy=deterministic_agent_summary

request 4:
original_input_tokens=32139
final_input_tokens=16925
max_input_tokens=23040
messages=18 -> 1
strategy=deterministic_agent_summary
```

第二次原始输入已经达到 32,139 tokens；门禁在 provider 调用前完成
压缩，最终没有把该超长请求发送给模型。

Provider 返回的实际输入用量为：

```text
evidence iteration 3: input_tokens=13103
evidence iteration 4: input_tokens=13194
```

RCA 的 provider-bound 输入为：

```text
actual_context_tokens=12358
max_input_tokens=23040
reserved_tokens=8000
estimated_total=20358
hard_guard.triggered=false
```

完整运行没有出现 `ContextWindowExceededError`。

### 9.3 为什么节点汇总仍可能显示超过 100%

Evidence 节点结束时的审计汇总为：

```text
input_tokens=26841
reserved_tokens=10096
budget_tokens=36937
budget_usage=115%
```

这个值表示整个 Evidence 阶段累计的静态上下文、工具观察和预留预算，
用于发现状态膨胀；它不是某一次真实 provider 请求。真正决定是否会
超过模型窗口的是：

```text
budget/evidence_agent_guard_*.json
```

本次两次超限候选请求均在发送前被压缩到 23,040 tokens 以下。

### 9.4 压缩后关键证据保留情况

以下事实均从 Evidence 保留到 RCA 输入、RCA 输出和最终报告：

```text
required config PAYMENT_GATEWAY_TOKEN is missing
CONFIG_MISSING
fatal_configuration_error
exit_code=78
Reason: OOMKilled
Exit Code: 137
```

最终报告使用配置错误日志、BackOff 事件和 Prometheus 重启增量构建了：

```text
PAYMENT_GATEWAY_TOKEN 缺失
  -> 应用启动校验失败并退出
  -> kubelet 重启容器
  -> 连续 BackOff
  -> CrashLoopBackOff
```

这证明硬预算压缩没有丢失主异常 Pod 的决定性证据。

## 10. 可观测性查询审计

本次完整运行成功完成 Kubernetes 和 Prometheus 采集，但 ES 与
DeepFlow/Tempo 查询没有达到语义成功：

```text
Prometheus:
status=query_succeeded
coverage=present

Elasticsearch:
status=query_rejected
error=invalid_fields
fields contains unsupported values:
event, error_code, missing_config, exit_code, memory

DeepFlow:
status=query_rejected
error=TYPE_MISMATCH
response_status 字段为 UInt8，但查询使用字符串 error

Tempo:
未获得可核验的成功 application span 结果
```

最终报告正确披露了这些失败，没有把外层 MCP `success` 当作查询成功，
也没有编造 topology 边或调用链。

## 11. 最终判定

上下文硬预算目标：**PASS**

- 运行时压缩真实触发。
- 两次 provider-bound 超限候选请求被强制降低。
- RCA 输入安全。
- 无 `ContextWindowExceededError`。
- `PAYMENT_GATEWAY_TOKEN` 和 OOMKilled 事实保留到最终报告。

T007 完整可观测性目标：**REWORK**

- Kubernetes、Prometheus 成功。
- ES 查询因不支持字段被拒绝。
- DeepFlow 查询因字段类型不匹配被拒绝。
- Tempo 没有成功的 application span 证据。
- 没有真实 topology 边。

因此不能把本次运行描述为 metrics、logging、DeepFlow、Tempo、
topology 全部通过。下一次验收需要先修正通用日志字段选择和
DeepFlow `response_status` 类型约束，再重新运行同一模糊问题。

## 12. 临时资源清理

审计结束后已删除隔离比较资源：

```text
deployment/aiops-copilot-gpt56-probe deleted
secret/aiops-gpt56-probe-secret deleted
```

生产状态：

```text
deployment/aiops-copilot ready=1/1
```

运行 `7b766f6f1a7a4be2` 的 ContextArchive 和最终报告仍保留在
`aiops-reports-pvc`。
