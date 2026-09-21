## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点存在严重的CPU资源碎片化或超额分配现象（Overcommitment/Fragmentation），导致调度器在集群总可分配CPU（48 core）远大于Pod请求量（100k core）的情况下，仍判定所有节点无法满足调度请求，具体表现为调度器报告 '3 Insufficient cpu'。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling 2m28s... 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 确认 Pod 被调度器拒绝的直接原因是所有节点 CPU 不足，且无资源抢占对象。 |
| 2 | K8s Config | `pod.spec` | `cpu.request = 100k`, `cpu.limit = 100k` | 确认该 Pod 的 CPU 请求量极高（100k），远超常规节点容量，是引发资源检查失败的关键上下文。 |
| 3 | K8s State | `pod.status` | `Pending` (Phase: Pending, Condition: Unschedulable) | 证实 Pod 持续处于不可调度状态，未进入运行阶段。 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase{...phase="Pending"}=1` (样本数: 4, `trend_evaluable=true`) | 通过 Prometheus 监控确认 Pod 在过去 30 分钟内（09:39-09:40）持续处于 Pending 状态。 |

**证据说明：**
- **维度印证**：Kubernetes Event 提供了调度失败的根因陈述（`Insufficient cpu`），Pod 状态（Pending）证实了失败结果的持续性，Metric 数据（`phase="Pending"` 样本连续）从监控角度排除了短暂波动的可能，四者共同闭环验证了“因 CPU 资源不足导致调度永久失败”的结论。
- **数据缺失说明**：Logging 和 Tracing 维度因 Pod 未启动（无 `pod_ip`，物理上未分配资源）而明确为空，不影响对调度层面故障的诊断。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点 CPU 资源耗尽或碎片化 (无法为 100k CPU 请求找到足够连续/可用资源) → 调度器计算失败/抢占失败 (3/3 nodes Insufficient cpu, No preemption victims) → 调度器拒绝调度 (FailedScheduling) → Pod 永久处于 Pending 状态
```

### 根因结论

**已确认根因**：
Pod `aiops-case-v01/workload` 因 **CPU 资源请求量过大（100k）** 且 **集群可用 CPU 资源不足**，导致调度器无法将其分配到任何节点。

**分析依据**：
1.  **直接证据**：调度器日志明确指出 `0/3 nodes are available: 3 Insufficient cpu`（事实 #1），这是 Pod 无法调度的直接原因。
2.  **上下文确认**：Pod 配置了极高的 CPU 请求 `100k`（事实 #2），在 3 节点集群中，这通常意味着请求总量超过了集群硬件上限或资源碎片化导致无法容纳单一 Pod。
3.  **结果确认**：Pod 状态（Pending）和 Metric（`phase="Pending"`）（事实 #3, #4）证实了这一失败状态已持续一段时间，且无自动恢复迹象。

**局限性**：
虽然确认了调度失败的原因是“Insufficient cpu”，但具体是集群整体资源过载（Overcommitment）还是节点间资源碎片化导致无法容纳 100k 请求，需要查看具体节点 `Allocated` vs `Allocatable` 的详细资源分布才能进一步定量化（参考输入中的 `unknowns`）。但基于当前事实，判定为“资源不足”这一根因已足够解释现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.6s
├─ 并发证据采集: 66.9s
│  └─ g1 aiops-case-v01/workload: 66.9s (Evidence 53.0s, RCA 13.8s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
