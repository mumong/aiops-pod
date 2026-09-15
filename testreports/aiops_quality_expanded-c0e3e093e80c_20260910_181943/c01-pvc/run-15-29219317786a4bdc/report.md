## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `aiops-case-v03/workload` 处于 `Pending` 状态，`node: <none>`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (default-scheduler) | `Warning FailedScheduling ... 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` (fact-8de74f530b71) | 直接指出调度失败的元凶是缺少 PVC `unavailable-claim`，且 3 个节点均无抢占受害者 (fact-8de74f530b71) |
| 2 | K8s State | kubernetes (Pod Status) | `Pending` 状态 (fact-5791f563b0ca) | 确认 Pod 处于无法调度的停滞状态 (fact-5791f563b0ca) |
| 3 | K8s Config | kubernetes (Resource Requests/Limits) | CPU Request `5m`, Limit `50m`；Memory Request `8Mi`, Limit `32Mi` (fact-6e7d38b9bf40, fact-8fe213608ad3) | 证明资源请求极小，排除集群整体资源耗尽或由于 Pod 资源需求过大导致的调度过晚 (fact-6e7d38b9bf40, fact-8fe213608ad3) |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (fact-d722dba44f3a) | 独立度量确认了 Pod 的 Pending 状态 (fact-d722dba44f3a) |
| 5 | 工具调用 | kubectl | `kubectl describe pvc unavailable-claim -n aiops-case-v03` 返回 `Error from server (NotFound): persistentvolumeclaims "unavailable-claim" not found` (failed_tool_attempts) | 独立证实了该 PVC 在集群中确实不存在 (failed_tool_attempts) |

**证据说明：**
Kubernetes Event 直接揭示了 `FailedScheduling` 的机制是 PVC `unavailable-claim` 缺失。资源配置证据排除了资源不足导致调度过晚的可能性。Metrics 与 Pod 状态的直接确认相互印证。工具调用的失败结果独立证实了 Event 中提到的缺失资源。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义中引用了不存在的 PVC `unavailable-claim` → default-scheduler 调度检查发现 PVC 缺失并无法满足持久化卷挂载条件 → 调度器抛出 `FailedScheduling` 事件且无抢占方案 → Pod `aiops-case-v03/workload` 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 的 Volume 配置错误引用了不存在的 `PersistentVolumeClaim` (`unavailable-claim`)**。

调度器在尝试将 Pod 调度到节点时，检测到依赖的 PVC 不存在，导致调度失败 (`FailedScheduling`)。由于集群中没有满足抢占条件的节点（"3 No preemption victims found"），该问题持续存在，使得 Pod 无法启动。证据 (fact-8de74f530b71) 和工具调用 (failed_tool_attempts) 一致证实了这一点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 22.5s
├─ 并发证据采集: 27.9s
│  └─ g1 aiops-case-v03/workload: 27.9s (Evidence 20.6s, RCA 7.2s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable, pod-volume-mount-failed
