## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 namespace is stuck in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling` (Warning): `0/3 nodes are available: 3 Insufficient memory.` | 明确调度失败原因，集群节点内存不足 |
| 2 | K8s Config | kubernetes | 容器 `app` 内存请求值 (request) = `1Pi` | 提供导致资源不足的异常配置源头 |
| 3 | K8s Config | kubernetes | 容器 `app` 内存限制值 (limit) = `1Pi`；CPU 请求=5m，限制=50m | 辅助确认资源定义的异常性（单位极大，不符合常规集群规模） |
| 4 | K8s State | kubernetes | Pod 状态 = `Pending` | 确认当前系统状态为调度挂起 |

**证据关联说明**：
Kubernetes 配置事实（#2, #3）展示了异常的资源请求规模（1Pi），这直接导致了 #1 中调度器报出“3 Insufficient memory”的 `FailedScheduling` 事件，最终表现为 #4 的 `Pending` 状态。由于容器未启动，Metrics、Logging 和 Tracing 维度均处于 `not_applicable` 状态，无其他维度事实。

## 🎯 根因分析 · g1

### 因果链

```text
异常资源定义 (请求 1Pi 内存) → 调度器资源校验失败 (集群 3 节点均无法满足) → 触发 FailedScheduling 事件 → Pod 卡在 Pending 状态
```

### 根因结论

**已确认根因**：集群内存资源不足。
具体为 Pod `aiops-case-v02/workload` 的容器 `app` 请求了 **1Pi (Petabyte)** 的内存资源（证据编号 #2），该请求量远超集群中所有 3 个节点的可用内存总和，导致默认调度器（default-scheduler）在尝试分配时因资源不足（Insufficient memory）且无可抢占对象而宣告失败（证据编号 #1），致使 Pod 无法进入运行状态。

该根因基于 Kubernetes 控制面的原始事件日志和资源配置事实，证据链完整。

---

## 📊 性能统计

```text
├─ 总耗时: 44.8s
├─ 问题定位: 18.3s
├─ 并发证据采集: 19.2s
│  └─ g1 aiops-case-v02/workload: 19.2s (Evidence 14.2s, RCA 4.9s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
