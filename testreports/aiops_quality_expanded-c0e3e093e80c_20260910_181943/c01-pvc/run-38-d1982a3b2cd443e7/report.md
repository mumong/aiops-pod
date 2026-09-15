## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 'aiops-case-v03/workload' stuck in Pending state with FailedScheduling events |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 22m (x5 over 42m) ... 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (`fact-7c98e3b7bcc7`) | 直接表明调度器因找不到 PVC 'unavailable-claim' 而拒绝调度，重复出现确认该状态已持续 42 分钟。 |
| 2 | K8s Config | kubernetes | Pod 资源配置：CPU request `5m`, memory request `8Mi`; CPU limit `50m`, memory limit `32Mi` (`fact-d60bb2bbf652`, `fact-f35f0e68df09`, `fact-5ea06763eb0f`, `fact-331d6b704998`) | 提供上下文证明资源需求极低，排除了集群资源不足导致调度的可能性。 |
| 3 | K8s State | kubernetes | Pod 'aiops-case-v03/workload' 状态为 `Pending` (`fact-9c1321fe3453`) | 描述 Pod 当前的停滞状态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 在 `Pending` 状态值为 `1`，在 `Running` 状态值为 `0` (`fact-95bb040e26c8`, `fact-08a7a9cec907`) | 量化确认 Pod 自检查点以来一直保持在 Pending 阶段。 |
| 5 | Logging | elasticsearch | 状态 `not_applicable`，因为容器未启动 (`fact` list 为空) | 确认缺失应用日志是因为 Pod 被调度器拦在入口，并未进入运行环境。 |

**证据印证说明**：
事件（#1）和 K8s 状态（#3）共同描述了“调度失败导致 Pod 停滞”的闭环事实。指标（#4）确认了该状态不仅是瞬时的，而是持续的。配置（#2）排除了资源瓶颈，进一步锁定故障点在存储依赖（PVC 不存在）上。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 声明引用了不存在的 PVC 'unavailable-claim' → 调度器无法绑定该 Volume → FailedScheduling 事件触发 → Pod 始终处于 Pending 状态
```

### 根因结论

已确认的根因为：**Pod 的规范中引用了一个不存在的 PersistentVolumeClaim（PVC）'unavailable-claim'。**

这导致了调度器无法完成卷的绑定操作，从而触发 `FailedScheduling` 事件，使 Pod 无法被调度到任何节点上，处于持续的 `Pending` 状态。该结论由 Kubernetes 事件记录（`fact-7c98e3b7bcc7`）直接证实，且 Pod 的资源配置极小（`fact-d60bb2bbf652`），排除了资源短缺等其他调度失败的原因。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 15.0s
├─ 并发证据采集: 551.8s
│  └─ g1 aiops-case-v03/workload: 551.8s (Evidence 545.3s, RCA 6.5s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
