## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，调度器返回 FailedScheduling 错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling 31m default-scheduler 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` (fact-6d248e30a03d) | 确认调度器在全部 3 个节点上均因内存不足且无抢占对象而调度失败 |
| 2 | K8s State | kubernetes | `pod.phase: Pending` (fact-9ed9948d303f), `pod.condition: Unschedulable` (fact-53233d02626e) | 确认 Pod 处于未调度的异常静止状态 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory: 1Pi` (fact-88edda8ad15a) | 展示导致资源不可分配的根本原因：1 Pebibyte 的内存请求 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (fact-760c642305c0) | 独立确认 Pod 状态为 Pending |

**证据说明：**
- 事件 (1) 明确指出了“3 Insufficient memory”且“无抢占对象”，这与 Pod 配置了 1Pi 的极端内存需求 (3) 构成直接因果关系。
- 状态 (2) 与 Metric (4) 互相印证了 Pod 未能被调度的事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置声明 1Pi 内存 (事实 3) → 集群所有节点物理内存均小于该值，且无抢占资源 (事实 1) → 调度器执行 FailedScheduling (事实 1) → Pod 保持 Pending 状态 (事实 2, 4)
```

### 根因结论

**已确认根因：Pod 资源配置错误（1Pi 内存需求）。**

- 容器 `app` 声明的 `memory.request` 和 `memory.limit` 均为 `1Pi`（1 Pebibyte，约 1126 TiB），该数值远超常规物理节点的实际容量。
- 调度器评估集群中 3 个可用节点，发现均无法满足 1Pi 的内存请求，同时由于资源量过大，无法通过抢占其他 Pod 来腾出空间。
- **证据引用**：调度事件 `FailedScheduling` (证据 1) 明确记录了 `Insufficient memory` 及 `No preemption victims found`，直接证明了资源定义与集群物理容量严重不匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.9s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v02/workload: 35.6s (Evidence 27.8s, RCA 7.7s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
