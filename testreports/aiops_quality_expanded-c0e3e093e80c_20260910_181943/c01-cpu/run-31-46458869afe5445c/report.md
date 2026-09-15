## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，调度器报告 Insufficient cpu。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Pending` (fact_id: `fact-9b8ff3893dc6`) | 确认 Pod 未处于运行状态。 |
| 2 | K8s State | `pod.condition` | `Unschedulable`: "0/3 nodes are available: 3 Insufficient cpu" (fact_id: `fact-0aafbca76f5f`) | 直接指出资源调度失败的机制是 CPU 不足。 |
| 3 | K8s Event | `event.message` | "FailedScheduling ... 3 Insufficient cpu" (fact_id: `fact-05beb9a25b1c`) | 历史事件佐证持续 40 分钟以上的调度失败现象。 |
| 4 | Metric | `kube_pod_container_resource_requests` | 值: `100000` core (fact_id: `fact-11a7298778a9`) | 证实 Prometheus 解析到的实际请求量为 100,000 核心。 |
| 5 | K8s Config | `resource_request.cpu` | `100k` (fact_id: `fact-383ed7c05c86`) | 暴露根本配置异常，`k` 后缀被非标准解析为千倍，导致 100k 变成 100,000 核心。 |

K8s 状态与事件确认了“Insufficient cpu”的调度失败机制，同时 Prometheus 指标（100,000 core）与 Pod 配置（100k）在数值上高度吻合，印证了配置后缀错误被解析为超大资源请求导致调度器无法分配节点。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec cpu 请求配置错误 (100k) → 资源管理器将其解析为 100000 核心 (100000000m) → 调度器检测到所有 3 个节点剩余 CPU 不足 → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因：Pod 规范（Pod spec）中 `cpu` 资源请求字段配置错误。**

具体而言，Pod 将 CPU 请求设置为 `100k`。在标准 Kubernetes 命名约定中，`m` 表示毫核（milli-cores），而 `k` 通常用于千位后缀。此处 `100k` 被调度器及监控系统错误解析为 100,000 核心（即 100,000,000m），这一资源需求量远超集群 3 个节点的可用总量（3 Insufficient cpu），直接导致了 Pod 因资源不足而被持续调度失败。证据编号：1, 2, 3, 4, 5。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.8s
├─ 并发证据采集: 53.3s
│  └─ g1 aiops-case-v01/workload: 53.3s (Evidence 42.2s, RCA 11.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
