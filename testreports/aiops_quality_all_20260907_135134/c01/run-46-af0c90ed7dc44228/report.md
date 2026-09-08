## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态 `Pending` (fact-5209adeb4d0b, fact-d00a5b9d5afe) | 确认为调度失败导致的停滞状态 |
| 2 | K8s Event | Kubernetes | FailedScheduling 警告: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (fact-9567c8202718) | 提供调度器明确指出的失败原因 |
| 3 | K8s Config | Kubernetes | 资源限制: `memory=32Mi`, `cpu=50m` (fact-28556d52897a, fact-537dbed383f0) | 排除因资源请求过大导致的溢出 |
| 4 | K8s Config | Kubernetes | 资源请求: `memory=8Mi`, `cpu=5m` (fact-abd10fb8773a, fact-c73dde5655c2) | 排除因资源请求过大导致的溢出 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` 值为 1 (Pending), 0 (Succeeded) (fact-6ed5caee5490, fact-453f752c1d07) | 量化确认 Pod 持续处于 Pending 状态 |
| 6 | Topology | Kubernetes | 集群共存在 3 个节点 (来自 event 事实) | 确认节点总数与调度器评估基数一致 |

**证据分析**：
Kubernetes 状态与事件日志 (1, 2, 6) 提供了直接且一致的因果证据：调度器因节点亲和性/选择器不匹配导致 3/3 节点均不可用。资源配置日志 (3, 4) 证明 Pod 请求量极低，不存在资源耗尽嫌疑。Prometheus 指标 (5) 独立验证了 Pod 处于 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不满足集群现状的节点标签选择器 (nodeSelector) → 调度器评估集群所有可用节点均不匹配 Pod 的亲和性约束 → 调度器触发 FailedScheduling 事件并返回 Unschedulable 状态 → Pod 进入 Pending 状态且未分配节点
```

### 根因结论

已确认的根因是 **Pod 的节点亲和性/选择器（nodeSelector）配置与集群节点标签不匹配**。
证据事实 2 明确指出所有 3 个节点均未匹配 Pod 的亲和性选择器，且无抢占机会；结合事实 1 与 6 确认的 Pod `Pending` 状态，以及事实 3-4 排除资源限制因素，充分证实该选择器约束是导致 Pod 无法调度的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.3s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 37.8s (Evidence 28.7s, RCA 9.1s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
