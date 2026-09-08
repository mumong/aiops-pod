## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器反复以 exitCode 137 终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container `app` 终止原因 `OOMKilled`，退出码 `137` (fact-c98777739ccc, fact-565958228f12) | 确认容器因资源耗尽被强制终止，这是崩溃的直接死因。 |
| 2 | K8s Config | kubernetes | 容器 `app` 的内存硬限制 `memory_limit` 为 `64Mi` (fact-0401244026a4) | 定义了触发 OOM 的资源阈值边界。 |
| 3 | Logging | elasticsearch | HTTP 日志模式 `/work`，窗口内 `allocated_mib` 从 `12` 增长至 `36` (fact-0f3699aec686 等) | 在日志记录的时间窗口内，内存分配量持续且线性上升，显示未释放的增长模式。 |
| 4 | K8s Event | kubernetes | `Warning BackOff`，在 `138m` 内发生 `533` 次重启 (fact-2a3d1074007b) | 证明容器在持续的高频崩溃循环中，而非孤立事件。 |
| 5 | Metric | prometheus | `restart_count` 从 `17` 累积至 `27`，样本数 `13`，呈上升趋势 (fact-72e7280bf857) | 独立证实了容器处于持续的 CrashLoop 状态。 |
| 6 | Tracing | tempo | `GET /work` 请求被标记为 `aiops.observed_mode: oom_growth` (fact-05c813c0c49c) | 从追踪层面直接定性了 `/work` 接口的内存分配行为为 OOM 增长模式。 |

**证据印证说明：**
Kubernetes 的 `OOMKilled` 和 `exitCode 137` 证实了资源耗尽导致的终止，配合 `memory_limit=64Mi` 提供了触发边界。日志记录的 `/work` 路径下内存分配持续增长（`12->36 MiB`），与追踪标记的 `oom_growth` 模式相互印证，表明该接口请求是触发内存不断逼近 64Mi 阈值的直接原因，最终导致 Kubernetes OOM Killer 介入并反复重启（`BackOff`）。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时发生持续内存增长 (Logging: allocated_mib 12->36; Tracing: oom_growth) → 
累积内存占用突破 64Mi 的 resource_limit 硬限制 (K8s Config: memory_limit=64Mi) → 
Linux OOM Killer 强制终止容器进程 (K8s State: OOMKilled, exitCode=137) → 
kubelet 触发重启策略进入 CrashLoopBackOff (K8s State: CrashLoopBackOff, K8s Event: BackOff)
```

### 根因结论

已确认根因为：应用容器在处理 `/work` 请求时存在持续未释放的内存增长（呈现线性增长模式，如日志所示分配量增加，追踪标记为 `oom_growth`）。随着每次请求处理，内存占用不断累积并逼近、最终超过 `64Mi` 的内存硬限制（`resource_limit`），触发操作系统的 OOM Killer 机制强制终止进程，导致容器反复崩溃并进入 `CrashLoopBackOff` 状态。

**证据支撑**：
- 容器被 `OOMKilled` (fact-c98777739ccc) 且资源限制仅为 `64Mi` (fact-0401244026a4)。
- 日志中 `/work` 请求的 `allocated_mib` 呈现从 12 到 36 的持续增长 (fact-0f3699aec686)。
- 追踪系统直接观测到该请求模式具有 `oom_growth` 属性 (fact-05c813c0c49c)。

**缺失信息**：具体哪一行代码逻辑或数据结构导致了内存未释放，需进一步代码审查。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 23.5s
├─ 并发证据采集: 92.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 92.8s (Evidence 81.3s, RCA 11.3s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
