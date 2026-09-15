## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `workload` 定义了引用 PVC `unavailable-claim` 的 Volume，但该 PVC 在集群中不存在，导致调度器因无法满足存储依赖而持续拒绝调度 (FailedScheduling)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | event.message | `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 确认调度失败的直接触发条件为 PVC 缺失 |
| 2 | K8s State | pod.condition | `PodScheduled: False` (`message`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.`) | 描述 Pod 未调度（Schedulable）的客观状态 |
| 3 | K8s State | pod.phase / pod.status | `Pending` | 描述 Pod 当前运行所处阶段 |
| 4 | K8s Config | resource_request | `memory: 8Mi`, `cpu: 5m` | 排除因资源需求过大导致调度的可能性 |
| 5 | Metric | kube_pod_status_phase | `Pending` (1个样本) | 从指标维度独立证实 Pod 仍处于等待状态 |

证据表说明：
Kubernetes 侧的 Event、Pod Condition、Pod Phase 均高度一致地指向 `FailedScheduling` 及 `unavailable-claim` 缺失。Metric 数据作为辅助印证，确认 Pod 在采集时刻仍处于 Pending 状态，未发生状态转变。

## 🎯 根因分析 · g1

### 因果链

```text
PVC unavailable-claim 缺失 → 调度器无法满足 Volume 依赖 → FailedScheduling / Pod Scheduled=False → Pod 长期处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v03/workload` 依赖的 PVC `unavailable-claim` 在集群中不存在，导致调度器无法满足存储卷依赖。

该结论由以下事实互相印证：
1. 调度器 Event 明确指出 `persistentvolumeclaim "unavailable-claim" not found` 是拒绝调度的原因（证据 #1）；
2. Pod 的 `PodScheduled` 状态为 `False` 且报错信息一致，证实因该依赖导致的调度阻塞（证据 #2）；
3. Pod 持续处于 `Pending` 状态（证据 #3, #5），且其资源请求极低（证据 #4），彻底排除了由于集群算力或内存不足导致调度的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.4s
├─ 并发证据采集: 36.0s
│  └─ g1 aiops-case-v03/workload: 36.0s (Evidence 31.7s, RCA 4.2s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
