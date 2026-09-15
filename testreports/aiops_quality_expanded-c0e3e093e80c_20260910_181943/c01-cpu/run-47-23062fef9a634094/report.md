## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | aiops-case-v01/workload Pod 处于 Pending 状态，调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v01/workload` phase=Pending, PodScheduled=False, reason=Unschedulable (fact-088513317b1b, fact-1f3835bd8f01) | 确认 Pod 调度失败及当前停滞状态 |
| 2 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found (fact-497e98cd2692) | 明确指出失败原因是集群节点 CPU 资源耗尽，且无法通过抢占其他 Pod 解决 |
| 3 | K8s Config | kubernetes | 容器 `app` 资源请求 `cpu=100k` (fact-19b0501249c9) | 提供调度失败的具体资源需求背景 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` 返回 1，且 `trend_evaluable=false` (fact-1e3fd2c18f54) | 独立验证 Pod 仍处于 Pending 状态 |

**证据链说明：**
K8s 事件 (fact-497e98cd2692) 与 Pod 状态条件 (fact-1f3835bd8f01) 均指向同一原因：所有 3 个节点 CPU 资源不足且预emption 失败。Metric 数据 (fact-1e3fd2c18f54) 佐证了该 Pending 状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源耗尽 → Scheduler 无法找到满足 100k CPU 需求的节点且 Preemption 失败 → Pod 被标记为 Unschedulable → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为集群节点 CPU 资源不足。K8s 事件显示 `3 Insufficient cpu`，且 `3 No preemption victims found`，表明所有可用节点均无法满足 Pod 的 CPU 资源请求（100k），且集群没有具备足够资源的 Pod 可以被抢占以腾出空间。Metric 数据确认该状态仍在持续。

由于未获取到各节点的具体 CPU 分配率及可调度余量指标，无法进一步量化资源紧缺程度。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.3s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-v01/workload: 42.0s (Evidence 33.1s, RCA 8.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
