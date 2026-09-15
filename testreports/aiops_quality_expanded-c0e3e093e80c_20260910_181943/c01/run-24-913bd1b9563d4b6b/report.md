## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 的 nodeSelector 配置为 'aiops.lab/unavailable=true'，但集群中所有可用节点均缺少该标签，导致调度器无法满足亲和性约束，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod condition | `PodScheduled=False`, reason=`Unschedulable`, message=`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 提供直接的调度失败原因，证明亲和性/选择器匹配失败 |
| 2 | K8s Event | Event message | `FailedScheduling` (36m, 25m), `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认调度器在时间窗口内持续判定调度失败，支持状态 1 |
| 3 | K8s Config | Resource Requests | `memory: 8Mi`, `cpu: 5m` | 资源请求极低，排除了资源不足作为本次调度失败的主因 |
| 4 | K8s Config | Resource Limits | `memory: 32Mi`, `cpu: 50m` | 仅作为资源配置上下文，证明不存在硬限制引发的冲突 |
| 5 | Metric | `kube_pod_status_phase` | `Pending=1` (Succeeded=0) | 状态指标与 K8s State 一致，确认 Pod 自始至终处于等待调度状态 |

**证据印证说明：**
K8s State 与 K8s Event 均一致指向“节点不匹配亲和性/选择器”（fact 1, 2）。Metrics 确认了 Pod 持续 Pending 的状态（fact 5）。资源请求极低（fact 3, 4）排除了资源耗尽导致的 Unschedulable。证据形成闭环，明确故障原因为调度器因标签/亲和性约束不匹配而拒绝调度。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了节点选择器/亲和性约束（未直接匹配节点标签） → 调度器判定节点不匹配（Affinity/Selector Mismatch） → 调度器拒绝绑定 Pod → Pod 持续处于 Pending (Unschedulable) 状态
```

### 根因结论

**已确认的根因：** Pod 的调度亲和性配置（节点选择器或亲和性规则）要求节点包含特定标签，但集群中所有 3 个可用节点均不满足该条件，导致 `default-scheduler` 无法为 Pod 分配任何节点。

*   **事实支撑：**
    *   `PodScheduled` 条件明确报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact 1)。
    *   连续两次 `FailedScheduling` 事件确认了该状态是持续性的而非瞬时抖动 (fact 2)。
    *   资源请求极低（8Mi/5m），确认节点未因资源不足而不可用 (fact 3, 4)。
    *   调度器未尝试抢占（`preemption: 0/3`），表明根本原因是硬性约束无法满足 (fact 2)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 25.3s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 32.3s (Evidence 26.6s, RCA 5.6s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
