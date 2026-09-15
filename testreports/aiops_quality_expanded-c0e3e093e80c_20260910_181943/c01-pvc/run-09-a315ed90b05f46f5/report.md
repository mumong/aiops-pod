## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 模板中引用了当前 namespace 下不存在的 PersistentVolumeClaim 'unavailable-claim'，导致 default-scheduler 因无法绑定 Volume 而持续拒绝调度（FailedScheduling）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (fact-87fa34ed3072, fact-e4cae7031740) | **核心因果**：调度器直接报错，指明 Pod 调度受阻的确切原因（PVC 不存在）。 |
| 2 | K8s State | Pod 状态 | `phase: Pending`, `PodScheduled: False` (`Unschedulable`) (fact-39cf6011a6fa, fact-928c71de5931, fact-faf9887e63f3) | **症状确认**：证明 Pod 持续处于未调度状态，与调度器的拒绝日志互为印证。 |
| 3 | Metric | `kube_pod_status_phase` | `Pending: 1` (无 Unknown 态) (fact-72e860b53454) | **状态支撑**：确认 Pod 状态稳定为 Pending，排除了处于未知或 CrashLoop 等其他复杂状态。 |

**证据链小结**：
K8s Event (证据 #1) 提供了决定性的失败机制：`default-scheduler` 因找不到 PVC `unavailable-claim` 而拒绝调度 Pod。K8s State (证据 #2) 中的 `PodScheduled: False` 与 Metric 数据 (证据 #3) 共同印证了这一结果，证明该异常是由于配置层面的 PVC 缺失导致的资源绑定失败，而非集群资源不足或网络拓扑问题。

## 🎯 根因分析 · g1

### 因果链
```text
namespace 下 PVC 'unavailable-claim' 缺失 (事实) → default-scheduler 无法绑定 Volume (失败机制) → Pod 持续 Pending (直接失败) → 用户可见调度阻塞 (用户可见现象)
```

### 根因结论
已确认的根因为 **PersistentVolumeClaim 配置错误**。Pod 模板引用了当前命名空间下不存在的 PVC `unavailable-claim`，导致 Kubernetes 调度器（default-scheduler）在预调度阶段校验失败，无法将 Pod 分配至任何节点。这一结论由调度器发出的 `FailedScheduling` 警告日志（证据 #1）强有力支撑，并与 Pod 持续处于 Pending 状态的客观事实（证据 #2、#3）一致。

---

## 📊 性能统计

```text
├─ 总耗时: 57.3s
├─ 问题定位: 18.1s
├─ 并发证据采集: 30.9s
│  └─ g1 aiops-case-v03/workload: 30.9s (Evidence 26.3s, RCA 4.6s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
