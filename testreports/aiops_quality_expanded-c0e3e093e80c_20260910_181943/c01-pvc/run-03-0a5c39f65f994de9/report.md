## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload in aiops-case-v03 is stuck in Pending state due to scheduling failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending` | 确认 Pod 未能被调度，处于待命状态。 |
| 2 | K8s Event | kubernetes | `FailedScheduling`: "0/3 nodes are available: persistentvolumeclaim \"unavailable-claim\" not found" | 提供直接调度失败原因：所需的 PVC 在集群中不存在，导致无法绑定卷。 |
| 3 | K8s Config | kubernetes | `resource_request.cpu: 5m` / `resource_limit.cpu: 50m`<br>`resource_request.memory: 8Mi` / `resource_limit.memory: 32Mi` | 提供资源请求上下文，排除因资源不足导致调度的可能性（资源请求极低）。 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 确认当前 Pod 确实处于 Pending 阶段，状态与事件匹配。 |

**证据说明：**
K8s Event 明确指出调度失败的核心原因是 PVC `unavailable-claim` 未找到，直接解释了 Pod 处于 Pending 状态（证据 #1）且 Metric 确认（证据 #4）无法被调度的原因。资源配置（证据 #3）处于合理且低负载范围，进一步排除了资源限制因素，证实问题是单纯的依赖缺失。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 声明引用 PVC 'unavailable-claim' → PVC 不存在导致卷绑定失败 → Scheduler 触发 FailedScheduling → Pod 滞留于 Pending 状态
```

### 根因结论

**已确认根因：**
Pod `workload` 调度失败的根本原因是其 Spec 中引用了一个不存在的 PersistentVolumeClaim (`unavailable-claim`)。

- Kubernetes 调度器在尝试将 Pod 绑定到节点时，首先必须验证并绑定所有声明的卷。
- 由于 PVC `unavailable-claim` 在该命名空间下不存在（证据 #2），调度器无法完成卷绑定，因此返回 `FailedScheduling` 事件，拒绝将 Pod 分配到任何节点（证据 #1、#4）。
- 现有的资源请求配置（证据 #3）表明节点具备充足的资源能力，因此该故障纯粹源于配置依赖缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 55.8s
├─ 问题定位: 11.4s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-v03/workload: 36.6s (Evidence 29.9s, RCA 6.6s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- 未调用 Runbook
