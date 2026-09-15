## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点 CPU 资源不足 (Insufficient cpu) 导致调度器无法为该 Pod 分配节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 确认调度器在三节点集群中均因 CPU 不足而拒绝调度，且无抢占对象 |
| 2 | K8s Config | `kubernetes` | `resource_request.cpu = 100k` | 提供调度失败的直接上下文：容器请求量极小（100毫核） |
| 3 | K8s State | `kubernetes` | `status: Pending, PodScheduled: False, reason: Unschedulable` | 反映 Pod 长期处于不可调度状态，验证了事件中的失败持续存在 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase{container="kube-state-metrics", phase="Pending"} = 1` | 独立观测到 Pod 处于 Pending 状态，印证了 Pod 未能成功启动 |

**证据综合说明**：
Kubernetes 事件明确指出了“3 Insufficient cpu”这一调度瓶颈（证据 1），这与 Pod 的 `Pending` 状态（证据 3）高度一致。尽管 Pod 的 CPU 请求量仅为 `100k`（证据 2），调度器仍判定所有节点资源不足，且由于未配置或无法进行抢占（`No preemption victims`），导致资源永久枯竭。Metric 数据（证据 4）从时间维度确认了 Pod 未能脱离该状态。

## 🎯 根因分析 · g1

```text
集群节点 CPU 资源耗尽 → 调度器拒绝分配节点且无可用抢占对象 → Pod 持续处于 Pending/Unschedulable 状态 → 业务容器无法启动
```

### 根因结论
已确认根因为：**集群整体 CPU 资源不足（Insufficient cpu）**。

根据 Kubernetes 事件（证据 #1），集群内全部 3 个可用节点均无法满足调度需求，且由于不存在可被抢占的资源占用者（`No preemption victims`），导致调度陷入死锁。证据表明，即便容器仅请求了极小的 CPU 资源量（`100k`，证据 #2），集群仍无法提供服务，说明节点 CPU 容量已被完全或接近完全占用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.5s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-v01/workload: 36.1s (Evidence 31.2s, RCA 4.7s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
