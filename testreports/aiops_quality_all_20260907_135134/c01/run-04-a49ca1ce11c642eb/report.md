## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod的NodeSelector配置`aiops.lab/unavailable=true`与集群节点实际标签不匹配，导致0/3节点满足调度条件。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-01/workload-68c557d875-bsq52` 状态为 `Pending` | 确认 Pod 无法被调度，处于异常停滞状态 |
| 2 | K8s Event | kubernetes | `FailedScheduling` (3m59s前): `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available` | 直接指出调度失败原因为节点标签/亲和性不匹配，且无法通过抢占解决 |
| 3 | K8s Config | kubernetes | 资源请求 (Request): CPU `5m`, Memory `8Mi` | 确认 Pod 调度所需的基础资源需求极小，排除资源配额导致的调度失败 |
| 4 | K8s Config | kubernetes | 资源限制 (Limit): CPU `50m`, Memory `32Mi` | 确认 Pod 的资源规格限制，非导致调度异常的直接因素 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` 值为 `1` | 从指标层面确证 Pod 持续处于 Pending 状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Running"}` 值为 `0` | 确认 Pod 从未成功进入运行状态，佐证调度失败 |

**证据分析**：
Kubernetes 状态明确显示 Pod 处于 `Pending`，Event 日志 `FailedScheduling` 将失败原因锁定为 `node affinity/selector` 不匹配（3/3 节点失败）。资源维度（Request/Limit）的极低配置排除了资源竞争导致 NodeSelect 无法选中的可能性。Metric 数据从宏观状态上佐证了 Pod 长期无法调度成功（Pending=1, Running=0）。Kubernetes 事件是判定“调度失败机制”的决定性证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 设置 node_selector: aiops.lab/unavailable=true → 集群无节点拥有该标签 → Scheduler 判定 0/3 节点满足条件 → Pod 持续 Pending 且不可调度
```

### 根因结论

已确认的根因为：**Pod 的 `node_selector` 配置不匹配**。

根据 K8s Event 事实（#2），调度器报告 `0/3 nodes are available` 且明确原因是 `didn't match Pod's node affinity/selector`。这表明集群中实际存在的 3 个节点均未打上 `aiops.lab/unavailable=true` 标签。Pod 因此无法被分配到任何节点，导致状态长期停滞在 `Pending`（证据 #1, #5, #6）。资源限制（#4）与请求（#3）极小，确认该现象纯粹由调度策略（NodeSelector）引起，而非资源不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.2s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 33.8s (Evidence 25.5s, RCA 8.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
