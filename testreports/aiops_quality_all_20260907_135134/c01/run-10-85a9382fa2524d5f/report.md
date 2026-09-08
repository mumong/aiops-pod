## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 配置了 nodeSelector `aiops.lab/unavailable: true`，集群中所有 3 个节点均不具备该标签，导致调度器无法找到满足亲和性要求的节点，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `status: "Pending"`, `phase: "Pending"`, `PodScheduled: False (Unschedulable)` | 确认 Pod 处于不可调度的停滞状态 |
| 2 | K8s Event | default-scheduler | `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确指出调度失败原因为节点亲和性/选择器不匹配 |
| 3 | K8s State | pod.condition | `message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 验证事件描述与 Pod 条件状态一致 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1`, `{phase="Unknown"} = 0` | 排除 Pod 处于未知或错误状态，确认状态稳定为 Pending |

**证据说明：**
Kubernetes 调度器事件（#2）与 Pod 条件状态（#3）均明确指出了 `node affinity/selector` 匹配失败是导致 `Unschedulable` 的直接原因。度量指标（#4）提供了辅助状态确认，排除了运行态异常的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector `aiops.lab/unavailable: true` → 集群中所有 3 个节点均不具备该标签 → 调度器无法找到满足亲和性要求的节点 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为 **NodeSelector 配置导致调度不可达**。Pod 强制指定了集群中不存在的所有 3 个节点都不满足的标签条件，导致调度器无法将其分配至任何节点。该结论由 Kubernetes 调度器事件与 Pod 状态直接证实（证据 #2、#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.8s
├─ 并发证据采集: 37.6s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 37.6s (Evidence 32.6s, RCA 4.9s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
