## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Application dependency unavailable causing HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (2m36s 间隔, x2286 次) | 直接观测到就绪探针因 503 状态码持续失败，是导致 Pod 状态 NotReady 的直接原因 |
| 2 | K8s State | kubernetes | `ContainersReady: False`, `Ready: False` (ContainersNotReady) | 确认 Pod 当前处于非健康状态，应用容器未就绪 |
| 3 | K8s Config | kubernetes | 内存 Limit: 96Mi (Request 24Mi); CPU Limit: 200m (Request 20m) | 提供容器资源约束上下文；内存与当前 0MiB 使用量无直接压力关联 |
| 4 | Logging | elasticsearch | Pattern: `dependency unavailable`, `http_status: 503`, `path: /work` (发生 8 次) | 揭示应用内部逻辑：HTTP 请求 `/work` 因下游依赖不可用而返回 503 错误 |
| 5 | Tracing | deepflow/Tempo | Span `GET /work` 返回 503 (src: 172.16.104.62, dst: 172.16.104.16), Flow 累计 9 次 | 跨维度追踪请求链路，确认 503 错误发生在 `/work` 接口处理阶段 |

**证据关联性说明**：
Kubernetes 事件（#1, #2）明确记录了 503 导致的不健康状态，这是用户可见的“症状”。Logging（#4）和 Tracing（#5）深入到应用层，证实 503 是应用程序主动返回的，且原因是“依赖不可用”，排除了基础设施（如 OOM、CrashLoopBackOff）导致的失败——资源限制（#3）和重启计数（0次）也佐证了进程仍在运行，仅应用逻辑失败。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖不可用 → HTTP GET /work 处理失败 → 返回 HTTP 503 → 就绪探针探测失败 (Readiness probe failed) → Pod 状态变为 NotReady
```

### 根因结论

**已确认根因**：应用依赖不可用导致 HTTP 503。

根据事实 `fact-3aa67cdc17b0` (Logging) 中的日志 `dependency unavailable` 以及 `fact-103a33e731fa` (Tracing) 中确认返回 503 的 Span，表明应用容器本身是存活并运行着的（重启次数为 0），但在处理业务请求 `/work` 时，因为调用下游依赖失败而主动返回了 503 状态码。由于该接口恰好被配置为就绪探针（Readiness Probe）的目标，探针接收 503 响应后判定探测失败，最终导致 Kubernetes 将该 Pod 标记为 `NotReady` 并从 Service 后端移除。故障本质是应用层面的依赖故障，而非集群层面的容器或调度故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.1s
├─ 并发证据采集: 56.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 56.6s (Evidence 52.0s, RCA 4.5s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
