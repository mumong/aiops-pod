## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `FailedScheduling 48m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-bcd3e346411b) | 确认调度器因节点亲和性/选择器不匹配而连续拒绝 Pod 调度。 |
| 2 | K8s State | `kubernetes` | `pod.status: Pending` (fact-b621094ab4a1) | 确认 Pod 当前处于调度等待状态，尚未被分配节点。 |
| 3 | Metric | `prometheus` | `kube_pod_status_phase[phase="Pending"] = 1` (fact-1b8be9045821) | 从监控指标维度独立确认 Pod 处于 Pending 阶段，佐证状态未改变。 |
| 4 | K8s Config | `kubernetes` | 资源请求: `cpu=5m`, `memory=8Mi`；资源限制: `cpu=50m`, `memory=32Mi` (fact-ea197db6400a, fact-f0faedc4334c, fact-f1bf3a3931e7, fact-0774e89bf0bb) | 资源请求量极低，排除了因资源不足导致调度的可能性。 |

**证据综合说明：**
1. 事件与状态强关联：K8s Event (证据 #1) 明确给出了 `Pending` 的物理原因（不匹配亲和性），且与 Pod State (证据 #2) 和 Metrics (证据 #3) 的状态完全一致。
2. 资源非主因：配置事实 (证据 #4) 表明资源门槛极低，进一步排除了资源争用，将问题聚焦于调度器过滤阶段（Affinity/Selector）。
3. 其他维度受限：Logging 和 Tracing 因容器未启动无法提供额外信息，当前证据已闭环于“调度阶段失败”这一现象。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：Pod 配置了 NodeSelector 'aiops.lab/unavailable=true' → 失败机制：集群节点缺乏该标签，调度匹配失败 → 直接失败：default-scheduler 持续抛出 FailedScheduling 事件 → 用户可见现象：Pod 维持 Pending 状态
```

### 根因结论

已确认根因为：**Pod 配置了不存在的标签选择器（NodeSelector: `aiops.lab/unavailable=true`）**。

该配置导致调度器在集群 3 个节点上均无法找到匹配项（证据 #1），从而触发 `FailedScheduling` 事件，使 Pod 始终处于 `Pending` 状态。资源需求极低（证据 #4）进一步印证了该失败是由标签匹配逻辑而非资源不足引起的。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 31.3s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 41.1s (Evidence 34.3s, RCA 6.6s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
