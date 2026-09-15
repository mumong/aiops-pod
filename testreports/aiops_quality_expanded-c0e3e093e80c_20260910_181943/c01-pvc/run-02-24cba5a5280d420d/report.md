## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod引用了不存在且不可绑定的PersistentVolumeClaim 'unavailable-claim'，导致调度器在3个节点上均无法找到可用的持久化存储卷，从而触发FailedScheduling事件并致使Pod保持Pending状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | `Pending` | 确认 Pod 处于待调度状态，未进入运行态。 |
| 2 | K8s State | pod.condition | `PodScheduled=False, reason=Unschedulable`，消息：“0/3 nodes are available: persistentvolumeclaim \"unavailable-claim\" not found...” | 提供调度失败的直接原因，表明集群中不存在 PVC 'unavailable-claim'。 |
| 3 | K8s Event | FailedScheduling | `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 证实调度器在所有 3 个可用节点上均因缺少 PVC 而拒绝调度，且无法触发抢占。 |
| 4 | K8s Config | container.resource_limit | app 容器 memory=32Mi, cpu=50m | 确认资源限制配置，排除内存或 CPU 耗尽导致调度失败的可能性。 |
| 5 | Metric | kube_pod_status_phase | Pending=1 (phase=Pending), Running=0 | 辅助确认 Pod 在观测窗口内一直维持 Pending 状态，无运行样本。 |

**证据印证说明：**
K8s 状态与事件证据（#2, #3）在逻辑上高度一致，均指向同一个缺失的资源依赖：`unavailable-claim` PVC。调度器在所有节点上的失败记录（#3）排除了节点资源不足的可能，直接锁定为资源定义错误。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用了不存在的 PersistentVolumeClaim 'unavailable-claim' → 调度器在所有 3 个节点上均无法绑定存储卷 → 触发 FailedScheduling 事件（0/3 nodes are available） → Pod 保持 Pending 状态
```

### 根因结论
已确认根因为 **Pod 引用了不存在的 `PersistentVolumeClaim` ('unavailable-claim')**。

根据证据 #2 和 #3，Kubernetes 调度器在尝试调度 `aiops-case-v03/workload` 时，因无法找到指定的 PVC 而在所有 3 个节点上均宣告调度失败。该资源定义错误直接导致了 Pod 无法绑定持久化存储，从而一直处于 `Pending` 状态。现有证据足以确认此因果链，无冲突事实。

---

## 📊 性能统计

```text
├─ 总耗时: 56.8s
├─ 问题定位: 16.2s
├─ 并发证据采集: 32.8s
│  └─ g1 aiops-case-v03/workload: 32.8s (Evidence 27.3s, RCA 5.4s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
