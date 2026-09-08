## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod设置了NodeSelector `aiops.lab/unavailable=true`，而集群中所有3个可用节点均缺少该标签，导致调度器无法找到匹配节点（PendingUnschedulable）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 提供调度失败的直接机制与错误描述 |
| 2 | K8s Event | `default-scheduler` | `FailedScheduling`: `Preemption is not helpful for scheduling..` | 排除抢占机制的补救可能 |
| 3 | K8s State | `pod.condition` | `PodScheduled`: `False`, Reason: `Unschedulable` | 确认 Pod 持续处于不可调度状态 |
| 4 | K8s State | `pod.phase` | `Pending` | 确认 Pod 运行阶段停滞在调度前 |
| 5 | Metric | `prometheus` | `kube_pod_status_phase{phase="Pending"}` = `1` (最近样本) | 量化确认 Pod 处于 Pending 状态的事实 |
| 6 | Metric | `prometheus` | `kube_pod_status_phase{phase="Failed"}` = `0` (最近样本) | 确认异常尚未进入 Failed 阶段，仅停留在调度环节 |

**证据印证说明**：
K8s 事件（事实 #1, #2）明确指出了 0/3 节点匹配失败的原因，K8s 状态（事实 #3, #4）与 Prometheus 指标（事实 #5, #6）分别从对象状态和指标数值两个维度相互印证了 Pod 持续处于 `Pending` 且无法调度的停滞现象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod声明NodeSelector `aiops.lab/unavailable=true` → 集群3个节点均未配置该标签，调度匹配失败 → Scheduler持续返回FailedScheduling → Pod保持Pending状态，未分配到任何节点
```

### 根因结论

已确认根因为 **Pod 调度亲和性/选择器（NodeSelector）配置与集群节点标签不匹配**。
*   Pod `aiops-case-01/workload-68c557d875-llhkh` 声明了 `aiops.lab/unavailable=true` 的 `NodeSelector`（事实关联：诊断状态）。
*   集群当前可用的 3 个节点均不具备该标签，导致调度器（Default Scheduler）在所有节点上均无法匹配到亲和性规则，持续抛出 `FailedScheduling` 事件（事实 #1, #2）。
*   因此 Pod 被永久阻塞在 `Pending` 状态，且由于无足够资源进行抢占（事实 #2），该状态将一直持续直至标签或选择器修正。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 45.7s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 45.5s (Evidence 38.0s, RCA 7.4s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
