## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod resource requests memory (1Pi) exceeds total cluster allocatable memory across all 3 nodes, causing Unschedulable. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory.` (fact_id: `fact-5e6d6f0b6629`) | 确证调度失败的直接原因：集群内存不足 |
| 2 | K8s Config | workload Pod | 容器 `app` 请求内存 `1Pi` (fact_id: `fact-3a24f6d58764`) | 揭示异常根源：资源请求量严重超出集群承载能力 |
| 3 | K8s Config | workload Pod | 容器 `app` 硬限制内存 `1Pi` (fact_id: `fact-83cb8981253d`) | 辅助印证配置意图 |
| 4 | K8s State | workload Pod | 状态 `Pending`，条件 `PodScheduled: False`，原因 `Unschedulable` (fact_id: `fact-82b94f6ec3ec`) | 提供 Pod 当前停滞状态的直接证据 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (fact_id: `fact-a1466dffb547`) | 独立指标数据佐证 Pod 处于 Pending 状态 |

**证据关联说明：**
Kubernetes 调度器报告“内存不足” (证据1) 与 Pod 配置中高达 1Pi 的内存请求 (证据2) 构成完整的因果闭环；Pod 的 Pending 状态 (证据3、4) 与 Prometheus 指标 (证据5) 从状态和时序两个维度一致确认了异常结果。由于容器未启动，Logging 和 Tracing 维度不适用。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 请求 1Pi 内存资源 → 超出集群总可用内存 (3节点) → 调度器标记 Unschedulable → Pod 处于 Pending 状态
```

### 根因结论
已确认根因为 **Pod 资源请求超出集群容量**。工作负载 `aiops-case-v02/workload` 申请了 1Pi 内存，导致集群中所有 3 个节点均无法满足该调度需求，进而引发持续的 `FailedScheduling` 事件。证据充分，逻辑闭环完整。

---

## 📊 性能统计

```text
├─ 总耗时: 55.1s
├─ 问题定位: 16.5s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-v02/workload: 30.5s (Evidence 26.6s, RCA 3.8s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
