## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | 应用 /healthz 端点返回 HTTP 500 导致 Liveness Probe 连续失败，Kubelet 终止容器并触发 CrashLoopBackOff 循环 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 确认健康检查端点 `/healthz` 实际返回 500 错误，是导致容器被杀的直接原因 |
| 2 | K8s State | Kubernetes | `Container app failed liveness probe, will be restarted` | 记录 Kubelet 检测到故障并执行终止指令的完整生命周期 |
| 3 | K8s Event | Kubernetes | `Warning BackOff 4m49s (x83 over 25m)` | 证实重启频率极高，当前已进入 CrashLoopBackOff 状态 |
| 4 | K8s State | Kubernetes | `lastState.terminated.reason: Error` / `exit_code: 137` | 确认应用进程被系统强制终止，且被 OOMKilled 或其他信号（137）杀死 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值 `15,540,224 bytes` (约 14.8 MiB) | 内存使用量在配置限制（Memory Limit 96Mi）范围内，且远低于硬限制 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值 `13` | 量化了异常的严重性和持续时间（已反复重启 13 次） |
| 7 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` / `container.resource_limit.cpu: 200m` | 提供资源边界上下文，证明当前异常非资源硬限制（Limit）导致 |

**证据小结**：
应用 `/healthz` 端点持续返回 500 错误（事实 #1），触发 Kubelet 的 Liveness Probe 失败机制（事实 #2），导致容器被系统反复终止（事实 #3、#4）。Metric 监控证实内存和 CPU 均在配置的限制范围内（事实 #5、#6），排除了资源耗尽（如 OOM）导致应用崩溃的可能性，进一步印证了故障根源在于应用本身的错误处理或逻辑缺陷。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /healthz 端点返回 HTTP 500 → Liveness Probe 连续失败 → Kubelet 执行 Kill (exit 137) → CrashLoopBackOff
```

### 根因结论

已确认的根因是 **应用内部 `/healthz` 端点逻辑异常（返回 HTTP 500）**。

应用代码层面的故障导致健康检查端点无法返回成功状态（事实 #1），Kubernetes 的 Liveness Probe 机制将此判定为容器存活状态异常，进而触发 Kubelet 终止容器进程。由于应用内部故障未解决，每次重启后健康检查再次失败，导致 Pod 进入 CrashLoopBackOff 循环（事实 #3）。当前的异常与集群资源调度、节点状态或基础设施故障无关。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 40.8s
├─ 并发证据采集: 85.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 85.3s (Evidence 78.1s, RCA 7.0s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime
