# AIOps 真实可观测性数据与 MCP 使用说明

**更新日期**：2026-07-27

**适用项目**：

- `data`：真实故障样本采集、Case Package 原型、离线校验和评测。
- `mcpstander`：生产环境可观测性采集和 MCP 服务。
- `robusta`：异常 Pod 发现、证据编排、RCA 和最终报告。

## 1. 当前结论

当前系统已经具备两条可观测性消费路径：

1. **Robusta 当前默认路径：自主组合查询**
   - Robusta 启用 `aiops-observability-query`，地址为
     `http://mcp-server-manager.mcp.svc.cluster.local:8100/sse`。
   - Evidence 节点对每个异常 Pod 首轮真实执行 Metrics、Logging、Tracing
     三个通用查询。
   - Topology 是独立通用工具，由模型在需要确认 owner、Service、Node 或调用
     关系时按需执行；未执行时报告不得推测拓扑边。
   - Qwen 可以根据首轮结果继续修改 PromQL、日志关键词、Trace 条件和时间窗。
   - 每次工具结果独立形成 `raw.txt`、`structured.json`、`summary.txt` 和
     Fact Ledger，不要求先生成完整磁盘 Case Package。

2. **Case Package 路径：粗粒度采集和按 case ID 读取**
   - mcpstander 的 `aiops-case` 服务仍在 8089 运行。
   - `collect_aiops_case` 一次采集 Kubernetes、Prometheus、日志、
     DeepFlow/Tempo 和轻量拓扑，并将结果保存为 Case Package。
   - `get_aiops_case` 和 `get_aiops_case_evidence` 可根据 `case_id` 和真实
     evidence ref 按需读取。
   - Robusta 当前配置中 `aiops-case-coarse.enabled=false`，该路径主要用于
     Sprint 验收、兼容和离线复盘；需要使用时可单独开启。

两条路径共用相同的证据语义：

```text
准确实体身份
  + 有界时间窗
  + 数据源 coverage
  + 真实 facts/samples
  + evidence refs
  + topology relationships
  -> Robusta Evidence
  -> Fact Ledger
  -> RCA
  -> 最终报告
```

设计底线是：**数据源没有返回结果时必须标记为
`empty`、`absent`、`weak` 或 `error`，不能由模型补造数据。**

## 2. 当前环境背景

| 组件 | 当前运行位置 | 作用 |
|---|---|---|
| Robusta Agent | namespace `aiops` | 发现异常 Pod、调用 MCP、生成 RCA 和报告 |
| MCP Server Manager | namespace `mcp` | 暴露 K8s 和 AIOps MCP 工具 |
| Prometheus | namespace `monitor` | Pod 指标和 kube-state-metrics |
| Elasticsearch/Filebeat | namespace `monitor` | 目标 Pod 和调用方日志 |
| DeepFlow/ClickHouse | namespace `monitor` | Pod L4/L7 网络流和 Trace 关联字段 |
| LGTM/Tempo | namespace `monitor` | 应用级 OTLP span |
| OOM 测试环境 | namespace `aiops-traced-oom` | 产生真实请求、内存增长、日志、flow 和 span |

mcpstander 当前配置的主要数据源包括：

```text
PROMETHEUS_URL=http://observability-prometheus.monitor.svc:9090
AIOPS_ES_EXEC_NAMESPACE=monitor
AIOPS_CLICKHOUSE_EXEC_NAMESPACE=monitor
AIOPS_TEMPO_EXEC_NAMESPACE=monitor
DEEPFLOW_CLICKHOUSE_DATABASE=flow_log
```

生产运行时不依赖 `data` 目录。`data` 中的脚本用于研发、样本生成和验收，
生产采集逻辑已经内建到 mcpstander。

## 3. 当前默认 Agent 路径

### 3.1 工具

Robusta 当前启用的通用可观测性 MCP 工具有：

| 工具 | 输入重点 | 真实数据源 |
|---|---|---|
| `execute_pod_promql` | namespace、pod、purpose、PromQL、查询类型 | Prometheus |
| `query_pod_logs` | namespace、pod、purpose、关键词、级别、trace ID、时间窗 | Elasticsearch/Filebeat |
| `query_pod_tracing` | namespace、pod、purpose、方向、协议、状态码、路径、trace ID | DeepFlow/ClickHouse + Tempo |
| `query_pod_topology` | namespace、pod、purpose | Kubernetes API |

这些工具不根据 `OOMKilled`、`ConfigError` 等故障名称在服务端做场景路由。
模型选择查询条件，工具负责：

- 强制 namespace 和 Pod 精确作用域。
- 校验 Pod UID，避免同名 Pod 生命周期串数据。
- 限制查询时间窗和返回大小。
- 生成可核验的查询描述、facts、samples 和 evidence refs。
- 明确返回 `present/empty/absent/weak/error`。

### 3.2 首轮门控

Evidence 节点会对每个已确认异常 Pod 补齐三个首轮查询：

```text
execute_pod_promql
query_pod_logs
query_pod_tracing
```

`query_pod_topology` 不属于当前强制首轮门控。模型需要确认 owner 链、
Service selector、Node 调度或真实调用关系时可以调用它。若本轮没有执行该工具，
最终报告只能写“本轮未查询拓扑”，不能根据 Pod 名称、标签或
`pod-template-hash` 推测 Deployment、Service 或调用边。

首轮 PromQL 是通用 Pod 生命周期基线，包含：

```promql
kube_pod_status_phase{namespace="<ns>",pod="<pod>"}
or kube_pod_container_status_waiting_reason{namespace="<ns>",pod="<pod>"}
or kube_pod_container_status_last_terminated_reason{namespace="<ns>",pod="<pod>"}
or kube_pod_container_status_restarts_total{namespace="<ns>",pod="<pod>"}
```

它用于先确认 phase、waiting reason、终止原因和重启次数，不是 OOM 专用查询。
对于 OOM，模型仍应根据返回继续查询：

```promql
container_memory_working_set_bytes{namespace="<ns>",pod="<pod>",container="<container>"}
kube_pod_container_resource_limits{namespace="<ns>",pod="<pod>",container="<container>",resource="memory"}
```

### 3.3 工具结果合同

自主查询工具的结构化结果包含：

```json
{
  "ok": true,
  "status": "query_executed",
  "source_system": "prometheus",
  "dimension": "metrics",
  "entity": {
    "namespace": "aiops-traced-oom",
    "pod": "trace-oom-api-...",
    "pod_uid": "..."
  },
  "purpose": "验证容器内存是否持续逼近 limit",
  "coverage": "present",
  "directness": "direct",
  "query": {},
  "facts": [],
  "samples": [],
  "evidence_refs": [],
  "truncated": false
}
```

单次返回限制在约 6 KiB。限制的是注入小模型的结构化投影，不是删除原始工具
输出；完整原文仍进入 Robusta 归档。

## 4. Case Package 路径

### 4.1 MCP 工具

8089 的 coarse MCP 暴露：

```text
collect_aiops_case
get_aiops_case
get_aiops_case_evidence
search_aiops_cases
```

职责分别是：

- `collect_aiops_case`：根据 namespace 和 Pod 实时采集并落盘。
- `get_aiops_case`：根据 case ID 返回有界摘要。
- `get_aiops_case_evidence`：按真实 evidence ID 或允许的相对文件路径展开证据。
- `search_aiops_cases`：按 namespace、Pod 或异常类型检索已有 case。

### 4.2 生产 Case Package 结构

真实样本：

```text
/root/huhu/agent/combine-aiops-mcp/aiops-cases/
└── sprint-audit-20260727-oom/
    ├── case.yaml
    ├── entities.jsonl
    ├── topology.jsonl
    ├── signals.jsonl
    ├── timeline.jsonl
    └── evidence/
        ├── k8s_pod.yaml
        ├── k8s_describe.txt
        ├── k8s_events.jsonl
        ├── metrics.jsonl
        ├── logs.jsonl
        ├── deepflow_l4.jsonl
        ├── deepflow_l7.jsonl
        └── tempo_traces.jsonl
```

文件职责：

| 文件 | 内容 | 是否核心 |
|---|---|---|
| `case.yaml` | case ID、异常 Pod、UID、IP、Node、时间窗、coverage、推荐 refs | 是 |
| `evidence/*` | 各数据源的真实原始或结构化证据 | 是 |
| `entities.jsonl` | 本 case 涉及的 Pod、Container、Node、Service、owner、Evidence 实体 | 是 |
| `topology.jsonl` | `owned_by`、`selects`、`calls`、`observes` 等关系 | 是 |
| `signals.jsonl` | 每个维度的角色、强度和引用入口 | 辅助索引 |
| `timeline.jsonl` | 跨数据源时间线 | 辅助索引 |

**根因判断的单一真实来源是 `evidence/*`。**
`signals.jsonl` 中“返回 50 条日志”一类内容只表示库存和查询命中，不足以支撑
根因。

### 4.3 `dimension_details`

`collect_aiops_case` 不把整个 package 返回给模型，而是从 `evidence/*` 中投影：

- 最多 5 个指标 highlight。
- 最多 8 条日志样本。
- 最多 5 条 DeepFlow flow。
- 最多 3 个 Tempo span。
- 最多 3 条调用链。
- 有界的拓扑实体和边。

整体约束在 6000 字符左右。若同一个 `trace_id` 同时存在于日志、DeepFlow 和
Tempo，投影会优先对齐同一组样本。

## 5. 真实 OOM Case 的核心证据

样本：

```text
case_id=sprint-audit-20260727-oom
namespace=aiops-traced-oom
pod=trace-oom-api-7c75757475-vgvxs
uid=02b86eed-e9db-449c-9c6a-9fce6f0ca566
pod_ip=172.16.104.25
node=node2
```

### 5.1 Kubernetes

```text
current state=CrashLoopBackOff
last reason=OOMKilled
last exit code=137
restart_count=925
Warning BackOff x21618 over 3d23h
```

含义：

- `OOMKilled + exit 137` 是容器被内存限制终止的直接状态证据。
- `CrashLoopBackOff` 和高重启次数是 OOM 后不断重启的结果。

### 5.2 Prometheus

```text
metric=container_memory_working_set_bytes
container=business-api
start=3.7Mi
max=79.0Mi
last=79.0Mi
limit=80.0Mi
max_limit_ratio=0.9872

06:52:46=3.7Mi
06:53:01=3.7Mi
06:53:16=28.8Mi
06:53:46=60.9Mi
06:54:01=79.0Mi
```

含义：容器工作集从约 3.7 MiB 上升到 79.0 MiB，达到 80 MiB 限制的
98.72%。这不是“有一条内存指标”，而是明确的内存增长轨迹。

### 5.3 Logging

代表性真实日志：

```json
{
  "event": "allocate",
  "trace_id": "7f54c092ad81bdc124e7d16034d07ca9",
  "path": "/allocate?mib=2&step=271038",
  "alloc_mib": 2,
  "allocated_mib": 62,
  "pod": "trace-oom-api-7c75757475-vgvxs"
}
```

含义：

- `alloc_mib=2`：本次请求让进程新增长期保留约 2 MiB 内存。
- `allocated_mib=62`：处理完成后，业务进程累计保留约 62 MiB。
- 日志解释了 Prometheus 内存增长的应用行为，但 OOM 终态仍以 Kubernetes 为准。

### 5.4 DeepFlow

同一 `trace_id` 的真实 L7 flow：

```text
2026-07-27 15:12:29
172.16.104.8 -> 172.16.104.25
HTTP GET /allocate?mib=2&step=271038
response_code=200
duration_us=11621
trace_id=7f54c092ad81bdc124e7d16034d07ca9
```

含义：调用方请求真实到达目标 Pod，并成功执行。DeepFlow 证明的是网络请求和
调用方向，不单独证明 OOM。

### 5.5 Tempo

同一 `trace_id` 的代表性应用 span：

```text
service=aiops-traced-oom-api
span=GET /allocate
trace_id=7f54c092ad81bdc124e7d16034d07ca9
aiops.allocated_mib.before=60
aiops.alloc_mib=2
aiops.allocated_mib.after=62
url.path=/allocate?mib=2&step=271038
```

含义：目标应用确实执行了 `/allocate`，业务累计分配量从 60 MiB 增长到
62 MiB。Tempo 给出应用内部语义，DeepFlow 给出网络事实，两者作用不同。

### 5.6 跨源因果链

```text
DeepFlow：driver 请求到达目标 Pod
  -> Tempo：应用执行 /allocate，60MiB -> 62MiB
  -> Logging：同一 trace_id 输出 allocated_mib=62
  -> Prometheus：工作集 3.7MiB -> 79.0MiB，limit=80MiB
  -> Kubernetes：OOMKilled/137
  -> caller logs：目标重启窗口出现 Connection refused
```

这条链可以支持：

> 业务请求持续触发内存保留，容器工作集逼近 80 MiB limit，随后被 cgroup
> OOM Kill，Deployment 管理的 Pod 进入 CrashLoopBackOff。

## 6. 人可读证据标准

### 6.1 不能只展示计数

以下内容只属于库存信息，不属于充分诊断证据：

```text
返回 50 条日志
返回 50 条 DeepFlow flow
返回 12 条 trace
Prometheus series=35
```

最终报告或证据摘要还必须包含：

| 维度 | 至少展示 |
|---|---|
| Metrics | metric 名称、关键时间点、max、limit、比例和单位 |
| Logging | 至少一条原始 `message`，保留决定性字段 |
| DeepFlow | src/dst、协议、请求、状态码、时延、trace ID |
| Tempo | trace ID、service、span name、关键 attributes |
| Kubernetes | reason、exit code、状态、重启次数或决定性 Event |
| Topology | source、relationship、target、directness、confidence |

### 6.2 `present` 与无返回

- coverage 为 `present` 时，对应的 decisive samples 不能为空。
- coverage 为 `empty/absent/error` 时，可以没有样本，但必须保留真实原因。
- “应用没有插桩”可以导致 Tempo 为空，但不能据此说 DeepFlow 也为空。
- “容器从未启动”通常会导致应用日志和 L7 flow 为空，这是符合事实的结果。

### 6.3 证据充分度

需要区分两个概念：

1. **维度覆盖度**：是否真实查询过数据源，以及返回什么 coverage。
2. **根因充分度**：返回内容是否能排除主要候选并支持当前根因。

四个维度都执行过，不代表根因一定充分。例如只有“50 条日志”和“12 条 trace”
计数时，覆盖度可以是高，但根因充分度仍然低。

## 7. Robusta 如何消费证据

### 7.1 工具归档

每次工具调用都会保存：

```text
/tmp/aiops/reports/context_archives/<run_id>/tools/
├── NNN-<node>-<tool>.raw.txt
├── NNN-<node>-<tool>.structured.json
└── NNN-<node>-<tool>.summary.txt
```

| 文件 | 用途 |
|---|---|
| `raw.txt` | 完整工具原始输出，人工审计的首选来源 |
| `structured.json` | 白名单化、机器可读的结构化事实 |
| `summary.txt` | 注入小模型的短文本摘要 |

### 7.2 Evidence 投影

Evidence 节点继续生成：

- `agent_facts`：最多约 10000 字符，适合小模型直接引用的事实文本。
- `agent_context`：最多约 12000 字符的结构化上下文或 Fact Ledger。
- `fact_ledger`：RCA 的权威事实接口，包含实体范围、fact ID、来源、
  directness、coverage 和 evidence refs。

RCA 和 Conclusion 不应只读取一句自然语言摘要，而是优先消费 Fact Ledger。

### 7.3 Case Package 与 Agent Evidence 的关系

二者**相似但不相同**：

| 项目 | Case Package | 当前默认自主查询 |
|---|---|---|
| 物理形态 | 一个 case 目录 | 多次独立工具事件和运行归档 |
| 完整原始数据 | `evidence/*` | `tools/*.raw.txt` |
| 结构化数据 | JSONL/YAML | `tools/*.structured.json` |
| 模型输入 | `dimension_details`/refs | summary + agent facts/context |
| 实体边界 | `primary_entity`/entities | 每个查询的 `entity` |
| 时间窗 | `case.yaml` | 每个查询的 `query` |
| coverage | case 维度 coverage | 每个工具自己的 coverage |
| 拓扑 | `topology.jsonl` | `query_pod_topology` facts/edges |
| RCA 接口 | 可转换为 Fact Ledger | 直接转换为 Fact Ledger |

因此，当前 Agent 并不是直接读取整个本地 Case Package；它使用与 Case Package
同源的证据模型。启用 coarse 路径时，Case Package 会直接成为工具结果的底层
存储。

两条路径的对应关系可以概括为：

```text
Case Package evidence/*.jsonl
  <-> 自主查询 tools/*.structured.json
  -> 统一实体身份、coverage、facts/samples、evidence refs
  -> Fact Ledger
  -> RCA
```

它们在“证据字段和消费接口”上相似，在“落盘粒度”上不同。Case Package 是
一个完整 case 目录；默认 Agent 路径是一次诊断中的多个独立工具结果，不会为了
在线诊断强制生成完整 case 目录。

## 8. 常用检查命令

检查当前 MCP 开关：

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
sed -n '65,145p' deploy/configmap/config.yaml
```

检查 MCP 服务：

```bash
kubectl get pod,svc -n mcp
kubectl logs -n mcp deployment/mcp-server-manager --tail=200 |
  grep -E 'aiops-case|aiops-observability-query|8089|8100'
```

检查一次 Agent 运行归档：

```bash
RUN_ID=<run_id>
kubectl -n aiops exec deploy/aiops-copilot -- \
  find "/tmp/aiops/reports/context_archives/${RUN_ID}" -maxdepth 3 -type f | sort
```

检查可观测工具原始结果：

```bash
RUN_ID=<run_id>
kubectl -n aiops exec deploy/aiops-copilot -- sh -c \
  "grep -RIlE 'execute_pod_promql|query_pod_logs|query_pod_tracing|query_pod_topology|collect_aiops_case' \
   /tmp/aiops/reports/context_archives/${RUN_ID}/tools"
```

## 9. 日志或 Tracing 显示无返回时如何定位

按以下顺序检查：

1. 查看工具 `raw.txt`，确认数据源真实返回还是后续投影丢失。
2. 查看 `structured.json` 的 `coverage`、`samples`、`flows`、`spans` 和
   `limitations`。
3. 查看 `summary.txt`，确认决定性样本是否进入小模型文本。
4. 查看 Evidence 到 RCA 的 handoff 和 Fact Ledger。
5. 最后检查报告，确认是否错误地把 `present` 写成“无数据”。

如果 `raw.txt` 本身为空，问题在数据源、实体身份、时间窗或应用埋点；如果
`raw.txt` 有数据但 `structured.json` 没有，问题在结构化投影；如果
`structured.json` 有数据但报告没引用，问题在 Agent/RCA/Conclusion 消费链路。

## 10. 能力边界

- Kubernetes 的 `OOMKilled/137` 是 OOM 终态权威证据。
- Prometheus 采样可能错过被杀前最后几秒，最大采样值不要求精确等于 limit。
- DeepFlow 无需应用埋点即可观察支持协议的网络流，但完整应用 span 通常需要
  OpenTelemetry 手工埋点、自动埋点或等价 Trace Context 传播。
- 当前 OOM 测试是单调用方到单 API 的受控链路，不代表复杂微服务全链路。
- Case Package 是文件存储，适合当前 Sprint、回放和审计；现阶段不需要额外图
  数据库或 RAG 才能完成一个典型场景验证。
