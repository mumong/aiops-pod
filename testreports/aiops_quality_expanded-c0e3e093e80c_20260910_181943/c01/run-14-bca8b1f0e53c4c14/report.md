## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 remains in Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-2c9ecac14d6e) | 直接记录调度失败原因：无匹配节点 |
| 2 | K8s State | kubernetes | `PodScheduled=False`，Reason `Unschedulable`，Message 同上 (fact-d8561763431c) | 确认 Pod 状态处于不可调度阶段 |
| 3 | K8s Config | kubernetes | 资源 Request：CPU `5m`, Memory `8Mi`；Limit：CPU `50m`, Memory `32Mi` (fact-2173dfb92894 等) | 排除资源配额过高导致调度的可能，定位到亲和性/选择器匹配问题 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 值为 `1` (Pending) (fact-16f6b942ed60) | 确认 Pod 持续处于 Pending 状态 |
| 5 | Topology | kubectl | 工具调用失败：`kubectl get -n` 参数错误 (failed_tool_attempts) | 导致未能直接获取节点标签事实，但事件中的报错已足够支撑判断 |

**证据互证说明**：K8s Event (fact-1) 与 Pod State (fact-2) 均指向“不匹配节点亲和性/选择器”。虽然由于工具调用失败未能直接展示节点标签缺失的证据，但事件明确排除了资源不足或驱逐等原因。结合资源配置 (fact-3)，确认是调度策略层面的匹配失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 配置了 nodeSelector/亲和性要求 → 集群内 3 个节点均未匹配该要求 → 调度器无可用节点 (0/3) → Pod 保持 Pending (FailedScheduling)
```

### 根因结论

已确认根因为 **FailedScheduling due to node affinity/selector mismatch**（节点选择器不匹配）。

根据 K8s Event (fact-1, fact-2) 中的真实报错信息 `3 node(s) didn't match Pod's node affinity/selector`，调度器未能找到符合 Pod 亲和性或节点选择器要求的节点。尽管缺少节点标签的直接快照（因工具调用失败），但 Event 中的明确表述排除了资源不足等其他常见原因，确认为策略匹配失败导致无法调度。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 25.7s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 43.0s (Evidence 35.3s, RCA 7.6s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
