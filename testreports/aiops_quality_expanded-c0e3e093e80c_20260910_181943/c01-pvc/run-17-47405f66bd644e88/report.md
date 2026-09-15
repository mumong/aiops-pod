## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod yaml 中声明引用了 PVC 'unavailable-claim'，但该 PVC 在 aiops-case-v03 命名空间中不存在（not found），导致调度器因无法满足存储卷挂载需求而将 Pod 保持在 Pending (Unschedulable) 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 调度器明确拒绝调度的原因：找不到 PVC |
| 2 | K8s State | kubernetes | `PodScheduled=False`: `persistentvolumeclaim "unavailable-claim" not found` | 状态条件与事件消息一致，确认阻塞状态 |
| 3 | K8s State | kubernetes | `Pod phase/status`: `Pending` | 确认 Pod 始终处于未调度状态 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}`: `1` | 从指标维度独立观测到 Pod 持续处于 Pending 状态 |

**证据说明：**
1. K8s Event (fact-3ebe3c1709c1) 和 K8s State (fact-987ff856ef9c) 直接指出了 `unavailable-claim` PVC 缺失是导致调度失败的直接原因。
2. Metric 数据 (fact-8967932aa9e3) 确认了 Pod 的 Pending 状态是客观存在的持续状态，而非瞬时波动。
3. 资源限制配置 (Fact IDs: 2fdd1ca4da0a, 72e819d3438c, 81efd0fd8e58, 8e4e0624c935) 显示资源请求量极低，排除资源竞争导致的调度延迟。

## 🎯 根因分析 · g1

### 因果链

```text
PVC 'unavailable-claim' 不存在 → 调度器亲和性检查失败 → Pod 保持 Unschedulable/Pending 状态
```

### 根因结论

已确认根因：Pod yaml 声明依赖的 PVC `unavailable-claim` 在 `aiops-case-v03` 命名空间中不存在，导致 K8s 调度器无法分配存储卷，从而将 Pod 保持在 `Pending (Unschedulable)` 状态。

**引用证据：**
- 事件消息明确指出 `persistentvolumeclaim "unavailable-claim" not found`（见证据 1, 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.8s
├─ 并发证据采集: 40.6s
│  └─ g1 aiops-case-v03/workload: 40.6s (Evidence 32.1s, RCA 8.5s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
