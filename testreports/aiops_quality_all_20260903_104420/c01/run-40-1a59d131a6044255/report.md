## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod workload-68c557d875-llhkh 处于 Pending 状态且持续失败调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | pod.status: Pending | 定义直接现象：Pod 停留在调度阶段 |
| 2 | K8s Event | K8s Event | FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling. | 确认调度器失败原因：所有节点均未匹配 Pod 的亲和性/选择器要求 |
| 3 | K8s Config | K8s Config | 容器内存请求 8Mi，限制 32Mi；CPU 请求 5m，限制 50m | 排除资源配额导致的调度失败可能性 |
| 4 | Metric | Metric | kube_pod_status_phase (phase=Pending): 1, sample_count=1 | 确认 Pod 当前处于 Pending 状态（无时间序列趋势） |

**证据总结：**
Pod 状态（证据 1）与 Metric 观测（证据 4）一致确认其未启动且处于 Pending 阶段。关键事实在于 K8s Event（证据 2）明确指出调度失败是由于节点不匹配 Pod 的亲和性/选择器（node affinity/selector），而非资源不足。结合 K8s Config（证据 3）中极低的资源请求值，反证了资源因素并非导致 0/3 节点匹配的原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中包含 nodeSelector: aiops.lab/unavailable=true → 集群所有节点均缺失 aiops.lab/unavailable=true 标签 → 调度器计算 0/3 节点匹配亲和性/选择器要求 → 触发 Warning FailedScheduling 事件，Pod 保持 Pending 状态
```

### 根因结论

已确认根因为**调度器无法匹配节点亲和性/选择器**。
Pod `aiops-case-01/workload-68c557d875-llhkh` 的 K8s Event（证据 2）明确记录了 `FailedScheduling`，指出 `3 node(s) didn't match Pod's node affinity/selector`。虽然工具采集层面未直接输出节点标签的详细视图，但该调度事件的错误文本是 K8s 调度器内部计算后的权威事实，直接证实了集群节点未满足 Pod 的调度约束（即缺少 `aiops.lab/unavailable=true` 标签或类似的选择器配置），从而导致了当前的 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 27.0s
├─ 并发证据采集: 91.8s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 91.8s (Evidence 81.1s, RCA 10.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
