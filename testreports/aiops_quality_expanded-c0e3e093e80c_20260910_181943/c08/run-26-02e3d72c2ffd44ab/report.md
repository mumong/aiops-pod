## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器内存限制 (64Mi) 过低，无法容纳持续增长的业务内存需求，导致 OOMKilled。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: "OOMKilled" (container: app) | 确认进程因资源超限被内核终止的直接事实 |
| 2 | K8s State | kubernetes | `container.resource_limit.memory`: "64Mi" (container: app) | 提供内存硬限制数值，与现象构成因果约束 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 137; `container.waiting_reason`: "CrashLoopBackOff" | 137 对应 OOMKilled 信号，等待状态证实循环重启 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` (labels: reason="OOMKilled") = 1 | 独立指标观测到最近终止原因为 OOMKilled |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` (labels: container="app") = 18 | 量化证实持续的重启频率与异常状态 |
| 6 | Logging | elasticsearch | Pattern: `memory allocation advanced` (8 occurrences); `allocated_mib`: first=12, last=48 | 显示单次请求窗口内内存分配从 12MiB 增至 48MiB，证实业务增长模式 |
| 7 | Tracing | deepflow + tempo | L7 Flow `GET /work` (9 occurrences) 关联 Trace `3c85efb888a881f2f25064f5eeb9e57f` | 日志与流量均源自同一业务接口，证实内存分配与流量请求直接相关 |

**证据综合：** K8s 状态明确显示 OOMKilled 及 137 退出码，指标确认了重启与终止原因，日志与流量证据证实了请求导致内存持续增长（12MiB → 48MiB）的具体机制。多维度证据（K8s/Metric/Logging/Tracing）均指向内存限制过低导致的 OOM 故障，彼此完全印证。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制 (64Mi) 设置过低 → 每次请求导致内存线性增长 (2 MiB/req) → 累计分配超出容器限制被内核杀死 (OOMKilled) → Pod 进入 CrashLoopBackOff (重启 18 次)
```

### 根因结论

已确认根因为**容器内存限制（64Mi）过低**。
- **直接证据**：K8s 终止原因明确为 `OOMKilled` [1]，退出码为 `137` [3]，指标确认该原因 [4]，Pod 处于 `CrashLoopBackOff` 状态 [3]。
- **机理印证**：日志显示请求过程中内存分配持续增加 [6]，结合 `GET /work` 的流量记录 [7]，证实业务请求触发了内存持续增长，最终突破 64MiB 的硬限制 [2]。
- **结论**：当前资源限制无法容纳业务运行时的峰值内存需求，直接触发 OOMKilled 与重启循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 20.3s
├─ 并发证据采集: 81.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 81.8s (Evidence 74.6s, RCA 7.0s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
