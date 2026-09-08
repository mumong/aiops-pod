## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，App 容器因内存超限被频繁杀死 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-0afdc4ea5983` | Warning BackOff, 3m12s (x99 over 31m) restarting failed container app | 证明异常组处于 CrashLoopBackOff 的持续失败重启状态 |
| 2 | K8s Config | `fact-6b1a4504e567` | `container.resource_limit.memory` = 64Mi | 提供容器实际可用的硬内存上限 |
| 3 | Logging | `repeated_log_pattern` (`fact-66e0e36251e3` 等) | 连续 8 次 "memory allocation advanced" 记录，`allocated_mib` 从 10.0 增加至 48.0 (Min: 10.0, Max: 48.0) | 证实单次请求内发生 38Mi 的内存分配操作，且峰值逼近硬限制 |
| 4 | K8s State | `fact-1d20e011e360` / `fact-08320e25bc64` | `last_terminated_reason`: OOMKilled; `last_exit_code`: 137 | 确证 Pod 进程是被内核 OOM Killer 终止的直接原因 |
| 5 | Metric | `fact-150b6559b369` | `kube_pod_container_status_restarts_total` = 9 (单次观测) | 量化了当前周期的重启次数，与事件中的重试状态吻合 |

**证据印证：**
证据 1 和 4 共同确立了 Pod 处于因 OOM 触发而持续 CrashLoopBackOff 的状态。证据 2 (硬上限 64Mi) 与证据 3 (日志显示单次操作内存需求已达 48Mi) 结合表明，容器内应用单次执行时已占用容器硬内存限制的 75%（48/64），在缺乏有效资源隔离缓冲的情况下，极容易触发内核级 OOM Killer，从而完美解释了证据 1 中的现象与证据 4 中的终止原因。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置硬限制内存极低 (64Mi) → 应用运行时单次内存分配达到 48Mi (占上限 75%) → 触发 OOM Killer 终止进程 (Exit 137) → Pod 进入 CrashLoopBackOff 状态并持续重试
```

### 根因结论

**已确认的根因：**
`workload-5c9c7b6489-wmjhr` 容器配置的硬内存上限 (`resource_limit.memory`) 仅为 `64Mi`，而应用日志证实 (`fact-3357d997dd28`) 在处理请求时内存分配量会迅速攀升至 `48Mi`。这种低配置与应用高内存占用的矛盾导致内核 OOM Killer 频繁介入终止进程 (`fact-1d20e011e360`)，进而引发 CrashLoopBackOff (`fact-0afdc4ea5983`)。

**未知项：**
当前证据仅证实存在单次高峰内存分配，无法确认是否存在持续增长的内存泄漏问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.9s
├─ 并发证据采集: 56.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 56.1s (Evidence 46.6s, RCA 9.3s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
