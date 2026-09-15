## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod引用了不存在的PersistentVolumeClaim 'unavailable-claim'，导致调度器无法绑定卷，Pod被永久挂起（Pending）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v03/workload` 状态为 Pending | 确认故障最终呈现的停滞状态 |
| 2 | K8s Event | Kubernetes | `FailedScheduling` (fact-55939d69ffaa, fact-bf49aafb8005): `persistentvolumeclaim "unavailable-claim" not found` | 指出调度失败的直接原因：依赖的 PVC 不存在 |
| 3 | K8s Config | Kubernetes | CPU request 5m, limit 50m; Memory request 8Mi, limit 32Mi (fact-08fb2c615eec, fact-734bd2004118) | 排除资源限制导致调度的可能性 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` 值为 1 (fact-d8b4d2ca721d) | 从监控维度独立印证 Pod 正处于挂起状态 |

Kubernetes 事件明确指向了卷绑定失败，而 Metrics 数据从另一个维度确认了 Pod 的 `Pending` 状态。K8s 配置显示资源请求非常低，不存在资源不足导致的调度延迟，从而锁定了故障点在于 PVC 资源的缺失而非集群资源瓶颈。

## 🎯 根因分析 · g1

### 因果链

```text
依赖的 PVC unavailable-claim 不存在 → 调度器无法绑定卷 → Pod 调度失败 (Pending) → 容器未启动
```

### 根因结论

已确认根因为：Pod 定义中引用了不存在的 PersistentVolumeClaim (`unavailable-claim`)，导致 Kubernetes 调度器无法为其创建所需的存储卷绑定，Pod 因此永久停留在 `Pending` 状态（证据 #2, #3）。该结论由 `FailedScheduling` 事件及 Pod 状态指标相互印证，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 47.2s
├─ 问题定位: 22.2s
├─ 并发证据采集: 18.4s
│  └─ g1 aiops-case-v03/workload: 18.4s (Evidence 15.1s, RCA 3.2s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
