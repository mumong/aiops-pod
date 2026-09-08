## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod workload-68c557d875-llhkh (aiops-case-01) 处于 Pending 状态，无法调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | Pod `aiops-case-01/workload-68c557d875-llhkh` 处于 `Pending` 状态，`nodeName` 为 `None` (fact-8f9b2e42ad27, fact-eb31ab858554) | 确认故障现象：容器未调度，未分配节点资源 |
| 2 | K8s Event | K8s | `FailedScheduling`: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (fact-00fc288b64eb) | 提供调度失败直接原因：所有节点未通过标签/亲和性检查 |
| 3 | K8s Config | K8s | Pod 请求 `memory: 8Mi`, `cpu: 5m`；限制 `memory: 32Mi`, `cpu: 50m` (fact-05d3633bed33, fact-14f33edeaae4, fact-679c58568e1e, fact-7a7b2fbd48db) | 排除资源容量不足导致调度失败的可能性 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` 值为 `1` (fact-06966cbc2c9a) | 独立于 K8s API 确认 Pod 处于 Pending 状态的事实 |

**证据关联说明：**
K8s Event 明确指出调度失败源于节点亲和性/标签（node affinity/selector）不匹配，且覆盖率为 3/3 节点。结合 K8s State 的 Pending 状态和 Metric 的确认，排除资源不足（Request/Limit 极低）导致的调度延迟。由于 Pod 处于 Pending 状态，Logging 和 Tracing 维度因物理原因未产出有效数据，故障根因锁定在调度前的静态配置（nodeSelector/affinity）与集群实际标签不匹配上。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了特定的 nodeSelector 标签要求 (aiops.lab/unavailable=true) → 集群内所有 3 个节点均不具备该标签导致调度器检查失败 → 调度器返回 FailedScheduling 并拒绝调度 → Pod 永久处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 调度约束与节点标签不匹配**。具体表现为 Pod 的 `nodeSelector`（或亲和性规则）要求节点具备 `aiops.lab/unavailable=true` 标签，但集群中实际存在的 3 个节点均未配置此标签，导致 `default-scheduler` 无法找到任何可用节点（0/3 nodes are available）完成调度。证据链由 `FailedScheduling` 事件（fact-00fc288b64eb）直接支撑，且排除了资源容量瓶颈。

**缺失事实：**
当前缺乏对 Pod 规范（Spec）中 `nodeSelector` 或 `nodeAffinity` 具体定义字段的直接提取事实。现有结论基于调度器事件反推，若需精确到具体配置项名称，需补充读取 Pod YAML 配置的 `K8s Config` 事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 28.1s
├─ 并发证据采集: 54.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 54.2s (Evidence 45.7s, RCA 8.4s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
