## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc in namespace aiops-case-09 is NotReady (READY 0/1) due to persistent Readiness probe failures (HTTP 503). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady: False`, `Ready: False`, reason: `ContainersNotReady`, message: `containers with unready status: [app]` (fact-1113d081de0c) | 确认容器虽在运行但未满足就绪条件。 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy`, `Readiness probe failed: HTTP probe failed with statuscode: 503`, 发生频率: `x1558 over 77m` (fact-0b19defbab1f) | 直接指示探测失败的原因及持续时间。 |
| 3 | K8s State | kubernetes | `pod.phase: Running`, `status: Running`, `restart_count: 0` (fact-6f975045477b) | 确认故障发生于就绪态而非重启态，排除容器崩溃。 |
| 4 | Logging | elasticsearch | Pattern: `dependency unavailable`, `http_status: 503`, `path: /work`, `service: aiops-lab-workload`, 时间窗: `01:49:56.254Z` 至 `01:50:24.395Z` (fact-1d4801fb7348) | 提供应用层报错的具体信息，解释了 503 的来源。 |
| 5 | Tracing | deepflow (L7 Flow) | `GET /work`, `response_code: 503`, `duration_us: min 17717, max 29001`, src_ip: `172.16.104.62`, dst_ip: `172.16.104.16` (fact-0ad8c440336d) | 独立确认对目标 Pod 的 `/work` 端点的流量请求确实返回了 503。 |
| 6 | Tracing | tempo (Span) | `aiops.observed_mode: readiness_fail`, `http.response.status_code: 503`, `http.route: /work`, trace_id: `3cfa8efe6e08de7a7e38cde3bae0f417` (fact-1268c99df0a8) | 关联了具体的 Trace ID，印证了 L7 Flow 和日志中的 503 响应。 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0`, `kube_pod_status_phase: Running (1)` (fact-81cd13cde825) | 确认容器未发生过重启，Pod 处于运行中。 |

**证据关联说明**：
1. Kubernetes 事件（#2）与 Deepflow Flow（#5）从控制面与网络流两个维度独立证实了 `/work` 端点返回 503 的状态。
2. Tempo Span（#6）通过 trace_id 将日志（#4）与 L7 Flow（#5）中的异常流量关联起来，证明 503 是由应用内部逻辑返回的。
3. Kubernetes 状态（#1, #3）与指标（#7）排除了容器崩溃重启的可能，锁定故障点为应用层服务不可用导致 Readiness Probe 持续失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑遭遇 "dependency unavailable" (fact-1d4801fb7348) → HTTP GET /work 端点返回 503 状态码 (fact-0ad8c440336d) → kubelet Readiness probe 持续检测失败 (fact-0b19defbab1f) → Pod Ready 条件置为 False，状态 NotReady (fact-1113d081de0c)
```

### 根因结论

已确认根因为**应用健康检查端点（`/work`）因依赖不可用而返回 HTTP 503 错误**。

该应用逻辑错误导致 kubelet 的 Readiness Probe 反复探测失败（`fact-0b19defbab1f`），尽管容器进程仍在正常运行（`fact-6f975045477b`），但 Pod 无法进入 `Ready` 状态，从而导致服务不可见或无法接收流量。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 14.2s
├─ 并发证据采集: 87.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 87.9s (Evidence 78.5s, RCA 9.3s)
└─ 汇总总结: 14.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
