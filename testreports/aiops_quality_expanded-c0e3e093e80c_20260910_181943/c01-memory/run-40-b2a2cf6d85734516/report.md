## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 is stuck in Pending state due to FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient memory.` (fact-8e8fda6cf0d3) | 调度器明确判定所有节点因内存不足无法调度 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory` 设置为 `1Pi` (fact-75712edd855d) | 定义异常的源：单容器请求了远超常规物理机的极大内存 |
| 3 | K8s State | kubernetes | Pod `workload` 状态持续为 `Pending` (fact-d9136a14595b) | 确认 Pod 因上述原因长期无法进入运行态 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory` 同样设置为 `1Pi` (fact-74bfab97f558) | 限制值与请求值一致，进一步阻断了任何弹性调度的可能 |

**证据说明：**
K8s Event 直接指出了 3 个节点全部因 `Insufficient memory` 拒绝调度的事实，结合 K8s Config 中高达 `1Pi` 的请求值（事实 2），确证了集群物理资源无法满足该调度条件。Pod 的 `Pending` 状态（事实 3）是这一冲突的必然结果。Metrics 层面由于 Pod 未启动，仅能侧面印证未进入正常/失败运行状态，无更多可量化的时序趋势支持。

## 🎯 根因分析 · g1

```text
Container 'app' configured with memory limit/request of 1Pi (fact-2, 4) 
→ Scheduler evaluates cluster nodes (3 total) against 1Pi requirement 
→ All 3 nodes report Insufficient memory, preventing binding (fact-1) 
→ Pod remains in Pending state indefinitely (fact-3)
```

### 根因结论
**已确认根因**：Pod 中容器 `app` 错误配置了 `1Pi`（1 Pebibyte）的内存请求与限制。集群所有 3 个节点均无法满足此资源请求，导致调度器反复 `FailedScheduling`，使得 Pod 长期处于 `Pending` 状态。

**证据支撑**：
- 调度器事件明确归因为 `3 Insufficient memory`（事实 1）。
- 容器配置事实明确记录请求与限制均为 `1Pi`（事实 2、4）。
- 集群节点总数确认为 3，且全部拒绝（事实 1 原文）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 33.2s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-v02/workload: 36.7s (Evidence 30.1s, RCA 6.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
