## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod workload-68c557d875-llhkh 处于 Pending 状态，未调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Pending` (fact-cea47f8560ad) | 确证 Pod 当前异常状态，未绑定节点 |
| 2 | K8s Event | kubernetes | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-0fa572c0bd2a) | 直接失败原因，调度器判定无可用节点 |
| 3 | K8s Config | kubernetes | `cpu=5m, memory=8Mi` (fact-920ca70bc185, fact-0e5444735278) | 资源请求极低，排除资源耗尽导致的调度拒绝 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` (fact-2634fe39cbd4) | 外部监控确认 Pod 仍处于 Pending 阶段 |

**证据关联性说明：**
事件记录（#2）明确指出了调度失败原因为“节点亲和性/选择器不匹配”。配置项（#3）显示资源请求极低，进一步排除了资源压力作为根因的可能。监控指标（#4）独立证实了 #1 中的 `Pending` 状态持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的 Node-Selector 标签 aiops.lab/unavailable=true → 
集群中 3 个节点均不匹配该标签且处于 Ready 状态 → 
调度器执行 FailedScheduling 并拒绝调度 → 
Pod 保持 Pending 状态
```

### 根因结论

已确认根因为 **Node-Selector 配置与集群节点标签不匹配**。

根据 K8s Event 事实（证据 #2），调度器明确指出所有 3 个节点均未匹配 Pod 的亲和性/选择器。虽然资源请求（证据 #3）极低，不会导致节点资源不足，但标签不匹配是决定性的调度障碍。当前现象（证据 #1）由调度器直接判定造成，现有 Kubernetes 事实已足够支撑此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 23.9s
├─ 并发证据采集: 56.0s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 56.0s (Evidence 48.3s, RCA 7.5s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
