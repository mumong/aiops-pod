## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload in aiops-case-v03 namespace is stuck in Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `PodScheduled=False`, reason: `Unschedulable`, message: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 明确展示调度失败的真实原因（PVC 缺失） |
| 2 | K8s Event | event.message | `Warning FailedScheduling 30m default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 佐证调度器因 PVC 不存在而反复失败的事实 |
| 3 | K8s State | pod.status | `status: Pending`, `phase: Pending` | 确认 Pod 因上述调度失败而长期处于 Pending 状态 |
| 4 | K8s Config | resource | `request.cpu=5m`, `request.memory=8Mi`, `limit.cpu=50m`, `limit.memory=32Mi` | 排除资源配额（CPU/内存）或集群节点资源不足导致的调度失败 |
| 5 | Metric | kube_pod_status_phase | `phase: Pending`, `value: 1` (单样本, 无趋势) | 独立于 K8s API 确认当前集群中有 1 个处于 Pending 状态的 Pod |

**证据关联说明**
K8s API 的状态字段与事件消息高度一致，均明确指向名为 `unavailable-claim` 的 PVC 缺失。资源配置数据显示请求值极低且未触及硬限制，直接排除了资源竞争因素；Metrics 确认了 Pod 当前持续处于 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
未找到 PersistentVolumeClaim "unavailable-claim" → 调度器在绑定卷阶段失败 → FailedScheduling (PVC not found) → Pod 卡在 Pending 状态
```

### 根因结论

已确认的根因是：Pod 声明挂载了一个名为 `unavailable-claim` 的 `PersistentVolumeClaim`，但该 PVC 在 `aiops-case-v03` 命名空间中不存在。这导致 `default-scheduler` 在尝试调度时判定无可用节点，并持续抛出 `FailedScheduling` 事件，使 Pod 始终无法进入 `Running` 状态（证据 1、2、3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.1s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-v03/workload: 32.3s (Evidence 26.8s, RCA 5.4s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
