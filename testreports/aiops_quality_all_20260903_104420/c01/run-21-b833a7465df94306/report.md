## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态超过 48 分钟，被调度器标记为 Unschedulable |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-30894266680a) | 确认调度失败的根本原因是节点亲和性/选择器不匹配，而非资源不足。 |
| 2 | K8s State | kubernetes | `pod.phase`: `Pending`, `pod.condition PodScheduled`: `False, reason: Unschedulable` (fact-324341e064f5) | 确认 Pod 处于无法调度的持续阻塞状态，未获得 IP 分配。 |
| 3 | K8s Config | kubernetes | `resource_request.cpu`: `5m`, `resource_limit.memory`: `32Mi` (fact-46f10c342432, fact-01484c62bede) | 排除资源超限导致的调度失败，Pod 资源请求极低。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase=P Pending): `1` (fact-10dadc348b46) | 确认 Pod 仍处于 Pending 状态，与 K8s 状态一致。 |

**证据分析：**
K8s Event (Fact 1) 明确指出调度失败是由于 `node affinity/selector` 不匹配，3 个可用节点均未通过检查。由于该 Pod 资源请求极低 (Fact 3)，且 Metric (Fact 4) 与 Pod 状态一致，排除了计算资源匮乏的可能性。所有证据共同指向 Pod 的调度约束条件与集群节点实际标签不兼容。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector (aiops.lab/unavailable=true) → 集群所有节点均缺失该标签 → 调度器评估 0/3 节点符合亲和性要求 → Pod 持续处于 Unschedulable (Pending) 状态
```

### 根因结论

已确认根因：Pod 的 `nodeSelector` 约束 `aiops.lab/unavailable=true` 与集群中所有节点的标签不匹配。
*   **证据支撑**：K8s Event 记录明确显示调度失败原因为 `3 node(s) didn't match Pod's node affinity/selector` (Fact 1)。
*   **排除项**：资源请求 (5m CPU / 8Mi Mem) 极低，非资源不足导致；Metric 数据确认了 Pending 状态的持续性。
*   **局限性说明**：Logging 和 Tracing 维度因容器未启动且底层存储/网络查询失败，未提供额外业务视角，但不影响基于 K8s 调度机制的根本原因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 27.8s
├─ 并发证据采集: 64.2s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 64.2s (Evidence 55.5s, RCA 8.6s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
