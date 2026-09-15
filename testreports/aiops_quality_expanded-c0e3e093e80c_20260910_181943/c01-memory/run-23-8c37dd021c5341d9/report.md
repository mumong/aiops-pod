## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 持续处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling 27m (x2 over 32m) default-scheduler 0/3 nodes are available: 3 Insufficient memory.` (fact-f4cdf3027dae) | 确认调度失败，且失败原因均为内存不足 |
| 2 | K8s State | Kubernetes | `pod.condition` 状态 `False`, reason `Unschedulable`, message `0/3 nodes are available: 3 Insufficient memory.` (fact-82dd44449be4) | 证实 Pod 因无法满足节点资源需求而被持续标记为不可调度 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory`: 1Pi (fact-0ca8a9ade4be) | 直接证明调度所需资源远超集群总量，是触发 Insufficient memory 的直接原因 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: 1Pi (fact-19597e69d7d4) | 确认 Pod 声明的内存资源规格极其不合理 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` 在 Pending 状态下值为 1 (fact-0c72d57928f5) | 独立验证 Pod 当前持续处于 Pending 状态 |

**证据印证说明：**
Kubernetes 事件 (fact-f4cdf3027dae) 和 Pod 条件状态 (fact-82dd44449be4) 一致表明调度器在所有节点上均遭遇内存不足。Prometheus 指标 (fact-0c72d57928f5) 从时序数据上佐证了 Pod 始终处于 Pending 状态。根本原因在于 (fact-0ca8a9ade4be, fact-19597e69d7d4) 中配置了高达 1Pi 的内存请求与限制，导致 3 个节点均无法满足该需求且无预emption 候选者，从而直接导致 Pod 持续无法调度。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1Pi 的 memory limit 且 request 也被置为 1Pi (fact-0ca8a9ade4be, fact-19597e69d7d4) → 调度器计算所需资源远超任何可用节点的 allocatable memory → default-scheduler 尝试 3 个节点均返回 3 Insufficient memory (fact-82dd44449be4) → 预emption 检查无受害者，调度持续失败，Pod 保持 Pending (fact-f4cdf3027dae, fact-0c72d57928f5)
```

### 根因结论

已确认根因为 **Pod 资源规格配置错误**。Pod 配置了不切实际的内存规格（1Pi），该资源请求远超集群中任何节点的能力上限，导致 `default-scheduler` 在所有节点上均因 `Insufficient memory` 而调度失败，且由于资源需求过大，系统无法寻找任何“预emption”候选者来释放资源，从而导致 Pod 持续处于 `Pending` 状态。证据 (fact-0ca8a9ade4be, fact-19597e69d7d4) 与 (fact-82dd44449be4, fact-f4cdf3027dae) 形成了完整的证据闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.1s
├─ 并发证据采集: 40.5s
│  └─ g1 aiops-case-v02/workload: 40.5s (Evidence 32.2s, RCA 8.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
