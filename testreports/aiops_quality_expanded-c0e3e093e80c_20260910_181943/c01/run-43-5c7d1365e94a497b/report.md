## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 定义中包含节点选择器 `aiops.lab/unavailable=true`，但集群中所有节点均缺少该标签，导致调度器无法找到匹配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling` 持续 67m；`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 直接确认 Pod 因节点亲和性/选择器不匹配被调度器拒绝 |
| 2 | K8s State | kubernetes | `status: "Pending"` | 症状确认：Pod 未进入 Scheduling/Running 阶段 |
| 3 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (样本量 1，trend_evaluable=false) | 确认 Pod 状态当前处于 Pending |

**证据说明**：
- 证据 #1 提供的错误信息直接指向“节点选择器/亲和性不匹配”，而非资源不足（如 CPU/Memory），这排除了资源争用类根因。
- 证据 #2 与 #3 一致，确认异常状态稳定。
- 因 Pod 未启动，Logging 和 Tracing 维度无数据，诊断仅依赖 K8s 控制面的调度事件。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 定义了节点选择器 `aiops.lab/unavailable=true` → 集群中所有节点均缺少该标签 → 调度器执行亲和性匹配失败 → Pod 保持 Pending 状态
```

### 根因结论
已确认的根因为 **节点选择器不匹配**（引用证据 #1）。
Pod 定义中强制要求节点拥有标签 `aiops.lab/unavailable=true`，但集群内所有 3 个节点均无此标签，导致调度器无法找到任何满足条件的节点。该事件已在集群中持续 67 分钟。

---

## 📊 性能统计

```text
├─ 总耗时: 49.0s
├─ 问题定位: 15.6s
├─ 并发证据采集: 27.2s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 27.2s (Evidence 22.6s, RCA 4.5s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
