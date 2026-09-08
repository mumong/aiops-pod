## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | workload-68c557d875-bsq52 is Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling`：5m7s (x13 over 65m)，错误信息 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" | 证明调度器因节点匹配失败拒绝了所有节点 |
| 2 | K8s Config | Kubernetes | `container.resource_request.cpu`: "5m" | 排除 CPU 资源不足导致调度的可能 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory`: "8Mi" | 排除内存资源不足导致调度的可能 |
| 4 | K8s State | Kubernetes | `pod.status`: "Pending" | 确认 Pod 处于未运行状态 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` (Pending): 1 (Sample: 1) | 监控指标确认 Pod 当前状态 |

**证据印证说明：**
1. Kubernetes 事件直接表明失败原因是“节点亲和性/选择器不匹配”，而非资源不足。
2. K8s 配置数据显示 Pod 请求的 CPU (5m) 和内存 (8Mi) 资源极小，进一步佐证了调度失败非集群资源瓶颈。
3. K8s 状态与 Prometheus 指标一致，均确认 Pod 处于 Pending 阶段，排除了运行异常导致的故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 NodeSelector 约束 'aiops.lab/unavailable=true'（未确认，由事件推断） → 集群内不存在具备该 Label 的节点 → 调度器因选择器不匹配拒绝所有 3 个节点 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因：Pod 调度约束与集群节点标签不匹配。**

*   证据 `#1`（K8s Event）明确指出调度失败的具体原因是 "3 node(s) didn't match Pod's node affinity/selector"，且持续时间达 65 分钟，排除了瞬时资源波动。
*   证据 `#2` 和 `#3`（K8s Config）显示 Pod 的资源请求极低，排除了因资源不足导致的 `Unschedulable`。
*   综上，Pod 维持 Pending 状态的根本原因是其 Spec 中定义的节点选择器（NodeSelector）在集群中无匹配节点，导致调度器无法为其分配运行环境。

---

## 📊 性能统计

```text
├─ 总耗时: 55.1s
├─ 问题定位: 15.0s
├─ 并发证据采集: 31.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 31.9s (Evidence 25.1s, RCA 6.7s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
