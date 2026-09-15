## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | workload pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling  3m53s  default-scheduler  0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 明确指出调度器拒绝调度的直接原因是 PVC 找不到 |
| 2 | K8s State | Kubernetes | `pod.condition type=PodScheduled status=False reason=Unschedulable message=... persistentvolumeclaim "unavailable-claim" not found` | 证实 Pod 长期处于非调度状态，原因与 Event 完全一致 |
| 3 | K8s State | Kubernetes | `pod.phase Pending` | 描述 Pod 当前停滞的可见状态 |
| 4 | Metric | Prometheus | `kube_pod_status_phase 1` (label: `phase="Pending"`, sample_count: 1) | 观测确认 Pod 在查询时间点（08:06）仍处于 Pending 状态 |
| 5 | Tool Result | Kubectl | `kubectl describe ... Error from server (NotFound): persistentvolumeclaims "unavailable-claim" not found` | 确凿证实指定命名空间下该 PVC 资源对象不存在，无法调度 |

**证据说明：**
Kubernetes 事件（#1）与 Pod 状态（#2）共同构建了“未调度”的完整表象；外部工具事实（#5）直接证实了事件中指出的缺失资源。Metric 数据（#4）进一步验证了该状态在查询时刻仍然存在。

## 🎯 根因分析 · g1

### 因果链
```text
命名空间内缺少 PVC 'unavailable-claim' (fact-064d9b79f112关联的PVC不存在) → default-scheduler 校验 PVC 失败 (fact-027e654dacf3关联事件) → Pod 持续处于 Pending 状态 (fact-27ed7d8996de关联状态)
```

### 根因结论
已确认根因为：**Pod 依赖的 PersistentVolumeClaim "unavailable-claim" 在命名空间 `aiops-case-v03` 中不存在**。

这一缺失导致 `default-scheduler` 在调度过程中校验失败，触发 `FailedScheduling` 事件，Pod 因此无法被调度到任何节点，表现为永久性的 `Pending` 状态。工具查询（#5）已确认该 PVC 物理上不存在。

---

## 📊 性能统计

```text
├─ 总耗时: 55.0s
├─ 问题定位: 19.4s
├─ 并发证据采集: 27.5s
│  └─ g1 aiops-case-v03/workload: 27.5s (Evidence 20.4s, RCA 7.0s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
