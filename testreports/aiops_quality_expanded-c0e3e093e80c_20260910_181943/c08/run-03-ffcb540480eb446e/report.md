## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | RecentRestart | 容器内存泄漏导致触发自身内存限制（64Mi），引发 OOMKilled 终止并进入 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container: app, reason: OOMKilled | 直接证明容器因内存超限被内核 Kill |
| 2 | K8s Event | kubernetes | BackOff restarting failed container app (x62 over 18m), Exit Code: 137 | 验证 OOMKilled 导致的 CrashLoopBackOff 循环现象 |
| 3 | K8s Config | kubernetes | resource_limit: 64Mi (app) | 明确触发 OOMKilled 的硬性资源上限 |
| 4 | Logging | elasticsearch | pattern: http_request [GET /work], allocated_mib: 18 -> 48 (first -> last) | 展示应用在处理正常业务请求时的内存持续增长趋势 |
| 5 | Tracing | tempo | span: GET /work, attributes: {"aiops.observed_mode": "oom_growth"} | 将内存增长现象与特定 HTTP 请求关联，确认泄漏触发点 |

**证据说明：**
日志记录显示在 `2026-09-10 22:16:34` 至 `22:17:04` 期间，应用处理 `/work` 请求时分配的内存从 18MiB 逐步攀升至 48MiB；与此同时，K8s 指标确认容器状态为 OOMKilled，且退出码 137。结合 K8s Event 中记录的频繁重启（62 次），证明应用存在内存泄漏，在处理特定业务请求时消耗了全部 64MiB 限制，导致 OOMKilled 并引发后续 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑内存泄漏 (Logging/Tracing) → 内存消耗突破 64MiB 硬限制 (K8s Config) → OOMKilled 进程终止 (K8s State) → CrashLoopBackOff 循环 (K8s Event)
```

### 根因结论

已确认根因：**容器内应用存在内存泄漏**。
证据编号 **4** (Logging) 和 **5** (Tracing) 记录了应用在处理业务请求时内存持续增长的现象（`oom_growth` 模式，18MiB 升至 48MiB）。这种增长最终触发了 K8s 配置中的 **64MiB 内存限制**（证据 **3**），导致内核执行 OOM Killer，容器异常退出（证据 **1, 2**），进而进入 CrashLoopBackOff 状态。

*注：由于缺乏 `metrics_memory_working_set` 的全局趋势数据，根因分析依赖于日志中观测到的单次泄漏增长模式及最终的 OOM 事实。*

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 527.6s
├─ 并发证据采集: 57.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 57.7s (Evidence 53.2s, RCA 4.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled
