## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod workload 的请求资源格式 (cpu=100k) 被 Kubernetes 调度器解析为无效的或远超预期量级的 CPU 数值（通常 100k 被解释为一亿毫核而非 0.1 核），导致调度器在 3 个总可用量仅为 48 核的节点上判定资源不足 (Insufficient cpu)，尽管节点宏观显示有大量空闲 CPU。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition (fact-7d674a8f1536) | `PodScheduled=False`, reason=`Unschedulable`, message=`0/3 nodes are available: 3 Insufficient cpu` | 确认 Pod 因资源不足被调度器直接拒绝，未发生任何抢占尝试。 |
| 2 | K8s Config | container.resource_request.cpu (fact-31af22deb4f8) | `value=100k` (单位: kubernetes_quantity) | 提供关键配置，Kubernetes 调度器会将后缀 `k` 解析为 $10^3$ 倍，即 100,000 个 CPU 核心。 |
| 3 | K8s Event | FailedScheduling (fact-2165e5d55955) | `3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 验证调度器在 3 个节点上均无法分配该资源请求，且集群无足够容量满足该量级的资源。 |
| 4 | K8s State | pod.status (fact-1decbecada01) | `status=Pending` | 记录最终的异常持续状态，确认 Pod 未进入运行阶段。 |

**证据说明：**
K8s 配置事实显示 Pod 请求了 100k CPU（即 10 万核），这远超 3 节点集群的总物理容量（48 核），直接导致了调度器报告的 `Insufficient cpu` 错误；K8s 状态与事件事实证实了 Pod 因此长期处于 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
资源请求格式错误 (cpu=100k) → 调度器将 'k' 误认为千位后缀导致量级溢出 (需 100,000 核) → 判定所有节点 CPU 不足并拒绝调度 → 用户可见 Pod 长期 Pending 且调度失败
```

### 根因结论

**已确认的根因：** Pod `workload` 的 CPU 资源请求量级错误。

**分析依据：** 证据 #2 显示配置中 `cpu=100k`，Kubernetes 调度器将该后缀解析为 $10^3$ 倍，导致实际调度请求达到 100,000 核。结合证据 #1、#3（3 个节点均报告 CPU 资源不足），这一极端的资源需求完全消耗了集群可用资源，从而触发了 `FailedScheduling`。

*注：由于容器从未成功启动，Metrics、Logging 和 Tracing 维度均不适用（数据为空），但 K8s 核心配置与调度状态事实已构成充分且自洽的证据闭环。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.3s
├─ 并发证据采集: 46.6s
│  └─ g1 aiops-case-v01/workload: 46.6s (Evidence 39.8s, RCA 6.6s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
