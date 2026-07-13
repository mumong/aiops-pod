# AIOps 细粒度可观测证据与 Trace OOM 设计

## 1. 背景

当前生产链路已经能够通过 `collect_aiops_case(namespace, pod)` 实时采集
Kubernetes、Prometheus、Elasticsearch/Filebeat、DeepFlow、Tempo 和轻量拓扑，
但 Agent 首次看到的内容主要是统计计数：

```text
Metrics: 13 series / 4 metrics
Logs: Elasticsearch returned 50 records
Topology: 7 entities / 6 edges
```

这些统计能够证明数据源已连接，却不足以让 Qwen 35B 稳定构建有证据支撑的因果链。
本次改造的目标是让 Qwen 在有限上下文中看到可直接理解的指标值、日志原文、
流量记录、span 和拓扑边，同时保留按 evidence ref 深挖的能力。

本设计还统一现有 OOM 测试环境。当前 `aiops-temp/aiops-oom-business` 只是后台循环
分配内存，没有请求驱动、`traceparent`、OTLP span 或持续客户端流量，所以
DeepFlow/Tempo 返回空结果是正确行为。之前带 Trace 的
`trace-oom-api + trace-oom-client` 是另一套测试环境，能力没有合并进当前 Pod。

## 2. 已确认决策

1. 升级现有唯一 OOM 场景，不再保留一套“无埋点 OOM”和一套“Trace OOM”。
2. 集群只保留一种异常：业务 Pod OOMKilled/CrashLoopBackOff。请求驱动 Pod 保持正常运行。
3. Qwen 自己决定是否调用 MCP 工具。Robusta 不再程序化强制注入
   `collect_aiops_case`，只通过 Prompt、工具描述和上下文结构引导。
4. `collect_aiops_case` 首次返回受限的细粒度摘要，避免 Qwen 必须再次调用工具才能
   获得可读原始数据。
5. `get_aiops_case_evidence` 继续作为按需深挖工具，但返回内容必须经过结构化裁剪，
   不把大段 raw 内容直接塞入模型上下文。
6. 生产运行仍不依赖 `data` 项目。测试 workload、MCP collector 和 Agent 消费能力
   分别落在 `robusta` 与 `mcpstander`。

## 3. 方案选择

### 方案 A：只改 Prompt

不采用。Prompt 无法引用 MCP 没有返回的原始值，容易继续出现“内存趋势可见”之类
没有指标样本支撑的结论。

### 方案 B：只让 Qwen 主动调用 `get_aiops_case_evidence`

不作为主方案。小模型可能不调用、重复调用或展开过多 evidence，稳定性和耗时不可控。

### 方案 C：细粒度首屏摘要 + 可选 evidence 深挖

采用。`collect_aiops_case` 返回每个维度少量但足够诊断的原始样本；Qwen 若认为证据
不足，再自行调用 `get_aiops_case_evidence`。这同时满足自主工具选择、上下文预算和
真实证据展示要求。

## 4. 总体数据流

```text
Robusta 发现异常 Pod
  -> Qwen 根据 Prompt/工具描述决定是否调用 collect_aiops_case
  -> mcpstander 实时查询 K8s/Prometheus/ES/DeepFlow/Tempo
  -> 生成完整 case package
  -> 返回 bounded dimension_details + evidence refs
  -> ObservationProcessor 保留细粒度字段并控制字符预算
  -> Qwen 可选调用 get_aiops_case_evidence 深挖某个 ref
  -> RCA 将多维信号挂到拓扑实体并构建因果链
  -> 最终报告引用人可读原始数据和 evidence ref
```

## 5. MCP 返回契约

`collect_aiops_case` 和 `get_aiops_case` 新增 `dimension_details`：

```json
{
  "dimension_details": {
    "metrics": {
      "coverage": "present",
      "source_system": "prometheus",
      "highlights": [
        {
          "metric": "container_memory_working_set_bytes",
          "container": "business-api",
          "start": "18.4Mi",
          "max": "63.2Mi",
          "last": "0.28Mi",
          "limit": "64Mi",
          "max_limit_ratio": 0.987,
          "samples": [
            "01:26:20=18.4Mi",
            "01:26:50=47.8Mi",
            "01:27:20=63.2Mi"
          ],
          "evidence_ref": "metric-..."
        }
      ]
    },
    "logs": {
      "coverage": "present",
      "source_system": "elasticsearch",
      "samples": [
        {
          "timestamp": "2026-07-13T01:26:50Z",
          "message": "trace_id=... allocated_mib=48",
          "container": "business-api",
          "evidence_ref": "log-..."
        }
      ]
    },
    "tracing": {
      "coverage": "present",
      "source_system": "deepflow",
      "flows": [
        {
          "timestamp": "2026-07-13T01:26:50Z",
          "src": "172.16.1.10",
          "dst": "172.16.2.20",
          "protocol": "HTTP",
          "request": "GET /allocate?mib=2",
          "response_code": 200,
          "duration_us": 4200,
          "trace_id": "...",
          "span_id": "...",
          "evidence_ref": "deepflow-..."
        }
      ],
      "spans": [
        {
          "trace_id": "...",
          "service": "aiops-oom-business",
          "name": "GET /allocate",
          "attributes": {
            "aiops.allocated_mib.after": 48
          },
          "evidence_ref": "tempo-..."
        }
      ]
    },
    "topology": {
      "coverage": "present",
      "entities": [
        "Pod/aiops-temp/aiops-oom-business-...",
        "Service/aiops-temp/aiops-oom-business",
        "Deployment/aiops-temp/aiops-oom-business",
        "Node/master"
      ],
      "edges": [
        {
          "relationship": "Service --selects--> Pod",
          "directness": "direct",
          "confidence": "high",
          "evidence_refs": ["k8s-..."]
        }
      ]
    }
  }
}
```

约束：

- 每个维度最多返回 3 到 8 条 highlight。
- 总摘要目标控制在 6,000 字符以内。
- `coverage=empty/absent/error` 时只返回查询目标、时间窗和诚实原因。
- 不返回 evaluator-only label、expected remediation 或大段未经裁剪的 raw。
- 所有 highlight 必须携带 evidence ref。

## 6. Prometheus 改造

当前 collector 只调用 `/api/v1/query`，采集时容器可能已退出，瞬时 working set 无法
证明 OOM 前趋势。本次增加 `/api/v1/query_range`：

- `container_memory_working_set_bytes`
- `kube_pod_container_resource_limits{resource="memory",unit="byte"}`
- 兼容旧版本的 `kube_pod_container_resource_limits_memory_bytes`
- `kube_pod_container_status_restarts_total`
- `kube_pod_container_status_last_terminated_reason`

处理规则：

1. 排除 `container=""`、`container="POD"`、pause 容器和无 image 的 cgroup。
2. 优先选择 Kubernetes Pod spec 中的目标容器名。
3. 对多套 Prometheus/kubelet 重复 scrape 按
   `namespace/pod/container/metric` 归并，不把重复 series 当成不同证据。
4. 对 range 数据计算 start/max/last、采样点、limit 和 max/limit ratio。
5. 不把 OOM 后的低瞬时值描述为 OOM 前内存趋势。

## 7. 日志与 Trace 摘要

### 日志

Elasticsearch collector 保留完整 case package，但 Agent 首屏只返回：

- 按时间顺序的代表日志行。
- timestamp、message、container、Pod UID/IP。
- 相邻重复行去重。
- 最多 8 条，优先包含 warning/error、trace_id 和结构化 key=value/JSON 字段。

日志摘要不硬编码 OOM 文案。它只提供真实原文和常见结构化字段，故障语义由 Agent结合
K8s、指标和 runbook 判断。

### DeepFlow

对目标 Pod IP 返回真实 L7 flow：

- 时间、源/目标 IP、协议、方法/资源、状态码、耗时。
- `trace_id/span_id` 非空时返回完整关联字段。
- `syscall_trace_id` 多跳链存在时返回最多 2 条 call chain。
- 只有 node 级上下文时继续标记 `related_context/weak`。

### Tempo

从 DeepFlow 和日志中发现 trace ID，再查询 Tempo。摘要返回：

- trace ID、service.name、span name、时间和关键属性。
- 最多 3 条 span。
- Tempo 无 span 时明确返回 empty，不把 DeepFlow flow 冒充为完整 span。

## 8. 拓扑设计

拓扑仍是轻量 evidence graph，不引入图数据库。细粒度摘要必须返回真实实体和真实边，
而不是只有计数。

主要关系：

```text
Pod --owned_by--> ReplicaSet --owned_by--> Deployment
Service --selects--> Pod
Pod --scheduled_on--> Node
Pod --assigned_to--> IP
Pod --owns_container--> Container
Driver Pod/IP --communicates_with--> Target Pod
Evidence --observes--> Entity
```

拓扑只表达关系和证据归属，不自动证明根因。DeepFlow peer 边的 directness/confidence
必须保留，Agent 不得把弱网络背景当作 Pod 级直接证据。

## 9. Robusta 消费设计

### ObservationProcessor

- 保留 `dimension_details`。
- 对 `get_aiops_case_evidence.record.payload` 做按维度白名单裁剪，而不是全部删除。
- Metrics 保留 highlight 和 sample。
- Logs 保留少量 timestamp/message。
- Tracing 保留 flow/span/call-chain 关键字段。
- Topology 保留少量 entity/edge。
- 每个维度独立限额，总体受 `max_observation_chars` 约束。

### 工具选择

移除 `_inject_aiops_case_plan_item` 的确定性强制注入。Evidence Prompt 改为：

- 已识别明确异常 Pod 时，优先考虑 `collect_aiops_case`。
- 如果普通 K8s 证据已经足够回答简单问题，可以不调用。
- 若要判断资源趋势、集中日志、调用链或拓扑责任实体，应调用该工具。
- `collect_aiops_case` 返回不足时，可按 `recommended_refs_by_dimension` 自行调用
  `get_aiops_case_evidence`。

Qwen 最终保留工具选择权，但工具描述要明确“何时调用、会返回什么、何时无需调用”。

### RCA 与最终报告

当某维度 `coverage=present` 时：

- Metrics 至少引用一个指标名、时间和值。
- Logging 至少引用一条带时间戳的真实日志。
- Tracing 至少引用一条 flow 或 span；没有时必须写 empty。
- Topology 至少引用一条真实 edge，并标注 directness/confidence。
- 因果链每一步必须能回指 evidence ref。

禁止根据统计计数生成“趋势可见”“调用链正常”等结论。

## 10. 标准 Trace OOM 测试环境

正式测试资源放入 Robusta：

```text
deploy/testcases/aiops-traced-oom.yaml
scripts/aiops-traced-oom.sh
docs/aiops-traced-oom-test-environment.md
```

资源组成：

```text
Namespace aiops-temp
Deployment aiops-oom-business       # 唯一异常工作负载
Service aiops-oom-business          # DeepFlow 可观察的稳定入口
Deployment aiops-oom-driver         # 正常请求驱动，不作为异常
```

业务链路：

```text
driver 每 5 秒生成 W3C traceparent
  -> GET Service /allocate?mib=2
  -> API 解析 traceparent
  -> 分配 2MiB 内存
  -> 打印 JSON 日志：trace_id/span_id/allocated_mib
  -> 向 lgtm.xnet.svc:4318/v1/traces 导出 OTLP span
  -> DeepFlow 捕获真实 HTTP L7 flow
  -> working set 在约 2 分钟内逼近 memory limit
  -> OOMKilled exit=137
  -> driver 继续请求，容器重启后再次触发 OOM
```

分配速度故意放慢到 Prometheus scrape 能捕获趋势，避免 10 多秒内 OOM 导致 range query
只有 OOM 后低值。

脚本支持：

```text
scripts/aiops-traced-oom.sh apply
scripts/aiops-traced-oom.sh status
scripts/aiops-traced-oom.sh logs
scripts/aiops-traced-oom.sh verify
scripts/aiops-traced-oom.sh cleanup
```

`apply` 会先删除旧的无埋点 standalone Pod 和旧 `aiops-dfotel-test` 测试 namespace，
再部署统一场景。`cleanup` 只删除本测试环境创建的资源。

## 11. 关于“应用是否必须埋点”

需要区分三种数据：

1. **DeepFlow L4/L7 flow**：应用不需要 OTel 埋点，但必须有真实网络流量，且协议能够被
   DeepFlow 识别。可以得到源/目标、协议、接口、状态码和延迟。
2. **DeepFlow eBPF 自动调用链**：不要求应用埋点，但依赖 DeepFlow agent、内核/eBPF
   能力、协议和多跳调用形态。不是每个单跳请求都能形成完整调用链。
3. **跨服务 trace ID 和 Tempo span**：通常需要应用或探针生成并传播 trace context，
   并将 span 导出到 OTel Collector/Tempo。没有埋点时一般得不到完整 span tree。

因此“没有埋点就完全没有 tracing 数据”并不准确。无埋点应用仍可获得 DeepFlow
网络流量和部分 eBPF 调用链，但要得到稳定的 trace ID、日志/flow/span 三方关联和
Tempo 完整 span，应用或自动探针必须支持 trace context。

## 12. 验收标准

### MCP

- `collect_aiops_case` 返回 `dimension_details`，不是裸计数。
- Metrics 包含 range trend、limit 和去重后的目标容器数据。
- Logs 包含带时间戳的人类可读原文。
- DeepFlow/Tempo 有数据时包含 flow/span；无数据时诚实 empty。
- Topology 包含真实 entities/edges 和 directness/confidence。
- 摘要受限，不泄漏评测字段。

### Robusta

- Qwen 自主决定工具调用，不存在程序强制注入。
- Agent 能消费并保留 `dimension_details`。
- 最终报告引用真实指标值、日志行、flow/span 和拓扑边。
- coverage empty/weak 不被写成强证据。
- 报告因果链可以逐步映射到 evidence ref。

### 真实集群

- 只存在一种测试异常：`aiops-oom-business` OOMKilled/CrashLoopBackOff。
- Prometheus 能看到 OOM 前内存上升并接近 limit。
- ES/Filebeat 能查到带 trace_id 的内存增长日志。
- DeepFlow 能查到目标 Pod 的 HTTP L7 flow 和 trace ID。
- Tempo 能按同一 trace ID 返回 span。
- Robusta 完整运行后，最终报告真实引用上述数据。

