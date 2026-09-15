## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc 处于 NotReady 状态，且持续返回 HTTP 503 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (事件触发 1350 次) | 直接触发 Pod 状态变更的持续检测失败原因 |
| 2 | K8s State | kubernetes | ContainersReady/Ready: False (原因: ContainersNotReady: [app]) | 确认 Pod 整体处于 NotReady 状态，且非 Pod 调度/镜像拉取问题 |
| 3 | Logging | elasticsearch | 聚合日志：error level, "dependency unavailable", path: "/work", http_status: 503 (时间窗 01:42:36 - 01:43:14) | 证实应用层在处理 `/work` 请求时因依赖问题主动返回 503 |
| 4 | Tracing | deepflow | L7 Flow: src_ip 172.16.104.62 -> dst_ip 172.16.104.16, HTTP GET /work, 响应 503 (重复 9 次) | 网络层面确认了请求路由至 Pod IP 后返回了 503 响应 |
| 5 | Tracing | tempo | Span: GET /work, status: 503, trace_id: 3cfa8efe6e08de7a7e38cde3bae0f417 | 与 DeepFlow 事实及日志模式中的 trace_id 一致，跨维度验证了具体的失败调用 |
| 6 | K8s State | kubernetes | Pod Restart Count: 0 | 排除因应用 CrashLoopBackOff 或资源越限（OOMKilled）导致的重启故障 |

证据分析：
*   **现象与机制一致**：K8s Event 显示探针因 HTTP 503 失败，Logging 和 Tracing 证实了应用在处理 `/work` 端点时返回了 503 且原因为 "dependency unavailable"。
*   **跨系统关联**：Logging 中的 8 个事实与 Tracing 中的 Flow/Span 共享相同的 trace_id 模式（例如 `3cfa8efe6e08de7a7e38cde3bae0f417` 同时出现在 Tempo Span 和 DeepFlow Flow 中），证明了应用层日志与网络流量层面的直接因果关联。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用服务 /work 端点处理失败并返回 HTTP 503 → Readiness 探针连续 1350 次检测失败 → Pod 状态变为 NotReady
```

### 根因结论

已确认的根因是**应用服务依赖的下游资源不可用**，导致应用在处理请求时抛出 503 错误。

*   **证据支撑**：Kubernetes 事件（#1）明确指出 Readiness Probe 失败是因为 HTTP 503；Logging（#3）进一步揭示了 503 的具体业务原因为 "dependency unavailable"；Tracing（#4, #5）从网络层面确认了该特定请求路径确实返回了 503。
*   **当前未知**：虽然确认是“下游依赖”导致的问题，但日志和追踪数据中未明确具体的**下游依赖服务名称**，也未提供该依赖本身的健康状态或连通性证据，因此无法精确定位是哪一个具体外部系统或微服务导致了本次故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 13.8s
├─ 并发证据采集: 76.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 76.4s (Evidence 62.6s, RCA 13.6s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
