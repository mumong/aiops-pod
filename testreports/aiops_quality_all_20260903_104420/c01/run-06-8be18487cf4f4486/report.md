## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod workload-68c557d875-llhkh (aiops-case-01) 持续处于 Pending 状态，未被调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending`, `pod.condition: Unschedulable` | 确证 Pod 未调度且处于不可调度状态 |
| 2 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available` | 明确指示所有节点均未通过亲和性/选择器检查 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu: 5m`, `memory: 8Mi`; `limit.cpu: 50m`, `memory: 32Mi` | 排除因资源不足导致调度的可能性 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}: 1` | 辅助确认当前处于 Pending 状态 |

**证据关联：**
K8s 事件（#2）明确指出“3 个节点都不匹配 Pod 的节点亲和性/选择器”，结合状态（#1）证实了调度失败。资源请求（#3）极低，排除了资源耗尽这一常见原因，将故障范围精准锁定在亲和性配置上。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 nodeSelector: aiops.lab/unavailable=true → 集群内 3 个节点均未设置该 label，无法匹配 → 调度器标记为 Unschedulable 并记录 FailedScheduling 事件 → Pod 持续处于 Pending 状态且 nodeName 为空
```

### 根因结论

已确认根因为 **Pod 配置了不存在的节点选择器**。

Pod 定义了 `nodeSelector: aiops.lab/unavailable: 'true'`（证据 #2），而集群内所有 3 个节点均未拥有该 Label。这导致 `default-scheduler` 在调度时判定所有节点均不满足亲和性要求，进而触发 `FailedScheduling` 事件并导致 Pod 永远处于 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.7s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 51.1s (Evidence 42.6s, RCA 8.3s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
