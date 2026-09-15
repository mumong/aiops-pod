## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，未分配到节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu.` | 直接表明调度失败原因：所有 3 个节点均因 CPU 资源不足无法调度。 |
| 2 | K8s State | kubernetes | Pod 状态 `Pending` | 症状确认，Pod 始终未进入 Running 阶段。 |
| 3 | K8s Config | kubernetes | CPU Request: `100k` | 提供调度约束参数，说明该容器对 CPU 的最低诉求极低。 |
| 4 | K8s State | kubernetes | 事件详情 `No preemption victims found for incoming pod` | 确认调度器尝试寻找资源抢占目标失败，排除通过牺牲其他 Pod 获得资源的可能。 |
| 5 | Metric | prometheus | `kube_pod_status_phase=1` (Label: `phase=Pending`, timestamp: 2026-09-11T05:53:02.223000Z) | 辅助确认 Pod 在最近一次采样时仍处于 Pending 状态。 |

**证据关联说明：**
Kubernetes 事件（#1, #4）给出了明确的失败逻辑：3 个节点 CPU 耗尽且无法通过抢占获得资源。Pod 状态（#2）与 Prometheus 指标（#5）共同印证了该 Pod 在当前时间窗口内确实未获得调度。配置项（#3）显示 CPU 需求极低，反证了“Insufficient cpu”是由于集群整体 CPU 负载极高，而非单 Pod 资源请求过大。Logging 与 Tracing 因容器未启动而未采集到相关数据，属于预期现象。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有可用节点 CPU 资源耗尽 → 调度器评估资源失败 (Insufficient cpu) → 抢占机制失败 (无符合条件的 victim) → Pod 处于 Pending 状态，调度器反复拒绝调度
```

### 根因结论

**已确认的根因**：集群内所有可用节点（共 3 个）的 CPU 资源已全部分配完毕，导致 `default-scheduler` 无法为 `aiops-case-v01/workload` 分配资源，且系统无法通过抢占现有 Pod 来腾出空间。

证据支撑：
- **K8s Event (fact-2af1de3702ae, fact-73730d94aea0)** 明确指出 `0/3 nodes are available: 3 Insufficient cpu`，且没有预占受害者 (`No preemption victims`)。
- **K8s Config (fact-24f107f438db)** 显示该 Pod 仅请求 100m (100k)，资源门槛极低，因此“CPU 耗尽”是集群层面的整体饱和，而非该特定应用的资源需求不合理。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.2s
├─ 并发证据采集: 31.7s
│  └─ g1 aiops-case-v01/workload: 31.7s (Evidence 24.7s, RCA 7.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
