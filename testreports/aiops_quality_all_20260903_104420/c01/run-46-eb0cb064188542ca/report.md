## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod workload-68c557d875-llhkh in aiops-case-01 remains in Pending state (PendingUnschedulable). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.condition (Unschedulable): 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.. (fact-cb4b74344665) | 直接失败原因：所有 3 个节点均不满足调度条件。 |
| 2 | K8s Event | kubernetes | FailedScheduling (x14 over 96m): 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. (fact-60b5b1983537) | 确认调度器长期处于失败状态，排除了瞬时资源争抢。 |
| 3 | K8s State | kubernetes | pod.phase: Pending (fact-120806a6f035) | 确认容器未启动，排除了运行期 CrashLoopBackOff 或 OOMKill 等运行时现象。 |
| 4 | Metric | prometheus | kube_pod_status_phase: Pending=1, Unknown=0 (fact-b89f9db17c38) | 仅有一个单点样本，确认 Pod 当前处于 Pending 状态；无法提供趋势变化，仅用于状态确认。 |
| 5 | K8s Config | kubernetes | container.resource_request.memory: 8Mi, limit: 32Mi; cpu request: 5m, limit: 50m (fact-127625449994, fact-1eda50f5bf70, fact-20a0affd48e3, fact-b0f44ea6db74) | 资源请求极低（8Mi/5m），证实“资源不足”（CPU/Memory Exhausted）不是调度失败的候选原因。 |

证据分析：
- **K8s State/Event** 高度一致，明确指出失败原因是 “didn't match Pod's node affinity/selector”。
- **Metrics** 数据证实了 Pod 持续处于 Pending 状态。
- **K8s Config** 显示资源请求极低，且结合 FailedScheduling 的错误原文中未提及 `insufficient memory/cpu`，进一步排除了常规的资源争用，将焦点锁定在 `node affinity/selector` 不匹配上。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中指定了不存在的 NodeSelector/NodeAffinity {aiops.lab/unavailable: true} → 调度器扫描所有 3 个节点均不匹配标签规则，且抢占无法解决 → 调度器返回 Unschedulable 错误 → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认根因：调度配置不匹配 (Misconfigured NodeSelector/Affinity)。**

*   **原因引用**：根据输入事实，调度器返回了明确的拒绝原因：“3 node(s) didn't match Pod's node affinity/selector” (fact-60b5b1983537, fact-cb4b74344665)。
*   **分析**：
    1.  Pod 资源请求（8Mi/5m）极低，且节点数量为 3 个，常规集群不存在整体资源枯竭，因此排除了资源不足。
    2.  日志和追踪维度未适用（容器未启动），但 K8s 事件已完整记录了 `FailedScheduling` 的精确机理，即节点标签与 Pod 的亲和性要求不匹配。
    3.  证据足以形成闭环：配置要求（不存在的标签）→ 调度器动作（全节点拒绝）→ 现象（Pending）。无需额外的日志或追踪来支撑此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.3s
├─ 并发证据采集: 50.6s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 50.6s (Evidence 42.7s, RCA 7.8s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
