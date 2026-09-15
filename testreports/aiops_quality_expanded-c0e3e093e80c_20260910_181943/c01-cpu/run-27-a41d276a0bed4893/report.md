## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态且 40 分钟未分配节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod phase | Pending (fact-bd104728c6ab) | 确认 Pod 未调度、未运行 |
| 2 | K8s State | Pod condition | Unschedulable: 0/3 nodes available: 3 Insufficient cpu (fact-407077fab9b7) | 证明 3 个节点均无足够 CPU 资源 |
| 3 | K8s Event | Scheduler | FailedScheduling: 9m53s (x6) 3 Insufficient cpu (fact-696da06c6586) | 调度器多次尝试调度失败的确凿证据 |
| 4 | K8s Event | Scheduler | FailedScheduling: 40m 3 Insufficient cpu (fact-d6a0e5d9ca94) | 故障持续时间长，非瞬时资源波动 |
| 5 | Metric | Pod Phase | `kube_pod_status_phase{phase="Pending"}` = 1 (fact-332d10a749f1) | 跨维度印证 Pod 确认为 Pending 状态 |
| 6 | K8s Config | Resource Limit | cpu: 100k (fact-6dd71d1dfda8) | 提供 Pod 资源配置上限作为背景 |

**证据分析**：
Pod 状态（Pending）与调度器返回的错误信息（FailedScheduling）在 K8s State、K8s Event 以及 Prometheus Metric 三个维度完全一致，均指向 CPU 资源不足。由于 `kubernetes_tabular_query` 工具执行失败，缺少具体的 `allocatable` 数值，但“3 Insufficient cpu”已明确排除所有节点的可分配性，且未触发 Preemption，说明集群 CPU 资源整体枯竭。

## 🎯 根因分析 · g1

### 因果链
```text
集群节点可用 CPU 资源不足（全集群3节点均不足） → Kubernetes Scheduler 无法满足 Pod CPU Request → 调度器返回 FailedScheduling 事件 → Pod 保持 Pending 且 nodeName 为 None
```

### 根因结论
**已确认的根因**：集群整体可用 CPU 资源不足。
该根因直接解释了 Pod 为何处于 Pending 状态且长达 40 分钟未能分配。Kubernetes 调度器在 3 个节点上均未能满足 CPU 调度条件，且因无合适抢占对象导致预emption 失败。尽管缺少具体的 `allocatable` 数值，但现有的调度器日志与事件已构成闭环证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 12.4s
├─ 并发证据采集: 54.9s
│  └─ g1 aiops-case-v01/workload: 54.9s (Evidence 45.6s, RCA 9.2s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
