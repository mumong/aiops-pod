## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 持续处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes (Pod) | 状态: Pending | 确认 Pod 未启动且未进入 Failed 或 Running 阶段 (fact-8c795cbbd0cc) |
| 2 | K8s Event | Kubernetes (Scheduler) | `FailedScheduling 29m (x7 over 59m) ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-3bb86de1479f) | 确认调度失败的根本原因是标签选择器不匹配，且该状态已持续超过 59 分钟 |
| 3 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}=1` (fact-3178a1a02ffc) | 通过指标侧确认 Pod 持续维持在 Pending 状态，无相变 (fact-5c3408e56048) |

**证据说明**：
Kubernetes 事件明确指出有 3 个节点因“不匹配节点亲和性/选择器”而被拒绝。Pod 状态 (Pending) 和 Prometheus 指标 (phase=Pending) 均确认了这一停滞状态。由于 Pod 未启动，Logging 和 Tracing 维度为 `not_applicable`，缺乏应用侧数据作为佐证。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义中包含 Node-Selector 'aiops.lab/unavailable=true'  → 集群内 3 个节点均不具备该标签 → default-scheduler 判定 0/3 节点匹配，返回 FailedScheduling → Pod 无法被调度，维持 Pending 状态
```

### 根因结论
根因确认为 **Pod 调度约束失败**。
Pod 的配置中定义了节点选择器 `aiops.lab/unavailable=true`，导致调度器在集群现有的 3 个节点上无法找到任何具备该标签的节点，从而持续拒绝调度并返回 `FailedScheduling` 事件。
目前无法确认配置该选择器的业务意图，也未确认集群中是否存在其他未在采样周期内展示的节点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 30.1s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 30.6s (Evidence 22.0s, RCA 8.5s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
