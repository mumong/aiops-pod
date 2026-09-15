## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 持续处于 Pending 状态，未分配到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 揭示调度失败直接原因：节点亲和性/选择器不匹配 |
| 2 | K8s Config | resource_request.cpu | `5m` | 排除资源超卖/资源不足导致的调度阻塞 |
| 3 | K8s Config | resource_request.memory | `8Mi` | 排除资源超卖/资源不足导致的调度阻塞 |
| 4 | K8s State | pod.condition | `PodScheduled=False; Reason=Unschedulable` | 确认 Pod 处于调度失败状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase` Pending: `1` | 从监控维度佐证 Pod 持续处于 Pending 状态 |

证据说明：
- 调度事件 (#1) 与 Pod 状态 (#4) 强一致，均指向节点选择器（Node Affinity/Selector）不匹配。
- 容器资源请求量极低 (#2, #3)，排除了资源配额导致调度失败的可能，佐证了问题在于标签/亲和性配置。
- 监控数据 (#5) 从时间维度持续验证了 Pod 的 Pending 现象，未见状态变化。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义包含 nodeSelector: aiops.lab/unavailable=true → 调度器发现集群中 3/3 节点均无此标签 → 触发 FailedScheduling 事件 → Pod 保持 Pending 状态 (nodeName=<none>)
```

### 根因结论
已确认根因为 **Pod 选择器配置与节点标签不匹配**。Pod 声明了 `nodeSelector: aiops.lab/unavailable=true`，但集群所有节点（共 3 个）均未设置该标签，导致调度器无法找到任何可用节点（0/3 nodes are available）。证据 (#1, #4) 明确支持该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.5s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 39.6s (Evidence 31.7s, RCA 7.7s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
