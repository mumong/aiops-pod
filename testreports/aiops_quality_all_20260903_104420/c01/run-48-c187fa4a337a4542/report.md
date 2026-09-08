## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，调度器持续报错 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling 33m (x14 over 98m) ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 核心故障现象：调度器连续 14 次拒绝调度，因节点亲和性/选择器不匹配 |
| 2 | K8s State | `pod.condition` | `PodScheduled: False, reason: Unschedulable, message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 确认 Pod 长期处于 Unschedulable 状态，且预抢占机制失效 |
| 3 | K8s State | `Kubernetes Topology` | `fact-2acbdcfa4629: 节点 master 缺少标签 aiops.lab/unavailable=true; fact-560611ff92a9: 节点 node1 缺少标签 aiops.lab/unavailable=true` | 验证集群中所有节点均不存在 Pod 期望的标签，构成调度阻塞 |
| 4 | K8s Config | `container.resource_request` | `cpu: 5m; memory: 8Mi` | 确认 Pod 资源请求极小，排除因资源不足被拒的可能性 |

**证据分析：**
Kubernetes Event (1) 和 Pod Condition (2) 相互印证了 Pod 持续处于 Pending 状态，且根因明确指向 `node affinity/selector`。结合节点拓扑事实 (3)，排除了资源不足 (4) 等常见原因。日志与追踪因 Pod 未启动且工具执行被拒（权限错误），无法提供补充业务上下文。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义 nodeSelector {aiops.lab/unavailable: 'true'} → 集群所有节点均无此标签 → 调度器匹配失败 (FailedScheduling) → Pod 持续 Pending (Unschedulable)
```

### 根因结论

根因确认为 **Pod 配置的 `nodeSelector` 标签在集群中不存在**。
证据 3 证实集群中所有可用节点均缺乏标签 `aiops.lab/unavailable`，导致调度器依据亲和性规则无法将 Pod 分配给任何节点。该结论由调度事件记录 (证据 1) 与节点拓扑事实 (证据 3) 形成闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.3s
├─ 并发证据采集: 57.8s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 57.8s (Evidence 49.4s, RCA 8.2s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
