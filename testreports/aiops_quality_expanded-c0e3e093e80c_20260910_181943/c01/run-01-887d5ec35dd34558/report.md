## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 NodeSelector 'aiops.lab/unavailable=true'，但集群内所有可用节点均缺乏该标签，导致调度器无法找到匹配节点（0/3 nodes match）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态: `Pending` | 确认 Pod 尚未被调度至任何节点 |
| 2 | K8s Event | Kubernetes | `Warning FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 直接证明集群中所有 3 个节点均不符合 Pod 的 NodeSelector 要求 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.cpu`: `50m` | 确认资源硬限制配置，非调度失败主因 |
| 4 | K8s Config | Kubernetes | `container.resource_request.cpu`: `5m` | 确认资源请求配置，非调度失败主因 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` (Pending): `1` (Sample: 1) | 指标确认 Pod 持续处于 Pending 阶段 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (Succeeded): `0` (Sample: 1) | 确认 Pod 未完成，无成功执行样本 |
| 7 | Logging | Elasticsearch | 采集为空 | 容器未启动，无法产生应用日志 |
| 8 | Tracing | DeepFlow/Tempo | 采集为空 | Pod IP 为空，无关联的流量追踪数据 |

Kubernetes Event 明确指出了调度失败的拓扑原因（3/3 节点标签不匹配），Metric 确认了该状态在持续，而 Logging 和 Tracing 的空值进一步证实了 Pod 在到达“运行”阶段前已被拦截在调度层。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 声明了 node_selector: aiops.lab/unavailable=true → 
集群中 3 个节点的标签不匹配该选择器 → 
Scheduler 触发 FailedScheduling 事件并拒绝调度 → 
Pod 状态保持在 Pending
```

### 根因结论

已确认根因为 **Pod 调度配置与集群节点标签不匹配**（证据 #1, #2, #5）。

Pod 声明了 `node_selector: aiops.lab/unavailable=true`，但集群内所有可用的 3 个节点均不具备该标签。调度器因无法满足节点亲和性/选择器要求（`0/3 nodes match`）而拒绝调度，导致 Pod 状态持续为 Pending。由于容器从未成功启动，Logging 和 Tracing 维度的数据缺失属于正常现象（证据 #7, #8），不构成额外故障证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.5s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 33.8s (Evidence 25.9s, RCA 7.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
