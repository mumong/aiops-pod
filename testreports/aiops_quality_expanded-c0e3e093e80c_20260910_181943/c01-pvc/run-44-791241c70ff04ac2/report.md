## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `workload` 的 Volume 定义中引用了不存在（或未被调度器找到）的 PersistentVolumeClaim `unavailable-claim`，导致调度器无法满足卷绑定依赖，持续触发 `FailedScheduling` 事件并将 Pod 维持在 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling 29m (x5 over 49m)`：`0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 证实调度器因找不到 PVC 而持续拒绝调度，是故障的直接触发器。 |
| 2 | K8s State | Pod Conditions | `PodScheduled=False`：`0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 确认 Pod 状态受 PVC 缺失限制，且无法通过抢占（preemption）恢复。 |
| 3 | Metric | `kube_pod_status_phase` | `Pending=1`，`Failed=0` | 验证 Pod 持续停留在 Pending 阶段，未转化为 Failed 或其他终态。 |

**证据互证说明：**
1. **事件 (1) 与状态 (2) 的因果关系**：调度器日志明确指出了缺失的对象 `unavailable-claim`；Pod 条件状态中的 Message 与事件完全一致，共同证明了 `Pending` 状态的直接原因是 Volume 绑定依赖失败。
2. **状态 (3) 的印证作用**：Metric 指标排除了 Pod 因资源过载或 CrashLoop 导致 `Failed` 的可能，确认异常停留在“等待资源就绪”阶段。

## 🎯 根因分析 · g1

### 因果链

```text
PVC unavailable-claim 不存在（未被调度器找到） → 调度器无法建立 Volume 绑定依赖 → Pod 触发 FailedScheduling 持续被拒绝 → 用户可见现象：Pod 处于 Pending 状态
```

### 根因结论

**已确认根因**：Pod `workload` 的 Volume 定义引用了不存在的 PersistentVolumeClaim `unavailable-claim`。

**证据支撑**：
- **K8s Event (`fact-6c30485c693c`, `fact-7737b4b9b73a`)** 连续记录显示调度器因 `persistentvolumeclaim "unavailable-claim" not found` 判定 `0/3 nodes are available`。
- **Pod Condition (`fact-cdd135ccc97d`)** 的状态消息与事件完全同步，证实了 Pod 被阻塞在 `PodScheduled` 阶段。
- **Metric (`fact-e492049cc425`)** 显示 `Pending` 状态持续存在，符合 PVC 缺失导致的等待现象。

**排除项**：资源限制（CPU 5m/50m，Memory 8Mi/32Mi）极小且未被标记为瓶颈（证据 `fact-01e81c38bd40`, `fact-5139b62e1629` 等仅作为上下文），Metric 也证实无 `Failed` 计数，故排除资源不足导致的竞态失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 24.4s
├─ 并发证据采集: 31.8s
│  └─ g1 aiops-case-v03/workload: 31.8s (Evidence 27.1s, RCA 4.7s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
