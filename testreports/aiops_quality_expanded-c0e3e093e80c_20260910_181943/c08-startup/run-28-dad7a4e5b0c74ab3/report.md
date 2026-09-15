## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload (aiops-case-v15) 处于 CrashLoopBackOff 状态，容器 app 反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | `reason: OOMKilled` | 证实容器因内存超限被操作系统强杀 |
| 2 | K8s State | `container.waiting_reason` | `reason: CrashLoopBackOff` | 展示容器反复重启失败的最终状态 |
| 3 | K8s Config | `container.resource_limit.memory` | `value: 64Mi` | 确立容器允许的内存使用硬上限 |
| 4 | K8s State | `container.last_exit_code` | `exit_code: 137` | 印证进程被内核 OOM Killer 强制终止 |
| 5 | K8s Event | `event.message` | `Back-off restarting failed container app` | 描述 Kubernetes 指数退避重试重启的过程 |
| 6 | K8s State | `container.waiting_message` | `back-off 5m0s restarting failed container=app...` | 展示最后一次重试的退避等待时长（5分钟） |
| 7 | Logging | `log.message` | `startup allocation 256Mi` | 证实启动过程需要分配的内存量远超配置限制 |
| 8 | Metric | `kube_pod_container_status_last_terminated_reason` | `reason: OOMKilled` | Prometheus 指标独立印证了 OOM 终止原因 |

**证据链说明：**
Kubernetes 事件与指标（#1, #8）共同锁定终止原因为 OOMKilled；退出码 137（#4）进一步确认这是由外部（内核/系统）强杀进程所致，而非程序内部逻辑错误。日志（#7）揭示了根本冲突：启动分配需求 256Mi 远超配置的内存上限 64Mi（#3）。这种持续的资源超支导致每次启动必败，最终触发 Kubernetes 的重启重试机制陷入 CrashLoopBackOff（#2, #5, #6）的死循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动分配 256Mi 内存需求 (日志) → 超出 64Mi 的容器硬限制 (K8s Config) → Linux OOM Killer 终止进程 (Exit Code 137) → Kubernetes 反复重启失败 (CrashLoopBackOff)
```

### 根因结论

**已确认的根因**：应用容器的内存资源限制配置过低（`limits.memory=64Mi`），无法满足应用启动时实际需要的内存大小（`allocation 256Mi`）。

该配置缺陷直接导致进程在启动阶段即触发 OOM Killer（Exit Code 137），进而引发 Kubernetes 的自动重启机制不断尝试失败，形成 `CrashLoopBackOff` 状态。这一结论由 Kubernetes 终止原因（OOMKilled）、退出码（137）、日志分配的内存数值（256Mi）与资源限制配置（64Mi）之间的数值矛盾及终止事实完全印证。

---

## 📊 性能统计

```text
├─ 总耗时: 9.5m
├─ 问题定位: 11.9s
├─ 并发证据采集: 550.0s
│  └─ g1 aiops-case-v15/workload: 550.0s (Evidence 538.9s, RCA 10.9s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
