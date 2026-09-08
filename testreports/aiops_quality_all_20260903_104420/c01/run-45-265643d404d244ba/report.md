## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 状态为 Pending，无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling. (fact-23c3cf809a2f) | 确认调度失败原因：所有节点不匹配 Pod 的亲和性/选择器 |
| 2 | K8s State | kubernetes | `PodScheduled` condition: False; Reason: `Unschedulable`; Message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. (fact-4ba6d11d16a0) | 持续验证 Pod 无法被调度的状态 |
| 3 | K8s State | kubernetes | `pod.phase`: Pending (fact-33bc4b8e37bf) | 确认 Pod 处于 Pending 状态 |
| 4 | K8s Config | kubernetes | container `app` resource_request.memory: 8Mi; resource_limit.memory: 32Mi; resource_request.cpu: 5m; resource_limit.cpu: 50m (fact-07f4d494b302, fact-2eb301901a7f, fact-57c5eb2a3c33, fact-72e2d5453a14) | 资源请求值极小，表明调度失败并非由于资源不足 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}`: 持续为 1，共 61 个样本 (fact-b3859db58fdd) | 从指标层面确认 Pod 在观察窗口内一直未调度成功 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Running"}`: 持续为 0 (fact-06250f04d461) | 确认 Pod 从未进入运行状态 |

**证据说明：**
- 证据 1、2、3 从 Kubernetes 事件、状态和 Pod Phase 三个维度一致确认了 Pod 因节点亲和性/选择器不匹配而处于 Pending 状态。
- 证据 4 排除了资源不足作为调度失败的可能原因。
- 证据 5、6 通过 Prometheus 指标确认了 Pod 在长时间内持续处于 Pending 状态，从未转为 Running，与 Kubernetes 状态一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 nodeSelector: {aiops.lab/unavailable: true} → 集群节点缺乏该标签或标签值不为 true → 调度器判定 0/3 节点可用并触发 FailedScheduling 事件 → Pod 持续保持 Pending 状态
```

### 根因结论

已确认根因：Pod 的 `nodeSelector` 配置了 `aiops.lab/unavailable=true`，而集群内所有节点均不满足该标签条件，导致调度器拒绝调度。

该结论由以下证据支撑：
- K8s 事件 `FailedScheduling` 明确指出调度失败原因是节点不匹配 Pod 的亲和性/选择器 (证据 1)。
- K8s 状态持续显示 `Unschedulable` 和 `Pending` (证据 2、3)。
- 资源请求值极小，排除了资源不足的可能 (证据 4)。
- 指标数据确认 Pod 长期处于 Pending 状态 (证据 5、6)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 24.3s
├─ 并发证据采集: 59.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 59.2s (Evidence 51.2s, RCA 7.8s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
