## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，节点为 <none>，PodScheduled=False。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `Warning FailedScheduling ... 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` (fact_id: fact-2577db867b5f, 重复 2 次) | 直接表明调度失败原因为 PVC 缺失 |
| 2 | K8s State | pod.condition | `PodScheduled=False`，原因 `Unschedulable`，消息指向同一个 `unavailable-claim` not found (fact_id: fact-0a3820454ca1) | 确认 Pod 处于持续不可调度状态 |
| 3 | K8s Config | container.resource_request.memory | `8Mi` (fact_id: fact-7659703b430e) | 排除内存资源请求过高导致的调度阻塞 |
| 4 | K8s Config | container.resource_limit.cpu | `50m` (fact_id: fact-79baf3214a4e) | 排除 CPU 限制过高导致的调度阻塞 |
| 5 | Metric | prometheus (Pending) | `kube_pod_status_phase` (phase="Pending") = 1 (fact_id: fact-f5c3559e8e39) | 确认 Pod 阶段维持为 Pending |
| 6 | Metric | prometheus (Running) | `kube_pod_status_phase` (phase="Running") = 0 (fact_id: fact-0268d24ae65c) | 确认无副本处于运行状态 |

**证据关联说明**：
Kubernetes 的事件 (1) 与 Pod 条件状态 (2) 共同确认了 `Pending` 状态由 `FailedScheduling` 导致，且根因锁定在 `unavailable-claim` 的卷绑定环节。Metric 数据 (5, 6) 佐证了该状态在观测窗口内的持续性。资源配置检查 (3, 4) 排除了资源不足的可能性，确证是 PVC 引用错误导致的问题。由于容器未启动，Logging 和 Tracing 维度无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 声明引用 PVC 'unavailable-claim' → PVC 在当前 namespace (aiops-case-v03) 中不存在 (Not Found) → Scheduler 无法绑定卷，返回 FailedScheduling 错误 → Pod 保持 Pending 状态，无法分配 nodeName
```

### 根因结论

已确认根因为：Pod YAML 定义中引用了名为 `unavailable-claim` 的 PVC，该 PVC 在当前 namespace `aiops-case-v03` 中不存在。

这一缺失直接导致 Kubernetes 调度器在执行卷绑定检查时失败，持续拒绝调度 Pod，从而表现出 Pod 处于 `Pending` 状态且 `PodScheduled` 条件为 `False` 的现象。证据 1 和 2 提供了决定性的事实支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 56.3s
├─ 问题定位: 17.8s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-v03/workload: 28.6s (Evidence 19.8s, RCA 8.7s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
