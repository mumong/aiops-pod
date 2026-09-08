## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 status is NotReady due to persistent Readiness probe failures |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `Ready: False` (reason: ContainersNotReady) | 确认 Pod 处于 NotReady 状态，应用容器未通过就绪检查 |
| 2 | K8s Event | Kubelet Readiness Probe | `Warning Unhealthy ... Readiness probe failed: HTTP probe failed with statuscode: 503` (重复 2701 次) | 直接证据：Readiness Probe 持续收到 503 响应导致 Pod 标记为不可用 |
| 3 | Logging | Elasticsearch | 聚合日志模式：`event: http_request, level: error, message: "dependency unavailable", http_status: 503, path: /work` (8次) | 应用侧日志证实业务逻辑返回 503 并报错“dependency unavailable” |
| 4 | Tracing | Tempo Span | HTTP GET /work 返回 503 (trace_id: `e77006b742996fbf78da7f4fe484c8dd`) | 链路追踪确认该请求在应用层失败，而非网络层面 |
| 5 | Metric | Prometheus (Memory) | `container_memory_usage_bytes`: 15.8 MiB (16560128 bytes) | 排除应用内存耗尽或 OOM 导致崩溃/无响应的可能性 |
| 6 | Metric | Prometheus (CPU) | `container_cpu_usage_seconds_total`: 21.04s (总量) | 排除应用 CPU 资源耗尽导致请求处理超时的可能性 |

**证据互证说明**：
Pod 的 `Readiness` 条件为 `False`（证据 1），这与 `kubelet` 报告的 Readiness Probe 频繁失败（证据 2）完全一致。日志（证据 3）和链路追踪（证据 4）共同证实 503 错误发生在应用内部逻辑层（提示“dependency unavailable”），而非网络连通性问题。同时，资源指标（证据 5, 6）显示内存和 CPU 均处于合理低位，排除了资源短缺引发的服务不可用。

## 🎯 根因分析 · g1

### 因果链

```text
依赖服务不可用 → 应用健康检查端点 /ready 返回 HTTP 503 → Kubelet 探测连续失败 → Pod 状态转为 NotReady
```

### 根因结论

**已确认的根因**：
应用容器的工作进程（app）因依赖项不可用（"dependency unavailable"），导致其 Readiness 检查端点（推测为 `/ready`）持续返回 HTTP 503 错误，致使 `kubelet` 无法判定应用已就绪。

**证据支持**：
- Kubelet 事件明确记录了 Readiness Probe 失败并返回 503（证据 2）。
- 应用日志和 Trace 数据在应用内部层面捕获了具体的 503 错误及 "dependency unavailable" 文本（证据 3, 4）。
- 资源监控显示应用未发生 OOM 或 CPU 过载（证据 5, 6），佐证了 503 是由业务逻辑引发的。

**缺失的决定性事实**：
输入中的诊断状态 `unknowns` 明确标注缺少“不可用依赖的具体名称/状态”以及“该依赖故障的根本原因”。当前事实仅证明了“应用因依赖不可用而拒绝服务”，但无法确认外部依赖（如数据库、缓存或其他微服务）的具体故障源。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.3s
├─ 并发证据采集: 72.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 72.2s (Evidence 62.1s, RCA 9.9s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
