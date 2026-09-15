## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 配置的 memory 资源请求与限制（1Pi）远超集群节点物理容量，导致 3/3 节点因 Insufficient memory 无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (pod.status) | `status: Pending` | 确认 Pod 未调度，处于等待资源状态 |
| 2 | K8s Config | kubernetes (resource_request/memory) | container app 请求 `1Pi` | 显示 Pod 要求的内存资源规模（1 PiB） |
| 3 | K8s Config | kubernetes (resource_limit/memory) | container app 限制 `1Pi` | 显示 Pod 的硬内存限制同样为 `1Pi` |
| 4 | K8s Event | kubernetes (FailedScheduling) | `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims` | 明确指出调度失败的直接原因：所有 3 个节点均因内存不足（Insufficient memory）且无法抢占而拒绝调度 |
| 5 | Metric | prometheus (kube_pod_status_phase) | `Pending: 1` (sample_count: 1) | 确认当前集群中有 1 个 Pod 处于 Pending 状态 |

证据 1、2、4 形成闭环：Pending 状态是由资源请求无法满足直接导致，调度器日志给出了确切的硬件资源瓶颈（所有节点内存不足），无需日志或追踪数据进行辅助，因 Pod 未启动且被调度阻塞，日志与追踪维度为无效。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置的内存请求/限制为 1Pi (证据 #2, #3) → 超出集群所有节点的可用内存上限 → 调度器在 3/3 节点上报 Insufficient memory 且无抢占空间 (证据 #4) → Pod aiops-case-v02/workload 长期保持 Pending 状态无法调度 (证据 #1)
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v02/workload` 的容器内存资源配置（`1Pi`）严重超出集群节点物理容量。

**证据支撑**：
- 调度器 Event（证据 #4）明确指出 `0/3 nodes are available: 3 Insufficient memory`，证明集群中没有节点能满足该内存申请。
- 资源配置事实（证据 #2, #3）显示请求与限制值均为 `1Pi`（1 Pebibyte），这一数值在一般集群物理节点上属于极不合理的配置，直接导致了调度失败。

---

## 📊 性能统计

```text
├─ 总耗时: 57.4s
├─ 问题定位: 20.2s
├─ 并发证据采集: 28.9s
│  └─ g1 aiops-case-v02/workload: 28.9s (Evidence 24.4s, RCA 4.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
