## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `reason`: OOMKilled (`fact-636f53340fc7`) | 确证异常终止的真实内核机制 |
| 2 | K8s Config | kubernetes | `memory.limit`: 64Mi (`fact-4b72ecc4aa56`) | 提供判定内存越界的资源硬限制 |
| 3 | K8s State | kubernetes | `last_exit_code`: 137 (`fact-c235e0e43abd`) | 直接指向 OOMKilled 的标准退出码 |
| 4 | Logging | elasticsearch | `log.message`: "startup allocation 256Mi" (`fact-0e0f3b5f125d`) | 记录触发 OOM 的精确内存请求数值 |
| 5 | K8s State | kubernetes | `container.waiting_message`: "back-off 5m0s restarting..." (`fact-494f0b8d8367`) | 确认当前的 CrashLoopBackOff 症状 |
| 6 | Metric | prometheus | `last_terminated_reason`: "OOMKilled", `restarts_total`: 8 (`fact-94b6e78e73a0`, `fact-af13bd137171`) | 独立于 K8s 状态监控对 OOM 与重启频次的佐证 |

**证据小结**
- **证据 1、3、6** 从退出码（137）、K8s 状态和 Metrics 三个维度高度一致地证明异常终止是由 OOMKilled 引起的。
- **证据 2 与 4** 构成了完整的因果链条：启动日志明确指出 256Mi 的分配量，这严格超过了 K8s 配置的 64Mi 硬上限，是导致 OOMKilled 的物理根因。
- **证据 5** 仅描述了 OOM 后的重试现象，由上述内存越界机制触发。

## 🎯 根因分析 · g1

### 因果链

```text
memory limit (64Mi) 过小 → 容器启动分配 256Mi 超出上限 → 触发内核 OOM Killer (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

已确认根因为**容器启动时分配的内存（256Mi）超过了 Kubernetes 配置的内存硬限制（64Mi）**，从而频繁触发 OOMKilled。

该结论拥有跨维度的充分事实支撑：
1.  **触发条件**：`kube_pod_container_status_last_terminated_reason` 指标与 `container.last_terminated_reason` 状态均明确为 `OOMKilled`（证据 1、6）。
2.  **根本矛盾**：日志记录显示进程启动时分配了 256Mi 内存（证据 4），这直接违反了配置中的 `memory.limit` (64Mi)（证据 2）。
3.  **结果验证**：异常退出码 137（证据 3）是 OOMKilled 的标准标志。

目前无需补充证据即可闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.6s
├─ 并发证据采集: 45.9s
│  └─ g1 aiops-case-v15/workload: 45.9s (Evidence 37.8s, RCA 7.9s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
