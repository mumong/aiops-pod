## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | aiops-case-v03/workload Pod 处于 Pending 状态，未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-087b04b639f2/fact-faf57aecd1ac`: `FailedScheduling: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | **直接归零**：调度器明确报告因找不到 PVC 导致 0/3 节点满足条件 |
| 2 | K8s Event | kubernetes | `fact-0f569aa55819`: Pod `aiops-case-v03/workload` 状态 `Pending` | **确认症状**：Pod 处于待调度状态，尚未运行 |
| 3 | K8s Config | kubernetes | `fact-439a01697f79/fact-b4cdfcb29761`: CPU 请求 `5m`，内存请求 `8Mi` | **排除资源争用**：资源需求极低，非因集群资源耗尽导致挂起 |
| 4 | Metric | prometheus | `fact-293ae71c7e76`: `kube_pod_status_phase` phase=Pending 值为 `1` (2026-09-11T08:38:16.022000Z) | **独立观测**：通过 Prometheus 确认目标 Pod 处于 Pending 状态 |
| 5 | Tool Output | kubectl | `kubectl_get_by_name`: `Error from server (NotFound): persistentvolumeclaims "unavailable-claim" not found` | **证据闭合**：验证了 PVC 确实不存在，证实调度事件中的错误原文 |

K8s Event 与 Prometheus Metric 在“Pod 处于 Pending”这一现象上互相印证。直接调用 `kubectl` 检查 PVC 返回 NotFound，提供了该 Pod 永远无法被调度的决定性证据。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义引用不存在的 PVC 'unavailable-claim' → 调度器检测到依赖 PVC 未绑定/不存在 → 0/3 节点满足调度条件 (FailedScheduling) → Pod 永久滞留于 Pending 状态
```

### 根因结论
根因已确认：Pod `aiops-case-v03/workload` 依赖的持久卷声明 `unavailable-claim` 在命名空间 `aiops-case-v03` 中不存在。

- **事实支撑**：调度事件明确指出 `persistentvolumeclaim "unavailable-claim" not found`（#1），且直接检查该资源的命令返回 `NotFound`（#5）。
- **排除干扰**：Pod 的资源请求（#3）非常低，且集群中有 3 个节点可用（事件原文），因此挂起纯粹由缺失的持久卷声明引起，而非资源不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.3s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-v03/workload: 41.4s (Evidence 34.6s, RCA 6.8s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
