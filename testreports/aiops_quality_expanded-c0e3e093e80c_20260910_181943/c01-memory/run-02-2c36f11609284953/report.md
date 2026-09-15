## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 持续处于 Pending 状态，调度失败 (FailedScheduling: 0/3 nodes are available: 3 Insufficient memory) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` (Fact: fact-5ece098656c4) | `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 确认调度器判定所有节点资源不足且无法抢占 |
| 2 | K8s Config | 容器资源限制 (Fact: fact-1d619719e15f) | `1Pi` (1 PiB) | 暴露 Pod 配置的极值内存限制 |
| 3 | K8s Config | 容器资源请求 (Fact: fact-62a56250fab5) | `1Pi` (1 PiB) | 暴露调度器必须满足的 1 PiB 内存硬请求 |
| 4 | K8s State | Pod 状态 (Fact: fact-3bc27a916066) | `PodScheduled=False`, `reason=Unschedulable` | 证明 Pod 处于不可调度的终态 |
| 5 | Metric | Prometheus (Fact: fact-4407cf92f67e) | `1125899906842624` bytes (1 PiB) | 独立数值确认 Pod 内存请求量为 1 PiB |

上述证据表明，Pod `aiops-case-v02/workload` 的 `Pending` 状态是由资源调度失败引起的。调度器返回的 `3 Insufficient memory` 错误，结合 K8s 配置中高达 `1Pi` 的内存 Request/Limit 以及 Prometheus 指标中精确的 `1125899906842624` bytes 数值，构成了闭环证据链。由于配置请求量远超常规集群节点的物理内存上限，导致无任何节点可满足资源约束，且缺乏可被驱逐的预emption 对象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1PiB (1,125,899,906,842,624 bytes) 的内存请求/限制 → 
调度器在 0/3 节点上无法找到满足该硬性请求的资源 → 
调度失败 (Insufficient memory) 且无抢占空间 (No preemption victims) → 
Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 资源请求超出集群节点物理上限**。

事实支持如下：
1. **配置极值异常**：容器 `app` 的内存请求 (`resource_request.memory`) 和限制 (`resource_limit.memory`) 均被设置为 `1Pi` (Fact: 2, 3)。
2. **调度失败验证**：Kubernetes Event 明确指出所有 3 个节点均因 `Insufficient memory` 拒绝调度，且不存在可用于抢占 (Preemption) 的 Pod (Fact: 1)。
3. **数据一致性**：Prometheus 指标 `kube_pod_container_resource_requests` 精确确认了该内存请求量为 `1125899906842624` bytes (Fact: 5)，证实了 `1Pi` 并非幻觉，而是 Pod 的实际配置状态。

鉴于 1 PiB 的请求量远超一般 K8s 集群节点（通常在数十 GiB 级别）的物理极限，这是不可调和的资源约束冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.7s
├─ 并发证据采集: 97.3s
│  └─ g1 aiops-case-v02/workload: 97.2s (Evidence 87.1s, RCA 10.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
