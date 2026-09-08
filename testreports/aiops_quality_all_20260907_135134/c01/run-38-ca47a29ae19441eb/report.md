## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | phase: Pending (fact-751f78ce546a) | 确认 Pod 处于未调度状态，未进入运行时阶段 |
| 2 | K8s Event | default-scheduler | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector (fact-2dbcf6ea0ab2) | 直接证明调度失败，原因是不满足节点亲和性/选择器匹配 |
| 3 | K8s State | pod.condition | PodScheduled=False, reason=Unschedulable, message=didn't match Pod's node affinity/selector (fact-d549d9fc2582) | 提供持久化的失败原因描述，与事件日志相互印证 |
| 4 | K8s Config | container.resource_request.cpu | 5m (fact-22b2a9a6c46e) | 资源请求极低，排除因资源不足导致调度的可能性 |
| 5 | K8s Config | container.resource_request.memory | 8Mi (fact-b8937a19c7d9) | 资源请求极低，排除因资源不足导致调度的可能性 |
| 6 | Metric | kube_pod_status_phase | Pending=1, Succeeded=0 (fact-a53096e76e84, fact-6cbccecc569a) | 从外部监控视角确认 Pod 处于 Pending 状态，且无成功终态记录 |

K8s 事件与状态字段均明确指向 "node affinity/selector" 不匹配，结合极低的资源请求量，证据表明该 Pod 未调度纯粹由配置约束引起，而非资源争抢或节点故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 nodeSelector 'aiops.lab/unavailable=true' → 集群节点不满足标签约束 → default-scheduler 报 FailedScheduling → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为 **调度约束不匹配**。

Pod `aiops-case-01/workload-68c557d875-bsq52` 被配置了节点选择器约束，要求目标节点必须具备 `aiops.lab/unavailable=true` 标签，但集群中所有可用节点均未设置该标签。这一配置导致 `default-scheduler` 无法找到匹配的节点进行调度，从而使 Pod 一直处于 Pending 状态且 `Unschedulable` 条件为真（详见证据 #2, #3）。

未确认：为何 Pod 被配置了期望节点具有 `unavailable=true` 标签的调度约束（可能是测试场景或配置错误）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 33.1s
├─ 并发证据采集: 42.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 42.3s (Evidence 33.0s, RCA 9.0s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
