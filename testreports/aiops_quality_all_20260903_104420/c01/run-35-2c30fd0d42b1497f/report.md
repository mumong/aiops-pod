## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，节点为 <none>，持续 71 分钟未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 核心异常信号，明确调度失败的直接原因是节点亲和性/选择器不匹配 |
| 2 | K8s State | Kubernetes | `PodScheduled` 条件状态 `False`，Reason: `Unschedulable` | 确认 Pod 处于持续的未调度状态 |
| 3 | K8s Config | Kubernetes | 容器资源请求：CPU `5m`, Memory `8Mi`；限制：CPU `50m`, Memory `32Mi` | 资源请求极低，排除资源配额不足导致的调度失败 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` (Pending): `1` | 确认 Pod 持续处于 Pending 状态，无其他状态波动 |

**证据印证：**
Kubernetes 事件与状态均一致指向 `Unschedulable` 阶段。事件原文 `3 node(s) didn't match Pod's node affinity/selector` 结合极低且合理的资源配置（证据 3），证明该异常纯粹由调度约束（选择器/亲和性）与集群实际节点拓扑不匹配导致，而非容量或资源竞争问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 调度约束配置为 nodeSelector: {aiops.lab/unavailable: true} → 集群所有 3 个节点均未匹配该节点选择器/亲和性要求 → 调度器触发 FailedScheduling 事件，PodScheduled 条件为 False → Pod 停留在 Pending 状态
```

### 根因结论

**已确认的根因：** Pod 配置了节点选择器 `aiops.lab/unavailable=true`，但集群中所有可用节点均不包含该标签，导致调度器无法找到匹配节点（NodeSelector 不匹配）。

**证据支撑：**
- **直接现象**：K8s Event 报告 `3 node(s) didn't match Pod's node affinity/selector`（证据 1），确认集群节点无法满足 Pod 的亲和性约束。
- **状态确认**：Pod 状态 `Pending`（证据 2、4），且持续时间长达 71 分钟，证明该约束问题持续存在。
- **排除资源瓶颈**：容器的资源请求（证据 3）极低，表明集群拥有足够的调度能力，问题仅限于拓扑约束匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.5s
├─ 并发证据采集: 43.8s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 43.8s (Evidence 35.1s, RCA 8.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
