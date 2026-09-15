## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源耗尽 (Insufficient cpu)，导致调度器无法为 Pod 分配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Pending | 确认 Pod 未能进入运行状态 |
| 2 | K8s State | kubernetes | `pod.condition` (type: PodScheduled): `status: False`, `reason: Unschedulable`, `message: 0/3 nodes are available: 3 Insufficient cpu` | 确认调度器因集群节点 CPU 耗尽而拒绝分配 Pod |
| 3 | K8s Event | kubernetes | `event.message` (x2): `FailedScheduling 8m38s (x2 over 13m) ... 0/3 nodes are available: 3 Insufficient cpu` | 提供调度失败的具体时间线和重复发生的事实（13分钟内连续2次），佐证资源短缺为持续状态 |
| 4 | K8s Config | kubernetes | `container.resource_request.cpu`: 100k (0.0001 Core) | 提供 Pod 的资源申请量，证实调度决策基于此申请进行计算 |

**证据说明**：
- K8s 事件（#3）的时间跨度（13分钟内2次警告）证实了集群 CPU 资源耗尽是导致 Pod 始终 Pending 状态的持续性原因，而非瞬时抖动。
- 节点状态（#2）与事件原因（#3）一致，明确指出 `Insufficient cpu` 为阻止调度的直接机制。

## 🎯 根因分析 · g1

```text
集群节点 CPU 资源耗尽 → 调度器无法满足 0.0001 Core 的 CPU 请求 → Pod 状态变为 Pending / Unschedulable → 服务未启动
```

### 根因结论
已确认的根因为 **集群节点 CPU 资源耗尽 (Insufficient cpu)**。

1. **现象确认**：`aiops-case-v01/workload` 的 Pod 状态为 `Pending`（证据 #1），且未满足 `PodScheduled` 条件（证据 #2）。
2. **直接原因**：调度器检查发现集群中 3 个节点均无可用的 CPU 资源，导致调度失败 `FailedScheduling`（证据 #2, #3）。
3. **因果链条**：集群整体 CPU 资源不足，致使调度器无法为申请 `100k` CPU 的 Pod 找到合适的节点，从而导致服务启动失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 25.8s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-v01/workload: 38.3s (Evidence 34.4s, RCA 3.8s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
