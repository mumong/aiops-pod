## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 持续 Pending 77分钟未调度，且无IP分配 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 12m (x13 over 72m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact-83fc92691142) | 证明调度器因节点选择器不匹配连续 13 次拒绝该 Pod，且排它性约束导致预emption 无效。 |
| 2 | K8s Config | kubernetes | `container: app, resource_request.cpu: 5m, resource_request.memory: 8Mi` (fact-388228cfba2a, fact-3b3d724d4591) | 展示资源请求极低，排除了资源容量不足导致 Pending 的可能。 |
| 3 | K8s Config | kubernetes | `container: app, resource_limit.cpu: 50m, resource_limit.memory: 32Mi` (fact-2d067d391313, fact-a99916b49f33) | 确认硬限制存在，进一步佐证调度失败并非由突发资源超限引起。 |
| 4 | K8s State | kubernetes | `status: Pending` (fact-f61cace08433) | 确立最终异常状态，证实容器未进入运行期，属于部署/调度阶段阻断。 |
| 5 | Metric | prometheus | `kube_pod_status_phase(phase="Pending") = 1` (fact-fd9e0371f3d9) | 指标侧独立确认该 Pod 持续处于 Pending 阶段。 |
| 6 | Metric | prometheus | `kube_pod_status_phase(phase="Running") = 0` (fact-48defbf749bd) | 指标侧确认 Pod 从未成功启动，排除了启动后崩溃导致 Pending 回退的可能。 |

**证据分析：**
K8s Event (fact-83fc92691142) 提供了核心诊断逻辑，明确指出了 `0/3 nodes are available` 是由于节点选择器不匹配（affinity/selector）。同时，Metric 数据 (fact-fd9e0371f3d9, fact-48defbf749bd) 从时序角度证实了该 Pod 长时间内一直处于 Pending 状态。由于 K8s Event 已明确归因于选择器匹配失败，而资源请求极低，因此资源限制配置 (fact-2d067d391313, fact-388228cfba2a) 在此处主要起佐证排除作用，证明非容量问题。Logging/Tracing 因 Pod 未启动而不可用，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 中配置了 `aiops.lab/unavailable=true` 节点选择器（约束） → 集群内 3 个节点均不匹配该选择器（机制） → 调度器连续 13 次尝试失败且预emption 无效（直接失败） → Pod 持续处于 Pending 状态且未分配 Node（现象）
```

### 根因结论

已确认的根因为：**Pod Spec 中的节点选择器（Node Affinity/Selector）配置错误。**

Pod 被配置了 `aiops.lab/unavailable=true` 的节点选择器约束，该约束要求目标节点必须具备 `aiops.lab/unavailable=true` 的标签。然而，集群内现有的 3 个节点均不具备此标签（或该标签值不匹配），导致调度器无法为 Pod 找到任何可用的候选节点（`0/3 nodes are available`）。

*   **支撑证据**：K8s Event (fact-83fc92691142) 明确提示节点未匹配 Pod 的节点亲和性/选择器；Metric (fact-fd9e0371f3d9) 确认了长期 Pending 状态；资源配置 (fact-388228cfba2a) 排除了资源瓶颈。
*   **未确认项**：该节点选择器配置 `aiops.lab/unavailable=true` 是业务故意用于隔离测试的配置，还是因拼写错误（例如想匹配 `aiops.lab/available=true`）导致的配置失误，现有证据无法直接判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.4s
├─ 并发证据采集: 34.5s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 34.5s (Evidence 24.9s, RCA 9.5s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
