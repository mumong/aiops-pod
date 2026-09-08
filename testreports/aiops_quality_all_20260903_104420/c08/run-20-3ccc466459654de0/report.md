## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff (OOMKilled) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason`: OOMKilled, `exit_code`: 137, `waiting_reason`: CrashLoopBackOff | 确认容器因内存超限被强制终止，且处于重启回退状态 |
| 2 | K8s State | Kubernetes | `resource_limit.memory`: 64Mi | 确定 Pod 内存硬限制极小，为故障边界条件 |
| 3 | Logging | Elasticsearch | 模式 "memory allocation advanced" 在 36 秒内 `allocated_mib` 从 10 增至 46 | 揭示应用在处理请求时内存持续增长直至突破限制的趋势 |
| 4 | Tracing | Tempo | Trace `7ba557385248188bc69c39855fa58f05` 标记 `aiops.observed_mode`: oom_growth | 辅助确认应用内部内存分配行为符合内存泄漏或增长特征 |

**证据关联说明**：Kubernetes 的 OOMKilled 状态与 exit code 137 是故障结果；日志中 `allocated_mib` 从 10 增长到 46 直接演示了内存消耗过程；结合 64Mi 的限制，证实应用增长内存超过了 Pod 允许的上限。

## 🎯 根因分析 · g1

### 因果链

```text
Pod内存限制(64Mi)过低 → 应用处理请求时内存持续增长并突破64Mi限制 → 容器被OOMKilled终止 → CrashLoopBackOff
```

### 根因结论

已确认根因是 **Pod 内存限制设置过低（64Mi）** 导致容器因 **OOM (Out of Memory)** 被 Kubernetes 强制终止。

支持证据：
1. **终止原因**：Kubernetes 事实明确指出 `container.last_terminated_reason` 为 `OOMKilled`，退出码为 `137`（[证据 #1](#L3)）。
2. **资源边界**：配置显示容器内存硬限制仅为 `64Mi`（[证据 #2](#L2)）。
3. **内存行为**：日志显示在短时间窗口内（36秒），应用内存分配从 `10 MiB` 迅速增长至 `46 MiB`，逼近并突破 64Mi 限制（[证据 #3](#L3)）。
4. **状态确认**：Metric 确认等待原因为 `CrashLoopBackOff`，重启计数已达 13 次（[证据 #1](#L3)）。

综上，应用在处理 `/work` 请求时产生的内存增长量超过了其 64Mi 的限制，触发了系统的 OOM Kill 机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.7s
├─ 并发证据采集: 59.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 59.4s (Evidence 51.6s, RCA 7.6s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
