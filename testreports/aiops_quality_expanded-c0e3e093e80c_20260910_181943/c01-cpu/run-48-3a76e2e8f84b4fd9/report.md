## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | Pod aiops-case-v01/workload 处于 Pending 状态，未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `aiops-case-v01/workload` 状态为 `Pending` (fact-e5787c31a19f) | 确认 Pod 未进入运行阶段，是故障直接表现。 |
| 2 | K8s Config | CPU Request | 容器 `app` CPU Request 为 `100k` (fact-2afeecba60c5) | 明确资源诉求值，用于判断调度器判定逻辑。 |
| 3 | K8s Event | FailedScheduling | `0/3 nodes are available: 3 Insufficient cpu` (fact-b63727d0ae5e) | 证明调度器尝试所有节点均失败，直接原因被归类为 CPU 资源不足。 |

**证据关系说明：**
Kubernetes 调度事件 (证据 #3) 直接解释了 Pod 状态 (证据 #1) 长期处于 Pending 的原因。调度器在所有 3 个节点均返回 `Insufficient cpu` 且无抢占受害者 (fact-b63727d0ae5e)，排除了单节点故障，指向集群整体资源池枯竭或配置错误。Metric 数据仅确认 Pending 状态持续存在 (证据表#1)，未提供 CPU 占用情况，无法量化缺口但确认无性能异常干扰。

## 🎯 根因分析 · g1

### 因果链

```text
集群所有节点 CPU 可分配资源不足以容纳 Pod 的 CPU Request → 调度器在所有 3 个节点检查出 Insufficient cpu 且无抢占受害者 → Pod 持续被拒绝调度 (FailedScheduling) → Pod 保持 Pending 状态，未分配 Node/IP
```

### 根因结论

已确认的根因为**集群所有节点 CPU 资源不足导致 FailedScheduling**。

事实支撑：
1. **资源诉求明确**：Pod 容器 `app` 请求了 `100k` CPU (证据 #2)。
2. **调度失败明确**：Kubernetes Event 显示 3 个节点均因 `Insufficient cpu` 无法调度，且没有可以抢占的受害者 (证据 #3)。这证实了失败并非由于单节点资源暂时性波动，而是所有节点的可分配资源均低于需求。

虽然输入中的 `100k` 格式不符合常规 `100m` (0.1 Core) 或 `100` (100 Cores) 标准，但调度器明确将其判定为 CPU 资源不足。若 `100k` 被集群解析为极高的 CPU 需求（如误解析为 100 Cores），则根因本质上是**Pod 资源请求配置过大或格式错误导致无法满足调度**。

已知缺失事实为节点具体的剩余 CPU 数值，但这不影响“所有节点均不足”这一核心结论的成立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.2s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-v01/workload: 39.5s (Evidence 31.2s, RCA 8.3s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v01/workload**: pod-pending-unschedulable
