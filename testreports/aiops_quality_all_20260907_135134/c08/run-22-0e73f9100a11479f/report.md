## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，重启 13 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: OOMKilled | 确定容器终止的直接原因为内存超限 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 137 | 验证 OOMKilled 产生的标准退出码 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: 64Mi | 锁定被触发硬限制的内存上限阈值 |
| 4 | K8s Event | Kubernetes | `Back-off restarting failed container app` (x197 over 55m) | 记录因 CrashLoopBackOff 导致的高频重启现象 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (reason=OOMKilled) | 独立于 K8s API 的指标证据，确证 OOMKilled 状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 13 | 量化故障发生的频次 |
| 7 | Logging | Elasticsearch | `memory allocation advanced` 日志模式，`allocated_mib` 从 14.0 增至 48.0 | 观察应用运行时内存分配持续增长的行为 |

**证据印证说明**：Kubernetes 的 OOMKilled 状态与 Prometheus 的 OOMKilled 指标相互印证，确证了内核 OOM Killer 介入的事实；同时，日志中 `allocated_mib` 的递增趋势（至 48Mi）与 64Mi 的 Limit 形成明确的因果关联，解释了为何会触发硬限制。

## 🎯 根因分析 · g1

### 因果链

```text
容器 Memory Limit (64Mi) 设置过小 → 应用运行分配内存超过 Limit → 触发 OOMKilled (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**容器内存限制配置过低 (64Mi)，无法支撑应用运行时的实际内存分配需求**。

证据表明，应用在运行过程中内存分配持续增长（日志记录分配值最高达到 48Mi），逼近并触发了 64Mi 的硬限制（证据 3、7）。内核 OOM Killer 介入导致容器以 Exit Code 137 退出（证据 1、2），并被 Prometheus 指标（证据 5）独立确认。高频的 CrashLoopBackOff 事件（证据 4）和重启计数（证据 6）均是这一机制的后续表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.2s
├─ 并发证据采集: 67.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 67.3s (Evidence 59.1s, RCA 8.1s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
