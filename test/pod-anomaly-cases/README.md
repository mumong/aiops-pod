# Pod Anomaly Observability Lab

这是一个长期、可重复的 Kubernetes Pod 异常案例库。默认入口只创建 namespace 级、有限资源、
可精确清理的案例；运行态案例会产生真实 Prometheus、Elasticsearch、DeepFlow 和 Tempo 证据。
案例不会部署标准答案或固定 AIOps 查询流程。

## Prerequisites

- 可访问目标集群的 `kubectl`，并有创建/删除 `aiops-case-01` 至 `aiops-case-11` 的权限。
- 集群已有 kube-state-metrics/cAdvisor、Prometheus、Filebeat/Elasticsearch、DeepFlow 和 Tempo。
- 节点可使用已缓存的 `xnet.registry.io:8443/observability/python:3-alpine`。
- c05 需要集群已安装 Multus 和 `NetworkAttachmentDefinition` CRD；它只引用 namespace 内不存在的
  secondary network，不创建或修改 CNI 配置。
- OTLP/HTTP collector 默认可通过 `http://lgtm.monitor.svc:4318/v1/traces` 访问。
- 本地使用 `python3`；所有离线测试只依赖 Python 标准库。

先复制验证器配置，不要提交含凭据的 `config.env`：

```bash
cp pod-anomaly-cases/config.env.example pod-anomaly-cases/config.env
```

## Quick start

以下命令都从本仓库根目录执行。

### Individual apply

普通单案例按“部署 -> 等待异常/遥测 -> 验收”执行。以能产生错误日志和 Trace 的 c07 为例：

```bash
kubectl apply -k pod-anomaly-cases/cases/config-error-traced
pod-anomaly-cases/scripts/validate.sh --case c07 --wait
```

其他案例只需按 [Case catalog](#case-catalog) 替换目录和 `cNN`。例如 OOM：

```bash
kubectl apply -k pod-anomaly-cases/cases/oomkilled-traced
pod-anomaly-cases/scripts/validate.sh --case c08 --wait
```

c11 需要先让应用产生至少一次真实请求，再触发不会自动结束的删除：

```bash
kubectl apply -k pod-anomaly-cases/cases/terminating-stuck
kubectl -n aiops-case-11 wait --for=condition=Ready pod/workload --timeout=180s
kubectl -n aiops-case-11 logs pod/workload --tail=20
kubectl -n aiops-case-11 delete pod workload --wait=false
pod-anomaly-cases/scripts/validate.sh --case c11 --wait
```

执行 `logs` 后应先看到至少一条 `"event":"http_request"`；否则等待几秒后重查，再执行删除。
c11 的异常事实是存活对象上的 `deletionTimestamp + finalizer`，Logging、DeepFlow 和 Tempo 展示的是
删除前同一请求产生的关联证据。

一键部署并验收全部非破坏性案例：

```bash
pod-anomaly-cases/scripts/deploy-safe.sh
```

无论部署一个还是全部案例，都推荐用统一脚本清理；它会先安全释放 c11 finalizer：

```bash
pod-anomaly-cases/scripts/cleanup.sh
```

## Architecture

运行态案例复用一个 ConfigMap-hosted Python 服务和一个 `traffic-driver`：

```text
traffic-driver (Pod UID = case_run_id)
  -> Service/workload -> workload Pod /work + traceparent
       -> stdout JSON -------------> Filebeat -> Elasticsearch
       -> Pod/app metric ----------> Prometheus
       -> direct Pod-IP L7 --------> DeepFlow ClickHouse
       -> OTLP/HTTP span ----------> collector -> Tempo
```

同一次请求的日志、DeepFlow flow 和 Tempo span 使用同一个 W3C trace ID。Prometheus 通过精确的
namespace、Pod 和重叠时间窗关联。`/metrics` 提供应用补充指标；即使注解抓取未启用，
kube-state-metrics/cAdvisor 的 phase、Ready、restart、reason、CPU 和 memory 仍是权威最低证据。

控制面案例的容器没有启动，因此只应有 Kubernetes status/Event 和 kube-state 指标，不能真实产生
应用日志、L7 flow 或 span。

## Current AIOps behavior

当前 AIOps 主链是 `Layer -> Evidence -> RCA -> Conclusion`。部署配置为 autonomous observability，
并对每个确认异常 Pod 首轮真实尝试 Metrics、Logging、Tracing 和 Topology。首轮维度覆盖是通用门控，
具体 PromQL、Elasticsearch DSL、DeepFlow 条件、trace ID 和后续补证由模型根据现场结果选择。

Runbook 只提供待验证方向和查询构造参考，不是证据，也不是固定工具序列。本目录的验证器只做实验
验收，AIOps 不读取它的 catalog，也不调用它作为诊断捷径。

## MCP compatibility

当前 MCP 暴露的是按实体、问题和时间窗查询真实后端的通用工具，不是 OOM 或其他故障类型的固定流程：

| 工具 | 真实来源 | Agent 选择的主要输入 |
|---|---|---|
| `execute_pod_promql` | Prometheus | PromQL、instant/range、时间窗 |
| `query_pod_logs` | Elasticsearch/Filebeat | 关键词、level、container、trace ID、时间窗 |
| `query_pod_tracing` | DeepFlow ClickHouse + Tempo | 方向、状态码、耗时、资源、trace ID、时间窗 |
| `query_pod_topology` | Kubernetes API | 目标 Pod、UID 和诊断目的 |

四个工具都以精确 `namespace + pod` 为实体，支持可选 Pod UID 防止同名生命周期串线，并限制查询
时间和返回量。工具输入没有 `scenario`、`oom` 或 `config-error` 参数：模型根据现场问题填入 PromQL
或结构化过滤条件，MCP 负责校验范围、构造有界查询并访问后端。因此它理论上可以查询本目录产生的
真实数据，但不能查询物理上不存在的信号；c01–c05 的日志或 Trace 返回 `empty/absent` 才是正确结果。

## Case catalog

| ID | 目录 | Kubernetes 表现 | 应用遥测 |
|---|---|---|---|
| c01 | `cases/pending-unschedulable` | Pending / FailedScheduling | 无进程 |
| c02 | `cases/imagepull-failed` | ErrImagePull / ImagePullBackOff | 无进程 |
| c03 | `cases/volume-mount-failed` | Pending / FailedMount | 无进程 |
| c04 | `cases/createcontainer-config-error` | CreateContainerConfigError | 无进程 |
| c05 | `cases/sandbox-create-failed` | 缺失 Multus secondary network，Pending / FailedCreatePodSandBox | 无进程 |
| c06 | `cases/crashloop-runtime` | CrashLoopBackOff / exit 2 | 退出前日志、flow、span |
| c07 | `cases/config-error-traced` | HTTP 500 后 exit 78 | 错误日志、500 flow、error span |
| c08 | `cases/oomkilled-traced` | OOMKilled / 137 / restart | 内存增长及 kill 前遥测 |
| c09 | `cases/readiness-probe-failed` | Running、Ready=False | 503 日志、flow、span |
| c10 | `cases/liveness-probe-failed` | Unhealthy / restart | 重启前遥测 |
| c11 | `cases/terminating-stuck` | deletionTimestamp + finalizer | 删除前遥测 |

可读答案只存在于不部署的 `catalog.yaml`。集群对象统一使用 `workload`、`traffic-driver` 和
`aiops-case-NN`，不会通过名称、annotation 或 runbook 字段泄露根因。

## OOMKilled 测试点一：单脚本交付

无需手工 port-forward 或 `export` 后端地址。下面一条命令会部署 c08、等待真实
`OOMKilled/137`、自动解析 Pod、采集 Kubernetes/Prometheus/Elasticsearch/DeepFlow/Tempo，
等待 90 秒供后端完成多个抓取/写入周期，并生成五维验收摘要：

```bash
pod-anomaly-cases/scripts/oom-testpoint1.sh run
```

该入口可重复执行：`aiops-case-08` 已存在时不会再次 `apply`，而是复用现有 workload
Pod，确认其已有 `OOMKilled/137` 后直接重新查询并生成一个新的 Case Package。

也可以严格按“异常 namespace + Pod 名称”的输入合同采集已有 Pod：

```bash
pod-anomaly-cases/scripts/oom-testpoint1.sh collect \
  --namespace <namespace> \
  --pod <pod>
```

默认输出不再倾倒整份 JSON，而是通过 `jq` 直接显示 Kubernetes OOM 事实、Prometheus
内存/limit/restart/termination reason、最大内存分配日志、同一 trace ID 对应的 DeepFlow
请求和 Tempo span。最后同时打印原始文件绝对路径和可复制的 `jq` 审查命令。

重复查看已有结果无需重新部署或采集：

```bash
pod-anomaly-cases/scripts/oom-testpoint1.sh view \
  --case cases/<oom-testpoint1-case-id>
```

重点文件：

- `acceptance-summary.json`：PASS/FAIL、OOMKilled/137、restart、内存起始/峰值/limit、各源数量、三源共有 trace ID。
- `evidence/k8s_pod.yaml`：Kubernetes Pod snapshot 和 OOM 决定性事实。
- `evidence/metrics.jsonl`：Prometheus 内存增长、limit、restart 和 termination reason 原始时间序列。
- `evidence/logs.jsonl`：当前 Pod 的 Elasticsearch/Filebeat 日志。
- `evidence/deepflow_l7.jsonl`：目标 Pod IP 的 DeepFlow L7 flow。
- `evidence/tempo_traces.jsonl`：由日志/flow 中真实 trace ID 查询到的 Tempo application span。

脚本会停止自己创建的本地 port-forward，但故意保留异常 namespace 供 AIOps 分析。验收后精确清理：

```bash
pod-anomaly-cases/scripts/oom-testpoint1.sh cleanup
```

## Safe apply

只 apply 聚合目录会创建全部安全资源，但不会自动触发 c11 删除：

```bash
kubectl apply -k pod-anomaly-cases/safe
```

推荐入口会先跑离线校验、apply、精确触发 c11，再等待状态与后端 coverage：

```bash
pod-anomaly-cases/scripts/deploy-safe.sh
```

脚本不会操作 Node、kubelet、hostPath 或集群范围 RBAC，也不会引用 `destructive/`。

## Backend configuration

`config.env` 只供本地验证脚本读取，支持：

- `PROMETHEUS_URL`
- `ELASTICSEARCH_URL`、`ELASTICSEARCH_USERNAME`、`ELASTICSEARCH_PASSWORD`、
  `ELASTICSEARCH_TLS_VERIFY`、`ELASTICSEARCH_CA_CERT`
- `DEEPFLOW_NAMESPACE`、`DEEPFLOW_CLICKHOUSE_SELECTOR`，可选
  `DEEPFLOW_CLICKHOUSE_CONTAINER`
- `TEMPO_URL`
- `OBSERVABILITY_TIMEOUT_SECONDS`

部署镜像和 OTLP endpoint 已在 manifests 中给出同名默认值；如环境不同，应使用本地 Kustomize
patch 修改，不要把凭据放进 manifest。后端为空或不可达会报告 `error`，不会伪装成 `empty`。

当前集群可用以下只读端口转发准备本地验证器连接（分别在独立终端运行）：

```bash
kubectl -n monitor port-forward svc/observability-prometheus 9090:9090
kubectl -n monitor port-forward svc/elasticsearch-master-headless 9200:9200
kubectl -n monitor port-forward deploy/lgtm 3200:3200
```

然后在 `config.env` 设置对应的 `PROMETHEUS_URL`、HTTPS `ELASTICSEARCH_URL` 和
`TEMPO_URL`。Elasticsearch 仍需使用集群授权的用户名、密码和可信 CA；只有连接本机
port-forward 的临时验收可显式设置 `ELASTICSEARCH_TLS_VERIFY=false`。不要把凭据或 CA 私钥
提交到仓库。DeepFlow 默认通过 `kubectl exec` 访问 `monitor` 中
`app.kubernetes.io/name=clickhouse` 的 Pod，无需本地开放 ClickHouse 端口。

## Validation

验收全部案例：

```bash
pod-anomaly-cases/scripts/validate.sh --wait
```

只验收一个案例：

```bash
pod-anomaly-cases/scripts/validate.sh --case c08
```

验证器每轮重新解析当前 workload Pod UID/IP，不把旧 Pod 和新 Pod 数据合并。查询均限制在当前
Pod 创建时间附近至当前时刻，最长一小时；Prometheus 使用精确 namespace/Pod matcher 和案例相关
状态指标，ES 使用 namespace + Pod UID/name + 当前 driver UID + timestamp，DeepFlow 只接受当前
Pod IP 的 `/work` L7 row，Tempo 只查询同时出现在 ES 与 DeepFlow 的真实 trace ID。输出只含
coverage、计数和短样本，不输出密码或完整后端响应。

离线验收：

```bash
python3 -m unittest discover -s pod-anomaly-cases/tests -v
kubectl kustomize pod-anomaly-cases/safe >/dev/null
```

## Live acceptance

2026-08-03 在目标集群从空环境执行了完整 `deploy-safe.sh`、重复
`kubectl apply -k pod-anomaly-cases/safe` 和 `cleanup.sh`：

- c01–c05 的 Kubernetes/Prometheus 为 `present`，Elasticsearch 为 `empty`，
  DeepFlow/Tempo 为 `absent`；这些案例没有运行应用进程。
- c06–c11 的 Kubernetes、Prometheus、Elasticsearch、DeepFlow、Tempo 均为
  `present`；日志和 direct Pod `/work` flow 的共有 trace ID 可在 Tempo 中命中。
- c08 的一次独立复核得到 89 组精确 Pod 指标、20 条当前运行日志、20 条 direct Pod L7
  flow，以及 5/5 共有 trace ID 的 Tempo span。
- 重复 apply 返回成功；c11 只产生“对象正处于删除中”的预期 warning。清理后 11 个目标
  namespace 全部不存在。

AIOps single-case 黑盒请求在约 3.4 分钟内完成，真实执行 Kubernetes、Metrics、Logging、
Tracing 和 Topology 工具。它识别了 c08 的 OOMKilled/137 和 Prometheus、DeepFlow 证据，
但最终报告仍混入集群中既有 `aiops-traced-oom` 的日志和指标。当前应先做 single-case 验收并
人工检查实体 namespace；同时部署 11 个案例可能超过现有模型上下文预算。这是 AIOps 的跨 namespace
聚焦限制，不是案例遥测缺失。本仓不保存黑盒原始响应，也不在此范围修改 Robusta。

## Observability conclusions

结论按“应用进程能否启动”划分，而不是强行要求每个异常都有四种信号：

- c01–c05 在容器启动前失败，因此有真实 Kubernetes status/Event 和 kube-state Prometheus 指标，
  但不会产生应用 stdout、direct Pod L7 flow 或 application span。
- c06–c10 的应用会短暂或持续运行，统一使用 `traffic-driver + traceparent + stdout JSON + OTLP`，
  因而能在异常窗口产生真实指标、日志、DeepFlow flow 和 Tempo span；OOM 不是唯一特殊埋点案例。
- c11 先正常运行并产生遥测，随后因 finalizer 卡在 Terminating。故障本身由 Kubernetes
  `deletionTimestamp + finalizer` 决定性证明；日志、flow 和 span 是删除前的时间关联上下文。
- c04 `CreateContainerConfigError` 是启动前配置错误，没有应用遥测；需要带真实应用错误遥测时使用
  c07 `config-error-traced`，它会返回 HTTP 500、输出 `CONFIG_MISSING` 日志并发送 error span。

这些 manifest 能让信号真实发生，但最终 coverage 仍受 Prometheus scrape 周期、日志/Trace 写入延迟、
后端连通性和保留周期影响。`error` 表示查询失败，`empty/absent` 表示查询成功但没有该实体能力或数据。

### Evidence matrix

| 案例 | Kubernetes | Prometheus | Elasticsearch | DeepFlow | Tempo |
|---|---|---|---|---|---|
| c01–c05 | status/Event present | Pod phase/waiting/reason present | empty | absent | absent |
| c06 | CrashLoop/exit 2 | restart/exit/resource present | 退出前日志 | 退出前 L7 | 退出前 span |
| c07 | CrashLoop/exit 78 | restart/Ready/resource present | CONFIG_MISSING + trace ID | HTTP 500 | error span |
| c08 | OOMKilled/137 | memory 趋势/limit/restart | 分配进度 + trace ID | kill 前 flow | kill 前 span |
| c09 | Ready=False | Ready/resource | 依赖错误 + trace ID | HTTP 503 | error span |
| c10 | Unhealthy/restart | probe/restart/resource | 重启前日志 | 重启前 flow | 重启前 span |
| c11 | deletionTimestamp/finalizer | deletion/phase/resource | 删除前日志 | 删除前 flow | 删除前 span |

## Expected absent signals

`empty` 和 `absent` 是正式证据边界，不是“采集成功”的伪数据：

- c01–c05 没有运行应用进程，ES 应为 `empty`，DeepFlow/Tempo 应为 `absent`。
- 没有 Pod IP 时不能用 Node IP flow 冒充 direct Pod flow。
- OOM 的最后一次请求可能在 span 导出前被 kill，但至少一个 kill 前请求应有完整关联。
- 后端连接失败始终是 `error`；只有真实查询返回零条或实体能力不存在才是 `empty/absent`。

## Cleanup

统一清理只操作 catalog 中的 11 个精确 namespace，并先释放 c11 的精确 Pod finalizer：

```bash
pod-anomaly-cases/scripts/cleanup.sh
```

脚本可重复执行，不使用 namespace 通配符、不删除 Node，也不执行 `delete --all`。

## AIOps black-box

不要在提问里给出 case 名或预期根因。可以使用：

```text
请检查 aiops-case-08 当前有什么问题，并说明不同可观测性来源各自支持了什么结论。
当前集群有什么异常？请根据真实证据分析，不要把 runbook 当成证据。
```

验收 AIOps 是否自主定位异常、执行通用 MCP 查询、按结果补证、区分 flow 与 application span，
并诚实表达控制面案例的日志/trace 缺失。

## Destructive separation

NodeLost 和真实节点压力 Evicted 位于 `destructive/`，不在 safe bundle 中。目录只包含低资源候选
Pod 和人工 runbook；停止 kubelet、隔离网络或施加节点压力必须由集群所有者在专用节点手工确认、
触发和恢复。本仓库不提供自动节点故障注入器。
