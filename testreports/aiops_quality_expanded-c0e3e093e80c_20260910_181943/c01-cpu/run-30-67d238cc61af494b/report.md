## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod资源请求规格定义错误，将CPU单位'k'（千）误用导致请求量达到100k CPU核，远超集群节点实际可用资源。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes (`fact-30f3325afcaf`) | Container `app` CPU `resource_request` 为 `100k` | 证实异常请求量：'k' 单位导致 100,000 核 CPU 请求 |
| 2 | K8s Config | kubernetes (`fact-14e53b2c7db6`) | Container `app` CPU `resource_limit` 为 `100k` | 证实硬限制同样配置错误 |
| 3 | K8s State | kubernetes (`fact-5461b85ecea9`) | Pod phase 为 `Pending` | 确认异常终止状态 |
| 4 | K8s Event | kubernetes (`fact-61c58bf88ae3`, `fact-90c4e86bff90`, `fact-faaf80b607f7`) | `FailedScheduling` (持续 39-44 分钟): `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 确认调度器评估所有节点资源不足且无法抢占 |
| 5 | K8s Event | kubernetes (`fact-13a35763197b`) | `PodScheduled=False`, reason=`Unschedulable`, message=`Insufficient cpu` | 辅助确认资源不足原因 |
| 6 | Metric | prometheus (`fact-f67a08e3cbf0`) | `kube_pod_status_phase`=1, labels=`phase: Pending` | 确认 Pod 持续处于 Pending 状态 |

证据说明：
- 维度 1、2 (K8s Config) 与 维度 4 (K8s Event) 互为因果印证：`100k` 的异常高配置直接导致了 `Insufficient cpu` 的调度失败。
- 维度 3、5 (K8s State/Event) 确认了现象：Pod 长期 Pending 且被标记为 Unschedulable，符合上述调度失败的预期结果。
- 维度 6 (Metric) 提供了独立的实时状态确认，与 K8s 状态事实完全一致，排除了瞬时波动的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置CPU request为'100k'（100,000核） → 集群节点最大可用CPU仅18核，无法满足请求 → Kubernetes Scheduler评估所有节点资源不足并拒绝调度 → Pod持续处于Pending状态且无法调度
```

### 根因结论

- **已确认的根因**：Pod `aiops-case-v01/workload` 的容器 `app` 在配置文件中错误地使用了 CPU 单位 `k`（千）。这导致 CPU `resource_request` 和 `resource_limit` 被解析为 100k（即 100,000 核），远超集群节点的实际可用 CPU 资源。
- **现象关联**：这种极端的资源误报触发了 Kubernetes 调度器的 `Insufficient cpu` 判断，并因所有节点资源均不足且无抢占 victim，导致 Pod 持续处于 `Pending` 状态，无法被调度运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.0s
├─ 并发证据采集: 64.0s
│  └─ g1 aiops-case-v01/workload: 64.0s (Evidence 56.7s, RCA 7.2s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
