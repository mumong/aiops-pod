## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling`, `0/3 nodes are available: 3 Insufficient memory` | 提供调度失败的直接原因 |
| 2 | K8s State | `pod.condition` | `PodScheduled: False`, `Unschedulable`, `3 Insufficient memory` | 证实 Pod 因资源不足不可调度 |
| 3 | K8s Config | `container.resource_request.memory` | `1Pi` | 证实容器请求的内存超出集群节点容量范围 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase` = `1` (phase: Pending) | 独立观测验证 Pod 确实处于 Pending 状态 |

**证据印证说明：**
Kubernetes 状态和调度事件均一致指向 `Insufficient memory`，Metric 证实了状态并未改变。证据链核心在于 Pod 配置的内存请求量级（1Pi）与集群实际节点容量的不匹配，排除了资源碎片或其他调度策略问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置 memory request 为 1Pi → 调度器评估节点剩余内存均不满足 → 触发 FailedScheduling 拒绝调度 → Pod 保持 Pending 状态
```

### 根因结论

**已确认根因：Pod 规格配置了超出集群物理承载能力的内存请求（1Pi）。**

事实依据（证据 #2, #3）表明，Pod `aiops-case-v02/workload` 的 `app` 容器请求了 `1Pi` 的内存资源。由于该数值远超集群内任意可用节点的剩余内存（证据 #1），导致 `default-scheduler` 无法为该 Pod 找到合适的节点，并明确返回 `Insufficient memory` 错误。由于资源请求本身不可行，系统未尝试进行抢占（preemption: 0 victims found），Pod 因此一直停留在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.8s
├─ 并发证据采集: 42.1s
│  └─ g1 aiops-case-v02/workload: 42.1s (Evidence 36.2s, RCA 5.8s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- 未调用 Runbook
