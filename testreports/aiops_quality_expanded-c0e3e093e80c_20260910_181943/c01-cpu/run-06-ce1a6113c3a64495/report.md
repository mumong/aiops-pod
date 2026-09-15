## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，调度器持续返回 FailedScheduling，原因显示 3 个节点均 Insufficient cpu。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `event.message` | `Warning FailedScheduling  2m2s   default-scheduler  0/3 nodes are available: 3 Insufficient cpu.` | 确认集群调度失败及根本原因，所有节点均因 CPU 不足被排除 |
| 2 | K8s Config | `container.resource_request.cpu` | `100k` (事实 ID: `fact-aaa3389fe58b`) | 提供 Pod 的 CPU 请求量配置，是导致资源不足的候选根因 |
| 3 | K8s Config | `container.resource_limit.cpu` | `100k` (事实 ID: `fact-16616f94a1d4`) | 确认限制值与请求值一致，符合单值异常特征 |
| 4 | Metric | `kube_pod_container_resource_requests` | `100000` (事实 ID: `fact-f2538b8e2bbe`) | 从 Prometheus 视角证实 Pod 实际占用的 CPU Request 资源量 |
| 5 | K8s State | `pod.status` | `Pending` (事实 ID: `fact-2f23b22e40b5`) | 确认容器当前处于待调度状态，与 FailedScheduling 现象一致 |

证据 1、3、4 直接互相印证：Pod 请求了 100,000 cores，导致调度器在评估集群时判定所有节点 CPU 资源不足，因此 Pod 维持在 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 配置 CPU requests/limits 为 '100k' (事实 3, 4) → 调度器评估节点资源，发现 100,000 cores 远超节点最大 allocatable → 调度器标记所有节点 Insufficient cpu 且无抢占候选 (事实 1) → Pod 保持 Pending 状态 (事实 5)
```

### 根因结论

已确认根因为**Pod 资源请求配置错误**。

Pod 的 CPU 请求量和限制量（`container.resource_request.cpu` 与 `container.resource_limit.cpu`）均配置为 `100k`（即 100,000 核）。该数值远超集群中任何单个节点的可用 CPU 资源（事实 1 显示 0/3 节点可用），导致调度器在评估时无法找到符合要求的节点，因此拒绝调度并持续返回 `Insufficient cpu` 错误（事实 1）。证据链闭环且相互支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.9s
├─ 并发证据采集: 51.5s
│  └─ g1 aiops-case-v01/workload: 51.5s (Evidence 40.5s, RCA 11.0s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
