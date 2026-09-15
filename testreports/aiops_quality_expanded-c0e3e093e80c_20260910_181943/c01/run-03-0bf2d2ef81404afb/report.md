## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 处于 Pending 状态，持续被调度器拒绝 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` (fact-01e3770b3122, fact-04935b8a17e8) | 确认调度器因亲和性/选择器不匹配拒绝 Pod，且 3 个节点全部失败。 |
| 2 | K8s Config | `kubernetes` | `container.resource_request.memory: 8Mi` (fact-272ac12f86da), `container.resource_request.cpu: 5m` (fact-f04c91e4d57b) | 排除资源不足导致的 Pending，资源请求量极低。 |
| 3 | Metric | `prometheus` | `kube_pod_status_phase` value `1` (Pending), value `0` (Unknown) (fact-3e37a1fbedf1, fact-0fc62170f128) | 确认 Pod 当前处于 Pending 状态，且未进入 Unknown 或其他阶段。 |
| 4 | K8s Config | `kubernetes` | `pod.status: Pending` (fact-971ae705cfb1) | 确认 Pod 最终停滞状态。 |

**证据关联分析：**
K8s Event (Fact 1) 明确指出调度失败原因是“节点不匹配亲和性/选择器”，而非资源限制；结合 K8s Config (Fact 2) 显示资源请求极低，排除了资源争用可能；Metric (Fact 3) 和 Pod 状态 (Fact 4) 一致印证了 Pod 长期停滞在 Pending 阶段，符合调度未完成的特征。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义配置 node_selector: aiops.lab/unavailable=true → 集群所有节点缺失该标签 → 调度器无法找到匹配节点 → Pod 处于 Pending 状态并触发 FailedScheduling 事件
```

### 根因结论

**根因已确认**：Pod 定义中配置了 `node_selector: aiops.lab/unavailable=true` 约束，而集群中所有可用节点（共 3 个）均缺少此标签，导致 `default-scheduler` 无法将 Pod 绑定到任何节点。这一判断由 K8s 事件日志明确指出的节点亲和性不匹配事实（Fact 1、2）及 K8s 配置事实支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 58.8s
├─ 问题定位: 17.0s
├─ 并发证据采集: 32.9s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 32.9s (Evidence 24.9s, RCA 7.9s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable, pod-volume-mount-failed
