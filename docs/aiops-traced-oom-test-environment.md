# AIOps Traced OOM 测试环境

## 目标

该环境用于验证 Robusta Agent 能否围绕一个真实 OOMKilled Pod，实时获取并关联：

- Kubernetes 状态：`lastState.reason=OOMKilled`、`exitCode=137`、重启次数、Pod IP、Node。
- Metrics：Prometheus 中目标业务容器的内存趋势、峰值、limit 和峰值占比。
- Logging：目标服务在 OOM 前输出的 `trace_id`、`span_id`、`allocated_mib` 原始日志。
- Tracing：DeepFlow 捕获的真实 HTTP L7 flow，以及 LGTM/Tempo 中对应的 OTLP span。
- Topology：Deployment、ReplicaSet、Pod、Service、Node 和 DeepFlow peer 之间的关系。

生产运行时不依赖 `data` 项目。测试 YAML、脚本和说明均在 Robusta 项目内。

## 场景结构

```text
trace-oom-driver Deployment
  -> W3C traceparent
  -> Service trace-oom-api
  -> trace-oom-api Deployment /allocate?mib=2
     -> 输出 trace_id/span_id/allocated_mib 日志
     -> 向 lgtm.xnet.svc:4318/v1/traces 上报 OTLP span
     -> 每次真实分配 2Mi 内存
     -> 达到 80Mi cgroup limit 后 OOMKilled

DeepFlow agent
  -> 从真实 HTTP 流量采集 L7 flow
```

`trace-oom-driver` 是健康的请求驱动器；唯一预期异常的业务工作负载是 `trace-oom-api`。

## 一键部署

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
./scripts/aiops-traced-oom.sh apply
```

脚本会等待 Deployment 可用，并继续等待 Kubernetes 首次记录真实 `OOMKilled`。

## 状态和日志

```bash
./scripts/aiops-traced-oom.sh status
./scripts/aiops-traced-oom.sh logs
./scripts/aiops-traced-oom.sh verify
```

`verify` 至少检查：

- `lastState.reason=OOMKilled`
- `lastState.exitCode=137`
- previous logs 中存在 `event=allocate`
- previous logs 中存在 `trace_id`、`span_id`、`allocated_mib`
- driver 日志中存在 `traceparent`
- Service Endpoints 中存在目标 Pod 关联；Pod 正处于 CrashLoopBackOff 时可能位于 `notReadyAddresses`

## 手工部署

```bash
kubectl apply -f testcases/aiops-traced-oom.yaml
kubectl rollout status deployment/trace-oom-api -n aiops-traced-oom --timeout=120s
kubectl rollout status deployment/trace-oom-driver -n aiops-traced-oom --timeout=120s
kubectl get pod -n aiops-traced-oom -w
```

查询目标 Pod：

```bash
POD=$(kubectl get pod -n aiops-traced-oom -l app=trace-oom-api -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod "$POD" -n aiops-traced-oom
kubectl logs "$POD" -n aiops-traced-oom -c business-api --previous --tail=100
```

## Agent 实时采集入口

异常 Pod 名称确定后，Agent 可自主选择：

```text
collect_aiops_case(
  namespace="aiops-traced-oom",
  pod="<trace-oom-api Pod name>",
  scenario="auto",
  window_minutes=30
)
```

首屏结果中的 `dimension_details` 应直接包含指标值、日志原文、flow/span 和拓扑边。只有首屏缺少关键字段时，再按 `recommended_refs_by_dimension` 调用 `get_aiops_case_evidence`。

## 清理

```bash
./scripts/aiops-traced-oom.sh cleanup
```

## 是否必须埋点

不一定，但要区分两类 tracing：

- DeepFlow 网络可观测：应用不埋点，只要存在 DeepFlow 支持协议的真实网络流量，通常仍可采集 L4/L7 flow、端点、响应码和时延。
- 稳定的分布式 Trace：若要获得跨服务一致的 `trace_id`、父子 span、业务属性和 Tempo span 树，应用需要手工埋点、OpenTelemetry 自动埋点或其他可传播并导出 trace context 的机制。

因此，普通未埋点应用仍可能有 DeepFlow flow，但通常不能保证得到完整、稳定、带业务语义的分布式 span。本测试同时保留两条链路：DeepFlow 是真实网络 flow 来源，OTLP/Tempo 用于验证应用级 span 和业务属性。
