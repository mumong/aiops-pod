## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，持续 59 分钟未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` (58m, 23m) | 确认调度器在三节点集群中均因标签/亲和性不匹配而过滤了节点，且无抢占机会。 |
| 2 | K8s State | `pod.phase` / `pod.condition` | `Pending`, `PodScheduled=False (Unschedulable)` (2026-09-10T10:19:45Z) | 确认 Pod 处于未调度状态，且已持续约 59 分钟。 |
| 3 | K8s Config | `container.resource_limit/requests` | CPU: `50m` limit / `5m` request; Memory: `32Mi` limit / `8Mi` request | 排除因资源请求或限制过高导致节点资源不足的可能性。 |
| 4 | Metric | `kube_pod_status_phase` | Running=0, Pending=1 (Sample count=1, 2026-09-10T11:18:19Z) | 验证 Pod 当前持续处于 Pending 阶段，未转换为 Running。 |

**证据关联与说明：**
1-2 号证据从事件和状态两个维度直接锁定了“调度失败”这一核心症状，排除了容器崩溃或重启等运行时故障。3 号证据排除了资源配额（Resource Quotas）作为调度失败的干扰因素。由于 Pod 未启动（Pending），4 号 Metric 仅反映当前相位状态，无法提供历史趋势；日志和链路追踪数据缺失（logging/tracing not_applicable）符合 Pod 尚未进入运行阶段的物理事实。所有证据均指向同一结论：调度阶段被拦截。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义 nodeSelector 要求标签 aiops.lab/unavailable=true → 集群 3 个节点（master, node1, node2）均无此标签 → Scheduler 过滤所有节点导致 0/3 nodes available → Pod 持续 Pending (FailedScheduling)
```

### 根因结论

已确认的根因为：**Pod 规格中的 `nodeSelector` 要求不满足。**
*   **原因**：Pod 配置了 `nodeSelector {aiops.lab/unavailable: true}`，要求调度目标必须拥有该标签。
*   **机制**：集群内所有可用节点（`master`, `node1`, `node2`）均缺失 `aiops.lab/unavailable` 标签或该标签值不为 `true`。
*   **依据**：
    *   **K8s Event (证据 #1)**：明确报告 `3 node(s) didn't match Pod's node affinity/selector`，且无其他资源类报错（如 `insufficient cpu`）。
    *   **K8s State (证据 #2)**：Pod 状态维持 `Pending`，证实调度器未能找到匹配节点。
    *   **资源配置 (证据 #3)**：Pod 的资源请求（5m CPU/8Mi Mem）与限制（50m CPU/32Mi Mem）非常低，非导致 `0/3 nodes available` 的资源瓶颈原因。

结论依据充分，无需补充事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.9s
├─ 并发证据采集: 61.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 61.0s (Evidence 52.4s, RCA 8.5s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
