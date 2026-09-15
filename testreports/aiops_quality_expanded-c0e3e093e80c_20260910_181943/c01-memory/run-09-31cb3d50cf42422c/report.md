## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod资源配置请求memory=1Pi远超集群节点可用内存，导致调度器因Insufficient memory无法将Pod调度至任何节点且无Preemption可能。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending` (fact_id: `fact-5ab53ca0c3aa`) | 确认 Pod 处于未调度状态，直接症状 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory: 1Pi` (fact_id: `fact-ccaea5d52ce3`) | 暴露资源请求值高达 1 Petabyte，明显超出常规集群规模 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 1Pi` (fact_id: `fact-bfd1e0574669`) | 确认硬限制与请求值一致，无弹性调度缓冲 |
| 4 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` (fact_id: `fact-6cf90bcec40b`, `fact-a666cf7b104a`) | 调度器核心反馈，明确判定所有节点内存不足且无法抢占 |
| 5 | Metric | prometheus | `kube_pod_status_phase(phase=Pending): 1` (fact_id: `fact-c37d2135d5d2`) | 监控指标印证 Pod 停留在 Pending 阶段 |
| 6 | Metric | prometheus | `kube_pod_status_phase(phase=Unknown): 0` (fact_id: `fact-11267d085be4`) | 排除 Pod 进入 Unknown 状态或调度异常分支，仅停留在 Pending |

**证据分析：**
K8s 配置事实证实 Pod 请求了 `1Pi` 内存，这一极端数值直接导致了调度失败。`FailedScheduling` 事件明确指出由于集群所有节点均无法提供足够的内存资源（`Insufficient memory`）且无抢占候选者，导致调度器放弃调度。Metric 数据作为辅助确认，仅显示 Pod 停留在 Pending 状态，没有更多变体。由于 Pod 始终未被调度，日志和链路追踪数据均为空（物理上无法生成），但这不影响基于 K8s 原生事件和配置得出确定性结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod资源请求memory=1Pi设定过高 → 集群所有节点内存不足(Insufficient memory)且无Preemption候选 → 调度器持续返回FailedScheduling错误 → Pod处于Pending状态
```

### 根因结论

已确认的根因是 **Pod 资源请求配置异常**。具体而言，Pod 的 `container.resource_request.memory` 被设置为 `1Pi`（1 Petabyte），这一数值远超常规集群节点的可用内存容量，导致 `default-scheduler` 无法找到任何满足条件的节点进行调度。调度器在尝试调度时返回了明确的 `FailedScheduling` 事件，指出所有 3 个节点均因内存不足且无法执行抢占操作而失败。现有证据链条完整（配置异常 -> 调度失败 -> 状态锁定），无需补充其他维度的日志或指标即可定责。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 16.0s
├─ 并发证据采集: 549.1s
│  └─ g1 aiops-case-v02/workload: 549.1s (Evidence 544.8s, RCA 4.2s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
