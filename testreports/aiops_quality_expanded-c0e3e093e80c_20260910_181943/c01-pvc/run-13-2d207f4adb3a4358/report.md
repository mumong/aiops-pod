## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，长时间未分配 Node |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `status: Pending` | 确认 Pod 未分配节点，处于无法调度的终态。 |
| 2 | K8s Event | default-scheduler | `Warning FailedScheduling ... 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接证明调度失败原因是 PVC 资源引用缺失。 |
| 3 | K8s Config | Pod Resource Limits | Container `app` Memory limit `32Mi` (request `8Mi`)，CPU limit `50m` (request `5m`) | 证实内存/CPU 资源请求极低，排除资源竞争或配额不足导致的调度拒绝。 |
| 4 | Metric | kube-state-metrics | `kube_pod_status_phase{phase="Pending"} = 1` | 从监控侧确认 Pod 持续处于 Pending 阶段。 |

调度器事件明确指出失败原因为 `persistentvolumeclaim "unavailable-claim" not found`，同时资源的内存与 CPU 请求值极低，排除了集群资源耗尽或超卖限制的可能性。Pod 状态持续为 Pending 且无后续状态变更，印证了依赖缺失导致调度器无法分配宿主机，进而容器无法启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 PVC 'unavailable-claim' → 调度器检测到持久卷依赖缺失并拒绝调度 → Pod 持续处于 Pending 状态，无法分配 Node 和 IP → 应用容器未启动
```

### 根因结论

已确认的根因是 **Pod 定义了对其名为 `unavailable-claim` 的 PersistentVolumeClaim 的依赖，但该 PVC 在当前 namespace (`aiops-case-v03`) 中实际不存在**。
*   **事实支撑**：
    *   Kubernetes 调度器发出了多次 `FailedScheduling` 事件，错误信息明确指向 `persistentvolumeclaim "unavailable-claim" not found`（证据 #2）。
    *   由于调度失败，Pod 状态长期停滞在 `Pending`（证据 #1），没有触发容器启动流程。
    *   Pod 的内存和 CPU 限制/请求值极低（证据 #3），证明调度器的拒绝并非由节点资源不足或限制策略引起。
    *   由于容器未启动，监控与日志/追踪系统均无有效数据，佐证了故障发生在调度层而非应用运行层。

---

## 📊 性能统计

```text
├─ 总耗时: 52.2s
├─ 问题定位: 16.6s
├─ 并发证据采集: 27.4s
│  └─ g1 aiops-case-v03/workload: 27.4s (Evidence 20.8s, RCA 6.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
