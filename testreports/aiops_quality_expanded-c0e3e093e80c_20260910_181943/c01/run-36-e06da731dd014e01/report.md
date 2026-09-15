## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 nodeSelector {aiops.lab/unavailable: true}，但集群中 3 个节点均缺少该标签，导致调度器因节点亲和性/选择器不匹配而无法调度 Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `PodScheduled=False`, reason=`Unschedulable`, message=`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-d4b50aea324b) | 证实 Pod 未进入 Running 状态，且失败原因为节点选择器不匹配 |
| 2 | K8s State | `pod.phase` | `Pending` (fact-2839feee0a24) | 确认 Pod 当前处于待调度状态，未发生崩溃或终止 |
| 3 | K8s Event | `FailedScheduling` | 56m 内持续出现 2 次 `FailedScheduling` 事件，明确提示 `3 node(s) didn't match Pod's node affinity/selector` (fact-5f6944db947c, fact-6e72e224715c) | 提供确切的调度器拒绝原因，确认亲和性冲突为唯一调度阻碍 |
| 4 | Metric | `kube_pod_status_phase` | 目标 Pod 的 `Pending` 状态值为 `1`，且无 `Unknown` 状态计数 (fact-8d49cc7d2ec5, fact-4d11abfa1344) | 从监控维度独立确认 Pod 处于 Pending 状态，与 K8s 状态一致 |
| 5 | K8s Config | Resource Requests/Limits | CPU: 5m/50m, Memory: 8Mi/32Mi (fact-371447c6cf93, fact-3c3c6b0b0ebc, fact-476ca176c5c3, fact-5e0aaf21e383) | 资源请求量极低，排除因资源不足导致的调度失败，聚焦于节点标签匹配问题 |

**证据互证与说明：**
K8s 状态（Phase=Pending, Scheduled=False）与调度器事件（FailedScheduling）在时间线和错误消息上高度一致，共同指向唯一的失败原因——节点亲和性/选择器不匹配。Prometheus 监控数据确认了该 Pod 持续处于 Pending 状态，排除了瞬态故障的可能。由于 Pod 未能调度启动，Logging 和 Tracing 数据为空，诊断完全依赖 K8s 层面事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector {aiops.lab/unavailable: true} → 集群 3 个节点均缺少该标签（调度器选择器匹配失败） → 调度器无法分配节点 (0/3 nodes matched) → Pod 持续处于 Pending 状态，无法启动
```

### 根因结论

已确认根因为 **节点选择器（nodeSelector）标签不匹配**。

1.  **已确认的根因及证据引用**：
    Pod 期望调度至包含 `aiops.lab/unavailable: true` 标签的节点，但集群中所有可用节点均无此标签。
    *   **直接证据**：K8s 调度器事件 `FailedScheduling` 明确指出 `3 node(s) didn't match Pod's node affinity/selector` (证据 #3)；Pod 条件 `PodScheduled=False` 及原因 `Unschedulable` 证实了调度失败的持久性 (证据 #1)。
    *   **辅助证据**：低资源请求量（证据 #5）与监控确认的 Pending 状态（证据 #4）排除了资源瓶颈，将故障范围锁定在标签匹配问题上。

2.  **证据完整性**：
    现有证据链完整，K8s 状态、事件与监控数据相互印证，足以确定根因。Logging 和 Tracing 因 Pod 未启动缺失，但不影响对此类调度类故障的判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.4s
├─ 并发证据采集: 35.5s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 35.5s (Evidence 29.2s, RCA 6.1s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable, pod-volume-mount-failed, pod-config-error
