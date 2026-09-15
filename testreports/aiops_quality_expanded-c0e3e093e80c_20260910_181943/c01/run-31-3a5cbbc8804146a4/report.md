## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 in aiops-case-01 namespace is stuck in Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `pod.phase`: `Pending` (fact_id: fact-2cfdaa37dc76) | 确认 Pod 未被调度 |
| 2 | K8s State | `kubernetes` | `pod.condition`: `PodScheduled=False`, reason=`Unschedulable` (fact_id: fact-7ad6aa22ab6d) | 确认调度器判定不可调度 |
| 3 | K8s Event | `kubernetes` | `FailedScheduling`: `3 node(s) didn't match Pod's node affinity/selector` (fact_id: fact-59fdfd4fb40a) | 指出失败原因与节点亲和性/选择器不匹配 |
| 4 | K8s Config | `kubernetes` | `container.resource_request.cpu`: `5m`; `resource_limit.cpu`: `50m` (fact_id: fact-2cdf8bfda276, fact-0916112b8331) | 确认资源请求量极低，排除资源不足导致的调度失败 |
| 5 | K8s Config | `kubernetes` | `container.resource_request.memory`: `8Mi`; `resource_limit.memory`: `32Mi` (fact_id: fact-8527e7175da6, fact-2cfdaa37dc76) | 确认内存请求量极低，排除资源不足导致的调度失败 |
| 6 | Metric | `prometheus` | `kube_pod_status_phase` (phase=Pending): `1` (fact_id: fact-cd9a60bc3b15) | 从监控角度验证 Pod 持续处于 Pending 状态 |
| 7 | Metric | `prometheus` | `kube_pod_status_phase` (phase=Failed): `0` (fact_id: fact-339a933663ec) | 确认 Pod 未进入失败状态，仅为等待调度 |

Kubernetes 事件明确指出了 `node affinity/selector` 不匹配是导致 `FailedScheduling` 的直接原因，同时低资源请求排除了资源短缺的可能性。Metrics 数据确认了状态持续未变。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了 nodeSelector {aiops.lab/unavailable: true} → 集群中 master, node1, node2 均未包含该标签 → default-scheduler 评估 0/3 节点可用 → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因：节点标签选择器不匹配（Label Selector Mismatch）。**

Pod 的 `nodeSelector` 配置要求目标节点必须拥有 `aiops.lab/unavailable=true` 标签，但当前集群中所有 3 个可用节点（`master`, `node1`, `node2`）均不具备该标签。这导致 `default-scheduler` 在调度时无法找到满足亲和性条件的节点，从而拒绝调度。证据 1-4 充分印证了调度失败是由标签过滤而非资源耗尽引起的。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.3s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 41.4s (Evidence 34.3s, RCA 7.1s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
