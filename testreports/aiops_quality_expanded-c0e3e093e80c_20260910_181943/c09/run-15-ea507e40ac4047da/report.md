## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用服务依赖不可用导致健康检查持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态：`Running`，`ContainersReady`=`False` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 确认应用容器处于存活但不健康的状态 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (3m16s 内连续 727 次) | 证实业务服务（应用）内部逻辑异常，拒绝正常流量 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: dial tcp 172.16.104.16:8080: connect: connection refused (38m 前首次) | 证实异常始于应用未就绪或端口不可达，持续至今 |
| 4 | Logging | Elasticsearch | 日志模式：`dependency unavailable` (HTTP 503, 路径 `/work`)，连续 8 次 (01:11:11 至 01:11:39)，涉及 8 个不同 trace_id | 证实应用持续抛出 503 错误，且依赖不可用是导致服务返回 503 的直接原因 |
| 5 | Tracing | Tempo | 服务 `aiops-lab-workload` 的 `GET /work` Span 返回 503，模式 `readiness_fail`，Span 持续时间约 3 微秒 (01:08:10) | 验证了快速失败的错误链路，确认是应用层主动拒绝而非连接超时 |
| 6 | Tracing | Deepflow | 9 次 HTTP `/work` 请求均返回 503，请求 IP `172.16.104.16`，持续时间 15.1ms-28.4ms | 从网络层视角确认了目标 Pod IP 持续处理并返回 503 错误 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 排除因 OOMKilled/CrashLoopBackOff 等容器崩溃重启导致的服务不健康 |

**证据印证说明：**
*   K8s Event (证据 2, 3) 与 Trace/Log 数据 (证据 4, 5, 6) 共同锁定了 503 错误的业务根因：应用依赖不可用 (`dependency unavailable`)，导致探针持续失败。
*   Metric 数据 (证据 7) 排除了容器自身崩溃的可能，印证了 `Running` 但 `NotReady` 的状态是应用逻辑层面的问题。
*   日志中的 8 个不同 trace_id 与 Deepflow 中的 9 次 Flow 存在重叠，证实了 503 错误在短期内以一定频率持续发生，属于系统性故障而非瞬时抖动。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务依赖不可用 → 内部抛出 503 拒绝服务 (Dependency unavailable) → 就绪探针 (Readiness Probe) 持续返回 503 → Pod 状态 NotReady / ContainersNotReady
```

### 根因结论

已确认根因为**应用服务依赖不可用**。该故障导致应用服务在 `/work` 路径上持续返回 HTTP 503 错误。Kubernetes 的健康检查机制捕获到这一持续失败（探针状态码 503 及早期连接拒绝），判定应用不健康，从而将 Pod 状态更新为 `NotReady`。日志中大量的 `dependency unavailable` 模式明确指出了上游依赖故障是应用返回 503 的直接诱因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 19.0s
├─ 并发证据采集: 88.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 88.6s (Evidence 82.6s, RCA 5.8s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
