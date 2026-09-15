## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | aiops-case-v03/workload 处于 Pending 状态，持续无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` (fact-1979215eb917) | `FailedScheduling`: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found. | 确认调度失败的具体原因，直接指向 PVC 缺失。 |
| 2 | K8s State | `kubernetes` (fact-5e4af75d5b39) | `PodScheduled=False`，message 同 Event 原文。 | 交叉印证 Pod 持续处于不可调度状态的根本机制。 |
| 3 | K8s State | `kubernetes` (fact-3d065b199672) | `phase: Pending` | 确立 Pod 当前停滞的状态表现。 |
| 4 | K8s Config | `kubernetes` (fact-5a94a1b3912f) | `container.resource_limit.memory`: 32Mi | 证明内存限制极低，排除因资源上限过高导致的 OOM 问题。 |

当前集群内无 Metric 趋势变化（样本不足，非趋势性异常）。
Logging 与 Tracing 因容器未启动被物理限制，无日志与链路数据可采集。
上述 K8s 事件与状态完全印证卷绑定依赖缺失是引发 Pod Pending 的唯一障碍。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用不存在的 PVC 'unavailable-claim' → 调度器卷绑定检查失败 → 抛出 FailedScheduling 警告并拒绝分配节点 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 Pod 定义中引用的 PersistentVolumeClaim `unavailable-claim` 在 `aiops-case-v03` 命名空间中不存在。
该依赖缺失导致 `default-scheduler` 无法完成调度计算，直接抛出 `FailedScheduling` 事件（见证据 #1、#2），最终使 Pod 锁定在 `Pending` 状态（见证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 18.0s
├─ 并发证据采集: 34.3s
│  └─ g1 aiops-case-v03/workload: 34.3s (Evidence 26.9s, RCA 7.3s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
