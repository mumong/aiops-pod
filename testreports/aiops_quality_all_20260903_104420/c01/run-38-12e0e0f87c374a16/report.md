## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未被调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling  19m (x14 over 84m)  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 证实 Pod 因节点标签/选择器不匹配，导致调度持续失败 |
| 2 | K8s State | pod.status | `status: Pending` | 确认为 Pod 的当前停滞状态 |
| 3 | K8s Config | container.resource_request.cpu | `5m` | 排除 CPU 资源配额不足导致的调度失败 |
| 4 | K8s Config | container.resource_request.memory | `8Mi` | 排除内存资源配额不足导致的调度失败 |
| 5 | Metric | prometheus | `kube_pod_status_phase {phase="Pending"} = 1` (单样本) | 确认当前 Pod 处于 Pending 状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase {phase="Running"} = 0` (单样本) | 确认 Pod 未处于 Running 状态 |

**证据说明：**
调度器产生的 `FailedScheduling` 事件（#1）给出了明确的拒绝原因：3个节点都不匹配 Pod 的亲和性/选择器。由于资源请求量极低（#3、#4），排除了资源不足导致的调度失败。Metric 数据（#5、#6）一致佐证了 Pod 停滞在 Pending 阶段且未进入运行状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 NodeSelector (fact-dce4e5b4ed91) → 集群节点缺失该标签 (fact-dce4e5b4ed91) → 调度器 3/3 节点评估不匹配 → Pod 持续 Pending (fact-32aa4dcc845d, fact-8a225c221024)
```

### 根因结论

根因是 **Pod 的调度选择器在集群中无匹配节点**。
调度器事件（#1）明确指出 Pod 的 NodeSelector/Affinity 导致所有节点评估失败。Pod 配置的资源请求（CPU `5m`, Memory `8Mi`）极小（#3、#4），排除了资源抢占或不足的问题。因此，调度失败完全归因于标签/亲和性规则限制，导致 Pod 无法被分配至任何可用节点。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 15.9s
├─ 并发证据采集: 574.6s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 574.6s (Evidence 566.4s, RCA 8.0s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
