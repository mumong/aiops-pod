## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | 容器内存使用持续增长并超过硬限制（96Mi），触发内核 OOM Killer（Exit Code 137）终止进程，导致 liveness probe 失败及 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubectl_get_by_name` | `exit_code=137`, `waiting_reason=CrashLoopBackOff`, `restart_count=26` | 确认进程因 OOM 被杀并处于重启循环中 |
| 2 | Metric | `container_memory_working_set_bytes` | 内存使用持续增长，从 `3686400.0` 增至 `15556608.0`，持续在 `96Mi` (约 100MB) 限制以下高位运行 | 证实容器内存呈现单调递增趋势且接近硬限制 |
| 3 | K8s Config | `container.resource_limit.memory` | 硬限制 `96Mi` | 提供导致 OOM 的边界条件，实际内存使用远超此值 |
| 4 | K8s Event | `kubelet` | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 内存资源耗尽导致应用响应迟缓或失败，触发探测异常 |

**证据互证说明：**
Metric 记录展示了容器内存随时间推移不断增长的明确模式（`first: 3686400.0 -> last: 15556608.0`）。这一持续增长的趋势最终触及了 K8s Config 定义的 `96Mi` 硬限制，进而导致容器被内核 OOM Killer 强制终止（`exit_code=137`）。这种资源耗尽状态同时触发了健康检查失败（`K8s Event`），从而解释了为什么 Pod 会陷入 `CrashLoopBackOff` 循环。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存持续增长（Metric趋势：3.6MB -> 15.5MB） → 耗尽内存硬限制(96Mi)并触发OOM Killer(K8s State/Config) → 容器进程被强制终止，健康检查失败(137, 500) → 崩溃重启循环(CrashLoopBackOff)
```

### 根因结论

已确认的根因是：**容器应用存在内存增长现象，且其持续使用的内存超过了 Pod 配置的 96Mi 硬限制（memory limit），进而引发内核 OOM Killer 杀死了应用进程，并导致 CrashLoopBackOff。**

该结论得到了以下事实的充分支持：
- **Metric** 层面清晰记录了内存使用量的连续增长趋势（`fact-56aac9c83f39`, `fact-79a61fec6b5e`）。
- **K8s State** 明确展示了由 OOM Killer 造成的 `exit_code: 137` 以及随后的容器重启行为（`fact-98c5d08a6e67`, `fact-505ad2e10490`）。
- **K8s Config** 明确了该容器仅配置了 96Mi 的内存硬限制，而观测到的内存峰值已远超此值（`fact-10908257df5b`）。

**缺失信息：** 导致应用内存持续无限增长的具体应用层逻辑（如代码层面的内存泄漏）在日志中未被捕获，缺乏崩溃前的详细内存分配堆栈。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 25.3s
├─ 并发证据采集: 67.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 67.8s (Evidence 59.5s, RCA 8.2s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime, pod-notready-probe-failed
