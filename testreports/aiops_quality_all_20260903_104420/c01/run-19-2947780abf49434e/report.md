## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | status: "Pending" | 确证 Pod 最终异常状态 |
| 2 | K8s State | pod.condition | PodScheduled: False, reason: "Unschedulable", message: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector..." | 提供调度器给出的具体失败机制：节点亲和性/选择器未匹配 |
| 3 | K8s Event | default-scheduler | Warning  FailedScheduling, message: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.." | 提供调度失败的直接事实记录，时间覆盖 44m 至 33m |
| 4 | K8s Config | container.resource_request.cpu | "5m" | 提供资源限制上下文（非调度瓶颈） |
| 5 | K8s Config | container.resource_request.memory | "8Mi" | 提供资源限制上下文（非调度瓶颈） |
| 6 | Metric | prometheus | kube_pod_status_phase=1 (phase="Pending", sample_count=1) | 独立观测确认 Pod 在监控指标中持续处于 Pending 状态 |

证据说明：
1. **多维度互相印证**：Kubernetes 的调度事件 (fact-155b8370ea74) 与容器条件状态 (fact-ea319bb701e6) 完全一致，均指向“节点亲和性/选择器未匹配”；同时 Prometheus 指标 (fact-5086899d266d) 从监控维度独立证实了 Pod 仍处于 Pending 阶段。
2. **排除资源因素**：资源请求事实 (fact-43650b387c11, fact-812260cd4052) 显示资源需求极低（5m CPU, 8Mi Memory），确认调度失败不是由资源不足引起，而是策略性配置（NodeSelector）不匹配。
3. **数据局限**：Logging 与 Tracing 因 Pod 未启动且 Pod IP 为空无法获取数据，但不影响基于 K8s 核心状态和事件对调度失败的结论。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：Pod 定义包含 nodeSelector: aiops.lab/unavailable=true（由事件及原因推导）
→ 失败机制：集群内所有可用节点均不存在该标签
→ 直接失败：调度器评估所有节点不满足亲和性/选择器约束，预调度失败
→ 用户可见现象：Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending/Unschedulable 状态
```

### 根因结论

**已确认的根因**：Pod 的调度配置（`nodeSelector: aiops.lab/unavailable=true`）与集群节点的实际标签状态不匹配。

**证据引用**：
- 调度事件与条件状态（#1, #2, #3）明确指出失败原因是“3 node(s) didn't match Pod's node affinity/selector”。
- 资源请求极低（#4, #5）排除了资源不足的可能性，进一步确认是配置约束导致。
- 指标数据（#6）佐证了该状态并非瞬时故障，而是持续的调度失败。

**不确定性说明**：
- 现有事实确证了“节点标签缺失导致调度失败”这一技术根因，但无法从输入事实中直接判断该 `nodeSelector` 是否为有意配置或部署配置错误（属于 `unknowns` 列表中的业务逻辑疑问，不影响故障技术定性的准确性）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 59.8s
├─ 并发证据采集: 74.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 74.1s (Evidence 64.8s, RCA 9.1s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
