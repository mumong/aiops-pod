## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 定义了强依赖的 PVC `unavailable-claim`，但该 PVC 在命名空间 `aiops-case-v03` 中不存在，导致调度器因无法绑定卷而持续拒绝调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` (Pending) | `PodScheduled` 条件为 `False`，消息显示 `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 确认 Pod 调度失败的直接原因：调度器在 3 个节点上均找不到名为 `unavailable-claim` 的 PVC |
| 2 | K8s Event | `FailedScheduling` 事件 | 27m 内累计 5 次失败 (首次 53m)，错误信息一致：`persistentvolumeclaim "unavailable-claim" not found` | 证实异常是持续性且高频发生的，确认调度器持续拒绝该 Pod 的调度请求 |
| 3 | Metric | `kube_pod_status_phase` | `Pending` 状态值为 1 | 从指标层面独立确认 Pod 当前处于 Pending 状态，与 K8s State 表现一致 |
| 4 | K8s Config | 资源限制/请求 | `cpu` 请求 `5m`/限制 `50m`；`memory` 请求 `8Mi`/限制 `32Mi` | 排除因资源配额不足（CPU/内存超限）导致 Pod 无法调度的可能性，缩小故障范围至存储依赖 |

**证据关联说明：**
K8s 事件 (Fact #2) 与 Pod 状态条件 (Fact #1) 高度一致，均明确指向 `unavailable-claim` PVC 缺失是触发 `FailedScheduling` 的原因。Metric (Fact #3) 从另一个维度确认了 Pod 长期停滞在 Pending 阶段。由于资源配置极其微小 (Fact #4)，调度器报错信息中排除了资源不足（Insufficient）的因素，使得存储绑定失败这一单一原因的证据闭环更加完整。日志和 Trace 因容器未启动而无法获取，属于预期内的“无数据”状态，不影响对调度失败的定论。

## 🎯 根因分析 · g1

### 因果链

```text
PVC `unavailable-claim` 在 `aiops-case-v03` 命名空间中缺失 → 调度器无法找到卷并进行绑定校验失败 → 触发 FailedScheduling 事件，Pod 持续处于 Pending 状态 → 用户观察到 `aiops-case-v03/workload` Pod 无法启动
```

### 根因结论

已确认根因为 **Pod 强依赖的 PVC `unavailable-claim` 缺失**。

1. **直接机制**：调度器在执行调度时，校验发现 `aiops-case-v03` 命名空间中不存在名为 `unavailable-claim` 的 PVC，导致 `PersistentVolumeClaim` 绑定条件不满足，从而持续拒绝调度该 Pod (证据 #1, #2)。
2. **证据支撑**：
   - `PodScheduled` 状态为 `False` 且报错明确提及 `not found` (证据 #1)。
   - 连续、多次的 `FailedScheduling` 事件 (证据 #2) 证实了故障的持续性，且未涉及资源竞争。
   - 极低的资源请求 (证据 #4) 排除了节点资源不足的可能性，强化了“卷缺失”是根本原因的可信度。
3. **局限性**：虽然故障现象已清晰，但 PVC 缺失的**业务层面原因**（如：未执行创建流程、资源 YAML 应用失败或被人工误删）目前无法通过自动化工具确证，这属于未决的业务流程问题，但不影响对“PVC 缺失导致 Pod 调度失败”这一技术根因的判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.6s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v03/workload: 35.6s (Evidence 28.1s, RCA 7.4s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
