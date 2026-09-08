## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod nodeSelector (aiops.lab/unavailable=true) 与集群所有节点标签不匹配导致调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 3 node(s) didn't match Pod's node affinity/selector (fact-fce965210bca) | 核心证据：明确指示调度失败源于节点亲和性/选择器不匹配 |
| 2 | K8s State | kubernetes | `PodScheduled=False`, Reason=`Unschedulable`, Message=`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-a2737823b3e7) | 确证事实：与事件一致，表明所有节点均不符合 Pod 的亲和性要求 |
| 3 | K8s State | kubernetes | `status: Pending` (fact-8c5b40e91e39) | 现象：Pod 始终处于调度挂起状态，未进入运行态 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase=Pending) = `1`; (phase=Failed) = `0` (fact-6206dabce57b) | 交叉验证：监控系统确认 Pod 保持 Pending 状态且无失败计数，符合未调度的特征 |

证据 1 和 2 均指向同一调度错误（亲和性不匹配），且 Metric 数据确认 Pod 持续处于 Pending 状态而非 CrashLoop，共同支撑“节点选择器导致调度失败”的结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod nodeSelector (aiops.lab/unavailable=true) 配置 → 集群节点标签不匹配导致调度失败 → 状态保持 Pending → 用户可见 Pod 无法正常启动
```

### 根因结论

已确认根因为 **Pod nodeSelector (`aiops.lab/unavailable=true`) 与集群中所有节点的标签不匹配** [证据: 1, 2]。调度器（default-scheduler）在尝试调度时，发现集群中不存在带有该特定标签的节点，导致调度条件无法满足，Pod 被标记为 `Unschedulable` 并保持 `Pending` 状态 [证据: 3, 4]。

---

## 📊 性能统计

```text
├─ 总耗时: 56.9s
├─ 问题定位: 18.8s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 30.6s (Evidence 25.4s, RCA 5.0s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
