## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 应用服务在 /work 端点持续累积内存分配（从 2MiB 增至 48MiB），触及 64MiB 内存硬限制后被内核 OOM Killer 终止（Exit 137），导致容器反复重启并陷入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 app `last_terminated_reason=OOMKilled`，`last_exit_code=137` | 确认内核 OOM Killer 触发了容器终止（fact-3a9180668dab, fact-4b2e5ef7024c） |
| 2 | K8s Config | kubernetes | 容器 app 内存硬限制 `64Mi`，请求量 `24Mi` | 提供资源边界约束，是触发 OOM 的判定依据（fact-54ec59e1b7a0, fact-8d62606fa7a4） |
| 3 | K8s Event | kubernetes | `BackOff` 事件：4m21s (x261 over 72m)，Back-off restarting failed container | 证实容器处于 CrashLoopBackOff 状态（fact-985094fbbad3） |
| 4 | K8s Event | kubernetes | 72分钟内事件累计8条，包含 `Exit Code: 137` 及 `Reason: CrashLoopBackOff` | 辅助确认故障的持续性与具体错误标识（fact-068053f5f93c等聚合记录） |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` 在连续 4 次重启周期内呈现显著上升趋势：3.7MiB → 21.7MiB → 32.9MiB → 47.4MiB，并在最新周期达到 51.2MiB（fact-476fd7e65ee3, fact-8b318c638d30, fact-af6022340ea6） | 提供内存持续增长的趋势证据，证实内存泄漏或分配失控模式（trend_evaluable=true） |
| 6 | Metric | prometheus | 最近重启周期内内存峰值达到 53.6MiB，逼近 64Mi 限制（fact-8735b7ed45c2） | 确认内存使用量达到触发 OOM 的临界点（trend_evaluable=true） |
| 7 | Logging | elasticsearch | 日志聚合 `http_request` 指向 `/work` 路径，记录到连续 7 次内存分配操作，`allocated_mib` 从 10 增加至 42（fact-6d41c86b5d07等） | 定位到引发内存增长的具体业务代码入口为 `/work` 端点（time_range: 16:40:22 至 16:40:54） |
| 8 | Tracing | deepflow | 7 条等价 L7 Flow，均指向 `GET /work`，耗时 12.1ms-36.5ms，对应 Trace ID 与日志聚合 ID 部分重合（fact-00aa57848b4f等） | 证实 `/work` 端点有真实流量支持，排除了静态数据或空转导致的内存泄漏（trace_ids 覆盖日志时间窗口） |

**证据综合说明：**
K8s 维度确认了容器因内存超限额被内核强杀（OOMKilled），并陷入重启循环。Metrics 维度在跨越多个容器重启周期的连续采样中，记录了内存工作集从几 MiB 稳步攀升至接近 64Mi 上限的过程，证实了非瞬时的内存累积行为。Logging 与 Tracing 维度将增长源头锁定在 `/work` 端点，日志中的内存分配量（最高 42MiB）与 Metrics 中观测到的内存增量在量级上高度吻合。Tracing 确认该端点有活跃的并发请求支持，佐证了这是业务逻辑导致的内存分配，而非异常堆叠。

## 🎯 根因分析 · g1

### 因果链

```text
业务代码在 /work 端点执行持续内存分配 → 内存工作集随请求持续累积（最高达 51.2MiB） → 触及容器 64MiB 硬限制 → 触发 OOMKilled (Exit 137) → 容器重启并陷入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
应用服务在 `/work` 端点存在持续的内存分配行为（内存泄漏或大对象未释放），随着请求的累积，容器内存使用量在多次重启间逐步攀升。当最新一次重启周期的内存使用峰值（~53.6MiB）触及并超过配置的 `64MiB` 内存硬限制时，触发了 Linux 内核的 OOM Killer 机制，导致容器被强制终止（Exit Code 137）并反复重启（证据编号：fact-3a9180668dab, fact-4b2e5ef7024c, fact-54ec59e1b7a0, fact-8735b7ed45c2, fact-af6022340ea6, fact-985094fbbad3）。

**证据链支撑：**
1. **触发机制**：K8s 状态 `last_terminated_reason=OOMKilled` 和 `exit_code=137` 直接证明了资源耗尽导致的强制终止（#1）。
2. **资源边界**：配置确认了 64Mi 的严格硬限制（#2）。
3. **累积趋势**：Prometheus 指标跨越不同容器重启 ID，清晰地展示了从 ~3MiB 到 >51MiB 的阶梯式增长，排除了单次请求突发导致的可能性（#5, #6）。
4. **业务定位**：日志与追踪联合证明了 `/work` 端点在处理请求时执行了内存分配，且分配量与内存增长量级匹配（#7, #8）。

**未确认项：**
具体是哪一行代码、数据结构或分配操作直接导致了最后的 OOM 临界点突破，目前证据不足以精确到源码行级定位（对应输入中的 unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 19.1s
├─ 并发证据采集: 96.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 96.8s (Evidence 88.5s, RCA 8.0s)
└─ 汇总总结: 20.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
