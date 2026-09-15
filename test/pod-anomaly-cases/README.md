# Pod 异常与可观测性实验库

为 AIOps 提供可复现的异常 Pod。基础 c01–c11 提供 Kubernetes 故障及可用的真实遥测；17 个[变体](variants/README.md)用于区分同症状的不同原因。正式计分、后台运行和断点续跑见[质量测试](../aiops_quality_e2e/README.md)。

## 前置条件

仅用于专用测试集群。执行者需要管理测试 namespace 的权限，部分验证需要对已有 Pod 执行 `pods/exec`。不要在 `aiops-case-01`～`aiops-case-11`、`aiops-case-v01`～`aiops-case-v17` 中存放业务资源。

- `kubectl`、Python 3；质量测试另需项目虚拟环境依赖。
- 节点能拉取清单镜像，基础应用默认使用 `xnet.registry.io:8443/observability/python:3-alpine`。
- 遥测验收需要 kube-state-metrics/cAdvisor、Prometheus、Filebeat/Elasticsearch、DeepFlow 和 Tempo。
- c05 需要 Multus 和 NetworkAttachmentDefinition CRD；案例仅引用缺失的 namespace 内 secondary network，不修改节点 CNI。
- 基础应用默认向 `http://lgtm.monitor.svc:4318/v1/traces` 导出 span；环境不同须修改相应清单。

## 部署、验证和清理

以下命令从仓库根目录执行：

```bash
kubectl config current-context
make case-list
make case-list-variants
make case-render CASE=c08
make case-deploy CASE=c08
make case-validate CASE=c08
make case-ask CASE=c08
make case-clean CASE=c08
```

`case-ask` 对指定 namespace 定向提问，调用已部署的 AIOps；不是盲测评分入口。盲测使用质量脚本。

基础 Case 的 `case-validate` 复用状态与遥测验收器；变体只校验状态和具体原因，不能把两者的通过含义混为一谈。

基础案例也可以直接部署并验收：

```bash
kubectl apply -k test/pod-anomaly-cases/cases/oomkilled-traced
test/pod-anomaly-cases/scripts/validate.sh --case c08 --wait
```

c11 需要先产生请求遥测再删除，单独 apply 不会自动形成 Terminating：

```bash
kubectl apply -k test/pod-anomaly-cases/cases/terminating-stuck
kubectl -n aiops-case-11 wait --for=condition=Ready pod/workload --timeout=180s
kubectl -n aiops-case-11 logs pod/workload --tail=20
# 确认至少一条 event=http_request 后再执行
kubectl -n aiops-case-11 delete pod workload --wait=false
test/pod-anomaly-cases/scripts/validate.sh --case c11 --wait
```

批量入口的范围不同：

| 命令 | 行为 |
|---|---|
| `make case-deploy-errors` | 部署 c01–c11 并触发 c11 删除，不验收遥测 |
| `make case-deploy-all` | 部署 c01–c11、触发 c11 并等待状态及遥测验收 |
| `make case-clean` | 清理基础 11 个 namespace，先释放 c11 测试 finalizer |
| `make case-clean-variants` | 清理变体 namespace；核对所有权后操作 |
| `make case-clean CASE=c03-secret` | 仅清理指定案例 |

清理会删除对应 namespace 内的资源。变体重复部署前先清理；不要通过强制删除未知对象或清除未知 finalizer 绕过失败。

## 基础场景

| ID | 目录 | 目标故障 |
|---|---|---|
| c01 | `cases/pending-unschedulable` | nodeSelector 不匹配 |
| c02 | `cases/imagepull-failed` | 无效镜像仓库域名 |
| c03 | `cases/volume-mount-failed` | 卷引用缺失 ConfigMap |
| c04 | `cases/createcontainer-config-error` | Secret 环境变量 key 缺失 |
| c05 | `cases/sandbox-create-failed` | Multus secondary network 缺失 |
| c06 | `cases/crashloop-runtime` | 应用退出 2 |
| c07 | `cases/config-error-traced` | CONFIG_MISSING，HTTP 500 后退出 78 |
| c08 | `cases/oomkilled-traced` | 内存增长触发 OOMKilled |
| c09 | `cases/readiness-probe-failed` | Readiness 失败，Ready=False |
| c10 | `cases/liveness-probe-failed` | Liveness 失败触发重启 |
| c11 | `cases/terminating-stuck` | deletionTimestamp + finalizer 阻塞删除 |

`catalog.yaml` 记录验收规则，不部署到集群；对象使用通用名称，不通过根因名称提示 Agent。变体详见[对应表与环境限制](variants/README.md)。

## 遥测如何产生

运行态案例复用 ConfigMap 中的 Python 应用与 traffic-driver：

```text
traffic-driver → workload /work + traceparent
                     ├─ stdout JSON → Filebeat → Elasticsearch
                     ├─ Pod/容器状态和资源 → Prometheus
                     ├─ L7 flow → DeepFlow
                     └─ OTLP span → collector → Tempo
```

日志、flow 和 span 用真实 trace ID 关联；指标按 namespace、Pod 和时间窗关联。Flow 不等于 application span，业务接口正常也不能证明健康探针正常。

| 场景 | Kubernetes / Metrics | Logging / Tracing |
|---|---|---|
| c01–c05 | 调度、等待原因和事件 | 应用未启动，不应要求应用日志或 span |
| c06–c10 | 重启、退出、Ready、资源等 | 应用退出前或运行中的真实遥测 |
| c11 | 删除时间与 finalizer | 删除前的关联上下文，不单独证明删除阻塞 |
| 新增变体 | 状态与具体原因验收 | 简单容器未统一生成业务 span，不能保证三维齐全 |

后端报错是 `error`；真实查询无匹配是 `empty`，实体不具备信号能力可能是 `absent`，不能把它们混为成功采集。没有 Pod IP 时，不能用 Node IP flow 冒充 Pod 流量。

## 后端连接与验收

配置仅供本地验证器使用，不是 Agent 配置：

```bash
cp test/pod-anomaly-cases/config.env.example test/pod-anomaly-cases/config.env
```

支持 `PROMETHEUS_URL`、`ELASTICSEARCH_URL` 及其用户名/密码/CA、`TEMPO_URL`、`DEEPFLOW_NAMESPACE`、`DEEPFLOW_CLICKHOUSE_SELECTOR`、可选容器和超时。按实际环境填写；不要提交凭据或 CA 私钥。DeepFlow 验证通过已有 ClickHouse Pod 的 exec 读取，无需创建额外查询 Pod。

必要时可在独立终端转发已有服务：

```bash
kubectl -n monitor port-forward svc/observability-prometheus 9090:9090
kubectl -n monitor port-forward svc/elasticsearch-master-headless 9200:9200
kubectl -n monitor port-forward deploy/lgtm 3200:3200
```

地址、协议、凭据和可信 CA 必须与实际服务一致，不能因为使用 port-forward 就省略认证。

基础验证器重新解析当前 workload UID/IP，限制时间窗及查询范围；ES/DeepFlow 的真实 trace ID 用于 Tempo 查询。验收通过只代表当时注入和遥测条件满足，不保证 Agent 理解正确，也不代表今后后端一直可用。

OOM 专项入口保留用于采集原始证据：

```bash
test/pod-anomaly-cases/scripts/oom-testpoint1.sh run
test/pod-anomaly-cases/scripts/oom-testpoint1.sh collect --namespace <namespace> --pod <pod>
test/pod-anomaly-cases/scripts/oom-testpoint1.sh view --case cases/<case-id>
test/pod-anomaly-cases/scripts/oom-testpoint1.sh cleanup
```

`run` 部署或复用 c08，保存 Kubernetes、指标、日志、flow 和 span 及 `acceptance-summary.json`；结束后停止自己的本地 port-forward，但保留故障供诊断，需显式 cleanup。

离线检查不向集群部署：

```bash
python3 -m unittest discover -s test/pod-anomaly-cases/tests -v
kubectl kustomize test/pod-anomaly-cases/safe >/dev/null
```

## Agent 与实验库的边界

Agent 的 `execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`、`query_pod_topology` 查询真实环境；实验库验收器不作为 Agent 的诊断捷径。具体调用能力以 MCP 服务版本为准，不从本目录推断当前服务的权限或提示词。

历史单次验收只代表对应运行，不能用来声明当前服务跨 namespace 诊断已经通过。正式比较请使用固定配置和归档报告，低分结合原文人工复核。

## 节点级场景

[destructive/](destructive/README.md) 中 NodeLost、节点压力 Evicted 仅有候选 Pod 和人工安全指引，不属于 safe 批量入口。必须由集群所有者在专用节点确认影响范围、停止条件和恢复通道；本库不自动停止 kubelet、隔离网络或制造节点压力。
