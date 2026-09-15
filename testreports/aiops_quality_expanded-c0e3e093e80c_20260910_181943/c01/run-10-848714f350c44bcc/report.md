## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 `nodeSelector: {aiops.lab/unavailable: 'true'}`，但集群中所有节点（master, node1, node2）均未设置该标签，导致调度器无法找到匹配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `status: "Pending"`, `phase: "Pending"`, `PodScheduled: False` | 确认 Pod 调度失败的直接症状。 |
| 2 | K8s Event | `event.message` | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确调度失败的机制为节点标签选择器匹配失败。 |
| 3 | K8s Config | `container.resource_request.cpu/memory` | `cpu: 5m`, `memory: 8Mi` | 确认资源请求值极低，排除因资源不足导致无节点可调度的可能性。 |
| 4 | K8s Event | `event.message` (fact-81a316787322) | `19m` 时的 `FailedScheduling` 事件记录 | 提供故障持续时间与事件发生的历史锚点。 |

**证据交叉印证：**
1. **配置与症状匹配**：证据 1 和 2 结合证实，Pod 处于 Pending 状态且无法调度。
2. **排除资源因素**：证据 3 提供的极小资源请求（5m CPU）排除了节点资源耗尽的可能性，指向调度逻辑或策略配置问题。
3. **逻辑闭环**：事件中的错误信息明确指出了 `affinity/selector` 不匹配，与已知的 Pod 配置（`nodeSelector: {aiops.lab/unavailable: 'true'}`）完全对应。由于 Pod 尚未启动，Logging 和 Tracing 维度无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了未存在于集群节点的 nodeSelector 标签 → 调度器无法找到满足亲和性/选择器条件的节点 → FailedScheduling 事件持续生成 → Pod 状态保持 Pending，无法进入 Scheduling/Running 阶段。
```

### 根因结论

**已确认的根因**：Pod 的 `nodeSelector` 配置 (`aiops.lab/unavailable: 'true'`) 与集群实际节点标签状态不一致。

*   **证据支撑**：
    *   **E1 (K8s Event)**：调度器报告 `3 node(s) didn't match Pod's node affinity/selector`。
    *   **E2 (K8s State)**：Pod 处于 `Pending` 状态且 `PodScheduled` 为 `False`。
    *   **E3 (K8s Config)**：资源请求极低，证明失败并非由资源分配瓶颈引起，而是纯粹的策略匹配失败。

该根因由官方诊断逻辑提供且证据充分，现象与配置偏差具有直接的因果关系。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.3s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 37.9s (Evidence 32.6s, RCA 5.2s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
