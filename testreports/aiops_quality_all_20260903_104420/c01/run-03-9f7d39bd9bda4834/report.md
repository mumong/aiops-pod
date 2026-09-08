## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 配置了 nodeSelector `aiops.lab/unavailable=true`，但集群中所有可用节点均不满足该标签选择器，导致调度器无法将 Pod 绑定到任何节点（FailedScheduling）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `phase: Pending`, `PodScheduled: False` (2026-09-03T02:44:26Z) | 确认 Pod 处于不可调度状态的事实。 |
| 2 | K8s Event | Kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (3m58s前) | 提供调度失败的直接原因：标签选择器不匹配。 |
| 3 | K8s Config | Kubernetes | `container.resource_request.cpu: 5m`, `memory: 8Mi` (容器 `app`) | 作为上下文，排除因资源超卖导致的调度失败。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.cpu: 50m`, `memory: 32Mi` (容器 `app`) | 作为上下文，排除因资源硬限制冲突导致的调度失败。 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` = 1 (phase: Pending) | 确认集群中该 Pod 实例目前保持 Pending 状态的监控事实。 |

**证据交叉印证说明：**
K8s Event (`#2`) 与 Pod State (`#1`) 相互印证，均指向调度失败且无节点满足亲和性要求；资源配置事实 (`#3`, `#4`) 证实请求量极低，佐证了失败并非由资源不足引起，而是纯粹的选择器匹配问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector: aiops.lab/unavailable=true → 集群 3 个节点均无此标签，调度器判定 0/3 节点可用 → FailedScheduling 事件 → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 的 `nodeSelector` 配置了 `aiops.lab/unavailable=true`，而集群中所有节点均不具备此标签。

根据 Kubernetes Event (`#2`) 和 Pod 状态 (`#1`)，调度器明确报告“3 node(s) didn't match Pod's node affinity/selector”。Pod 的资源请求极低（`#3`, `#4`），排除了资源竞争因素。因此，调度失败确认为标签选择器约束导致的节点匹配失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.5s
├─ 并发证据采集: 51.0s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 51.0s (Evidence 43.4s, RCA 7.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
