## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload (aiops-case-v03) 处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status` = `Pending` | 确立 Pod 未调度的直接症状。 |
| 2 | K8s Event | Kubernetes | `FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` (fact-04a86d4e958c, fact-e9ffeb774116) | 提供决定性证据，证明调度器因缺失 PVC 而拒绝调度。 |
| 3 | Metric | Prometheus | `kube_pod_status_phase` (phase=Pending, value=1) | 确认 Pod 处于 Pending 状态的客观观测 (fact-2146552ae0c2)。 |
| 4 | K8s Config | Kubernetes | CPU Request: `5m` / Limit: `50m`; Memory Request: `8Mi` / Limit: `32Mi` (fact-19843cf857b7 等) | 排除资源超限导致的调度失败，证明非资源类问题。 |
| 5 | Logging | Elasticsearch | `status=not_applicable`: "容器未启动，物理上不会产生应用日志" | 排除应用层错误导致启动失败的可能性。 |

**证据说明**：
Kubernetes 事件（#2）直接指出了调度失败的根本原因在于 PersistentVolumeClaim "unavailable-claim" 不存在。Pod 状态（#1）和 Metric（#3）一致确认了 Pod 停留在 Pending 阶段。资源配置（#4）显示请求量极低，排除了节点资源不足的原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 PVC 'unavailable-claim' → 调度器无法分配存储资源 → FailedScheduling 事件持续触发 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `workload` 定义中声明挂载了一个名为 `unavailable-claim` 的 PersistentVolumeClaim，但该 PVC 在 `aiops-case-v03` 命名空间下不存在。这导致 Kubernetes 默认调度器在尝试绑定卷资源时失败，从而阻止了 Pod 被调度到任何节点。

该结论由 Kubernetes Event `FailedScheduling` 明确记录（证据 #2）直接支撑，且排除了资源不足或容器启动失败等其他因素。

---

## 📊 性能统计

```text
├─ 总耗时: 49.1s
├─ 问题定位: 20.1s
├─ 并发证据采集: 20.9s
│  └─ g1 aiops-case-v03/workload: 20.9s (Evidence 15.9s, RCA 4.9s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
