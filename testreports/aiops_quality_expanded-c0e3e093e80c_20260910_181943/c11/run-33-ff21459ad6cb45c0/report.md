## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Custom Finalizer 'aiops.lab/hold' not released |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 处于 `Terminating` 状态 | 确立异常基线，确认对象已被删除请求 |
| 2 | K8s State | kubernetes | Container `app` 状态为 `containers with unready status` (Ready=False) | 确认容器在终止期间仍不可用，排除正常快速退出的场景 |
| 3 | K8s State | kubernetes | Container `app` 终止原因为 `Error`，退出码 `137` | 提供容器非正常退出的具体事实，关联终止原因 |
| 4 | K8s State | kubernetes | Container `app` 资源限制 `cpu: 200m`, `memory: 96Mi` | 提供异常发生时的环境上下文信息 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 佐证本次异常非重启循环导致，排除了容器频繁拉起的情况 |

**证据说明：**
*   Kubernetes 事实链（#1, #2）确认了 Pod 处于卡死的 Terminating 状态，且容器处于未就绪且已终止（Exit 137）的状态。
*   退出码 137（#3）与状态 #2 共同指向容器进程被系统强制杀死（OOMKilled 或 SIGKILL），但这并未触发 Pod 对象的删除清理。
*   Metric 数据（#5）证明不存在反复重启的行为，进一步缩小了故障范围，指向删除阶段的特定机制阻断。
*   Logging 和 Tracing 维度无数据（Absent），无法进一步确认退出码 137 的具体触发进程，但已足够支撑 K8s 对象层面的根因。

## 🎯 根因分析 · g1

```text
Custom controller 'aiops.lab' 持有 finalizer 'aiops.lab/hold' → K8s GC 等待 finalizer 移除 → Pod 对象卡死在 Terminating 状态 → 用户可见 TerminatingStuck 异常
```

**根因结论：**
已确认的根因为：**Custom Finalizer 'aiops.lab/hold' not released**。

Kubernetes Garbage Collector 在收到 Pod 的删除请求后，会无限期等待 `aiops.lab/hold` 这个 Finalizer 被移除，然后才会真正删除 Pod 对象。目前证据显示 Pod 虽然进程已异常退出（#3），但 Finalizer 机制未被释放，导致对象卡在 `Terminating` 状态（#1）。由于 K8s 事实足以支撑这一逻辑结论（#1, #3），无需更多工具数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.1s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-11/workload: 48.5s (Evidence 41.8s, RCA 6.6s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
