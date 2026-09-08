## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态且持续 24 分钟未能调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` (fact-06c321aec3a6) | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 直接确认 Pod 因亲和性/选择器不匹配被拒绝调度。 |
| 2 | K8s Config | `kubernetes` (fact-1a7d138899c4) | `container.app.cpu.request: 5m` | 排除 CPU 资源不足导致的调度失败。 |
| 3 | K8s Config | `kubernetes` (fact-465a569df863) | `container.app.memory.request: 8Mi` | 排除内存资源不足导致的调度失败。 |
| 4 | Metric | `prometheus` (fact-690befd25fd5) | `kube_pod_status_phase{phase="Pending"} = 1` | 确认 Pod 当前处于 Pending 状态的客观事实。 |

**证据总结：**
Pod 因 NodeSelector 不匹配被 K8s 调度器拒绝，但容器配置的 CPU (5m) 和内存 (8Mi) 请求量极低，集群资源瓶颈被排除。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 NodeSelector (aiops.lab/unavailable=true) → 集群节点未匹配该选择器 → 调度器触发 FailedScheduling → Pod 持续 Pending
```

### 根因结论

Pod `workload-68c557d875-bsq52` 配置了 `NodeSelector: aiops.lab/unavailable=true`，但集群中不存在携带该标签的节点（#1）。由于 CPU 和内存请求量极低（#2, #3），该调度失败纯粹由标签匹配策略与节点状态不一致导致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 22.1s
├─ 并发证据采集: 63.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 63.3s (Evidence 53.3s, RCA 10.0s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
