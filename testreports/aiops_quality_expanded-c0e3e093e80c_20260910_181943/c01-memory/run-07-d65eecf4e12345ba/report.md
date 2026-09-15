## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod内存请求量(1Pi)超过集群所有节点可分配内存上限，导致调度器无法找到合适节点分配该Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pod (aiops-case-v02/workload)` 状态为 `Pending` (`fact-6b3b4a9377d6`) | 确认应用处于无法运行的停滞状态 |
| 2 | K8s Event | Kubernetes | `FailedScheduling` 事件：`0/3 nodes are available: 3 Insufficient memory` (`fact-36e3d59c98da`, `fact-90a013dccddc`) | 证明集群所有节点均无法分配该资源，是 Pod 卡住的直接原因 |
| 3 | K8s Config | Kubernetes | 内存资源请求 `container.resource_request.memory` 设置为 `1Pi` (`fact-e0d95c2a7411`)；内存硬限制 `container.resource_limit.memory` 设置为 `1Pi` (`fact-98ab64624256`) | 定位异常资源参数，1Pi 远超常规物理节点容量 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 确认 `Pending` 值为 1，`Unknown` 值为 0 (`fact-667b33ca8e12`, `fact-34c0f994ce07`) | 辅助证实 Pod 停留在调度阶段，未进入运行或错误状态 |

**证据分析：**
Kubernetes 调度器的 `Insufficient memory` 报错直接由 Pod 配置的 `1Pi` 内存请求导致。由于该资源量超过集群所有 3 个节点的 Allocatable Memory 上限，调度器无法找到可用节点（Preemption 机制也未能解决），从而导致 Pod 处于 `Pending` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 1Pi 内存请求 (fact-3) → 超过集群所有节点可分配上限 → 调度器无法分配资源 (fact-2) → Pod 状态 Pending (fact-1, fact-4)
```

### 根因结论

已确认根因为：Pod `aiops-case-v02/workload` 的 `spec.containers[0].resources.requests.memory` 配置为 `1Pi`，该数值超过了集群所有可用节点（3 个）的内存容量上限。

由于资源请求量不合理，Kubernetes 调度器无法找到任何节点满足该调度约束（Evidence: `fact-2`），导致 Pod 永远无法被调度至具体节点运行（Evidence: `fact-1`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.5s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-v02/workload: 43.1s (Evidence 35.9s, RCA 7.1s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
