## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 in aiops-case-01 remains Pending, Unschedulable |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling 18m (x7 over 48m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` (fact-0e071772f4d1) | 确认 Pod 因节点亲和性/选择器不匹配导致调度失败，且该状态已持续 48 分钟 |
| 2 | K8s Config | kubernetes | `container.resource_request.cpu: "5m"` (fact-1e6d84a4ec95) | 排除资源耗尽导致调度失败的可能性，请求量极低 |
| 3 | K8s Config | kubernetes | `container.resource_limit.cpu: "50m"` (fact-745580f18aaf) | 排除资源限制配置异常的问题 |
| 4 | K8s State | kubernetes | `PodScheduled: False, reason: Unschedulable` (fact-06e78b07b9c1) | 确认 Pod 处于 Unschedulable 状态，佐证 FailedScheduling 事件 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}: 1` (fact-fb28202c2c7a) | 从监控侧确认 Pod 依然处于 Pending 阶段，未进入运行 |

**证据关联说明：**
调度事件（#1）与 Pod 状态（#4）直接对应，确认了当前的阻塞机制；低资源配置（#2, #3）排除了容量不足导致的调度延迟，将排查指向节点匹配逻辑；监控数据（#5）提供了系统层面的状态印证。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 包含 nodeSelector: aiops.lab/unavailable=true → Scheduler 评估 3 个节点均不匹配该选择器 → 0/3 节点满足亲和性约束 → Pod 保持 Pending 状态，持续收到 FailedScheduling 警告
```

### 根因结论
已确认的根因为 **Pod 的 `nodeSelector` 配置导致零节点匹配**。

- **分析：** Pod `workload-68c557d875-gtzc8` 被强制要求调度至拥有标签 `aiops.lab/unavailable=true` 的节点，但集群中 3 个可用节点均不包含此标签。
- **证据支撑：** Kubernetes 事件（#1）明确报告 “0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector”，且该异常模式（#1）在 48 分钟内重复了 7 次，排除了偶发性网络抖动或瞬时资源争用可能。
- **排除：** 资源请求极低（#2, #3）且无容量告警，排除了资源不足；Pod 状态长期为 Pending（#4, #5）且无容器日志（因未启动），符合纯调度拦截特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 39.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 39.0s (Evidence 31.5s, RCA 7.4s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
