## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | 容器 app 的 memory 资源请求（requests）被配置为 1Pi（1 Pebibyte），该数值远超集群节点可分配容量，导致调度器在所有候选节点上因 'Insufficient memory' 拒绝绑定该 Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态 `Pending` | 确认 Pod 未完成调度 |
| 2 | K8s Event | kubernetes | `Warning FailedScheduling`：`0/3 nodes are available: 3 Insufficient memory` | 确认调度器拒绝绑定的直接原因 |
| 3 | K8s Config | kubernetes | 容器 `app` 配置：`memory request` = `1Pi`，`memory limit` = `1Pi` | 确认异常的资源请求配置来源 |
| 4 | K8s Config | kubernetes | 容器 `app` 配置：`cpu request` = `5m`，`cpu limit` = `50m` | 排除 CPU 资源请求过高的可能 |
| 5 | Metric | prometheus | `kube_pod_status_phase` 处于 `Pending` 状态值为 `1` | 独立观测到 Pod 处于非运行态 |

**证据关联分析：**
Kubernetes 事件明确指出所有 3 个节点因 "Insufficient memory" 拒绝调度，这直接与 Pod 配置中 `1Pi` 的内存请求（证据 3）形成因果闭环。同时，Kubernetes 状态显示 Pod 处于 Pending（证据 1），Metric 数据也确认了这一非运行状态（证据 5）。CPU 请求极低（证据 4），进一步排除了 CPU 瓶颈，将故障点锁定在内存调度失败上。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 的 memory request 配置为 1Pi（证据 3） → 1Pi 远超节点可分配容量 → 调度器在所有 3 个节点上报 Insufficient memory 并触发 FailedScheduling（证据 2） → Pod 持续处于 Pending 状态（证据 1）
```

### 根因结论

已确认的根因为：**容器 `app` 的 `memory` 资源请求（requests）被配置为 `1Pi`（1 Pebibyte）**。该数值极大，超过了集群中所有候选节点的剩余可分配内存容量，导致 `default-scheduler` 无法找到满足条件的节点，最终触发 `FailedScheduling` 事件并使 Pod 保持 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 47.4s
├─ 问题定位: 16.0s
├─ 并发证据采集: 23.8s
│  └─ g1 aiops-case-v02/workload: 23.8s (Evidence 16.5s, RCA 7.1s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
