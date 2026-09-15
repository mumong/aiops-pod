## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | aiops-case-v15/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 终止原因为 `OOMKilled`，退出码 `137` (`fact-3a21cdd1f6f1`, `fact-198f6d9dda89`) | 确认进程被内核 OOM 杀手终止 |
| 2 | K8s State | Kubernetes | `app` 容器配置 `memory_limit=64Mi`，状态 `CrashLoopBackOff` (`fact-2567d581cd9b`, `fact-dd6571702875`) | 确定触发终止的资源上限与当前异常状态 |
| 3 | Logging | Elasticsearch | 启动日志: `startup allocation 256Mi` (`fact-545e18f06a78`) | 证实应用启动时内存需求远超硬限制 |
| 4 | Metric | Prometheus | `reason=OOMKilled` 且 `sample_count=1` (`fact-3084eed7ed05`) | 独立确认终止原因为 OOM |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` 当前值为 `3334144` bytes (约 3.18 MiB) (`fact-5c1ad41b0c21`) | 采样点仅反映 Pod 重启后重启初期的低水位状态 |
| 6 | K8s Event | Kubernetes | `Warning BackOff 3m14s (x235 over 53m)` (`fact-e12a149092b8`) | 说明 CrashLoop 持续较长时间，频繁触发重启 |

**证据互证说明**：
Kubernetes 状态（证据 1、2）直接记录了容器被 OOMKilled 和因 CrashLoopBackOff 重启的事实，并指出 `memory_limit` 仅为 `64Mi`。Elasticsearch 日志（证据 3）从应用内部视角证实了启动时的显式分配量 `256Mi`，解释了为何 `64Mi` 的硬限制会导致 OOM。Prometheus 指标（证据 4）从监控系统侧独立验证了 `OOMKilled` 原因。由于 `oom_killed` 指标在采样点 `sample_count=1` 时仅为状态确认（证据 5），因此 OOM 事实主要依赖 K8s 状态和日志的证据闭环。

## 🎯 根因分析 · g1

### 因果链

```text
配置 memory limit (64Mi) 过低 → 启动代码强制分配 256 MiB 内存 → 触发 OOMKilled (Exit Code 137) → Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认的根因是**容器内存限制设置过低**。Kubernetes 配置中 `app` 容器的 `memory limit` 硬限制为 `64Mi`（见证据 2），而应用启动日志明确显示其尝试分配 `256MiB` 内存（见证据 3）。这一内存需求超过了内核为该容器划定的硬限制，导致 Kubelet/OOM-Killer 直接终止进程（Exit Code 137，见证据 1），从而引发 `CrashLoopBackOff`（见证据 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 18.2s
├─ 并发证据采集: 91.0s
│  └─ g1 aiops-case-v15/workload: 91.0s (Evidence 82.0s, RCA 8.8s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
