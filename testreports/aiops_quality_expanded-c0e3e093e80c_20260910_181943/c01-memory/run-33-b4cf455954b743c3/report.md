## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | 条件 `PodScheduled` 为 `False`，原因 `Unschedulable`，消息包含 `0/3 nodes are available: 3 Insufficient memory` | 直接描述 Pod 调度的失败机制与系统判定状态 |
| 2 | K8s Event | event.message | `FailedScheduling` 事件，明确提示 `3 Insufficient memory` 且 `No preemption victims found for incoming pod` | 记录调度器拒绝 Pod 的具体事件反馈 |
| 3 | K8s Config | container.resource_request.memory | 容器 `app` 的资源请求内存为 `1Pi` | 揭示导致调度失败的根源配置参数 |
| 4 | K8s State | pod.status / phase | 状态为 `Pending`，Phase 为 `Pending` | 证实 Pod 因调度失败而停滞在初始阶段 |
| 5 | Metric | kube_pod_status_phase | 容器 `kube-state-metrics` 的 `Pending` 状态值为 1，`Running` 状态值为 0 (样本数各 1) | 提供 Pod 生命周期状态的量化佐证，排除已运行可能性 |

**证据链说明**
1. 证据 3 中的 `1Pi` 内存请求量在常规集群环境中极为异常，直接导致节点无法满足调度要求。
2. 证据 1、2 分别从 Pod 条件和事件层面一致确认了 `Insufficient memory` 是阻塞调度的唯一原因。
3. 证据 4、5 进一步从不同维度（状态字段与指标监控）交叉印证了 Pod 长期处于 Pending 状态，未启动容器，因此缺失 Logging 和 Tracing 数据属正常物理现象。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了 1Pi 的内存请求 (fact 3) → 集群可用节点内存不足 1Pi，无法满足资源请求 (fact 1, 2) → 调度器触发 FailedScheduling 且无节点可抢占 (fact 2) → Pod 持续处于 Pending 状态 (fact 4)
```

### 根因结论
已确认根因为**Pod 资源配置错误**。`workload` 中的 `app` 容器将内存请求（`resource_request.memory`）配置为 `1Pi`（事实 #3），该数值远超 3 个集群节点的物理内存总和。这直接触发了 `default-scheduler` 的 `FailedScheduling` 事件（事实 #2），判定所有节点均 `Insufficient memory`，进而导致 Pod 状态被阻塞为 `Pending`（事实 #1, #4）。现有 Kubernetes 事件与资源配置事实已充分闭合该逻辑链条。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 35.8s
├─ 并发证据采集: 30.4s
│  └─ g1 aiops-case-v02/workload: 30.4s (Evidence 22.5s, RCA 7.7s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
