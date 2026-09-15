## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 (aiops-case-01)处于Pending状态，无法调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | status: Pending (fact-fcbd86d5ff2c) | 确定 Pod 的终端异常状态 |
| 2 | K8s Event | kubernetes | FailedScheduling: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (fact-13ad7b1f9c40) | 确认调度失败的具体机制是标签不匹配 |
| 3 | K8s Config | kubernetes | container.resource_request.cpu: 5m, memory: 8Mi; limits: cpu: 50m, memory: 32Mi (fact-4ddc2004317d ~ fact-c3f5bf8fa6a6) | 排除资源请求量过大导致的调度失败 |

**证据关联说明：**
证据 1 确认 Pod 无法进入调度流程；证据 2 提供了根本原因的直接文本支持，指明 3 个可用节点均因“node affinity/selector”未匹配而不可用。证据 3 证明该 Pod 的资源消耗极低（仅 5m CPU / 8Mi 内存），证实调度失败并非由资源争抢引起，进一步排除了资源维度的可能性。

## 🎯 根因分析 · g1

```text
Pod Spec配置 NodeSelector: aiops.lab/unavailable=true → 集群所有节点标签与该NodeSelector不匹配 → 调度器返回 FailedScheduling → Pod持续处于Pending状态 (68+分钟)
```

### 根因结论
**已确认根因：Pod 的 NodeSelector 配置与集群节点标签不匹配。**

依据证据 2（`FailedScheduling` 事件），调度器明确报告所有 3 个节点均因 `didn't match Pod's node affinity/selector` 而无法调度。结合证据 3 显示资源请求极低，排除了容量不足的可能性。该配置导致 Pod 无法找到任何符合要求的节点进行绑定，从而维持在 `Pending` 状态超过 68 分钟。

---

## 📊 性能统计

```text
├─ 总耗时: 58.3s
├─ 问题定位: 20.1s
├─ 并发证据采集: 31.1s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 31.1s (Evidence 22.6s, RCA 8.4s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
