## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 持续处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending` | 确认 Pod 处于未调度状态，直接体现调度失败的症状。 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory: 1Pi` | 暴露异常的资源请求配置。1Pi 远超常规物理节点容量，是导致资源判定失败的根本配置。 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 1Pi` | 确认内存限制同样配置为 1Pi，限制与请求一致，进一步排除了仅是 Request 过高的假设。 |
| 4 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory` | 调度器的明确报错，证实集群所有 3 个节点均无法提供所需的内存资源。 |

以上证据表明，Pod 持续 Pending 的根本原因是调度器在尝试调度时，在所有 3 个可用节点上均因 `Insufficient memory` 而失败。这一结果与 `container.resource_request.memory` 被设定为 `1Pi` 的配置事实完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存请求与限制配置为 1Pi → 调度器在节点资源筛选时发现所有节点内存不足 → 触发 FailedScheduling 事件 → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为：Pod 容器 `app` 的内存资源请求（`1Pi`）和限制（`1Pi`）严重超出集群所有节点的可用物理内存容量，导致 Kubernetes 调度器在所有 3 个节点上均判定 "Insufficient memory" 并拒绝调度。

依据：
- 配置事实显示内存请求/限制均为 1Pi (`fact-c6ba3adce7e0`, `fact-f1e7f93b25e8`)；
- 调度事件显示所有 3 个节点均报告内存不足 (`fact-1c26bfb77241`)；
- Pod 状态确认为 Pending (`fact-86edf56e3bbd`)。

---

## 📊 性能统计

```text
├─ 总耗时: 53.1s
├─ 问题定位: 13.2s
├─ 并发证据采集: 32.4s
│  └─ g1 aiops-case-v02/workload: 32.4s (Evidence 23.1s, RCA 9.2s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
