## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 在 aiops-case-01 命名空间中持续处于 Pending 状态，未能调度至任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling` (x7 over 42m): `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (fact-20b1a82acb53, fact-3dd10a730477) | 确认调度失败核心原因：亲和性/选择器不匹配，且无节点满足条件 |
| 2 | K8s State | kubernetes | `PodScheduled=False`, reason=`Unschedulable` (fact-2e1d6f767b91) | 验证 Pod 长期处于 Unschedulable 状态，未发生状态转换 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu=5m`, `memory=8Mi` (fact-71453b1f4944, fact-66da750c0069) | 确认资源请求极低，非资源不足导致的调度失败 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu=50m`, `memory=32Mi` (fact-60a64ac01dbf, fact-4d0b2accacd9) | 确认资源限制极低，非资源过载导致的调度失败 |
| 5 | Metric | prometheus | `kube_pod_status_phase` for `phase: Pending` is `1` (fact-b0a65c93fb1e) | 指标确认 Pod 当前阶段仍为 Pending，未见 Succeeded 或 Running 状态 |
| 6 | Logging | elasticsearch | 容器未启动，物理上不会产生应用日志或业务 Trace (fact-logging-limitation) | 解释无日志数据的原因，排除应用层故障 |
| 7 | Tracing | deepflow+tempo | Pod-scoped Flow/Span 查询无法执行 (fact-tracing-limitation) | 解释无追踪数据的原因，确认未产生流量 |

证据链逻辑：K8s Event 明确指出 0/3 节点因亲和性/选择器不匹配而拒绝调度，K8s State 和 Metric 确认该状态持续存在。配置数据显示资源请求/限制极低，排除了资源不足的可能性。日志和追踪数据缺失符合 Pod 未启动的物理事实，进一步佐证问题出在调度层面而非应用运行时。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置 nodeSelector: {aiops.lab/unavailable: true} → 集群节点缺乏该标签，亲和性/选择器匹配失败 → 默认调度器触发 FailedScheduling 事件 (Unschedulable) → Pod 保持在 Pending 状态且不重启
```

### 根因结论

已确认根因为 **Pod 配置了不存在的节点选择器 `nodeSelector: {aiops.lab/unavailable: true}`**。

- 调度器在尝试调度 Pod 时，检查集群中所有节点，发现没有节点拥有 `aiops.lab/unavailable=true` 标签，导致 0/3 节点满足亲和性/选择器条件。
- 证据 #1 和 #2 直接支持此结论，显示 `FailedScheduling` 事件和 `Unschedulable` 状态。
- 证据 #3 和 #4 排除了资源不足的可能性，证据 #5 确认了 Pod 的 Pending 状态持续存在。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.1s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 33.8s (Evidence 26.7s, RCA 7.0s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
