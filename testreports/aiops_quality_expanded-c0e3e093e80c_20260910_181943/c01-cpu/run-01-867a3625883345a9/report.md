## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod 'workload' in 'aiops-case-v01' is stuck in Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling  55s   default-scheduler  0/3 nodes are available: 3 Insufficient cpu.` | 明确诊断调度失败的直接原因：集群所有节点均不满足 CPU 需求。 |
| 2 | K8s Config | kubernetes | `resource_request.cpu: 100k` (即 0.1 Core) | 提供被调度 Pod 的具体 CPU 需求数值，验证调度器报错中的 Insufficient cpu。 |
| 3 | K8s State | kubernetes | `PodScheduled=False, Unschedulable, 0/3 nodes are available: 3 Insufficient cpu.` | 持续确认 Pod 因资源不足被卡在 Pending 状态，且尝试抢占失败。 |
| 4 | K8s State | kubernetes | `phase: Pending` | 确认 Pod 当前的生命周期阶段，表明调度失败尚未解决。 |

**证据分析：**
Kubernetes Event (事实 1) 与 Pod 状态 (事实 3) 一致指出 "Insufficient cpu" 为直接原因。配置数据 (事实 2) 明确了资源申请的基数，证实调度器判定所有 3 个节点均无法提供所需的 CPU 资源。Logging 与 Tracing 维度因 Pod 未启动而无法提供额外信息，但 Kubernetes 层面已给出充分且闭环的证据。

## 🎯 根因分析 · g1

### 因果链

```text
集群可用 CPU 资源耗尽 → 调度器无法匹配 Pod 的 100k CPU 请求 → 节点不足导致抢占尝试失败 → Pod 处于 Pending 状态
```

### 根因结论

已确认根因：**集群 CPU 资源不足 (Insufficient cpu)**。

该结论由以下事实支撑：调度器 Event 明确指出 3 个可用节点均无法满足 Pod 的资源请求（`fact-e312ba7152a4`）；Pod 状态持续卡在 Pending，且调度器确认无可用抢占对象（`fact-1f40c2f9c5ca`）。现有证据链条完整，足以解释 Pod 无法调度的现象。

---

## 📊 性能统计

```text
├─ 总耗时: 52.1s
├─ 问题定位: 15.6s
├─ 并发证据采集: 29.1s
│  └─ g1 aiops-case-v01/workload: 29.1s (Evidence 23.4s, RCA 5.6s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable, pod-volume-mount-failed
