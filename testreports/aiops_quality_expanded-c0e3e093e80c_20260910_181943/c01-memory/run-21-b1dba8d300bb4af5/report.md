## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod `aiops-case-v02/workload` 的 container `app` 声明了 `1Pi` 的内存请求（memory: 1Pi），该数值远超集群所有节点（最大约 31.3 TiB）的总可用内存。由于调度器无法在任何节点上找到满足 `1Pi` 资源请求的节点，且无合适的抢占目标，导致 Pod 持续处于 `Pending` 状态（FailedScheduling）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | `kubernetes` | `container.app` 的 `memory.request`: `1Pi`, `cpu.request`: `5m` | 定义异常的资源请求配置，明确调度失败的根本约束。 |
| 2 | K8s State | `kubernetes` | Pod `phase`: `Pending`, `PodScheduled` condition: `False` | 确认异常现象，Pod 未被调度到任何节点。 |
| 3 | K8s Event | `kubernetes` | `reason`: `FailedScheduling`, `message`: `0/3 nodes are available: 3 Insufficient memory` | 直接证据，证明调度器在所有 3 个节点上均判定内存不足。 |
| 4 | Topology | `kubernetes` | `pod:aiops-case-v02/workload` owns container `aiops-case-v02/app` | 建立实体层级关系，确认内存配置属于当前异常的容器。 |

证据链逻辑：
配置事实（证据 #1）给出了极大的内存申请（`1Pi`）。状态事实（证据 #2）显示了 Pod 挂起的结果。调度器发出的 Event 事实（证据 #3）直接排除了其他原因，明确指出是“内存不足”（Insufficient memory）导致 3 个节点均拒绝调度。Topology 事实（证据 #4）验证了配置与 Pod 的归属关系，确保没有配置混淆。

## 🎯 根因分析 · g1

### 因果链

```text
Pod `aiops-case-v02/app` 配置了 1Pi 的内存请求 (证据 #1) → 该数值远超集群任意单节点（约 31.3 TiB）的物理容量 → 调度器对所有 3 个可用节点判定 Insufficient memory，且无抢占者 → Pod 持续处于 Pending 状态，PodScheduled 为 False (证据 #2, #3)
```

### 根因结论

已确认根因为**资源请求超限导致调度失败**。

容器 `aiops-case-v02/app` 声明了 `1Pi` (1 Pebibyte) 的内存请求，该数量级远超集群中任何单节点（约 31.3 TiB）的总容量，导致 Kubernetes 调度器无法在任何节点上满足该资源约束。调度器在 `0/3 nodes are available: 3 Insufficient memory` 的事件记录（证据 #3）中直接证实了这一机制。因此，Pod 持续处于 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.6s
├─ 并发证据采集: 71.4s
│  └─ g1 aiops-case-v02/workload: 71.4s (Evidence 58.7s, RCA 12.7s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
