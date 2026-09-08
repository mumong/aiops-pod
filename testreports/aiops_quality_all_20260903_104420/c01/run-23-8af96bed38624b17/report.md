## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态，无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-68c557d875-llhkh` status `Pending`, phase `Pending`, condition `PodScheduled=False`, reason `Unschedulable` | 确认 Pod 处于未调度状态及根本调度条件不满足 |
| 2 | K8s Event | kubernetes | Event `FailedScheduling` (x8 over 45m): "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" | 确认证调度器尝试失败的具体原因及持续时间 |
| 3 | K8s State | kubernetes | Condition `PodScheduled=False` message: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" | 提供调度器判定节点不可用的精确逻辑判定结果 |
| 4 | Metric | prometheus | `kube_pod_status_phase` = `1` (labels: container=kube-state-metrics, phase=Pending), sample_count=1 | 从监控维度证实 Pod 处于 Pending 状态的当前事实 |
| 5 | Metric | prometheus | `kube_pod_status_phase` = `0` (labels: container=kube-state-metrics, phase=Succeeded), sample_count=1 | 排除 Pod 已成功完成的情况 |
| 6 | K8s Config | kubernetes | Container `app` resource_request.memory: `8Mi`, cpu_request: `5m`; limits: memory `32Mi`, cpu `50m` | 确认资源请求量极低，排除了因资源请求过高导致的调度失败 |

上述证据（#1, #2, #3, #6）互相印证：Pod 资源请求极少，但调度器报告所有 3 个节点均无法匹配，结合 `node affinity/selector` 报错信息，将问题范围精确锁定为标签选择器配置而非资源配额。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了非标准的 nodeSelector: aiops.lab/unavailable=true → 集群中所有 3 个节点 (master, node1, node2) 均不满足该标签选择器条件 → 调度器判定 0/3 节点可用，持续触发 FailedScheduling 事件 → Pod 维持 Pending 状态且 nodeName 为 None
```

### 根因结论

已确认的根因是 Pod 配置了节点选择器 `nodeSelector {aiops.lab/unavailable: 'true'}`，而集群中的所有节点均缺少该标签，导致调度器无法匹配任何可用节点。

该结论由以下证据支持：
1. **状态确认**：Pod 持续处于 `Pending` 状态且 `PodScheduled` 条件为 `False`（证据 #1）。
2. **失败机制**：Kubernetes Event `FailedScheduling` 明确指出失败原因是 "didn't match Pod's node affinity/selector"（证据 #2, #3）。
3. **排除干扰**：Pod 的资源请求极低（证据 #6），且监控指标确认 Pod 未进入 Succeeded 状态（证据 #5），排除了资源不足或已完成的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 33.6s
├─ 并发证据采集: 61.6s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 61.6s (Evidence 49.8s, RCA 11.6s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
