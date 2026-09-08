## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52处于Pending状态，无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-5777cffa1fb4) | 直接归因：节点选择器不匹配导致调度失败 |
| 2 | K8s State | kubernetes | `pod.status: Pending` (fact-a43a6fd92137) | 症状：Pod 当前处于不可调度状态 |
| 3 | K8s State | kubernetes | `pod.condition.PodScheduled: False (Unschedulable)` (fact-74388edbe1a3) | 症状：Pod 调度条件未满足 |
| 4 | K8s Config | kubernetes | `container.resource_request.cpu: 5m` (fact-421d01139f98) | 上下文：资源请求量极小，非资源不足导致 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` (fact-6f39b46d2262) | 上下文：内存请求量极小，非资源不足导致 |
| 6 | Metric | prometheus | `kube_pod_status_phase(phase=Pending) = 1` (fact-efe5e40248d6) | 确认：监控确认该 Pod 持续处于 Pending 阶段 |

**证据总结**：
Kubernetes 事件 (fact-5777cffa1fb4) 与 Pod 条件状态 (fact-74388edbe1a3) 高度一致，明确指出了调度失败的具体原因是 "affinity/selector" 不匹配。资源请求数据 (fact-421d01139f98) 表明该限制不是由 CPU/Memory 容量不足引起的。Metric (fact-efe5e40248d6) 提供了持续的监控佐证。由于 Pod 未启动，Logging 与 Tracing 数据不适用。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义 nodeSelector: {aiops.lab/unavailable: true} → 集群节点缺少对应标签 → 调度器无法匹配 3/3 节点 → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod 的调度约束（nodeSelector）与集群实际节点标签不兼容。
具体而言，Pod 被要求必须调度到具有 `aiops.lab/unavailable=true` 标签的节点上，但调度器在集群所有可用节点（3个节点）中均无法找到满足此条件的目标（证据：fact-5777cffa1fb4）。
现有 Kubernetes 事实（事件、配置）已构成闭环证据，无需 Logging/Tracing 补充即可判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.4s
├─ 并发证据采集: 47.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 47.3s (Evidence 39.4s, RCA 7.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
