## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 25m (x14 over 90m) 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available. (fact-4f8a85d8b3da) | 明确调度失败原因：节点不匹配 |
| 2 | K8s State | kubernetes | Pod `aiops-case-01/workload-68c557d875-llhkh` 状态为 `Pending`，`PodScheduled` 条件为 `False` (Unschedulable) (fact-9b0734c8d09d, fact-e47f9ce30ebf) | 确认 Pod 持续处于不可调度状态 |
| 3 | K8s Config | kubernetes | 内存请求 8Mi，CPU 请求 5m；内存限制 32Mi，CPU 限制 50m (fact-86ce323ae200, fact-bf7d4a1d372a, fact-139d44bf1002, fact-aaf012d2cf90) | 提供资源上下文（资源请求极低，排除资源不足因素） |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` 在 04:19:45 时刻值为 1 (fact-9114f6655e59) | 独立观测验证 Pod 处于 Pending 阶段 |

日志与追踪采集因初始化容器异常及权限问题未能获取有效业务数据；现有证据通过 K8s 事件与配置明确指向调度约束失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector: aiops.lab/unavailable=true → 集群内 3 个节点均未持有该标签 → 调度器无法匹配任何可用节点 (0/3) → Pod 保持 Pending 状态，无法调度
```

### 根因结论

**已确认根因**：Pod 的 `nodeSelector` 配置了不存在的标签 `aiops.lab/unavailable=true`，导致集群内所有节点均无法满足调度约束 [证据 1, 2]。该配置与调度器返回的 `didn't match Pod's node affinity/selector` 事件完全吻合 [证据 1]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.6s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 42.0s (Evidence 34.8s, RCA 7.1s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
