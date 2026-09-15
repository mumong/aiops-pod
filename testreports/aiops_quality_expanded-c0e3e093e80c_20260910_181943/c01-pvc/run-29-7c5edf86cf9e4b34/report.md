## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，持续无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v03/workload` phase=`Pending`, `PodScheduled=False`, reason=`Unschedulable` (fact-222951407cb6, fact-e74b4b7e6370) | 确认 Pod 处于持续调度失败的停滞状态 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (fact-39cc194f69a8) | 核心故障机制：调度器明确报出 PVC 资源找不到，阻断调度 |
| 3 | K8s Config | kubernetes | Pod resource limits: `cpu=50m`, `memory=32Mi`; requests: `cpu=5m`, `memory=8Mi` (fact-cb2b99ae823f, fact-6242eb917319, fact-3cbba228def5, fact-492c0570b1b3) | 资源请求极低且合法，排除因集群资源枯竭导致无法调度的可能 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}=1`, `kube_pod_status_phase{phase="Failed"}=0` (fact-99a65819ad3f, fact-3d31ebc13496) | 确认 Pod 停留在 Pending 阶段，未发生容器启动失败或崩溃，印证是调度前置校验卡点 |

**证据关联说明：**
Kubernetes State 和 Event 事实 (1, 2) 直接指出了 Pod 处于 Unschedulable 状态，并给出确切原因为 PVC 缺失。Metric 数据 (4) 佐证了该异常是持续存在的静态阻塞而非瞬时波动。资源配置事实 (3) 排除了资源竞争因素。Logging/Tracing 因容器未启动，属于物理不可达，如实记录为不适用。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 引用不存在的 PVC 'unavailable-claim' → Scheduler 执行 Volume 校验失败 → 抛出 FailedScheduling 异常 → Pod 持续保持 Pending 状态
```

### 根因结论
**已确认的根因：** 调度失败的根本原因是 `PersistentVolumeClaim "unavailable-claim"` 在目标 Namespace (`aiops-case-v03`) 中不存在。

*   **现象印证：** 调度器日志明确指出 `persistentvolumeclaim "unavailable-claim" not found` (证据 2)，导致 `PodScheduled` 条件置为 `False` (证据 1)。
*   **排除干扰：** Pod 的 CPU/内存请求量极低 (5m/8Mi) 且资源上限合理 (证据 3)，集群中无处于 Failed 状态的 Pod 记录 (证据 4)，排除了资源不足或镜像拉取失败等因素。
*   **结论：** PVC 缺失是导致该工作负载处于 Pending 状态的唯一决定性原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.0s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-v03/workload: 43.0s (Evidence 33.9s, RCA 9.1s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable, pod-volume-mount-failed
