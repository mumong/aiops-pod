## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Container memory limit (64Mi) is significantly lower than the application's memory allocation (256Mi), triggering OOMKilled (Exit Code 137) and CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 等待原因为 `CrashLoopBackOff`，最后终止原因为 `OOMKilled` | 定位应用反复崩溃的直接状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 退出码为 `137` | 确认进程被系统强制终止（OOM Killer 行为） |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存硬限制（resource_limit.memory）为 `64Mi` | 提供资源限制事实，构成根因的必要条件 |
| 4 | K8s State | Kubernetes | Pod 状态为 `Running`，但 `ContainersReady` 和 `Ready` 均为 `False` | 确认 Pod 处于无法提供服务的异常运行态 |
| 5 | Logging | Elasticsearch | 应用日志消息显示：`startup allocation 256Mi` | 提供应用内存诉求事实，证实资源限制（64Mi）显著低于预期 |
| 6 | K8s Event | Kubernetes | 事件消息：`Back-off restarting failed container app` (发生 8 次) | 印证 CrashLoopBackOff 机制及重启频率 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 标签为 `OOMKilled` (值为 1) | 独立于 K8s API 确认终止原因 |

**证据印证：**
- **内存限制冲突**：K8s 配置显示内存硬限制为 `64Mi` [3]，而应用日志明确表明其启动分配的内存为 `256Mi` [5]。这一量级差异直接证实了 OOM（内存不足）发生的物理基础。
- **OOM 确认闭环**：应用日志的内存分配 [5] 与 K8s 状态 [1, 2] 及 Prometheus 指标 [7] 均指向 `OOMKilled` 及退出码 `137`，证实应用因内存不足被系统强杀，进而触发重启并进入 `CrashLoopBackOff` 状态 [1, 6]。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制 (64Mi) 远低于应用实际诉求 (256Mi) → OOMKilled (Exit Code 137) → 触发 K8s 重启与退避逻辑 (BackOff) → Pod 持续处于 CrashLoopBackOff 状态 (ContainersNotReady)
```

### 根因结论

已确认根因为：**容器内存配置严重不足**。

Kubernetes 集群中 `aiops-case-v15/workload` 的 `app` 容器被强制设置了 `64Mi` 的内存硬限制，但应用启动时实际需求 `256Mi` 内存。这一配置缺陷导致进程在启动后瞬间触发 OOM Killer，被操作系统强制终止（Exit Code 137）。Kubernetes 检测到容器非正常退出后，触发指数退避重试机制，最终表现为容器长期处于 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 26.8s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-v15/workload: 50.0s (Evidence 44.0s, RCA 5.7s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
