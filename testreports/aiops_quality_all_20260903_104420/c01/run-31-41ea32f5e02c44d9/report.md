## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了 nodeSelector 'aiops.lab/unavailable=true'，而集群内所有 3 个节点均缺失该标签，导致调度器因节点亲和/选择器不匹配（FailedScheduling）而无法调度 Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `phase: Pending` | 确认目标 Pod 停留在初始化阶段，尚未被调度到任何节点。 |
| 2 | K8s Event | event.message | `Warning FailedScheduling 30m (x8 over 65m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` | 直接归因证据：调度器因亲和/选择器不匹配拒绝调度，且明确排除预emption 可能性。 |
| 3 | K8s Config | container.resource_request | `cpu: 5m`, `memory: 8Mi` | 排除资源超卖或资源不足导致的调度阻塞，确认为纯标签/选择器问题。 |
| 4 | Metric | prometheus | `kube_pod_status_phase(phase="Pending")` = 1 (持续观测) | 量化佐证：集群内目标 Pod 长期处于 Pending 状态，无向上游自愈的迹象。 |

**证据印证说明：**
- **事实 2 (Event)** 直接指出失败原因为 `3 node(s) didn't match Pod's node affinity/selector`，这解释了 **事实 1 (State)** 中 Pod 为何永远处于 Pending 状态。
- **事实 3 (Config)** 的资源请求极低（5m CPU, 8Mi Mem），结合 Event 中的全节点不匹配，排除了节点资源紧张导致 Pod 被挤占的可能，进一步锁定根因为 Pod 配置与集群节点标签的不兼容。
- **事实 4 (Metric)** 作为时间维度的佐证，确认了该故障状态已持续一定时间且未自动恢复。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector 'aiops.lab/unavailable=true' → 集群节点缺失该标签导致调度匹配失败 → 调度器抛出 FailedScheduling 事件拒绝绑定 → Pod 持续保持 Pending 状态无法启动
```

### 根因结论

**已确认根因**：调度器亲和/选择器配置冲突。

目标 Pod 配置了 `nodeSelector: { aiops.lab/unavailable: "true" }`，但集群内所有 3 个节点均未设置该标签（或设置为 false），导致 `default-scheduler` 无法满足调度要求。调度器反复尝试失败（Event 显示 30 分钟内重试 8 次），且明确提示 `3 node(s) didn't match Pod's node affinity/selector`。由于缺乏符合标签要求的节点，Pod 无法被调度，处于不可恢复的 Pending 状态。该诊断基于 **事实 1、2、3** 的直接证据链，证据充分且相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 42.4s
├─ 并发证据采集: 38.4s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 38.4s (Evidence 32.1s, RCA 6.2s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
