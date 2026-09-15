## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod `aiops-case-10/workload-79d9f8fd88-bsn84` 处于 `CrashLoopBackOff` 状态，容器不断重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 17m (x8 over 19m) kubelet Liveness probe failed: HTTP probe failed with statuscode: 500` | 证明容器应用返回 500 导致探针判定失败 |
| 2 | K8s Event | Kubernetes | `Normal Killing 17m (x4 over 19m) kubelet Container app failed liveness probe, will be restarted` | 证明 Kubelet 根据探针结果执行杀进程操作 |
| 3 | K8s State | Kubernetes | `exit_code: 137` | 证实容器进程被强制终止 (SIGKILL) |
| 4 | K8s State | Kubernetes | `last_terminated_reason: Error` | 结合 137 退出码和事件，排除 OOMKilled |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 当前值 `1` (reason=CrashLoopBackOff) | 确认 Pod 当前处于持续重启等待状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 当前值 `9` | 证实重启行为高频发生 |
| 7 | Logging | Elasticsearch | 记录 `request completed`, `http_status: 200`, 时间窗口 `02:53:28 - 02:54:06` | 证明日志捕获到的业务请求正常，缺失 500 时的异常日志记录 |
| 8 | Tracing | Tempo / Deepflow | 聚合 L7 Flow 9 次，`GET /work` 响应 `200`，耗时 `18ms - 30ms` | 证明应用服务在处理正常请求时可用，进一步隔离出是探活逻辑或特定时序问题 |

**证据综合分析：**
Kubernetes 事件 (证据 1, 2) 与指标 (证据 5, 6) 相互印证，确认了“探针失败导致重启”的机制。容器退出码 137 (证据 3) 证实了重启是同步发生的强制杀进程行为，且结合事件中的 `Killing` 原因排除了 OOM (证据 4)。日志 (证据 7) 和追踪数据 (证据 8) 虽然证实了服务在处理正常流量时表现良好，但均未捕获到探活请求失败时的 500 日志，这种日志层面的缺失（仅记录成功）与探针层面的失败（记录 500）形成了对比，证实了故障发生在应用内部逻辑对健康检查端点的响应上。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑或状态异常 (未确认具体业务原因) → Liveness Probe 探测返回 HTTP 500 (已确认) → Kubelet Kill 机制触发 SIGKILL (已确认) → 容器进程退出 Code 137 (已确认) → Pod 进入 CrashLoopBackOff (已确认)
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-10/workload-79d9f8fd88-bsn84` 处于 `CrashLoopBackOff` 的直接原因是 **Liveness Probe 探测失败**。
*   证据 #1 和 #2 明确显示 Kubelet 持续收到探活请求的 `HTTP 500` 错误，并随后执行了 `Killing` 操作。
*   证据 #3 和 #4 确认了容器因收到 `SIGKILL` (Exit 137, reason=Error) 而退出，非内存溢出。

**缺失的决定性事实：**
日志和追踪记录中未捕获到探活请求失败时的具体堆栈或异常信息。
*   证据 #7 和 #8 仅记录了成功的 `HTTP 200` 业务请求，表明应用主业务逻辑可能正常，或者应用将探活请求与业务请求混用且仅在探活时触发特定逻辑。
*   目前无法确认应用返回 500 的具体代码级原因（如：特定的 Bug、依赖服务暂时不可用、或探针逻辑本身设计缺陷），需进一步检查应用代码逻辑以区分是业务故障还是探活接口误报。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 23.7s
├─ 并发证据采集: 80.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 80.1s (Evidence 68.8s, RCA 11.2s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime, pod-oomkilled
