## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Container memory limit (64Mi) exceeded by application memory allocation pattern, resulting in OOMKilled (Exit Code 137). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: OOMKilled | 直接定位崩溃触发机制 |
| 2 | K8s State | Kubernetes | `container.resource_limit.memory`: 64Mi | 确认限制阈值，对比证实超额 |
| 3 | K8s Event | Kubernetes | `BackOff`: 104m 内因 app 容器重启 Back-off 396 次 | 确认处于 CrashLoopBackOff 症状中 |
| 4 | K8s Config | Kubernetes | `resource_request.memory`: 24Mi, `resource_limit.memory`: 64Mi | 确认容器资源配额仅为 64Mi |
| 5 | K8s State | Kubernetes | `container.last_exit_code`: 137 | 137 码对应 OOMKilled 信号，印证状态 |
| 6 | Metric | Prometheus | `container_memory_usage_bytes`: 观测窗口内 `max` 达 64,131,072 bytes (~61.1Mi)，`last` 为 241,664 bytes | 证实应用内存峰值触及硬限制 |
| 7 | Logging | Elasticsearch | 日志模式 `memory allocation advanced`: 连续记录中 `allocated_mib` 从 10 递增至 48 | 揭示内存持续增长的应用行为 |
| 8 | Tracing | Tempo | Span: `GET /work` 标记 `aiops.observed_mode: oom_growth` | 确认 `/work` 接口触发 OOM 模式 |

**证据关联说明：**
- **状态与配置印证 (1, 4, 5, 6)**：K8s 事件中的 OOMKilled 和 Exit Code 137 结合 Prometheus 指标中逼近 64Mi 限制的最大内存值，从操作系统和监控层面闭环证实了资源限制导致的终止。
- **行为溯源 (7, 8)**：日志显示 `/work` 端点请求导致内存从 10MiB 逐步增长至 48MiB，Tempo 的 `oom_growth` 标记直接关联了这一业务行为，解释了为何 64MiB 限制会被触及。

## 🎯 根因分析 · g1

### 因果链

```text
应用对 /work 端点发起请求，内存申请量逐次增大 (2MB 至 48MB+) → 应用内存累积触及容器硬性限制 (64Mi) → Linux OOM Killer 强制终止容器进程 (Exit Code 137) → Kubelet 持续重试失败导致 Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器内存硬限制配置过低 (64Mi) 无法容纳应用运行时的内存增长峰值**。

**证据支撑：**
1. **配置瓶颈**：容器 `app` 的内存限制被硬性设定为 64Mi (`fact-88a1a2fcbb4a`)。
2. **触发机制**：通过日志 (`fact-448d688aed98`) 和 Trace (`fact-214127102127`) 确认，调用 `/work` 接口会引发应用的内存逐步分配（最高记录 48MiB，标记为 `oom_growth`）。
3. **直接后果**：内存消耗逼近并触发硬限制，导致内核 OOM Killer 介入，容器以 137 退出码终止 (`fact-011e8dbc9f90`, `fact-3318ebc32a73`)。

---

## 📊 性能统计

```text
├─ 总耗时: 7.0m
├─ 问题定位: 15.7s
├─ 并发证据采集: 393.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 393.7s (Evidence 386.7s, RCA 6.8s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
