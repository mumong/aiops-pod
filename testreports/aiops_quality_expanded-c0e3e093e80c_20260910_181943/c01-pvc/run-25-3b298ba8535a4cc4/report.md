## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload (aiops-case-v03)处于Pending状态，未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling ... persistentvolumeclaim "unavailable-claim" not found` | 明确失败原因，调度器因无法找到 PVC 拒绝调度 |
| 2 | K8s State | Kubernetes | `PodScheduled=False, reason=Unschedulable` | 记录 Pod 最终状态为不可调度 |
| 3 | K8s State | Kubernetes | `Pod Phase=Pending` | 确认 Pod 停留在启动前的等待阶段 |
| 4 | K8s Config | Kubernetes | `container app: memory_request=8Mi, cpu_request=5m` | 排除内存/CPU 资源不足导致调度失败的可能性 |
| 5 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 验证集群监控中确认该 Pod 状态持续为 Pending |

Kubernetes 事件 (事实 #1) 直接指出缺失的依赖资源 "unavailable-claim"，这与 Pod 状态 (事实 #2, #3) 的 Unschedulable 现象完全一致。资源请求数据 (事实 #4) 显示资源要求极低，排除了节点资源争用，进一步确证故障源于卷依赖而非容量限制。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 引用不存在的 PVC 'unavailable-claim' → 调度器校验卷依赖失败 → FailedScheduling (persistentvolumeclaim not found) → Pod 持续 Pending
```

### 根因结论

**已确认根因**：Pod 定义中引用了名为 `unavailable-claim` 的 PersistentVolumeClaim，但集群中该 PVC 不存在（事实 #1）。

**影响机制**：Kubernetes 调度器在执行调度前会检查 Pod 的卷挂载需求。由于无法找到指定的 PVC，调度器判定任何节点都无法满足该 Pod 的调度要求，导致 0/3 节点可用并拒绝调度（事实 #2），使 Pod 始终保持在 Pending 状态（事实 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 16.2s
├─ 并发证据采集: 36.2s
│  └─ g1 aiops-case-v03/workload: 36.2s (Evidence 28.8s, RCA 7.3s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
