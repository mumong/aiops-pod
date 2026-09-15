## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload in aiops-case-v03 remains Pending due to FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedScheduling`：`0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接解释调度失败的具体原因 |
| 2 | K8s State | Kubernetes | Pod `phase=P`, `PodScheduled=False`，原因 `Unschedulable` | 确认 Pod 持续处于不可调度状态 |
| 3 | K8s State | Kubernetes | `kubectl get pvc` 失败：`Error from server (NotFound): persistentvolumeclaims "unavailable-claim" not found` | 确认 PVC 确实不存在，验证了事件中的错误事实 |
| 4 | K8s Config | Kubernetes | 资源请求：`memory=8Mi`, `cpu=5m`；限制：`memory=32Mi`, `cpu=50m` | 排除因资源请求过高导致节点不可用的可能性 |

**证据链说明**：
Pod 持续处于 Pending 状态（证据 2），调度器报错明确指出缺少 PVC（证据 1）。通过直接查询确认该 PVC 不存在（证据 3），从而排除了集群整体故障或资源不足的可能，将故障锁定在存储卷的缺失上。

## 🎯 根因分析 · g1

### 因果链

```text
PVC 'unavailable-claim' 在命名空间 aiops-case-v03 中未创建 → Pod 调度器无法绑定卷并调度 → PodScheduled 条件失败 (Unschedulable) → 应用 Pod 保持在 Pending 状态
```

### 根因结论

**已确认的根因**：
应用 Pod 在 Volume 配置中引用了 PVC `unavailable-claim`，但该资源在命名空间 `aiops-case-v03` 中不存在（证据 3），导致默认调度器无法完成存储绑定（证据 1）。这是导致 Pod 长期处于 `Pending` 状态（证据 2）的唯一技术原因。

**未知项**：
现有工具事实无法解释为什么 PVC `unavailable-claim` 不存在。无法确定是部署清单中遗漏了该资源定义，还是该资源被意外删除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.8s
├─ 并发证据采集: 37.1s
│  └─ g1 aiops-case-v03/workload: 37.1s (Evidence 29.4s, RCA 7.7s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
