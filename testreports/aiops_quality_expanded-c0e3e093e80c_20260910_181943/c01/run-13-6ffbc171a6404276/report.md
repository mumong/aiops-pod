## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，持续 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling 12m (x2 over 17m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact-a6330f553ef6) | 明确触发失败的机制：调度器在 3 个节点上均无法匹配节点亲和性/选择器。 |
| 2 | K8s State | Kubernetes | `PodScheduled` 状态为 `False`，原因为 `Unschedulable`，消息与事件一致（fact-eda4f7cd01cf）。 | 确认 Pod 调度器判定失败，状态持续为 Pending。 |
| 3 | Metric | Prometheus | `kube_pod_status_phase` 针对 phase=Pending 持续为 1，phase=Running 为 0（fact-54c748903304, fact-1b6540a3bd6a）。 | 交叉验证 Pod 未进入运行状态。 |
| 4 | K8s Config | Kubernetes | 容器 CPU Request `5m` / Limit `50m`；Memory Request `8Mi` / Limit `32Mi`（fact-035039b54c2f, fact-0c314468334c 等）。 | 排除因资源请求过大导致的 NoCapacity 失败。 |

调度器日志 (fact-1) 结合状态 (fact-2) 证实 Pod 处于调度等待中。由于资源请求 (fact-4) 极低且处于 Pending 状态，排除了计算资源不足的可能，进一步指向调度策略（节点选择器）配置错误导致无可用节点。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 nodeSelector: {aiops.lab/unavailable: true} → 集群内所有 3 个节点均无此标签 → 调度器判定 0/3 nodes available → Pod 保持 Pending 且持续触发 FailedScheduling
```

### 根因结论

根因已确认为 **调度器匹配失败**。Pod 定义的 `nodeSelector` 配置了 `aiops.lab/unavailable=true`，而集群当前的 3 个可用节点均未打上该标签（证据 1, 2），导致 `default-scheduler` 始终无法匹配任何节点并完成调度。资源配置极低（证据 4）进一步佐证了非资源不足问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 28.1s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 37.8s (Evidence 29.1s, RCA 8.6s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
