## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，13 次重启，最近退出码 137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v17/workload` 状态 `Running` 但 `ContainersReady=False`；Container `app` 状态 `CrashLoopBackOff`，重启 13 次，最近退出码 137 (`fact-37c586cd144e`, `fact-fc185ee524f1`, `fact-16826b307146`, `fact-429fd306d124`) | 确立异常状态与持续重启现象 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed`: `Get "http://172.16.104.36:18080/health": context deadline exceeded` (`fact-d828154eee39`)；`Killing`: `Container app failed liveness probe, will be restarted` (`fact-0434ef902f82`) | 直接归因于 Liveness 探针超时触发 `SIGKILL` (Exit 137) |
| 3 | Metric | Prometheus | 容器内存工作集 `3.1 MiB` 至 `11.3 MiB` 波动，未触及 `64Mi` 硬限制 (`fact-3c8028829144`, `fact-80022e60ccfd`, `fact-7a136bcd5d26`) | 排除 OOM 导致 `SIGKILL` 的可能 |
| 4 | K8s Config | Kubernetes | Container `app` Liveness 探针配置导致 `context deadline exceeded` (`fact-d828154eee39`)，内存 Limit 设为 `64Mi` (`fact-77bc66a6317f`) | 证实探针超时机制与资源限制存在 |
| 5 | Logging | Elasticsearch | 应用日志显示 `/ready` 请求返回 `HTTP 200` (`fact-0faeed5ee951` 等) | 排除应用完全不可用或无响应的问题 |
| 6 | Tracing | Deepflow | HTTP `GET /health` 请求耗时 `3001095` - `3001920` μs (3-3.001s) (`fact-3c0efe8d8c1b` 等) | 证实应用处理 `/health` 请求耗时 (3s) 远超探针超时阈值 (1s) |

**证据印证**：
Trace 事实 (#6) 与应用日志 (#5) 一致表明应用正在处理 HTTP 请求且 `/ready` 可达，但 `/health` 请求耗时约 3s。Kubernetes 探针事件 (#2) 明确指出探针在 1s 内未获响应即判定失败，直接导致了容器被杀 (Exit 137, 事实 #1)。Metric 事实 (#3) 证明内存未超限，排除了 OOM，确认了因探针超时触发的 `SIGKILL` 是重启的唯一主因。

## 🎯 根因分析 · g1

### 因果链
```text
Liveness 探针超时阈值 (1s) < 应用 /health 端点响应延迟 (3s) → kubelet 判定探针失败并发送 SIGKILL → 容器被强制终止 (Exit 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论
已确认根因为 Liveness Probe 配置严重超时与应用实际响应延迟不匹配。
Trace 数据证实应用处理 `/health` 请求需要 3s 以上，而 Kubernetes 探针机制（事实 #2）在 1s 超时后即认为失败，进而触发 `SIGKILL` 终止容器。内存监控数据排除了 OOM 因素，确认了退出码 137 完全由探针超时引发，导致 Pod 陷入频繁重启的 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 23.6s
├─ 并发证据采集: 86.9s
│  └─ g1 aiops-case-v17/workload: 86.9s (Evidence 77.9s, RCA 8.7s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
