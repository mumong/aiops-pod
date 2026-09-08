## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 in aiops-case-01 namespace is in Pending status, node assigned is <none>. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-68c557d875-bsq52` 状态: `Pending` | 确认 Pod 未被调度，处于停滞状态 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling` 持续 34m~23m：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 证实调度器已尝试调度但因节点亲和性/选择器不匹配而全部失败 |
| 3 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` = `1`；`phase="Unknown"` = `0` | 确认 Pod 始终停留在 Pending 阶段，未进入 Unknown 或 Running 状态 |
| 4 | K8s Config | Kubernetes | 容器内存请求 `8Mi`，限制 `32Mi`；CPU 请求 `5m`，限制 `50m` | 证明资源请求量极低，资源配额不足并非导致调度失败的直接原因 |

**证据互证说明**：
K8s 事件（证据 #2）明确指出了调度失败的原因为“未匹配 Pod 的节点亲和性/选择器”，且覆盖节点数为 0/3。结合状态（证据 #1）和指标（证据 #3）确认该 Pod 长期处于因调度受阻而导致的 Pending 状态。资源配置（证据 #4）排除了资源竞争因素，进一步聚焦于标签或选择器的不匹配问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 包含节点选择器 'aiops.lab/unavailable=true' → 集群中 0/3 节点携带该标签匹配失败 → Scheduler 报告 FailedScheduling 且无法抢占 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为**Pod 节点选择器与集群节点标签不匹配**。Pod 配置要求节点必须具备 `aiops.lab/unavailable=true` 标签，但集群中所有可用节点（3/3）均未满足此条件，导致调度器无法将 Pod 放置到任何节点上，表现为 Pod 长时间处于 Pending 状态。该结论由 K8s 事件中的 `FailedScheduling` 消息（证据 #2）直接支撑，且已通过低资源请求（证据 #4）排除了资源不足的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 57.9s
├─ 问题定位: 17.4s
├─ 并发证据采集: 32.4s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 32.4s (Evidence 25.5s, RCA 6.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
