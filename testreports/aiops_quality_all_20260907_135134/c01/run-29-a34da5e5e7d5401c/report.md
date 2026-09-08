## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 持续处于 Pending 状态且未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | phase=Pending, status=Pending, reason=Unschedulable | 明确 Pod 处于调度失败的停滞状态 |
| 2 | K8s Event | Scheduler | FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector | 确认调度失败的具体原因为节点亲和性与选择器不匹配 |
| 3 | K8s Event | Scheduler | (x7 over 41m) FailedScheduling 重复发生，Preemption 无效 | 证明问题具有持续性，且无法通过抢占缓解 |
| 4 | K8s Config | Resource Limit | container: app, memory=32Mi, cpu=50m | 提供资源上限信息（32Mi 极低，但并非导致调度失败的直接原因） |
| 5 | K8s Config | Resource Request | container: app, memory=8Mi, cpu=5m | 提供资源请求信息，表明资源量本身很小 |

**证据综合说明**：
Kubernetes 事件与 Pod 状态 (事实 #1, #2) 高度一致，均指向 `FailedScheduling`，明确排除了资源不足（通常报告为 Insufficient CPU/Memory）的可能性，将根本原因锁定在调度策略层面。重复的调度失败事件 (事实 #3) 证实了问题的稳定性。资源配置 (事实 #4, #5) 数值极小，侧面验证了集群中不存在因资源极度紧张导致的调度瓶颈。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector {aiops.lab/unavailable: true} → 集群节点均不包含 aiops.lab/unavailable=true 标签 → default-scheduler 触发 FailedScheduling 事件 → Pod 持续 Pending，node=<none>
```

### 根因结论

**已确认的根因**：Pod 配置了 `nodeSelector {aiops.lab/unavailable: true}`，而集群中所有 3 个可用节点均缺少该标签，导致调度器因节点选择器不匹配而持续拒绝调度（FailedScheduling）。

该结论由事实 #2（调度器明确报告节点未匹配选择器）与事实 #1（Pod 持续 Pending）直接支撑。由于集群中没有任何节点满足该标签要求，调度器无可用节点可调度，且预抢占机制（Preemption）因无符合亲和性条件的目标节点而无法生效（事实 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.2s
├─ 并发证据采集: 34.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 34.8s (Evidence 25.9s, RCA 8.7s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
