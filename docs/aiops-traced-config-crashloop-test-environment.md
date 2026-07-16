# AIOps Traced Config CrashLoopBackOff 测试环境

## 目标

该环境用于验证 Robusta Agent 面对一个与 OOM 无关的常见异常 Pod 时，能否仅根据
`namespace + pod` 实时获取并关联：

- Kubernetes：`CrashLoopBackOff`、上一轮 `reason=Error`、`exitCode=78`、重启次数。
- Metrics：Prometheus 中目标容器的 restart、last terminated reason、phase 和内存背景值。
- Logging：业务 API 的配置缺失、HTTP 500、完整 trace ID 和 fatal exit 日志。
- Tracing：DeepFlow 的真实 HTTP L7 flow，以及 LGTM/Tempo 中对应的错误 span。
- Topology：Driver Pod、Service、目标 Pod、ReplicaSet、Deployment、Node 和 Pod IP。

生产运行时不依赖 `data` 项目。

## 故障链

```text
trace-config-driver
  -> traceparent
  -> Service trace-config-api
  -> GET /checkout
  -> PAYMENT_GATEWAY_TOKEN 缺失
  -> HTTP 500 + config_missing 日志 + Tempo error span
  -> 连续失败三次
  -> 进程 exit 78
  -> Kubernetes 重启
  -> CrashLoopBackOff
```

退出码 `78` 表示应用配置错误，本场景不会制造内存增长，也不会触发 OOMKilled。

## 一键部署

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
./scripts/aiops-traced-config-crashloop.sh apply
```

脚本会等待目标 Pod 真实进入：

```text
current_reason=CrashLoopBackOff
last_reason=Error
last_exit=78
```

## 查看和验证

```bash
./scripts/aiops-traced-config-crashloop.sh status
./scripts/aiops-traced-config-crashloop.sh logs
./scripts/aiops-traced-config-crashloop.sh verify
```

手工查看目标 Pod：

```bash
POD=$(kubectl get pod -n aiops-traced-config -l app=trace-config-api \
  -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod "$POD" -n aiops-traced-config
kubectl logs "$POD" -n aiops-traced-config -c business-api --previous --tail=120
```

## Agent 实时采集入口

```text
collect_aiops_case(
  namespace="aiops-traced-config",
  pod="<trace-config-api Pod name>",
  scenario="auto",
  window_minutes=30
)
```

Agent 不应从 Pod 名猜测故障类型。有效结论必须引用 `dimension_details` 中的
Kubernetes 终止状态、配置错误日志、HTTP 500 flow/span 和拓扑关系。

## 清理

```bash
./scripts/aiops-traced-config-crashloop.sh cleanup
```
