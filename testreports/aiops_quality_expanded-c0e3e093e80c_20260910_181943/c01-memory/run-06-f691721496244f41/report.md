## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod内存资源请求（1Pi）远超集群可用内存，导致调度器在所有节点上均因'Insufficient memory'失败且无法抢占 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | 3/3 节点因 `Insufficient memory` 失败调度，`preemption: No preemption victims found` | 证明集群内存耗尽且无法抢占，直接解释调度失败原因 |
| 2 | K8s Config | Pod 配置 | `container.resource_request.memory`: `1Pi` | 揭示资源瓶颈根源：内存请求量（1Pi）远超常规集群规模 |
| 3 | K8s State | Pod 状态 | `pod.status`: `Pending` | 描述异常持续存在的最终状态，符合无法分配资源的预期 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 值 `1`，标签 `phase: Pending` | 通过监控确认 Pod 始终停留在 Pending 状态，未见成功或异常崩溃转移 |

调度事件显示集群资源无法满足请求，且无抢占空间，这与 Pod 配置中高达 `1Pi` 的内存请求在逻辑上完全闭环；监控数据作为独立视角，证实了该异常状态已持续存在且稳定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置了 1Pi 的内存请求 → 集群内存资源无法满足 → 调度器在所有节点上触发 Insufficient memory 且无可用抢占对象 → Pod 处于 Pending 状态无法调度
```

### 根因结论

已确认的根因是 Pod `aiops-case-v02/workload` 的容器内存资源请求（`1Pi`）严重超出集群可用资源，导致调度器无法为该 Pod 分配任何节点。

这一结论由以下事实强支撑：
- **资源配置事实**：容器 `app` 的 `resource_request.memory` 被硬编码为 `1Pi`（事实 #2）。
- **系统反馈事实**：调度器明确拒绝该 Pod 并记录 `Insufficient memory`，且指出 `No preemption victims`（事实 #1），说明集群已无多余内存空间且未配置抢占。
- **状态一致性**：Pod 长期处于 `Pending` 状态（事实 #3、#4），证明该资源缺口未被修复。

---

## 📊 性能统计

```text
├─ 总耗时: 49.5s
├─ 问题定位: 16.1s
├─ 并发证据采集: 26.0s
│  └─ g1 aiops-case-v02/workload: 26.0s (Evidence 21.5s, RCA 4.5s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
