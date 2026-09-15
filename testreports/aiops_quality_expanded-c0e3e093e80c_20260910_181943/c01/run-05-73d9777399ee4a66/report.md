## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，未调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `phase: Pending` (fact-0af1e7ee87bd) | 症状：Pod 处于不可调度状态 |
| 2 | K8s Event | Scheduler | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-45b4ce444501, fact-e20feafd88d0) | 直接原因：调度器因亲和性/选择器不匹配拒绝所有节点 |
| 3 | K8s Config | Resource Request | `container: app`, `memory: 8Mi`, `cpu: 5m` (fact-384ee1c616c3, fact-70f645fb3ac5) | 上下文：资源请求极低，排除资源竞争或分配失败 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` (Pending) = 1, (Unknown) = 0 (fact-b63b5a376dc7, fact-a10ac685f887) | 辅助确认：集群层面确实存在一个 Pending 状态的 Pod，无其他异常相位 |

**证据综合说明**：
Kubernetes 状态和事件日志直接证实了 Pod 卡在 `Pending` 状态，且失败机制明确为 `node(s) didn't match Pod's node affinity/selector`。由于资源请求极低（8Mi 内存），排除了资源不足的可能性。Metric 数据作为辅助，确认了这一状态在整个集群范围内的表现。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 Node-Selector `aiops.lab/unavailable=true` → 集群所有节点（master, node1, node2）缺少该标签 → 调度器评估 0/3 节点匹配 → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因是**节点选择器（Node-Selector）配置与集群节点标签不匹配**。

证据编号 2（K8s Event）明确显示调度器因 `didn't match Pod's node affinity/selector` 拒绝了所有 3 个可用节点。虽然输入未直接提供节点标签列表，但结合证据编号 1（Pod 状态）和调度器行为，可以确定 Pod 中定义的节点亲和性约束在当前集群环境中无法得到满足，导致 Pod 无法被调度。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.3s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 37.8s (Evidence 29.7s, RCA 8.0s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
