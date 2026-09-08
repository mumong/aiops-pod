## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` (fact-0f65e68ba8b2) | `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 直接显示调度器在集群所有节点上均因亲和性/选择器不匹配而拒绝调度，且无抢占空间。 |
| 2 | K8s State | `kubernetes` (fact-059cbbee294c) | Pod 状态为 `Pending` | 确认 Pod 始终无法进入运行状态，是调度过失败的直接表现。 |
| 3 | K8s Config | `kubernetes` (fact-4a87effbe42f, fact-79b485bdb988) | `resource_request`: Memory `8Mi`, CPU `5m`; `resource_limit`: Memory `32Mi`, CPU `50m` | 资源请求极其微小，排除因资源配额不足导致的调度阻塞。 |
| 4 | Metric | `prometheus` (fact-051645be8718) | `kube_pod_status_phase{phase="Pending"}` 值为 `1` | 确认当前 Pod 确实处于 Pending 阶段，无状态切换。 |

**证据分析：**
1. Pod 的 Pending 状态（#2）与 Prometheus 指标持续为 Pending（#4）相互印证，排除了状态抖动可能。
2. 调度事件明确指出了拒绝原因是 `node affinity/selector` 不匹配（#1），而非资源不足。
3. 极低的资源请求配置（#3）进一步证实了调度失败并非由资源争抢引起，而是纯粹的配置匹配问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 包含 Node-Selector `aiops.lab/unavailable=true` → 集群节点标签中不存在 `aiops.lab/unavailable` → 调度器过滤全部节点，返回 FailedScheduling 事件 → Pod 持续保持 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 调度约束（Node-Selector）与集群节点标签不匹配**。
调度器根据 Pod 的 Node-Selector `aiops.lab/unavailable=true` 进行过滤，但集群中所有节点均缺乏该标签，导致调度失败（见证据 #1）。Pod 的 Pending 状态（见证据 #2）是该机制的唯一可观测现象。资源请求极低（见证据 #3）排除了资源瓶颈。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.3s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 53.1s (Evidence 45.1s, RCA 7.9s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
