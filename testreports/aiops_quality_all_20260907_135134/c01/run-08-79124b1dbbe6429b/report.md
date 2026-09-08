## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod配置了节点选择器 'aiops.lab/unavailable=true'，但集群中所有节点均无此标签，导致调度器无法匹配任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | Pending | 确认 Pod 当前处于未运行状态。 |
| 2 | K8s Event | `FailedScheduling` | "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector." (17m 与 6m38s 均发生) | 证实所有节点因不匹配 Pod 的节点亲和性/选择器被调度器排除。 |
| 3 | K8s Config | `container.resource_request/memory` | 8Mi | 资源请求极低，排除了资源不足导致的不匹配。 |
| 4 | Metric | `kube_pod_status_phase` | phase=Pending (value=1, 时间戳 2026-09-07T06:08:32.921000Z) | 独立于 K8s API 确认了 Pod 处于 Pending 阶段。 |
| 5 | Metric | `kube_pod_status_phase` | phase=Failed (value=0, 时间戳 2026-09-07T06:08:32.921000Z) | 排除了 Pod 处于 Failed 阶段的可能性，与 Pending 状态相互印证。 |
| 6 | Logging | — | Pod 未启动，无物理日志 | 确认无业务日志，状态停留在调度阶段。 |
| 7 | Tracing | — | pod_ip is empty | 确认无网络通信，排除运行时流量问题。 |

**证据分析：**
K8s Event 明确指出所有 3 个节点因不匹配节点亲和性/选择器而被拒绝，且该事件持续发生。Metric 的 Pending 计数与 Event 描述的现象一致。Logging 和 Tracing 的缺失（状态为 not_applicable）是 Pod 未被调度的正常结果，进一步证实故障点位于调度阶段而非运行时。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的节点标签选择器 (aiops.lab/unavailable=true) → 调度器在 3/3 节点上匹配失败 → 容器无法调度 (Pending) → 应用不可用
```

### 根因结论

根因已确认：Pod 配置了节点选择器 `aiops.lab/unavailable=true`，但集群中所有节点均没有此标签，导致调度器无法匹配任何可用节点。
该结论由以下证据链支持：
1. **K8s State/Config (证据 #1, #2, #3)**：Pod 状态为 Pending，且调度器明确报错 0/3 节点不匹配亲和性/选择器。
2. **Metric (证据 #4)**：独立指标确认 Pod 处于 Pending 状态。
3. **Logging/Tracing (证据 #6, #7)**：确认 Pod 从未进入运行状态，故障完全发生在调度阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 20.8s
├─ 并发证据采集: 27.9s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 27.9s (Evidence 22.2s, RCA 5.6s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
