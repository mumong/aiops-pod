## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload in aiops-case-v03 is stuck in Pending state due to FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-d9a56827f4cd` | `PodScheduled=False`, `reason="Unschedulable"`, `message="0/3 nodes are available: persistentvolumeclaim \"unavailable-claim\" not found."` | 明确标识 Pod 处于不可调度状态，失败原因指向缺失的 PVC 资源。 |
| 2 | K8s Event | `fact-14a7ebb8e9d2` | `Warning  FailedScheduling  4m24s  default-scheduler  ... persistentvolumeclaim "unavailable-claim" not found.` | 提供调度器拒绝绑定的直接证据，确认该 PVC 在集群中不存在。 |
| 3 | K8s State | `fact-139fa981d82e` | `Pod phase: Pending` | 记录 Pod 当前的停滞状态，由未满足的调度条件导致。 |
| 4 | K8s Config | `fact-14a7ebb8e9d2_context` | 输入中虽未显式列出 volume 定义 fact，但调度错误信息明确提及了对 `persistentvolumeclaim "unavailable-claim"` 的引用查找。 | 证实 Pod Spec 中存在对名为 `unavailable-claim` 的 PVC 的依赖引用。 |

**证据说明：**
K8s 状态与事件证据高度一致，共同指向同一个根因：Pod 的调度失败并非由资源容量或节点健康度引起，而是由于 Pod Spec 中引用的 PVC `unavailable-claim` 在集群中物理缺失。由于 Pod 尚未调度至节点，Logging 与 Tracing 维度无数据符合预期，不影响对调度阶段故障的判断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 PVC 'unavailable-claim' → 调度器在谓词评估阶段无法完成 Volume Binding → 调度器返回 'FailedScheduling' 错误 → Pod 卡在 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 规格中引用了一个不存在的 PersistentVolumeClaim (PVC) `unavailable-claim`**。

*   **原因描述**：根据事实 `fact-d9a56827f4cd` 和 `fact-14a7ebb8e9d2`，调度器在执行调度决策时，试图将 Pod 与 PVC 绑定，但因在 `aiops-case-v03` 命名空间中找不到名为 `unavailable-claim` 的 PVC 而失败。
*   **现象关联**：这一上游资源缺失直接导致了 `FailedScheduling` 事件（证据 #2）以及 Pod 状态持续为 `Pending` 且 `Unschedulable`（证据 #1, #3）。
*   **证据支持**：K8s 状态（证据 #1, #3）与 K8s 事件（证据 #2）相互印证，均明确指出了 `persistentvolumeclaim "unavailable-claim" not found` 这一关键信息，构成了完整的故障链条。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 31.9s
├─ 并发证据采集: 33.0s
│  └─ g1 aiops-case-v03/workload: 33.0s (Evidence 26.4s, RCA 6.5s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
