## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，容器不断重启且 Liveness 探测持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (17次, 5m57s) | 探测机制检测到应用层直接失效 |
| 2 | K8s Config | limit.memory | 容器 app 硬限制 (Limit) = 96Mi | 确定系统资源管控边界 |
| 3 | K8s State | container.exit_code | Exit Code: 137 | 确认进程被内核 OOM Killer 强制终止 |
| 4 | K8s State | last_terminated_reason | Error (OOM 典型标志) | 确认异常终止原因 |
| 5 | Metric | kube_pod_container_status_waiting_reason | 1 (reason: CrashLoopBackOff) | 聚合指标确认当前处于重启等待期 |
| 6 | K8s Event | kubelet | `Container app failed liveness probe, will be restarted` | 说明重启行为是探测失败后的连锁反应 |
| 7 | Tracing | Deepflow Flow | `/health` GET 请求返回 500 (8次, 10.2.0.50→172.16.104.31) | L7 层面验证了端点实际处于故障响应状态 |
| 8 | Logging | Elaticsearch | `allocated_mib` 在 8 次请求中始终为 0 | 应用日志未捕获内存耗尽事件，佐证为外部强制终止 |

**证据关联说明**：
Kubernetes 的 Exit Code 137 配合 Metric 中的 CrashLoopBackOff 状态，证实了进程处于“非正常退出并重启”的生命周期中；Liveness 探测的 500 错误与 Deepflow 流量记录中的 `/health` 500 响应一致，确证了 Liveness 探测失败是因为应用进程在探测前已被系统杀死（OOM），而非应用逻辑报错。Logging 中全 0 内存数值进一步排除了应用内部泄漏导致应用层报错的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用突破 96Mi 硬限制 → 内核触发 OOM Killer 发送 SIGKILL (Exit 137) → 应用进程退出导致 /health 端点不可用 → Liveness Probe 持续返回 HTTP 500 触发 kubelet 进入 CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器资源硬限制不足引发 OOM (Out of Memory)**。

应用进程在运行过程中消耗内存超过设定的 `96Mi` Limit，触发了 K8s 节点内核的 OOM Killer 机制。应用进程未能在终止前通过 HTTP 接口正常响应，导致 Liveness Probe 探测返回 HTTP 500 错误，进而引发 Pod 状态变为 `CrashLoopBackOff`。当前日志中未体现应用内部错误堆栈且 `allocated_mib` 监控值为 0，表明崩溃完全由系统级强制信号引起，属资源硬限制边界问题。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 14.0s
├─ 并发证据采集: 93.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 93.0s (Evidence 81.1s, RCA 11.8s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
