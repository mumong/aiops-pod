## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" | 确认容器因内存溢出被强制终止的触发原因 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: "CrashLoopBackOff", `container.waiting_message`: "back-off 5m0s restarting failed container" | 说明当前 Pod 处于频繁重启后的冷却等待状态，是 OOM 循环的直接现象 |
| 3 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload_aiops-case-v15(da351bf0-c4ab-47a0-b24d-7c7a75950753)` (x165 over 35m) | 记录了长达 35 分钟的异常重启过程，与当前等待状态一致 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: "64Mi" | 提供容器内存硬限制，用于判断溢出依据 |
| 5 | K8s Config | Kubernetes | `container.resource_request.memory`: "8Mi" | 提供调度预留量，确认资源限制配置 |
| 6 | Logging | Elasticsearch | `log.message`: "startup allocation 256Mi" | 揭示应用启动时的实际内存申请量，直接解释了导致溢出的行为 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 11 | 量化确认容器已重启 11 次，验证了 CrashLoopBackOff 的严重程度 |

**证据印证分析**：
日志 (证据 6) 确认应用需要 256Mi，而 K8s 配置 (证据 4) 限制为 64Mi，这种 4 倍的差距直接导致了证据 1 的 `OOMKilled`。K8s 事件 (证据 3) 和指标 (证据 7) 从不同维度印证了由于频繁的 OOM 导致容器不断重启并最终进入 `CrashLoopBackOff` 状态 (证据 2)。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动申请内存 256Mi → 超过容器硬限制 64Mi → 触发 OOMKilled (Exit Code 137) → Pod 频繁重启导致 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存限制配置过低**。
日志证据 (证据 6) 显示应用启动分配 `256Mi`，而容器硬限制 (证据 4) 仅为 `64Mi`。内存超限导致容器被内核 OOM Killer 终止 (证据 1)，进而引发 Pod 频繁重启 (证据 7) 并进入 `CrashLoopBackOff` 状态 (证据 2)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 29.9s
├─ 并发证据采集: 52.5s
│  └─ g1 aiops-case-v15/workload: 52.5s (Evidence 43.1s, RCA 9.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled
