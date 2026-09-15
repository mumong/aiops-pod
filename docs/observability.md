# 可观测性采集与结果解读

[返回 README](../README.md)。后端部署见[可观测性组件](http://10.2.0.86/platform/observability)，接口实现与完整参数以 [MCP 仓库](http://10.2.0.86/wanghuhu/mcpstander)为准。

## 工具职责

| 工具 | 来源 | Agent 提供什么 |
|---|---|---|
| execute_pod_promql | Prometheus | namespace、pod、purpose、PromQL、即时/范围查询及时间参数 |
| query_pod_logs | Elasticsearch / Filebeat | 目标 Pod、purpose、时间窗、容器、关键词、级别等 |
| query_pod_tracing | DeepFlow / ClickHouse；可关联 Tempo | 目标 Pod、purpose、入站/出站、请求路径、响应码、耗时、trace ID 等 |
| query_pod_topology | Kubernetes API | 目标 Pod 和 purpose，查询控制器、Service、节点等关系 |

Pod 查询可携带 pod_uid；MCP 校验对象范围。PromQL 由模型编写，每个向量选择器需符合精确 namespace/pod 的作用域约束。Logs 和 Tracing 不要求模型编写 ES DSL 或 SQL，由工具按照结构化条件构建查询。

支持复杂查询不等于模型每次都会选择合适条件。默认首轮是通用基线，关键问题可能需要第二轮专项查询。节点/集群的通用指标查询使用 /query 路径及相应 Prometheus 工具，不绕过 Pod 工具的范围约束。

## 指标查询示例

以下是工具能力示例，不是固定故障脚本。替换 namespace、Pod、container，指标是否可用取决于 exporter 抓取和标签。

~~~promql
# 最近 5 分钟 CPU 用量，单位为核
rate(container_cpu_usage_seconds_total{namespace="production",pod="api-xxx",container="app"}[5m])

# 内存工作集，单位 bytes；使用范围查询观察趋势
container_memory_working_set_bytes{namespace="production",pod="api-xxx",container="app"}

# 最近 30 分钟重启增量
increase(kube_pod_container_status_restarts_total{namespace="production",pod="api-xxx",container="app"}[30m])

# 上次终止原因是否被记录为 OOMKilled
kube_pod_container_status_last_terminated_reason{namespace="production",pod="api-xxx",container="app",reason="OOMKilled"}
~~~

内存趋势调用示例（MCP 工具参数，不是 /ask 的 JSON body）：

~~~json
{
  "namespace": "production",
  "pod": "api-xxx",
  "purpose": "核对异常前内存是否持续增长",
  "promql": "container_memory_working_set_bytes{namespace=\"production\",pod=\"api-xxx\",container=\"app\"}",
  "query_type": "range",
  "window_minutes": 30,
  "step": "30s"
}
~~~

单点 gauge 不能证明趋势；increase 使用历史窗口，即时执行也可能得到小数。空结果不是 0。CPU rate 0.5 表示约半核，不是节点 CPU 使用率 50%；内存 bytes 除以 1048576 才是 MiB。

## 日志和链路专项补查

例如调查健康检查失败，给 query_pod_logs 传入：

~~~json
{
  "namespace": "production", "pod": "api-xxx",
  "purpose": "查看健康检查相关日志",
  "window_minutes": 30,
  "keywords": ["/health"], "keyword_mode": "phrase", "max_records": 20
}
~~~

给 query_pod_tracing 传入：

~~~json
{
  "namespace": "production", "pod": "api-xxx",
  "purpose": "核对健康检查入站请求的响应",
  "window_minutes": 30, "direction": "inbound",
  "request_resource": "/health", "response_codes": [500],
  "include_tempo": true, "max_records": 20
}
~~~

DeepFlow Flow 是网络观测，Tempo Span 是应用埋点。include_tempo=true 不保证取得 Span，需有效 trace ID 和后端已有数据。相同 Pod、接口或响应码不代表同一请求；跨源请求关联须核对 trace ID，流向还需核对 src/dst。

应用没记录 /health 日志时，查询不能凭空生成；容器尚未启动时，应用日志和链路为空通常合理，应转向 Kubernetes 状态与 Event。

## 结果如何进入报告

数据经过“后端查询 → MCP 响应 → Agent 规范化 → 有限摘要 → 分组 RCA 与报告”。

raw 保存 Agent 收到的响应；structured 保存解析后的观测；summary 按预算选择代表记录并附引用。Logs 可按模式归并并统计业务数值 first/last/min/max；Flow 和 Span 分开，不能把两者数量或时延含义混为一谈。

| 字段 | 含义及边界 |
|---|---|
| entity、window | 对象与时间范围；不能跨 Pod 生命周期随意拼接 |
| source_system、dimension | 来源和维度，不是模型推测的来源 |
| evidence、事实 ID | 本次解析出的观测及回查标识，不是因果正确证明 |
| status、coverage、source_coverage | 区分查询成功、失败、无匹配与部分来源缺失 |
| counts、truncation | 读取、返回和省略情况，具体键随数据源不同 |
| summary_selection | 摘要选中/省略记录及选择策略 |
| raw_ref、structured_ref、summary_ref | 同次调用的归档入口 |

MCP 返回仍受查询时间窗、条数和数据源能力限制；Agent 摘要还受模型输入预算限制。不要沿用旧文档的固定 6 KiB 最终响应上限，也不要把“未额外截断”解释为读取了数据源全部历史。

## 一个真实例子：为什么要保留字段含义

[c10-timeout 第 1 次报告](../testreports/aiops_quality_expanded-c0e3e093e80c_20260910_181943/c10-timeout/run-01-111899003f6d4385/report.md)记录：

- Kubernetes：Liveness probe failed，context deadline exceeded。
- Tracing：GET /health，duration_us 约 3001350–3001920，即约 3 秒。
- Logging：/health 最终返回 200。
- 探针超时阈值：1 秒。

“最终返回 200”和“探针在 1 秒超时”可以同时成立；不能只按状态码认为健康。该报告还将退出码 137 写成确认 OOM，这是需要纠正的模型解释，不是这些观测本身证明了 OOM。

同理，/work 成功不代表 /health 健康；allocated_mib 是测试应用业务字段，不是容器总内存；Flow min/max 不等于 P95/P99。三维数据的价值在于回答具体调查问题，而不是凑齐三行。

## 维护与验收

分别检查三层，不能用其中一层替代另一层：

1. **工具**：目标身份、时间、过滤条件正确；返回值、覆盖和计数与源端一致；错误和空结果明确区分。
2. **上下文**：raw 可回读，structured 和 summary 保持来源关系；预算省略可见，正常值与零值不因“不是错误”就被误删。
3. **诊断**：模型是否选对接口/时段，是否误解单位、流向、终止原因，是否把假设写成确认根因。

基础实现入口见[核心实现](current-aiops-diagnosis-architecture.md)。历史测试与人工审阅只能说明对应批次，不作为当前部署已验收的声明。
