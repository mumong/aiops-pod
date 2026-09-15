## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod配置了不存在的节点选择器(aiops.lab/unavailable=true)，导致调度器无法在集群中找到匹配节点，持续Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `PodScheduled` 状态为 `False`，Reason: `Unschedulable` (fact-9f68ce366acb) | 确认 Pod 当前处于不可调度状态 |
| 2 | K8s State | Kubernetes | 拒绝原因：`3 node(s) didn't match Pod's node affinity/selector` (fact-9f68ce366acb) | 定位失败机制为节点亲和性/选择器不匹配 |
| 3 | K8s Event | Kubernetes | 事件 `Warning FailedScheduling`：持续 49 分钟内发生 7 次，确认 0/3 节点匹配 (fact-96f4aa01a147, fact-b63212190b1a) | 确认故障持续发生，且集群中无其他可调度目标 |
| 4 | K8s Config | Kubernetes | 资源配置：CPU Request 5m / Limit 50m, Memory Request 8Mi / Limit 32Mi (fact-3166acc6779f, fact-3f127bb30de1, fact-55dcf5897f57, fact-57b0bcfc2b43) | 确认资源请求值极小，非资源耗尽导致 Pending |
| 5 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` = 1；`kube_pod_status_phase{phase="Running"}` = 0 (fact-843c472a12b2, fact-01b5cb263455) | 独立观测确认 Pod 状态未发生转换，维持 Pending |

**证据说明**：
*   Kubernetes 的 Event 记录（证据 2、3）与 Pod 的 Condition 状态（证据 1）在“调度失败”这一结论上完全一致，且均指向节点选择器不匹配（Affinity/Selector Mismatch）。
*   尽管资源请求（证据 4）非常低，但调度仍然失败，排除了资源不足的可能性，进一步佐证了亲和性配置是唯一的阻断原因。
*   Prometheus 指标（证据 5）作为独立维度，验证了 Pod 自启动以来一直停留在 Pending 阶段，与 K8s 事件记录的时间范围相符。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的节点选择器(aiops.lab/unavailable=true) → 调度器筛选节点失败 (3/3 nodes rejected) → 调度事件 Warning FailedScheduling → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-01/workload-68c557d875-gtzc8` 配置了节点选择器 `aiops.lab/unavailable=true`，导致集群内所有节点（0/3）均不满足该亲和性/选择器条件。

**支撑事实**：
*   **现象确认**：Pod 处于 `Pending` 状态（证据 1、5）。
*   **机制确认**：调度器明确报错 `didn't match Pod's node affinity/selector`（证据 2、3）。
*   **排除其他**：资源请求极低（证据 4），且所有节点均被拒绝，排除了资源争用或其他非选择器类的调度限制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 20.2s
├─ 并发证据采集: 30.7s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 30.7s (Evidence 26.1s, RCA 4.6s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
