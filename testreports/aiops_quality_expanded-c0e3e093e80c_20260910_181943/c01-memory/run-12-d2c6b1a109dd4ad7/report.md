## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod `aiops-case-v02/workload` 的 `resources` 配置了极端异常的内存值 `memory: 1Pi`（1 Pebibyte）。调度器在尝试将该 Pod 分配至任何节点时，因所有可用节点的内存 `allocatable`（最大约 31.25 Gi）均无法提供 `1Pi` 的内存请求，判定为 `Insufficient memory` 而持续拒绝调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | `fact-4646b9f6e779` | `container: "app"`, `value: "1Pi"` | 暴露 Pod 配置中极不合理的内存请求量 |
| 2 | K8s State | `fact-1260b84c9eb3` | `status: "Pending"` | 明确 Pod 当前处于无法被调度的停滞状态 |
| 3 | K8s Event | `fact-496612a6ec23` | `message: "0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.."` | 直接陈述调度器拒绝调度的核心原因：内存不足且无抢占空间 |
| 4 | K8s State | `fact-bac04f7ebbbb` | `type: "PodScheduled", status: "False", reason: "Unschedulable"` | 确认 Pod 调度条件始终未满足 |

**证据说明**：
配置事实 `fact-4646b9f6e779` 提供了根本原因（1 PiB 内存请求远超物理集群承载能力），而事件 `fact-496612a6ec23` 和调度条件 `fact-bac04f7ebbbb` 在状态层面形成了因果闭环，证实调度失败并非因节点故障或资源竞争，纯粹是资源规格配置越界导致的物理不可行。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 请求 1Pi 内存 (fact-4646b9f6e779) → 调度器判定所有 3 节点内存不足 (fact-496612a6ec23) → Pod 状态锁定为 Pending (fact-1260b84c9eb3)
```

### 根因结论

已确认根因：**Pod `aiops-case-v02/workload` 的 `container.app` 配置了极端异常的内存请求值 `1Pi`（1 Pebibyte）。** 该数值远超集群节点的最大可用内存（约 31.25 Gi），导致调度器在所有 3 个可用节点上均因 `Insufficient memory` 而持续拒绝调度，并因无抢占对象（`No preemption victims`）而无法通过抢占方式缓解，最终表现为 Pod 状态长时间维持在 `Pending`（见证据编号 `fact-4646b9f6e779`、`fact-496612a6ec23`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.0s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-v02/workload: 49.1s (Evidence 40.4s, RCA 8.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
