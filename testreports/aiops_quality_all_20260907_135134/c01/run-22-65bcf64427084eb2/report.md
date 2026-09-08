## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod workload-68c557d875-bsq52 持续处于 Pending 状态，无法调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (pod.status) | status: Pending | 直接确认 Pod 停留在调度前阶段 |
| 2 | K8s Event | kubernetes (event.message) | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available | 明确排除资源不足或抢占问题，指向亲和性/选择器不匹配 |
| 3 | K8s Config | kubernetes (container.resource_request) | cpu: 5m, memory: 8Mi | 资源请求极小，佐证失败原因非容量耗尽 |
| 4 | Metric | prometheus (kube_pod_status_phase) | value: 1, labels: {phase: "Pending"}, sample_count: 1 | 时序指标侧面印证 Pod 当前处于 Pending 状态 |

上述证据链清晰：Pod 因 `node_selector` 或 `node affinity` 约束无法满足而被调度器拒绝（#2），导致其停留在 Pending 状态（#1, #4）。极小的资源请求（#3）排除了资源瓶颈的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 node_selector 'aiops.lab/unavailable=true' (已知事实) → 集群所有 3 个节点均无该标签 (机制) → 调度器因亲和性/选择器约束不匹配返回 FailedScheduling (直接失败) → Pod 保持 Pending 状态 (用户可见现象)
```

### 根因结论

已确认根因为 **调度亲和性/选择器约束不匹配**。

集群中存在的 3 个节点均不具备 Pod 要求的标签或亲和性匹配条件，导致调度器无法为 Pod 分配任何节点。尽管集群存在容量，且 Pod 资源请求极低（5m CPU / 8Mi Memory），但节点标签的缺失是阻碍调度的直接且唯一原因，这也解释了为何 `preemption` 尝试无果（#2）。

---

## 📊 性能统计

```text
├─ 总耗时: 42.7s
├─ 问题定位: 13.0s
├─ 并发证据采集: 22.7s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 22.7s (Evidence 16.3s, RCA 6.3s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
