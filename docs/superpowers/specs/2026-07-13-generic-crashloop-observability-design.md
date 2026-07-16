# 通用 CrashLoopBackOff 可观测性验证设计

## 目标

新增一个与 OOM 无关、但属于常见 Pod 异常状态的真实测试场景，用于验证现有
`namespace + pod + scenario=auto` 采集和 Robusta 诊断链路是否具备通用性。

## 场景

测试业务 API 缺少必需配置 `PAYMENT_GATEWAY_TOKEN`。API 启动后可以短暂接收
`/checkout` 请求，但每次请求都：

- 返回 HTTP 500；
- 输出包含 `trace_id`、`span_id`、错误码和缺失配置名的结构化日志；
- 向现有 LGTM/Tempo OTLP HTTP 入口上报错误 span；
- 连续失败三次后以退出码 `78` 退出。

Kubernetes 重启容器后，目标 Pod 最终进入常见的 `CrashLoopBackOff`，其上一轮状态为
`reason=Error`、`exitCode=78`。独立 Driver Pod 持续通过 Service 发起真实 HTTP 请求，
DeepFlow 可采集真实 L7 流量和调用端点。

## 数据链路

```text
trace-config-driver Pod
  -> traceparent
  -> trace-config-api Service
  -> trace-config-api Pod /checkout
     -> HTTP 500
     -> structured error log
     -> OTLP error span -> lgtm.xnet.svc:4318
     -> exit 78
     -> CrashLoopBackOff

DeepFlow
  -> Driver Pod 到 API Pod 的真实 L7 flow

Prometheus
  -> restart、last terminated reason、phase、memory working set
```

## 输入边界

Agent 和 MCP 只接收：

```text
namespace=aiops-traced-config
pod=<实际生成的 trace-config-api Pod 名称>
scenario=auto
window_minutes=30
```

不向 Agent 提供 `ConfigError`、缺失配置名、退出码或预期根因。

## 拓扑要求

至少应生成以下有证据来源的关系：

- Driver Pod `calls` API Pod；
- Service `selects` API Pod；
- Pod `owned_by` ReplicaSet；
- ReplicaSet `owned_by` Deployment；
- Pod `scheduled_on` Node；
- Pod `assigned_to` Pod IP。

无法解析为 Kubernetes 实体的 DeepFlow peer 只能作为
`communicates_with / related_context / weak`，不得升级为因果边。

## 验收标准

1. 目标 Pod 真实进入 `CrashLoopBackOff`，上一轮 `reason=Error`、`exitCode=78`。
2. previous logs 包含真实 `config_missing`、`PAYMENT_GATEWAY_TOKEN`、完整 trace ID。
3. Prometheus 返回目标 Pod 的 restart 和 last terminated reason，内存只作为背景数据。
4. DeepFlow 返回目标 Pod 相关的真实请求、响应码、端点和 flow trace ID。
5. Tempo 返回日志 trace ID 对应的错误 span及 `http.response.status_code=500`。
6. topology 包含真实 Kubernetes 关系和 Driver 到 API 的直接调用边。
7. Robusta 自主选择实时 MCP 工具，并在报告中引用原始值和 evidence refs。
8. 报告不得声称 OOM、内存泄漏或生成与事实不符的 `MEMORY_PATTERN`。

## 改动边界

第一阶段只新增 testcase YAML、部署验证脚本、文档和静态契约测试。真实运行暴露通用
缺陷后，才对 MCP 或 Robusta 做最小修复；不改现有 OOM 场景，不依赖 `data` 项目。
