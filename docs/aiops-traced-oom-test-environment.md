# AIOps Traced OOM 测试环境与采集使用说明

**更新日期**：2026-07-27

## 1. 测试目标

该环境用于制造一个真实、可重复、可关联的 Pod OOMKilled 故障，并验证：

- Kubernetes：`OOMKilled`、exit code 137、CrashLoopBackOff、重启次数和 Event。
- Prometheus：目标容器内存随请求增长并逼近 memory limit。
- Logging：目标服务输出真实分配行为、trace ID 和累计分配量。
- DeepFlow：真实 HTTP 请求的调用方向、路径、状态码、时延和 trace ID。
- Tempo：目标应用上报的 `GET /allocate` span 和业务内存属性。
- Topology：Driver、Service、Deployment、ReplicaSet、Pod、Container、Node
  和 Evidence 之间的关系。

这不是只打印固定文本的 BusyBox。目标 Pod 是一个真实 HTTP API，Driver Pod
持续发送请求，每个请求都会让目标进程新增并保留内存，最终由容器 memory
limit 触发 OOMKilled。

## 2. 环境结构

```text
trace-oom-driver Deployment
  -> 生成 W3C traceparent
  -> 调用 Service trace-oom-api
  -> GET /allocate?mib=2&step=N

trace-oom-api Deployment
  -> 解析 traceparent
  -> 上报 OTLP span 到 lgtm.monitor.svc:4318
  -> 输出 event=allocate 业务日志
  -> 每次长期保留 2 MiB 内存
  -> 工作集逼近 80 MiB memory limit
  -> OOMKilled / exit 137
  -> CrashLoopBackOff

Filebeat -> Elasticsearch
DeepFlow agent -> ClickHouse L7 flow
Prometheus -> cAdvisor + kube-state-metrics
```

资源配置：

```text
container=business-api
memory request=32Mi
memory limit=80Mi
CPU limit=300m
```

字段含义：

- `mib=2`：当前 HTTP 请求要求新增约 2 MiB 内存。
- `alloc_mib=2`：本次实际分配量约为 2 MiB。
- `allocated_mib=62`：当前进程累计保留约 62 MiB。
- `MiB`：二进制内存单位，`1 MiB = 1024 * 1024` 字节。

## 3. 部署和清理

进入 Robusta 项目：

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
```

一键部署并等待首次真实 OOM：

```bash
./scripts/aiops-traced-oom.sh apply
```

查看状态：

```bash
./scripts/aiops-traced-oom.sh status
```

查看目标当前/上一轮日志和 Driver 日志：

```bash
./scripts/aiops-traced-oom.sh logs
```

执行工作负载级验证：

```bash
./scripts/aiops-traced-oom.sh verify
```

`verify` 至少检查：

- `lastState.terminated.reason=OOMKilled`
- `lastState.terminated.exitCode=137`
- previous logs 存在 `event=allocate`
- previous logs 存在 `trace_id`、`span_id`、`allocated_mib`
- Driver 日志存在 `traceparent`
- Service Endpoints 能关联目标 Pod

测试完成后清理：

```bash
./scripts/aiops-traced-oom.sh cleanup
```

## 4. 手工检查

动态获取目标 Pod：

```bash
NS=aiops-traced-oom
POD=$(kubectl get pod -n "${NS}" -l app=trace-oom-api \
  -o jsonpath='{.items[0].metadata.name}')
echo "${NS}/${POD}"
```

检查 Kubernetes 终态：

```bash
kubectl get pod "${POD}" -n "${NS}" \
  -o jsonpath='state={.status.containerStatuses[0].state.waiting.reason} restarts={.status.containerStatuses[0].restartCount} last_reason={.status.containerStatuses[0].lastState.terminated.reason} last_exit={.status.containerStatuses[0].lastState.terminated.exitCode} pod_ip={.status.podIP} node={.spec.nodeName}{"\n"}'
```

预期包含：

```text
state=CrashLoopBackOff
last_reason=OOMKilled
last_exit=137
```

检查上一轮业务日志：

```bash
kubectl logs "${POD}" -n "${NS}" -c business-api \
  --previous --tail=100
```

预期出现连续增长：

```json
{"event":"allocate","alloc_mib":2,"allocated_mib":58}
{"event":"allocate","alloc_mib":2,"allocated_mib":60}
{"event":"allocate","alloc_mib":2,"allocated_mib":62}
```

## 5. 使用 `data` 脚本采集标准 Case Package

### 5.1 适用范围

`data/scripts/collect_case.py` 的标准入口是：

```text
namespace + pod + scenario + case_id + output
```

它适合验证 Sprint 中“给定异常 namespace 和 Pod，脚本自动采集真实多模态数据”
这一目标。

该通用脚本采集：

- Kubernetes
- Prometheus
- Elasticsearch/Filebeat
- DeepFlow L4/L7
- 轻量拓扑

其中 Tracing 指 DeepFlow 网络流和存在时的 trace/span 关联字段。标准
`collect_case.py` 不负责查询 Tempo application span；Tempo 是生产 coarse
collector 和专用 Trace 审计路径的增强维度。

### 5.2 真实采集命令

```bash
cd /root/huhu/agent/combine-aiops-mcp/data

NS=aiops-traced-oom
POD=$(kubectl get pod -n "${NS}" -l app=trace-oom-api \
  -o jsonpath='{.items[0].metadata.name}')
CASE_ID="oom-script-$(date +%Y%m%d-%H%M%S)"
OUT="/root/huhu/agent/combine-aiops-mcp/data/cases/${CASE_ID}"

python3 scripts/collect_case.py package \
  --scenario auto \
  --namespace "${NS}" \
  --pod "${POD}" \
  --case-id "${CASE_ID}" \
  --output "${OUT}"
```

校验 package：

```bash
python3 scripts/collect_case.py validate --case "${OUT}"
```

预期输出：

```text
ok
```

### 5.3 标准脚本 Package 结构

```text
<case-id>/
├── case.yaml
├── queries.yaml
├── entities.jsonl
├── topology.jsonl
├── signals.jsonl
├── timeline.jsonl
├── diagnosis-input.yaml
├── labels.yaml
└── evidence/
    ├── k8s_pod.yaml
    ├── k8s_describe.txt
    ├── k8s_events.jsonl
    ├── metrics.jsonl
    ├── logs.jsonl
    ├── deepflow_l4.jsonl
    └── deepflow_l7.jsonl
```

文件分层：

| 层级 | 文件 | 作用 |
|---|---|---|
| 身份和范围 | `case.yaml` | Pod UID、IP、Node、时间窗、异常类型、coverage |
| 查询审计 | `queries.yaml` | 实际 PromQL、日志查询、DeepFlow SQL 和 K8s 命令 |
| 原始证据 | `evidence/*` | 根因判断的真实数据 |
| 实体和关系 | `entities.jsonl`、`topology.jsonl` | 轻量拓扑 |
| 索引 | `signals.jsonl`、`timeline.jsonl` | 证据角色和时间线 |
| Agent 输入 | `diagnosis-input.yaml` | 不含评测答案的压缩入口 |
| 评测标签 | `labels.yaml` | 只用于离线评测，不应提供给在线 Agent |

### 5.4 哪些是核心真实数据

必须优先检查：

1. `case.yaml`
   - namespace、Pod 名、UID、Pod IP 和时间窗是否属于当前 Pod 生命周期。
   - coverage 是否如实反映每个维度。
2. `evidence/k8s_pod.yaml` 和 `evidence/k8s_describe.txt`
   - 是否存在 `OOMKilled` 和 exit 137。
3. `evidence/metrics.jsonl`
   - 是否包含工作集时间序列、restart、last terminated reason 和 memory limit。
4. `evidence/logs.jsonl`
   - 是否包含目标 Pod 的原始业务日志，而不是只有命中条数。
5. `evidence/deepflow_l7.jsonl`
   - 是否包含目标 Pod IP、HTTP `/allocate`、状态码、时延和 trace ID。
6. `topology.jsonl`
   - 是否能从 Driver/Service/owner/Node 关系定位责任实体。

`signals.jsonl` 是索引，不是最终原始证据。以下内容不能单独判定通过：

```text
logging evidence captured
tracing_flow evidence captured
returned 50 rows
```

必须继续查看 `evidence/*` 的决定性数值和原文。

## 6. 完整 Tempo 关联验收

如果测试目标还包括 application span，应使用当前 mcpstander coarse collector
或默认自主 `query_pod_tracing`：

```text
DeepFlow L7
  + 日志中的 trace_id
  -> 查询 Tempo /api/traces/<trace_id>
  -> 返回 service、span name 和业务 attributes
```

一个有效的完整关联至少应存在同一 `trace_id`：

```text
Logging:
  event=allocate, allocated_mib=62

DeepFlow:
  GET /allocate?mib=2, HTTP 200

Tempo:
  GET /allocate
  aiops.allocated_mib.before=60
  aiops.alloc_mib=2
  aiops.allocated_mib.after=62
```

真实参考样本：

```text
/root/huhu/agent/combine-aiops-mcp/aiops-cases/
  sprint-audit-20260727-oom
```

代表性 `trace_id`：

```text
7f54c092ad81bdc124e7d16034d07ca9
```

## 7. 脚本测试通过标准

满足以下条件才判定“真实 OOM 多模态脚本采集通过”：

1. 输入是运行中的真实 namespace 和 Pod 名，不使用离线样本。
2. `validate` 返回 `ok`，所有 JSONL 可逐行解析。
3. Kubernetes 存在 `OOMKilled/137`。
4. Prometheus 至少存在一条目标业务容器内存序列，并能与 limit 比较。
5. Logging 至少保留一条目标 Pod 的真实分配日志。
6. DeepFlow 至少保留一条目标 Pod IP 相关的真实流量；如没有，coverage 必须
   如实为 `empty/absent/error` 并记录原因。
7. `entities.jsonl` 和 `topology.jsonl` 非空，关键边能回查到 K8s 或 DeepFlow。
8. `diagnosis-input.yaml` 不包含 `labels.yaml`、root cause label 或 expected
   remediation 等评测答案。

完整 Tempo 增强验收还要求：

9. Logging、DeepFlow、Tempo 至少共享一个真实 trace ID。
10. Tempo span 包含目标 service、Pod 和至少一个业务内存属性。

## 8. Tracing 是否必须埋点

不完全必须，需要区分：

- **DeepFlow 网络可观测性**：应用不埋点，只要存在受支持协议的真实网络流量，
  通常仍可获得 L4/L7 flow、端点、状态码和时延。
- **稳定的应用分布式 Trace**：若要获得一致的 trace ID、父子 span、业务属性
  和 Tempo span 树，应用通常需要 OpenTelemetry 手工埋点、自动埋点或等价
  Trace Context 传播与导出。

因此，未埋点应用的 DeepFlow 结果仍可能有价值，但不能保证获得带业务语义的
Tempo span。本测试同时保留两者，用来验证网络事实和应用语义可以在同一
trace ID 上关联。
