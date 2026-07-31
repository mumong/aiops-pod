# Robusta AIOps 可观测性 Sprint 测试指南

**文档日期**：2026-07-29

**近期优先级**：先完成“真实 OOMKilled 脚本采集”验收，再进行 MCP 和完整
Agent 流程验收。

## 1. 测试范围

本指南覆盖以下三个目标。

### Sprint 测试一

> 实现 Pod OOMKilled 典型场景的真实数据采集，覆盖 Kubernetes、
> Prometheus、日志、DeepFlow/Trace。

测试点：

> 输入异常 Pod 的 namespace 和 Pod 名称，脚本输出真实 Kubernetes、
> Prometheus、Logging、Tracing 和 Topology Case Package。

### Sprint 测试二

> 开发 MCP 工具，让 Agent 根据真实环境实时采集可观测数据；开发本地读取
> 工具，根据 case ID 按需读取结构化证据。

测试点：

1. Agent 或 MCP Client 可以实时查询 Metrics、Logging、Tracing 和 Topology。
2. `collect_aiops_case` 生成 case ID 后，可以使用
   `get_aiops_case` 和 `get_aiops_case_evidence` 读取指定证据。

### Sprint 测试三

> 完成 OOMKilled 场景的 Agent 诊断验证。

测试点：

> 完整运行一次 Robusta 诊断，真实获取 Kubernetes、Metrics、Logging 和
> Tracing，并基于真实证据输出人可读报告。Topology 若被 Agent 调用，必须只
> 展示工具返回的真实实体和关系边；未调用时不得推测。

## 2. 环境背景

### 2.1 项目目录

```text
/root/huhu/agent/combine-aiops-mcp/
├── data
├── mcpstander
├── robusta
└── aiops-cases
```

### 2.2 集群组件

| 组件 | namespace | 说明 |
|---|---|---|
| Robusta | `aiops` | Agent 和报告生成 |
| mcpstander | `mcp` | MCP Server Manager |
| Prometheus | `monitor` | 指标数据 |
| Elasticsearch/Filebeat | `monitor` | 日志数据 |
| DeepFlow/ClickHouse | `monitor` | L4/L7 flow |
| LGTM/Tempo | `monitor` | OTLP application span |
| OOM 测试环境 | `aiops-traced-oom` | 真实请求驱动的 OOM Pod |

### 2.3 前置检查

```bash
kubectl get pod -n aiops
kubectl get pod -n mcp
kubectl get pod -n monitor
```

至少确认：

- `aiops-copilot` Running。
- `mcp-server-manager` Running。
- Prometheus、Elasticsearch、Filebeat、ClickHouse、DeepFlow Agent 和
  LGTM/Tempo 对应 Pod Running。

检查 mcpstander 已配置当前 `monitor` namespace：

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
sed -n '35,90p' deploy/configmap.yaml
```

预期包含：

```text
PROMETHEUS_URL=http://observability-prometheus.monitor.svc:9090
AIOPS_ES_EXEC_NAMESPACE=monitor
AIOPS_CLICKHOUSE_EXEC_NAMESPACE=monitor
AIOPS_TEMPO_EXEC_NAMESPACE=monitor
```

## 3. Sprint 测试一：真实 OOM 脚本采集

这是当前最优先的测试。

本测试必须区分两个结论：

1. `validate=ok`：只证明 Case Package 结构合法、文件可解析。
2. 多模态采集通过：还必须证明 Prometheus、Logging、DeepFlow、Tempo 的真实
   记录非空，或以明确状态说明真实缺失，并展示决定性数值或原文。

只看到目录和 `ok`，不能判定真实可观测数据已经采集成功。

### 3.1 部署真实 OOM 工作负载

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
./scripts/aiops-traced-oom.sh cleanup
./scripts/aiops-traced-oom.sh apply
./scripts/aiops-traced-oom.sh verify
```

`apply` 会等待首次真实 OOMKilled；`verify` 验证 OOM 终态、业务日志、
trace context 和 Service Endpoint。

获取采集输入：

```bash
NS=aiops-traced-oom
POD=$(kubectl get pod -n "${NS}" -l app=trace-oom-api \
  -o jsonpath='{.items[0].metadata.name}')
echo "namespace=${NS}"
echo "pod=${POD}"
```

### 3.2 配置脚本访问真实数据源

`data/scripts/collect_case.py` 从环境变量读取 Prometheus、Elasticsearch 和
DeepFlow 地址。未设置这些变量时，脚本仍可能生成结构完整的 package，但对应
证据会为空。因此这一步是脚本验收的强制前置条件。

当前集群的数据系统位于 `monitor` namespace。

终端一：

```bash
kubectl -n monitor port-forward svc/observability-prometheus 19090:9090
```

终端二：

```bash
kubectl -n monitor port-forward pod/elasticsearch-master-0 19200:9200
```

采集终端：

```bash
export PROMETHEUS_URL=http://127.0.0.1:19090
export ELASTICSEARCH_URL=https://127.0.0.1:19200
export ELASTICSEARCH_INDEX='filebeat-*'
export ELASTICSEARCH_USERNAME="$(
  kubectl get secret -n monitor elasticsearch-master-credentials \
    -o jsonpath='{.data.username}' | base64 -d
)"
export ELASTICSEARCH_PASSWORD="$(
  kubectl get secret -n monitor elasticsearch-master-credentials \
    -o jsonpath='{.data.password}' | base64 -d
)"
export DEEPFLOW_CLICKHOUSE_URL='kubectl://monitor/observability-clickhouse-0?container=clickhouse'
export TEMPO_EXEC_ENABLED=true
export TEMPO_EXEC_NAMESPACE=monitor
export TEMPO_EXEC_SELECTOR='app=lgtm'
export TEMPO_LOCAL_URL='http://127.0.0.1:3200'
```

连通性检查：

```bash
curl -fsS "${PROMETHEUS_URL}/-/ready"
curl -fksS -u "${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD}" \
  "${ELASTICSEARCH_URL}/_cluster/health"
kubectl -n monitor exec observability-clickhouse-0 -c clickhouse -- \
  clickhouse-client --query 'SELECT 1'
```

预期分别返回 Prometheus ready、Elasticsearch health JSON 和 `1`。

### 3.3 采集 Case Package

```bash
cd /root/huhu/agent/combine-aiops-mcp/data

CASE_ID="oom-script-$(date +%Y%m%d-%H%M%S)"
OUT="/root/huhu/agent/combine-aiops-mcp/data/cases/${CASE_ID}"

python3 scripts/collect_case.py package \
  --scenario auto \
  --namespace "${NS}" \
  --pod "${POD}" \
  --case-id "${CASE_ID}" \
  --output "${OUT}"
```

校验：

```bash
python3 scripts/collect_case.py validate --case "${OUT}"
```

通过结果：

```text
ok
```

注意：`validate=ok` 不是多模态数据通过的充分条件，必须继续执行后面的
Kubernetes、Metrics、Logging、DeepFlow 和 Tempo 内容检查。

### 3.4 检查 Package 结构

```bash
find "${OUT}" -maxdepth 2 -type f -printf '%P\n' | sort
```

必须存在：

```text
case.yaml
queries.yaml
entities.jsonl
topology.jsonl
signals.jsonl
timeline.jsonl
diagnosis-input.yaml
labels.yaml
evidence/k8s_pod.yaml
evidence/k8s_describe.txt
evidence/k8s_events.jsonl
evidence/metrics.jsonl
evidence/logs.jsonl
evidence/deepflow_l4.jsonl
evidence/deepflow_l7.jsonl
evidence/tempo_traces.jsonl
```

### 3.5 检查输入身份

```bash
python3 - "${OUT}/case.yaml" <<'PY'
import sys
from pathlib import Path
import yaml

case = yaml.safe_load(Path(sys.argv[1]).read_text())
print("case_id=", case.get("case_id"))
print("abnormal_type=", case.get("abnormal_type"))
print("primary_entity=", case.get("primary_entity"))
print("time_window=", case.get("time_window"))
print("coverage=", case.get("coverage"))
PY
```

通过标准：

- `case_id` 等于输出目录名。
- `primary_entity.namespace` 和 `primary_entity.name` 等于本次输入。
- Pod UID、IP、Node 非空。
- `abnormal_type=oomkilled`，或至少 K8s 证据明确显示 OOMKilled。
- 时间窗属于当前 Pod 生命周期。

### 3.6 检查 Kubernetes 核心证据

```bash
grep -nE 'OOMKilled|exitCode|CrashLoopBackOff|restartCount|BackOff' \
  "${OUT}/evidence/k8s_pod.yaml" \
  "${OUT}/evidence/k8s_describe.txt" |
  head -n 30
```

通过标准：

- 存在 `OOMKilled`。
- 存在 exit code 137。
- 能看到 CrashLoopBackOff、重启次数或 BackOff Event。

### 3.7 检查 Prometheus 核心证据

查看实际执行的 PromQL：

```bash
grep -nE 'container_memory_working_set_bytes|resource_limits|restarts_total|last_terminated_reason' \
  "${OUT}/queries.yaml"
```

查看真实指标记录：

```bash
jq -c '{
  evidence_id,
  source,
  summary,
  query: .query,
  value: .value,
  raw: .raw
}' "${OUT}/evidence/metrics.jsonl" | head -n 20
```

通过标准：

- 至少包含目标业务容器的 `container_memory_working_set_bytes`。
- 能看到多个时间点，而不是只有“Prometheus 查询成功”。
- 能取得 memory limit，或可从 K8s 资源配置独立核对为 80 MiB。
- 最终可以比较 `max memory / limit`。

### 3.8 检查 Logging 核心证据

```bash
jq -r 'select((.raw.message // .summary // "") != "") |
  [.timestamp, .entity, (.raw.message // .summary)] | @tsv' \
  "${OUT}/evidence/logs.jsonl" |
  grep -E 'event.*allocate|allocated_mib|trace_id' |
  tail -n 20
```

通过标准：

- 日志属于当前 namespace、Pod 和 Container。
- 至少存在一条真实 `event=allocate` 或等价 JSON message。
- 至少能看到 `alloc_mib` 和 `allocated_mib`。
- 不能只看到“返回 50 条日志”。

### 3.9 检查 DeepFlow 核心证据

```bash
jq -c '{
  timestamp,
  entity,
  directness,
  trace_correlation,
  summary,
  raw
}' "${OUT}/evidence/deepflow_l7.jsonl" |
  grep -E '/allocate|trace_id|status=' |
  head -n 20
```

通过标准：

- 至少一条 flow 的源或目标 IP 等于目标 Pod IP。
- 存在真实 HTTP `/allocate` 路径、响应码和 trace ID。
- 存在 trace ID 时，应保留 trace ID 和关联状态。
- 没有 DeepFlow 数据时不能伪造，coverage 必须为 `empty/absent/error` 并说明原因。

### 3.10 检查 Tempo application span

```bash
jq -c '{
  timestamp,
  summary,
  trace_id: .raw.trace_id,
  span_count: .raw.span_count,
  services: .raw.services,
  spans: [.raw.spans[] | {
    service,
    name,
    duration_ms,
    attributes
  }],
  evidence_id
}' "${OUT}/evidence/tempo_traces.jsonl" |
  head -n 20
```

通过标准：

- 至少一条 span 的 service 为目标应用。
- span name 包含真实业务入口，例如 `GET /allocate`。
- attributes 包含业务语义，例如
  `aiops.allocated_mib.before/after` 和 `aiops.alloc_mib`。
- 某个失败请求没有 span 时，对应 query 应为 `absent`，不能伪造。

### 3.11 检查三源共同 trace ID

```bash
comm -12 \
  <(comm -12 \
    <(jq -r '.raw.message // empty' "${OUT}/evidence/logs.jsonl" |
      grep -oE '"trace_id": "[0-9a-f]{32}"' |
      sed -E 's/.*"([0-9a-f]{32})"/\1/' | sort -u) \
    <(jq -r '.raw.trace_id // empty' "${OUT}/evidence/deepflow_l7.jsonl" |
      grep -E '^[0-9a-f]{32}$' | sort -u)) \
  <(jq -r '.raw.trace_id // empty' "${OUT}/evidence/tempo_traces.jsonl" |
    sort -u)
```

通过标准：至少输出一个完整 trace ID。该 ID 必须能分别回查到：

- Logging 的原始 message。
- DeepFlow 的 src/dst/request/status。
- Tempo 的 service/span/attributes。

### 3.12 检查轻量拓扑

```bash
wc -l "${OUT}/entities.jsonl" "${OUT}/topology.jsonl"
jq -c . "${OUT}/topology.jsonl" | head -n 30
```

重点检查关系：

```text
Pod --scheduled_on--> Node
Pod --assigned_to--> Pod IP
Pod --owns/owns_container--> Container
Pod --owned_by--> ReplicaSet --owned_by--> Deployment
Service --selects--> Pod
Evidence --observes--> Pod
```

有可核验 DeepFlow 调用方时，还应出现：

```text
Caller Pod --calls--> Target Pod
```

同一个 trace ID 存在时，还应出现：

```text
Trace Group --correlates--> Service/Pod
OTel Service --emits_trace--> Trace Group
```

### 3.13 检查 Agent 安全输入

```bash
sed -n '1,240p' "${OUT}/diagnosis-input.yaml"
```

不得出现：

```text
labels.yaml
root_cause_label
expected_remediation
ground_truth
scoring
```

`labels.yaml` 是离线评测文件，不应提供给在线 Agent。

### 3.14 Sprint 测试一验收记录

填写：

```text
测试日期：
namespace：
pod：
pod_uid：
case_id：
输出目录：
Kubernetes：present / empty / error
Prometheus：present / empty / error
Logging：present / empty / error
DeepFlow：present / empty / error
Tempo：present / empty / error / not_tested
Topology：present / empty / error
validate：pass / fail
核心原始摘录：pass / fail
跨源 trace ID：pass / fail / not_tested
结论：pass / fail
```

## 4. Sprint 测试二：MCP 实时采集和按 case ID 读取

当前需要分别测试默认自主查询和 coarse Case Package。

### 4.1 测试默认自主查询 MCP

Robusta 当前配置应为：

```yaml
aiops-observability-query:
  enabled: true

aiops-case-coarse:
  enabled: false

workflow:
  evidence:
    observability_mode: autonomous
    observability_first_round_gate:
      enabled: true
```

模块测试：

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
/root/huhu/agent/combine-aiops-mcp/robusta/.venv/bin/python -m pytest -q \
  tests/test_aiops_observability_query_contract.py \
  tests/test_aiops_observability_query_metrics.py \
  tests/test_aiops_observability_query_logs.py \
  tests/test_aiops_observability_query_tracing.py \
  tests/test_aiops_observability_query_topology.py
```

通过标准：

- `execute_pod_promql` 拒绝没有精确 namespace 和 Pod matcher 的 PromQL。
- 范围查询优先使用 `window_minutes`；若显式 `start/end` 早于当前 Pod
  生命周期，必须返回明确错误或在受控规则下纠正，不能混入同名旧 Pod 数据。
- `query_pod_logs` 返回真实 message，而不是只有 count。
- `query_pod_tracing` 分开返回 DeepFlow flows 和 Tempo spans。
- `query_pod_topology` 只返回来源可核验的关系。
- 每次返回有 purpose、entity、coverage、directness、query、facts、samples 和
  evidence refs。
- 单次返回保持有界，不把全部原始数据塞入 Qwen。

### 4.2 测试 coarse MCP 的 SSE 工具

启动本地端口转发：

```bash
kubectl -n mcp port-forward svc/mcp-server-manager 18089:8089
```

在另一个终端执行：

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander

NS=aiops-traced-oom
POD=$(kubectl get pod -n "${NS}" -l app=trace-oom-api \
  -o jsonpath='{.items[0].metadata.name}')

NS="${NS}" POD="${POD}" python3 - <<'PY'
import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    async with sse_client("http://127.0.0.1:18089/sse") as streams:
        read_stream, write_stream = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools=", [tool.name for tool in tools.tools])

            collected = await session.call_tool(
                "collect_aiops_case",
                {
                    "namespace": os.environ["NS"],
                    "pod": os.environ["POD"],
                    "scenario": "auto",
                    "window_minutes": 30,
                },
            )
            case = json.loads(collected.content[0].text)
            print(json.dumps({
                "case_id": case.get("case_id"),
                "primary_entity": case.get("primary_entity"),
                "coverage": case.get("coverage"),
                "dimension_details": case.get("dimension_details"),
                "topology_summary": case.get("topology_summary"),
                "recommended_refs_by_dimension":
                    case.get("recommended_refs_by_dimension"),
                "package_ref": case.get("package_ref"),
            }, ensure_ascii=False, indent=2))

            case_id = case["case_id"]
            loaded = await session.call_tool(
                "get_aiops_case",
                {"case_id": case_id},
            )
            print("get_aiops_case=", loaded.content[0].text[:2000])

            refs = case.get("recommended_refs_by_dimension", {})
            selected_ref = (
                (refs.get("logs") or refs.get("metrics")
                 or refs.get("tracing") or refs.get("k8s"))[0]
            )
            evidence = await session.call_tool(
                "get_aiops_case_evidence",
                {
                    "case_id": case_id,
                    "evidence_ref": selected_ref,
                    "max_bytes": 12000,
                },
            )
            print("get_aiops_case_evidence=",
                  evidence.content[0].text[:12000])


asyncio.run(main())
PY
```

### 4.3 coarse MCP 通过标准

`collect_aiops_case` 必须返回：

- `case_id`
- `primary_entity`，包含 namespace、Pod、UID、IP 和 Node
- `coverage`
- `dimension_details`
- `topology_summary`
- `recommended_refs_by_dimension`
- `package_ref`

若某维度为 `present`，首屏必须包含核心样本：

- Metrics：metric、关键值、limit、比例。
- Logging：至少一条真实 message。
- Tracing：至少一条 flow 或 span。
- Topology：至少两条可核验关系边。

推荐统一检查以下七个字段，而不是直接展示整段 JSON：

```text
source + purpose + coverage + core_fact + raw_excerpt + evidence_ref + limitation
```

其中 `raw_excerpt` 保留 1 至 3 条最有判别力的原始记录。完整原始输出继续存放在
Case Package 或 Robusta `raw.txt`，避免把小模型上下文撑满。

以下结果判定为失败：

```text
logs=present，但只有 returned 50 records，没有 message
tracing=present，但只有 returned 12 traces，没有 flow/span
metrics=present，但只有 series 数量，没有数值
topology 未执行，但报告根据标签或 Pod 名称推测 Deployment/Service 关系
```

`get_aiops_case_evidence` 必须：

- 使用前一步真实返回的 case ID。
- 使用前一步真实返回的 evidence ref。
- 返回指定 evidence record 或允许文件的有界内容。
- 拒绝 `../../etc/passwd`、`labels.yaml`、root cause label 和 evaluator 文件。

### 4.4 真实 OOM coarse 基线

参考 case：

```text
case_id=sprint-audit-20260727-oom
package=/root/huhu/agent/combine-aiops-mcp/aiops-cases/sprint-audit-20260727-oom
```

覆盖：

```text
k8s=present
metrics=present
logs=present
tracing=present
trace=present
caller_logs=present
topology=present
```

真实核心值：

| 维度 | 基线 |
|---|---|
| Kubernetes | `OOMKilled`、exit 137、restarts 925 |
| Prometheus | 3.7 MiB -> 79.0 MiB，limit 80 MiB，98.72% |
| Logging | `/allocate?mib=2`，`allocated_mib=62` |
| DeepFlow | Driver IP -> Pod IP，HTTP 200，带 trace ID |
| Tempo | `GET /allocate`，60 MiB -> 62 MiB |
| Topology | 11 entities、10 edges，包含 `calls` 和 owner 链 |

2026-07-27 只读 SSE 复验结果：

```text
list_tools:
  collect_aiops_case
  get_aiops_case
  get_aiops_case_evidence
  search_aiops_cases

get_aiops_case(sprint-audit-20260727-oom):
  coverage: k8s/metrics/logs/tracing/trace/caller_logs/topology 全部 present
  metric_highlights=1
  log_samples=2
  deepflow_flows=1
  tempo_spans=1
  topology_edges=4

get_aiops_case_evidence:
  使用真实日志 ref 成功返回 event=allocate、trace_id、alloc_mib=2、
  allocated_mib=62 和目标 Pod
  使用 ../../etc/passwd 返回 invalid evidence_ref
```

这里的 `2/1/1/4` 是 6000 字符首屏预算下的代表性投影，不是磁盘 package
中的全部记录。它证明当前首屏已经包含核心原始样本，不再只有命中数量。

### 4.5 Case Package 与 Agent Evidence 的对应关系

Agent 实时调用得到的证据与 Case Package **采用相同的证据语义，但不是同一种
物理存储形式**。

| 证据概念 | Case Package / coarse MCP | 默认自主查询 Agent |
|---|---|---|
| 目标实体 | `case.yaml.primary_entity` | 每次工具结果的 `entity` |
| 查询时间窗 | `case.yaml.time_window`、`queries.yaml` | 每次工具结果的 `query` |
| 数据覆盖状态 | `case.yaml.coverage` | 每次工具结果的 `coverage` |
| 完整原始数据 | `evidence/*` | `tools/*.raw.txt` |
| 结构化证据 | `evidence/*.jsonl` | `tools/*.structured.json` |
| 小模型输入 | `diagnosis-input.yaml`、`signals.jsonl`、推荐 refs | `tools/*.summary.txt`、`agent_facts`、`agent_context` |
| 深入读取入口 | `get_aiops_case_evidence(case_id, evidence_ref)` | 工具归档 ref，或模型再次调用细粒度查询工具 |
| RCA 接口 | Package 证据转换为 Fact Ledger | 工具结果直接转换为 Fact Ledger |

因此：

1. 启用 coarse MCP 时，`collect_aiops_case` 会实时生成完整 Case Package，
   `get_aiops_case_evidence` 再按 case ID 和 evidence ref 展开原始证据。
2. 当前默认自主查询模式不会先生成完整 case 目录；它按 Metrics、Logging、
   Tracing、Topology 分次查询，并把每次真实结果归档。
3. 两条路径最终都以实体、时间窗、coverage、核心 facts/samples 和 evidence
   refs 进入 Fact Ledger，所以 RCA 的消费合同相同。
4. Case Package 更适合 Sprint 验收、离线复盘和评测；默认自主查询更适合在线
   诊断和模型按需补证。

更完整的设计说明见
`docs/aiops-observability-mcp-design.md` 的“7.3 Case Package 与 Agent
Evidence 的关系”。

## 5. Sprint 测试三：Robusta 完整 OOM 诊断

### 5.1 测试输入

保持环境中只存在一个目标异常 OOM Pod，然后使用模糊问题：

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=我的集群现在有什么问题？"
```

记录流式输出中的 `run_id`。

### 5.2 检查工具调用

```bash
RUN_ID=<run_id>

kubectl -n aiops exec deploy/aiops-copilot -- \
  find "/tmp/aiops/reports/context_archives/${RUN_ID}/tools" \
  -maxdepth 1 -type f | sort
```

当前默认自主模式下，至少应看到以下工具的真实调用归档：

```text
execute_pod_promql
query_pod_logs
query_pod_tracing
```

`query_pod_topology` 是按需工具，不要求每轮强制调用。若报告出现拓扑实体或关系，
则必须能找到对应的 `query_pod_topology` 归档和真实 edge；否则该拓扑内容判定为
模型推测，测试失败。

同时应存在必要的 Kubernetes 当前态查询。

### 5.3 检查原始数据和结构化数据

列出可观测工具文件：

```bash
kubectl -n aiops exec deploy/aiops-copilot -- sh -c \
  "ls /tmp/aiops/reports/context_archives/${RUN_ID}/tools |
   grep -E 'execute_pod_promql|query_pod_logs|query_pod_tracing|query_pod_topology'"
```

人工抽查每个工具的三层归档：

```text
*.raw.txt
*.structured.json
*.summary.txt
```

检查重点：

- `raw.txt`：数据源的完整真实返回。
- `structured.json`：coverage、facts、samples、flows、spans、refs。
- `summary.txt`：注入小模型的内容是否仍保留决定性数值和原文。

如果 `raw.txt` 有日志或 Trace，但 `structured.json` 没有，属于投影缺陷。
如果 `structured.json` 有数据但最终报告未引用，属于 Agent 消费缺陷。

对“日志/Tracing 无返回”必须按下表判责：

| 检查结果 | 问题位置 | 测试结论 |
|---|---|---|
| `raw.txt` 无记录，coverage=`empty/absent/error` | 数据源、查询条件、实体身份、时间窗或埋点 | 诚实缺失，不允许补造 |
| `raw.txt` 有记录，`structured.json` 无 samples/flows/spans | Observation 结构化投影 | 失败 |
| `structured.json` 有 samples/flows/spans，报告写“未返回” | RCA/Conclusion 消费或渲染 | 失败 |
| 报告有原文，但 evidence ref 不存在 | 引用完整性 | 失败 |

### 5.4 检查 Evidence 到 RCA

```bash
kubectl -n aiops exec deploy/aiops-copilot -- \
  sed -n '1,260p' \
  "/tmp/aiops/reports/context_archives/${RUN_ID}/handoff/evidence-to-rca.json"
```

通过标准：

- 每个核心事实有明确实体范围。
- Metrics、Logging、Tracing 至少有 coverage 状态；Topology 仅在真实调用后
  才进入覆盖统计。
- `present` 维度保留真实 samples。
- RCA 使用 Fact Ledger/fact ID 或等价结构化事实，不只使用一句摘要。

### 5.5 最终报告通过标准

报告必须让人能够直接理解以下内容。

#### 现象

```text
目标 Pod 处于 CrashLoopBackOff；
上一轮容器 OOMKilled，exit code 137；
重启次数持续增加。
```

#### 根因核心证据

至少引用：

- Prometheus 内存从低值上升到接近 80 MiB limit。
- 一条真实 `event=allocate` 日志。
- 一条 DeepFlow `/allocate` flow。
- 存在时的一条 Tempo `GET /allocate` span。
- Kubernetes `OOMKilled/137`。

#### 因果逻辑

报告应形成：

```text
Driver 请求
  -> 目标应用执行内存分配
  -> 容器工作集持续增长
  -> 逼近 memory limit
  -> OOMKilled/137
  -> CrashLoopBackOff
```

#### 拓扑责任

只有真实调用 `query_pod_topology` 并返回关系边时，报告才应说明：

```text
Driver Pod --calls--> API Pod
Service --selects--> API Pod
API Pod --owned_by--> ReplicaSet --owned_by--> Deployment
```

这用于判断责任实体和后续修复对象，不是为了替代 Trace。

#### 人可读性

不允许只写：

```text
Prometheus 有数据
日志返回 50 条
Trace 返回 12 条
拓扑有 10 条边
```

必须写出决定性数值、日志原文、请求路径、trace ID 或 span attributes。

可观测性总表与机器附录必须一致：

- 如果附录已经存在日志 message、flow 或 span，总表不得显示“未返回可用日志
  原文”，也不能只显示 trace ID。
- 每个 `coverage=present` 的维度至少展示一条人可读核心结果；原始 JSON 可以
  截取关键字段，但必须保留 evidence ref，便于继续展开。
- 未执行 `query_pod_topology` 时，报告不得根据标签、Pod 名称或
  `pod-template-hash` 推测 owner、Service 或调用关系。

#### 缺失边界

如果某维度真实为空：

- 报告明确写 `empty/absent/error` 和原因。
- 不把缺失数据写成已验证事实。
- 不因某一个维度为空而否定其他维度的真实证据。

## 6. 证据充分度判定表

| 级别 | 判定 |
|---|---|
| 高 | K8s 终态、指标趋势、业务日志和 DeepFlow/Tempo 能形成同实体、同时间窗、可交叉核验的因果链 |
| 中 | K8s 终态和指标/日志可以直接支持根因，但 Trace 为空或只能作为影响证据 |
| 低 | 只执行过工具，只有 coverage/count，没有决定性原始值、message、flow 或 span |
| 不可信 | 数据属于其他 Pod/生命周期，或模型生成了数据源不存在的值 |

OOM Sprint 最低通过线是“中”；当前 traced OOM 基线应达到“高”。

“把工具核心结果放到报告里”是正确方向，但应放入**有界的核心原始摘录**，而
不是完整 raw：

- Metrics：3 至 5 个关键时间点、最大值、limit 和比例。
- Logging：1 至 3 条决定性 message 原文。
- DeepFlow：1 至 3 条 flow 的 src/dst/request/status/duration/trace ID。
- Tempo：1 至 3 条 span 的 service/name/关键 attributes。
- K8s：终态 reason、exit code、restart count 和关键 Event。
- Topology：2 至 8 条与责任定位直接相关的边。

完整结果通过 `raw_ref` 或 `get_aiops_case_evidence` 展开。

## 7. 三项 Sprint 最终验收表

| Sprint | 验收项 | 通过标准 | 结果 |
|---|---|---|---|
| 测试一 | namespace + Pod 脚本采集 | Package 校验通过，K8s/Prometheus/Logging/DeepFlow/Tempo/Topology 有真实证据或诚实缺失状态 | **已通过**：2026-07-29，`oom-script-20260729-094641` |
| 测试二 | MCP 实时采集 | 通用查询 MCP 能返回真实有界证据；coarse MCP 能生成 case ID | **核心功能已有真实基线，本轮未重新现场复验**：按 4.1 至 4.3 重新执行后封版 |
| 测试二 | case ID 按需读取 | `get_aiops_case` 和 `get_aiops_case_evidence` 使用真实 refs 成功读取，非法路径被拒绝 | **已有 2026-07-27 SSE 实测记录，本轮未重新现场复验** |
| 测试三 | Robusta 完整诊断 | 模糊提问触发真实工具，RCA 和报告引用核心原始证据并形成因果链 | **待回归**：2026-07-27 历史运行根因正确，但 Metrics 时间窗、报告渲染和未查询拓扑边界未全部通过 |

当前状态不能简化为“三项全部通过”：

- 本轮已经用标准脚本重新完成测试一，证据覆盖 Kubernetes、Prometheus、
  Logging、DeepFlow、Tempo 和轻量拓扑。
- 测试二有已部署能力、模块测试和 2026-07-27 SSE 读取基线，但本轮没有针对
  当前部署重新执行完整 MCP Client 流程。
- 测试三需要使用当前版本和同一个模糊问题再运行一次 Robusta，确认 Metrics、
  Logging、Tracing 的决定性原始证据进入 RCA 和最终报告；Topology 只在真实
  调用后展示。

## 8. 真实运行审计示例

### 8.1 2026-07-29 标准脚本验收

```text
case_id=oom-script-20260729-094641
namespace=aiops-traced-oom
pod=trace-oom-api-7c75757475-vgvxs
pod_uid=02b86eed-e9db-449c-9c6a-9fce6f0ca566
output=/root/huhu/agent/combine-aiops-mcp/data/cases/oom-script-20260729-094641
validate=pass
```

| 维度 | coverage | 真实结果 |
|---|---|---|
| Kubernetes | present/4 | restart count `1335`，上一轮 `OOMKilled/137`，memory limit `80Mi` |
| Prometheus | present/9 | working set `26.8 MiB -> 68.9 MiB`，restart `1333 -> 1334`，OOM reason `1`，limit `80.0 MiB` |
| Logging | present/20 | `event=allocate`、`alloc_mib=2`、`allocated_mib=48` 和完整 trace ID |
| DeepFlow | present/80 | `172.16.104.8 -> 172.16.104.25`，`GET /allocate?mib=2&step=304943`，HTTP `200` |
| Tempo | present/11 | `GET /allocate` span，`allocated before=46`、`alloc=2`、`after=48` |
| Topology | present | trace group 同时关联 Service、Pod、DeepFlow evidence 和 Tempo evidence |

Logging、DeepFlow、Tempo 三方共同 trace ID 共 `9` 个。代表值：

```text
192d16297831f81fa46afa473f763631
```

本测试判定：**Sprint 测试一通过**。该结论基于真实 source evidence，不是只基于
`validate=ok`。

### 8.2 2026-07-27 Agent 运行历史审计

运行信息：

```text
run_id=5a7686b8d5614336
question=我的集群现在有什么问题？
target=aiops-traced-oom/trace-oom-api-7c75757475-vgvxs
```

真实采集结果：

| 维度 | 结果 | 代表性事实 |
|---|---|---|
| Kubernetes | present | `Reason=OOMKilled`、`Exit Code=137`、restart count 950、BackOff 事件累计 22198 次 |
| Logging | present | ES 日志包含 `event=allocate`、`path=/allocate?mib=2`、`allocated_mib=20/22/24` 和 trace ID |
| Tracing | present | DeepFlow 返回 `GET /allocate?mib=2`、HTTP 200、调用方/目标 IP；Tempo 同 trace ID 的 span 包含 `allocated_before=46`、`allocated_after=48` |
| Metrics | error | Qwen 传入 `2024-01-01T00:00:00Z` 到 `2024-01-01T01:00:00Z`，早于当前 Pod 的 `2026-07-23T07:25:45Z` 创建时间，MCP 返回 `range_precedes_pod_lifecycle` |
| Topology | not executed | 本轮未调用 `query_pod_topology`，因此不应输出推测的 Deployment 关系 |

本次运行的诊断根因正确，但 Sprint 测试三暂不应判定为完全通过：

1. Prometheus 查询参数错误导致三维决定性证据只有 2/3，充分度为 67%。
2. 日志和 Trace 原始事实已进入 Fact Ledger 和机器附录，但可观测性总表没有
   展示代表性原文，存在人可读渲染缺口。
3. 本轮未执行拓扑工具，报告仍推测了 Deployment 关系，不符合真实证据边界。

该示例可作为后续修复的回归基线：修复后必须使用同样的模糊问题重新运行，并
逐项确认 Metrics、Logging、Tracing 和按需 Topology 的真实结果。

## 9. 测试完成后的清理

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
./scripts/aiops-traced-oom.sh cleanup
```

保留需要归档的 Case Package 和 Robusta `run_id` 报告，不删除
`testreports`。
