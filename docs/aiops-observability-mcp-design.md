# AIOps 可观测性 MCP 工具设计文档

> 本文档介绍本轮设计的 AIOps 可观测性采集能力：做了什么 MCP 工具、它真实采集的是什么数据、
> 为什么这些数据能代表 **Metrics / Logging / Tracing / 图拓扑** 四大可观测维度，
> 以及从「设计 → 工具实现 → 真实调用结果 → 最终报告分析」如何一以贯之地体现真实数据。
>
> 关联：mcpstander `servers/aiops_observability/`（采集实现）、robusta `app/core/prompts.py`（报告体现）、
> ADR `docs/adr/0001-behavior-preserving-perf-optimization.md`。

---

## 1. 一句话概述

本轮在 **mcpstander**（MCP Server Manager）内部实现了一组「AIOps 可观测性采集器」，
对外通过 **coarse MCP server（端口 8089）** 暴露一个核心工具 `collect_aiops_case`，
让 Robusta Agent 只需传入「异常 Pod 的 namespace + pod」，即可**实时**从集群真实组件采集
Kubernetes 状态、Prometheus 指标、Elasticsearch/Filebeat 日志、DeepFlow 网络流量/调用链、
Tempo 分布式 trace，并构建 Pod 级图拓扑，压缩成一份 agent 可稳定消费的 case package。

设计铁律：**只采真实数据；采不到就诚实标 empty/absent 并给原因，绝不编造。**

---

## 2. 设计目标与背景

| 目标 | 说明 |
|------|------|
| 生产不依赖 `data` | 采集能力内建在 mcpstander，运行时不 import/shell 到 `data` 脚本 |
| 任意 Pod 可用 | 输入统一为 `namespace + pod`，不针对某种异常类型硬编码 |
| 真实可交叉核验 | 每条数据都能用 kubectl / Prometheus / ClickHouse / Tempo 独立复核 |
| 诚实优先 | 空/弱/缺失/错误显式标记，不伪造正向证据 |
| 小模型友好 | Agent-facing 返回 compact 摘要 + refs，大证据按 ref 展开 |
| 低侵入 | Robusta 只做配置、prompt、observation 分支增量，不重构主 workflow |

---

## 3. MCP 工具设计

### 3.1 工具面（对外接口）

coarse server（8089，Robusta 默认启用）暴露 4 个工具：

| 工具 | 作用 |
|------|------|
| `collect_aiops_case(namespace, pod, scenario?, window_minutes?)` | 一次性采集异常 Pod 的全维度证据，返回 compact case summary |
| `get_aiops_case(case_id)` | 读回已采集 case 的 compact 摘要 |
| `get_aiops_case_evidence(case_id, evidence_ref)` | 按 ref 展开单条证据/受限文件（拒绝路径穿越、拒绝评测标签） |
| `search_aiops_cases(namespace?, pod?, abnormal_type?)` | 检索已采集 case |

fine server（8090，默认关闭）提供 Pod 级单源查询工具，供专家/调试模式使用。

### 3.2 内部结构

```
mcpstander/servers/aiops_observability/
├── schemas.py          # EvidenceItem / SourceResult / TimeWindow 契约
├── config.py           # 运行时配置（端点、kubectl-exec 参数、凭证 secret）
├── evidence_store.py   # 文件型 case package 读写 + 路径安全 + 反泄漏
├── case_builder.py     # 编排：调各 collector → 建拓扑 → 生成信号/时间线 → 落盘 → compact summary
├── topology.py         # Pod 级图拓扑构建
└── collectors/
    ├── _kube.py        # kubectl 辅助：run_kubectl / secret_value(base64) / exec_in_pod / find_pod
    ├── kubernetes.py   # K8s 状态：get/describe/events/logs + owner 链 + matching Service
    ├── prometheus.py   # 指标：受控 PromQL
    ├── elasticsearch.py# 日志：kubectl-exec 进 ES pod 查 Filebeat
    ├── deepflow.py     # 网络流量/调用链：ClickHouse L7 flow + eBPF 自动追踪
    └── tempo.py        # 分布式 trace：按 trace_id 查 Tempo span
```

`collect_aiops_case` 的执行流水线（`case_builder.collect_case`）：

```
输入 namespace + pod
  1. collect_kubernetes  → Pod json/describe/events/current+previous logs + ownerReferences 链 + Service
  2. collect_prometheus  → 4 个受控 PromQL（内存/重启/终止原因/phase）
  3. collect_elasticsearch → kubectl exec 进 ES pod，curl filebeat-*/_search（凭证自动获取）
  4. collect_deepflow    → kubectl exec 进 ClickHouse，查 L7 flow（含 eBPF syscall_trace_id）
  5. discover_correlation → 发现 trace_id + caller IP
  6. collect_tempo       → 用发现的 trace_id 查 Tempo 分布式 span
  7. caller logs         → caller IP 反查 pod，采其日志（request_driver）
  8. build_topology      → 实体 + 边（owner/service/调度/网络/证据观测）
  9. 生成 role 信号 + 时间线 → 落盘 case package → 返回 compact summary
```

---

## 4. 四大可观测维度 + 图拓扑：采什么、怎么采、为什么能代表

每个维度产出一条带 **role（语义角色）+ observed（真实原文）+ interpretation（大白话解读）+ strength** 的信号，
既给人讲故事，也给小模型精确关联。

### 4.1 Metrics（指标）— 来源：Prometheus

**采什么**：容器工作集内存、重启次数、上次终止原因、Pod phase 等受控 PromQL 的**真实数值**。

**为什么能代表指标**：直接查 Prometheus HTTP API（`/api/v1/query`），拿的是指标核心原始输出——
资源使用趋势是否逼近/超过 limit 的第一手证据。

**真实例子**（OOM Pod）：
```
[metrics/resource_trend] src=prometheus
  container_memory_working_set_bytes ≈ 17584128 (16.8MiB)；limit=67108864 (64Mi)；request=33554432 (32Mi)
```
> 交叉核验：live Prometheus 查同一 Pod 返回 `17301504`（抓取时刻微差），limit 字节数 `67108864` 与 kubectl `64Mi` 逐字节吻合。

### 4.2 Logging（日志）— 来源：Elasticsearch/Filebeat（+ K8s 容器日志）

**采什么**：目标 Pod 在时间窗内的真实日志原文行。

**怎么采（关键实现）**：不直连 ES（脆、要认证、TLS 麻烦），而是**学 data 脚本**：
从 K8s secret `xnet/elasticsearch-master-credentials` **自动获取凭证**（base64 解码），
`kubectl exec -i elasticsearch-master-0 -- curl -u user:pass localhost:9200/filebeat-*/_search`。
若 ES 未接入，退化为 K8s 容器 current/previous 日志。

**日志归属正确性（重要）**：ES 查询把 **Pod 身份（pod.name/pod_name/pod.uid）设为必需的 `must` 条件**，
namespace 只作 `filter`——避免"命名空间内其他 Pod 的日志被错误归到目标 Pod"的串味问题。

**为什么能代表日志**：拿到的是应用失败前的**进程内真实行为**，解释异常"是怎么发生的"。

**真实例子**（OOM Pod，崩溃前内存增长）：
```
[logs/pre_failure_behavior] src=elasticsearch（来源：kubectl exec elasticsearch-master-0 -> filebeat-*）
  allocated business cache chunk=22 approx_mib=44
  allocated business cache chunk=23 approx_mib=46
  allocated business cache chunk=24 approx_mib=48   ← 应用不断分配缓存直到触及 64Mi limit
```
> 交叉核验：`kubectl logs aiops-oom-business -n aiops-temp --previous` 逐条一致；每条记录 `kubernetes.pod.name` 均为目标 Pod，无混入。

### 4.3 Tracing（链路/流量）— 来源：DeepFlow（eBPF）+ Tempo

这是本轮最有价值的一块。分两层，**任意 Pod（无需插桩）都能得第一层**：

**① DeepFlow eBPF 网络流量与自动调用链（无需 app 插桩）**

DeepFlow 是 eBPF，内核层自动抓所有 Pod 的真实 L7 流量。关键字段：
- `request_resource`（真实 SQL/HTTP 路径）、`response_code`、`response_duration`（真实延迟）
- `syscall_trace_id_request/response`（eBPF 内核生成，~50% 流量有）、`req_tcp_seq`（100%）—— **无需 app 埋点即可拼调用链**

> 数据佐证：全集群近 30min 有 81 万条 flow，其中带 app `trace_id` 的只有 0.018%，但带 eBPF `syscall_trace_id` 的约 50%。
> 即：真实生产 Pod 极少插桩，但 eBPF 自动追踪对它们都有效。

**真实例子**（未插桩的 MySQL Pod，eBPF 自动拼出 2 跳调用链）：
```
[tracing] eBPF 自动追踪拼出调用链（syscall_trace_id=594288737879969836）
  172.16.219.65 → 172.16.219.127  MySQL  COMMIT               dur=43us
  172.16.219.65 → 172.16.219.127  MySQL  SELECT dashboard.org_id...
```

**② Tempo 分布式 trace（插桩 Pod 的额外增强）**

对被 OpenTelemetry 插桩的 Pod，`trace_id` 会出现在日志/flow 里。
`discover_correlation` 从 DeepFlow flow **和日志文本**里提取 `trace_id`，
再 `kubectl exec` 进 lgtm/Tempo pod 查 `/api/traces/{trace_id}` 取真实 span。

**真实例子**（插桩 OOM Pod）：
```
[trace/span_evidence] src=tempo
  Tempo 返回 10 条 trace 的分布式 span：e2e054876b6a5b936572000000000001, ...0002, ...
```
> 交叉核验：独立审计逐个打 Tempo API 确认 `...0001/...000a` 有 span；失败 trace `...000b`（触发 OOM 无响应）Tempo 返回 404，工具**也确实没报它**——有据、不虚报。

**为什么 tracing 能代表**：DeepFlow 给出真实调用方向/端点/延迟/调用链（谁调用了它、慢在哪），
Tempo 给出端到端 span 路径。**弱/强分级严格**：DeepFlow node 级流量只算 `related_context/weak`，
Pod IP 直连 flow 算 `medium`，绝不当强因果。

### 4.4 Kubernetes（状态事实）— 来源：K8s API

**采什么**：Pod phase、containerStatuses、lastState.terminated（reason/exitCode）、events、owner、finalizers 等真实状态。

**为什么能代表**：K8s 终态与事件是根因状态的**直接证据**（OOMKilled/exit137、FailedScheduling、ImagePullBackOff）。

**真实例子**：
```
[k8s/root_cause_state] src=kubernetes
  Last terminated state: business-api=OOMKilled exit=137；restarts=2406；Warning BackOff x56536 over 8d
```

### 4.5 图拓扑（Topology）— 来源：K8s owner/Service + DeepFlow peer

**采什么**：真实实体（Pod/Container/Node/IP/ReplicaSet/Deployment/StatefulSet/Service/Evidence）
和它们之间带 `directness/confidence` 的关系边。

**为什么能代表拓扑**：不是画复杂图数据库，而是让模型明确"每条证据属于哪个实体、责任落在哪一层"——
避免把同 namespace/同 node/历史日志误判为直接证据。

**真实例子**（插桩 Pod，10 实体 9 边）：
```
Pod trace-oom-api-...      --scheduled_on-->  Node node2                [direct/high]   调度
Pod trace-oom-api-...      --assigned_to-->   IP 172.16.104.27          [direct/high]
Pod trace-oom-api-...      --owns_container-> Container api             [direct/high]
Pod trace-oom-api-...      --owned_by-->      ReplicaSet trace-oom-...  [direct/high]   ┐ 工作负载归属链
ReplicaSet trace-oom-...   --owned_by-->      Deployment trace-oom-api  [direct/high]   ┘
Service trace-oom-api      --selects-->       Pod trace-oom-api-...     [direct/high]   流量入口
evidence:prometheus-metrics--observes-->      Pod                       [direct/high]   ┐ 证据挂载
evidence:logs             --observes-->       Pod                       [direct/medium] │
evidence:deepflow         --observes-->       Node                      [related_ctx/weak]┘
```
> 若 Pod 无 ownerReferences，则明确标"独立直投 Pod，无上层控制器"；若无匹配 Service，标"无 Service 暴露"。
> 拓扑理解会**直接影响修复命令**：识别出独立 Pod → 修复从 `kubectl set resources deployment` 改为 `kubectl patch pod`。

---

## 5. 工具实现的关键设计点（保证"真实 + 稳定"）

| 设计点 | 解决的问题 |
|--------|-----------|
| **kubectl-exec 采集模式** | ES/DeepFlow/Tempo 不直连（认证/TLS/网络脆），而是 exec 进后端 Pod 查 localhost，稳定 |
| **凭证自动获取** | 从 K8s secret base64 解码 ES 账号，无需手工配置密钥 |
| **ClickHouse 时区显式 UTC** | ClickHouse 服务器时区是 Asia/Shanghai，窗口用 UTC 差 8h 会错过全部近期 flow → `toDateTime(..,'UTC')` |
| **ES 查询 Pod 身份必需** | Pod 身份进 `must`、namespace 进 `filter`，杜绝跨 Pod 日志串味 |
| **role 信号 + interpretation** | 借鉴 data 脚本，让信号人可读、直接指向问题 |
| **从日志提取 trace_id** | 插桩 Pod 即使窗口内无新 flow，日志里的 trace_id 也能查到 Tempo span |
| **compact summary + refs** | Agent-facing 返回摘要 + `recommended_refs_by_dimension`，大证据按需展开 |
| **反泄漏** | 拒绝返回 root_cause label / expected_remediation / evaluator-only 文件 |

---

## 6. 真实调用结果示例（端到端）

对插桩 Pod `aiops-dfotel-test/trace-oom-api-...` 调用 `collect_aiops_case` 的真实返回（compact summary）：

```json
{
  "coverage": {"k8s":"present","metrics":"present","logs":"present","tracing":"empty","trace":"present","topology":"present"},
  "signals_summary": [
    {"dimension":"k8s","role":"root_cause_state","source_system":"kubernetes","observed":"Last terminated state: api=OOMKilled exit=137"},
    {"dimension":"metrics","role":"resource_trend","source_system":"prometheus","observed":"Prometheus pod metrics queried: series=16 metrics=4"},
    {"dimension":"logs","role":"pre_failure_behavior","source_system":"elasticsearch","observed":"..."},
    {"dimension":"tracing","role":"network_flow","source_system":"deepflow","observed":"..."},
    {"dimension":"trace","role":"span_evidence","source_system":"tempo","observed":"Tempo 返回 10 条 trace 的分布式 span：e2e054876b..."}
  ],
  "topology_summary": {"entity_count":10,"edge_count":9,"relations":{"owned_by":2,"selects":1,"scheduled_on":1,...}},
  "recommended_refs_by_dimension": {"k8s":[...],"logs":[...],"metrics":[...],"tracing":[...]},
  "package_ref": "/app/aiops-cases/auto-..."
}
```

**数据分层（审计时要认清）**：MCP 工具的**原始输出**是上面这份干净 JSON（归档 `raw.txt`）；
Robusta 后台 ObservationProcessor 会把它**压缩成叙述式摘要**（`key_facts/missing`，归档 `summary.txt`）喂给小模型。
**单一真值源是 raw.txt**，摘要是忠实但有损的压缩。

**稳定性**：同一 Pod 连采多次结果确定性一致（独立审计 10/10 = 100%）。

---

## 7. 数据真实性保证

1. **可交叉核验**：每条数据都能用 kubectl / Prometheus / ClickHouse / Tempo 独立复核同一 Pod、同一窗口。
   例：MCP 报 restarts=2406 → live kubectl=2421（涨了，仍在崩溃循环，同源一致）；limit 67108864B → kubectl 64Mi 逐字节吻合。
2. **无编造**：coverage=absent/empty/error 时如实说明原因，不虚构任何数值/日志/flow。
   例：失败 trace 无 span → Tempo 404 → 工具不报；ImagePullBackOff Pod 容器没起来 → logs/tracing 诚实 empty。
3. **无串味**：ES 查询 Pod 身份必需，日志逐条归属目标 Pod。
4. **诚实的窗口语义**：Prometheus/ClickHouse 严格按声明窗口；K8s 容器日志与 Tempo 按 trace_id 取整段 buffer，
   可能包含窗口外的崩溃前证据（对诊断是好事，消费方需知晓非严格窗口内）。

---

## 8. 最终报告如何体现（Robusta 侧）

Robusta 的 conclusion 报告模板新增 **`## 📊 可观测性数据（三维度 + 拓扑）`** 模块（`app/core/prompts.py`），
强制体现真实数据、标注来源、串联逻辑：

```markdown
## 📊 可观测性数据（三维度 + 拓扑）
### 三大观测维度
| 维度 | 数据来源 | 覆盖状态 | 关键原始信号（人可读的真实数据） | 证据 ref |
| Metrics | Prometheus PromQL container_memory_working_set_bytes | present | 56MB working_set / 64Mi limit / 32Mi request | metric-... |
| Logging | Elasticsearch/Filebeat（kubectl exec）| present | allocated business cache chunk=24 approx_mib=48 | log-... |
| Tracing | DeepFlow L7（eBPF）/ Tempo | present/empty | 真实 flow/调用链 或 诚实标空 | deepflow-.../tempo-... |
| K8s | Kubernetes API | present | OOMKilled exit=137 restarts=2406 | k8s-... |
### 拓扑关系（实体与边）
- Pod --owned_by--> ReplicaSet --owned_by--> Deployment（工作负载归属）
- Service --selects--> Pod（流量入口）
- 拓扑结论：责任落在 Pod / ReplicaSet / Deployment / Service 哪一层
```

严格规则（prompt 强制）：
1. 证据来自 `collect_aiops_case` 时该模块必填；每条证据标明来源（Prometheus/ES-Filebeat/DeepFlow-ClickHouse/K8s-API）。
2. 写**人可读的真实原始数据**（真实日志行/指标值/flow），不写 `series=13` 这种裸计数。
3. 某维度 coverage=absent/empty/error 时**如实说明未采集到，严禁猜测或编造**。
4. 根因分析必须串联「三维度信号 → 拓扑责任实体 → 因果链」，不能各说各话。
5. 弱证据（`related_context`/`weak`，如 DeepFlow node 级）不得当强因果。

**效果（真实报告片段）**：报告显示 Metrics(56MB/64Mi 自洽真实值)、Logging(真实 cache 增长日志)、
Tracing(诚实标 empty 或真实调用链)、K8s(OOMKilled/137)、Topology(独立 Pod 无 Deployment)，
且拓扑理解直接改变了修复建议（独立 Pod → `kubectl patch pod` 而非 `set resources deployment`）。

---

## 9. 版本与部署

- **mcpstander**：coarse `aiops-case`=8089（默认启用）、fine `aiops-observability-fine`=8090（默认关闭）。
  采集端点/凭证通过 env 与 K8s secret 配置（`AIOPS_ES_EXEC_*`、`AIOPS_CLICKHOUSE_EXEC_*`、`AIOPS_TEMPO_EXEC_*`，均有本集群默认值）。
- **Robusta**：`deploy/configmap/config.yaml` 的 `mcp_servers.aiops-case-coarse.enabled: true` 连接 SSE 端点；
  observation 分支保留 `coverage/topology_summary/signals/directness/confidence` 字段；prompt 体现可观测模块。
- 部署：各自 `make build && make push && make deploy`（mcpstander ns=`mcp`，robusta ns=`aiops`）。

---

## 附：设计到验证的一致性

本设计经过多轮真实集群端到端验证与**独立 agent 审计**（fresh context，逐项 kubectl/Prometheus/ClickHouse/Tempo 交叉核验）：
数据真实性 1:1、诚实度可信、稳定性 100%；与 data 脚本真值对比——对同一 Pod 采到的真实数据同源一致，
唯一差异是 data 脚本「主动部署插桩 workload + 注入已知 trace_id」的受控实验部分（那需要自建 workload，不适用于诊断任意现成 Pod）。
