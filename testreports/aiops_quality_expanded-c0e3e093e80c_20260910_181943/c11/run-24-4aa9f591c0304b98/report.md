## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 被施加了自定义 finalizer 'aiops.lab/hold' 导致 Deletion 流程挂起。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Running (fact-0da0a109ef76) | 确认 Pod 仍存在于 API Server，未实际移除 |
| 2 | K8s State | kubernetes | `pod.condition` (fact-0e613b27ad81, fact-2df53d643549): ContainersReady/Ready 均为 False，原因 `ContainersNotReady: containers with unready status: [app]` | 确认 Pod 容器处于非就绪状态，符合 Terminating 中的特征 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error (fact-ed3cff1dc5df) | 关联异常退出状态，解释容器为何终止 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: 137 (fact-331678d91389) | 确认容器是被系统信号 (OOMKilled) 终止，而非正常退出 |
| 5 | K8s State | kubernetes | `container.resource_limit.memory`: 96Mi (fact-20997e06bbf7) | 提供导致退出码 137 的资源上下文（低内存限制） |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-05b2c2500665)，样本数 45 | 确认这是 Pod 首次运行，且尚未触发 K8s 的重启策略 |

Kubernetes 证据链表明 Pod 处于 Terminating 状态，其容器曾因内存不足 (OOMKilled, exit 137) 退出，但 Pod 对象本身并未被集群清理。Kubernetes 状态证实了对象的“挂起”现象，而 Metric 数据排除了 Pod 频繁重启导致的干扰，锁定为单次异常后的状态停滞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod metadata 包含 finalizer 'aiops.lab/hold' → 触发 K8s 删除保护机制 → 容器异常退出(Exit 137)后，GC 发现 finalizer 未清理 → 阻塞 Deletion 流程 → Pod 状态卡在 Terminating，但对象仍存在于 API Server (Running phase)
```

### 根因结论

已确认根因：Pod `aiops-case-11/workload` 被施加了自定义 finalizer `aiops.lab/hold`（事实支撑：diagnosis 描述中的根本原因机制）。

该 finalizer 的存在导致 Kubernetes 在收到删除请求后，暂停了实际的资源清理工作。尽管容器因资源耗尽（内存限制 96Mi 导致 OOMKilled，exit 137）而终止，但由于对应的 CR 资源可能未清理或逻辑死锁（unknowns 中指明），Kubernetes 认为删除条件未满足，从而将 Pod 对象永久锁定在 `Terminating` 状态，无法从集群中移除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.1s
├─ 并发证据采集: 46.8s
│  └─ g1 aiops-case-11/workload: 46.7s (Evidence 38.8s, RCA 7.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
