## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload in aiops-case-v03 is Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.condition`: Type=PodScheduled, Status=False, Reason=Unschedulable, Message="0/3 nodes are available: persistentvolumeclaim \"unavailable-claim\" not found." | 直接定位调度失败原因：依赖的 PVC 'unavailable-claim' 不存在 |
| 2 | K8s State | Kubernetes | `pod.phase`: Pending | 确认 Pod 始终无法进入运行状态，符合调度受阻特征 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory`: 8Mi, `container.resource_request.cpu`: 5m | 确认资源请求极低，排除集群资源耗尽导致调度失败的可能 |

证据表明：Pod 处于 Pending 状态，调度器明确报错指出 0/3 节点可用。根本原因是 Pod 引用的 PVC `unavailable-claim` 在集群中不存在，导致持久卷绑定失败，进而触发调度器 `Unschedulable` 判定。资源请求（5m CPU/8Mi Memory）极低，非资源瓶颈。

## 🎯 根因分析 · g1

### 因果链

```text
Pod定义引用了不存在的PVC 'unavailable-claim' → 调度器评估持久卷绑定状态失败 → 调度器判定0/3节点可用(FailedScheduling) → Pod保持Pending状态无IP/节点分配
```

### 根因结论

已确认根因：Pod `aiops-case-v03/workload` 的定义中引用了名为 `unavailable-claim` 的 PVC，但该 PVC 在集群中不存在（`not found`）。

- 调度器因无法绑定该 PVC，直接判定集群中 0/3 节点可用，导致 `PodScheduled` 条件为 `False`。
- 这解释了为何 Pod 持续处于 `Pending` 状态且未分配节点/IP。
- 资源请求极低（5m CPU, 8Mi Memory）进一步排除了资源不足的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.3s
├─ 并发证据采集: 50.2s
│  └─ g1 aiops-case-v03/workload: 50.2s (Evidence 44.2s, RCA 5.9s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
