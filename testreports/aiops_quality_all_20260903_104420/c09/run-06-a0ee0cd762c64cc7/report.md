## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用服务依赖的上游服务不可用 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 状态 `Running`，但 `Ready=False`，Reason: `ContainersNotReady`，Message: `containers with unready status: [app]` | 定义故障现象：Pod 存活但应用不可用 |
| 2 | K8s Event | Kubernetes | `containers with unready status: [app]` | 确认 `app` 容器是触发 Ready 失败的主体 |
| 3 | Logging | Elasticsearch | 出现 8 次 `http_request` 错误：`service="aiops-lab-workload"`, `path="/work"`, `http_status=503`, `message="dependency unavailable"` (Trace IDs: `e1b909...`, `339759...`, `d8fc9a...` 等) | 证明应用正在主动抛出依赖服务不可用错误 |
| 4 | Tracing | Deepflow | HTTP GET /work 的 L7 Flow 统计：10 次请求中 3 次返回 503，`src_ip=172.16.104.19`, `dst_ip=172.16.104.26` (Trace ID: `d882babe0b383bda1a35dd7116d979a4` 存在) | 从网络流层面确认对外返回 503 状态码，与日志一致 |
| 5 | Tracing | Tempo | 单个 Span `GET /work` 返回 `503`，`trace_id="d882babe0b383bda1a35dd7116d979a4"`，耗时极短 (3ms) | 确认单个请求快速失败，无重试迹象，故障发生在当前层级 |
| 6 | Metric | Prometheus | `kube_pod_container_status_running{container="app"}=1`, `kube_pod_container_status_restarts_total{container="app"}=0` | 排除容器崩溃 (OOM/CrashLoop) 导致的重启 |
| 7 | K8s Config | Kubernetes | 容器 `app` 配置：`resource_limit.cpu=200m`, `resource_limit.memory=96Mi`, `resource_request.memory=24Mi` | 排除因资源限制导致容器被杀 (Kill) 的可能 |

**证据逻辑总结：**
1. Pod 处于 `Running` 状态且无重启记录 (事实 6, 7)，排除了容器自身的崩溃或资源耗尽问题。
2. 日志 (事实 3) 和追踪 (事实 4, 5) 均显示应用在 `/work` 端点主动返回 `503` 并伴随 `dependency unavailable` 消息，证明应用逻辑已执行但调用外部依赖失败。
3. 这种“快速返回 503 且伴随明确错误消息”的现象，与上游依赖不可用（如连接超时、DNS 失败或被拒绝）的特征完全一致。

## 🎯 根因分析 · g1

### 因果链
```text
上游服务不可用（未验证具体原因，如网络/依赖方故障） → 应用调用上游依赖获取数据失败 → 应用按逻辑返回 503 "dependency unavailable" → Pod Readiness Probe 检查未通过（Ready=False），应用对外不可用
```

### 根因结论
- **已确认的根因**：**应用服务依赖的上游服务不可用**。
  证据编号：Logging (事实 3) 明确报告 `dependency unavailable`；Tracing (事实 4, 5) 和 K8s State (事实 1) 确认了由此导致的 503 响应和 Readiness 失败。
- **缺失的决定性事实**：虽然现象指向依赖不可用，但输入事实中未提供 `aiops-lab-workload` 的下游调用拓扑（如调用了哪个 Service/Endpoint），也未提供上游服务的状态日志或连接错误详情（如 `Connection Refused`、`Timeout` 或 `DNS resolution failure`）。因此，无法精确定位是哪个具体的上游服务或网络策略导致了不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 24.6s
├─ 并发证据采集: 71.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 71.0s (Evidence 64.8s, RCA 6.0s)
└─ 汇总总结: 14.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
