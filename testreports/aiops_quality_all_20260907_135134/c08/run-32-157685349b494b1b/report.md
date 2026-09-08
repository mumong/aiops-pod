## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 状态 Running 但容器 app 处于 CrashLoopBackOff，连续重启 18 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason`: "OOMKilled", `last_exit_code`: 137 (`fact-1e32b3011f46`, `fact-2904f96fc92e`) | 直接确认最后一次终止是由系统 OOM 机制触发 |
| 2 | K8s Config | Kubernetes | `resource_limit.memory`: 64Mi, `resource_request.memory`: 24Mi (`fact-67c7654222e6`, `fact-047988178b05`) | 确认容器硬内存限制为 64Mi，资源配置较低 |
| 3 | Logging | Elasticsearch | `allocated_mib` 从 4Mi 增长至 46Mi，且出现 8 次相同模式 (`fact-logging-pattern-1`) | 揭示应用存在内存增长行为，逼近并可能超出 64Mi 限制 |
| 4 | Tracing | Tempo | Span `fb24dc3f...` 属性标记 `aiops.observed_mode: oom_growth` (`fact-4530b28bad85`) | 关联应用调用与 OOM 增长模式，排除外部流量突发因素 |

**证据关联说明**：Kubernetes 明确显示 `OOMKilled` 是终止原因（#1）；日志中应用内存从 4Mi 增长至 46Mi（#3），结合 64Mi 的硬限制（#2），证实内存持续增长的逻辑与 OOM 触发一致；Trace 数据（#4）进一步印证了内存增长的应用侧行为。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制为 64Mi → 应用运行内存持续增长逼近并触发限制导致 OOMKilled (Exit 137) → Kubernetes 终止容器并进入 CrashLoopBackOff → Pod 状态 Running 但容器不 Ready
```

### 根因结论

根因是**应用内存增长超出限制**。证据显示：应用容器内存使用量在最近日志中已达到 46Mi（`fact-logging-pattern-1`），而容器的硬内存限制仅为 64Mi（`fact-67c7654222e6`）。Kubernetes 记录的最后终止原因为 `OOMKilled`（`fact-1e32b3011f46`），这与应用内存持续增长且接近配置上限的行为完全吻合。虽然未能获取完整的工作集内存趋势（如 `container_memory_working_set_bytes` 历史数据），但现有日志内存分配增长事实与 OOMKilled 状态足以支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 19.0s
├─ 并发证据采集: 114.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 114.3s (Evidence 106.8s, RCA 7.4s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled, pod-crashloop-runtime, pod-evicted
