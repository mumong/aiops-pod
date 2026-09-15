## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `aiops-case-v03/workload` 引用了不存在的 PVC `unavailable-claim`，导致调度器因持久卷绑定失败而持续拒绝调度 (FailedScheduling)，使 Pod 保持在 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling` (21s, 5m35s): `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接指出调度失败的具体原因是 PVC 缺失，形成连续证据 |
| 2 | K8s State | kubernetes | `pod.condition` (PodScheduled=False): `Unschedulable` / `pod.status` (Pending) | 确认 Pod 处于不可调度状态 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: `32Mi` / `cpu`: `50m` | 证明资源需求极低，排除资源不足导致调度的可能性 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (Pending=1, Failed=0): 单样本 | 辅助验证 Pod 持续处于 Pending 阶段，无 CrashLoopBackOff 迹象 |
| 5 | Topology | kubernetes | `kubectl_find_resource` (PVC "unavailable-claim"): `Command failed (exit 1)` | 确认集群中确实不存在该 PVC 资源 |

**证据关联说明**：
K8s 事件（#1）与 Pod 状态（#2）互相印证了调度阻塞现象。K8s 配置（#3）排除了资源瓶颈，将原因锁定在存储绑定问题。Topology 查询结果（#5）证实了事件指出的 PVC 不存在，确立了故障的终止原因。由于 Pod 未启动，Logging 和 Tracing 为空，符合预期。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用不存在的 PVC --> 调度器执行失败 (FailedScheduling) --> 节点无合适调度位点 (0/3 nodes available) --> Pod 处于 Pending 状态
```

### 根因结论
**已确认的根因**：Pod `aiops-case-v03/workload` 配置中引用了名为 `unavailable-claim` 的 PVC，但该资源在集群中不存在。

**证据支撑**：
1. 调度器持续抛出 `FailedScheduling` 事件，明确报错 `persistentvolumeclaim "unavailable-claim" not found`（证据 #1）。
2. 尝试查找该 PVC 的命令失败，证实该资源未被创建（证据 #5）。
3. Pod 资源请求值极低（证据 #3），排除了节点资源竞争导致 Pending 的可能。

综上，Pod 因依赖的持久卷声明不存在而无法满足调度条件，导致持续处于 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 58.3s
├─ 问题定位: 15.3s
├─ 并发证据采集: 34.3s
│  └─ g1 aiops-case-v03/workload: 34.3s (Evidence 29.3s, RCA 4.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
