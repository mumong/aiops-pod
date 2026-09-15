## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 的 nodeSelector 配置 `aiops.lab/unavailable=true` 与集群节点标签不匹配，导致调度器无法将 Pod 分配到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kube-state-metrics | `phase: Pending` | 确证 Pod 当前处于不可调度状态 |
| 2 | K8s Event | default-scheduler | `FailedScheduling ... 3 node(s) didn't match Pod's node affinity/selector` | 提供调度的直接失败原因 |
| 3 | K8s Config | Deployment Spec | `container.resource_request.cpu: 5m`, `memory: 8Mi` | 排除资源配额不足导致的调度失败 |

Kubernetes 事件明确指出了调度失败的原因是由于亲和性/节点选择器不匹配（Node Affinity/Selector），而容器的资源请求非常低，因此排除了资源不足的因素。

## 🎯 根因分析 · g1

### 因果链

```text
节点选择器配置错误 (nodeSelector) → 匹配不到任何集群节点 → 调度器无法分配 Pod → Pod 状态持续 Pending
```

### 根因结论

已确认的根因为**节点选择器配置错误**：Pod 的 `nodeSelector` 配置了 `aiops.lab/unavailable=true`，而集群中的节点均不具备该标签，导致调度器在 3 个节点上均无法匹配成功。当前现象（Pod Pending）与该配置直接相关，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.2s
├─ 并发证据采集: 39.7s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 39.7s (Evidence 34.8s, RCA 4.8s)
└─ 汇总总结: 4.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
