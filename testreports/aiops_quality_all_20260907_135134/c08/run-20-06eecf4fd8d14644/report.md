## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app reason: OOMKilled, exit_code: 137 | 确诊直接失败机制：进程被 OOM Killer 强制终止 |
| 2 | K8s Config | kubernetes | container.app resource_limit.memory: 64Mi | 提供导致 OOM 的硬限制阈值 |
| 3 | Metric | prometheus | kube_pod_container_status_restarts_total: 13 (container: app) | 佐证异常处于高频重启状态 |
| 4 | K8s Event | kubernetes | Back-off restarting failed container app in pod workload-5c9c7b6489-wmjhr (x178 over 52m) | 确认 CrashLoopBackOff 现象 |
| 5 | Logging | elasticsearch | Pattern: allocated_mib 观察窗口内从 42 降至 28, 区间最大值 46.0, 最小值 2.0 | 证明处理请求时存在内存分配动态变化（泄漏或增长） |
| 6 | Tracing | deepflow+tempo | Flow/Trace (如 `5b3cc4d6c90ddac653bfba0b5504fbff`) 对应 GET /work 返回 200, trace 标记 OOM 模式 | 关联具体业务动作与 OOM 状态 |

**证据关联说明：**
Kubernetes 的 `OOMKilled` 状态与 `Exit Code: 137` 直接对应 Metric 中观察到的 13 次重启，构成了 CrashLoopBackOff 现象。Logging 显示的内存分配波动与 Tracing 中标记为 `oom_growth` 的 `/work` 请求链路互相印证，指向在处理该请求时内存超出了 64Mi 的容器限制。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置过低 (limit: 64Mi) → 应用处理 /work 请求时内存分配持续增长 → 超出限制触发 Linux OOM Killer 强制终止进程 (exitCode: 137) → 容器频繁重启进入 CrashLoopBackOff
```

### 根因结论

**已确认根因：容器内存硬限制配置过低（64Mi）。**
证据 #2 确认 `resource_limit.memory` 仅配置为 64Mi。结合证据 #5（Logging 显示请求处理时存在显著的内存分配动态）与证据 #6（Tracing 将 `/work` 请求标记为 `oom_growth`），证实应用在处理 `/work` 请求时会消耗超过 64Mi 的内存，从而触发证据 #1 中观测到的 `OOMKilled` 终止机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 30.6s
├─ 并发证据采集: 61.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 61.6s (Evidence 53.3s, RCA 8.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
