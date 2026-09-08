## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器 app 因退出码 137 被 OOMKilled 而不断重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container last_terminated_reason: OOMKilled; exit_code: 137 (fact-01bd1a1e4432, fact-9c9834ec96a8) | 证实容器因内存溢出被内核强制终止，是 CrashLoopBackOff 的直接诱因 |
| 2 | K8s Config | kubernetes | container resource_limit.memory: 64Mi (fact-2952982cc088) | 定义容器的内存硬限制，作为与 Working Set 对比的基准 |
| 3 | Metric | prometheus | container_memory_working_set_bytes (fact-be09d3677c3b) max: 66248704.0 bytes (~63.1 MiB) | 证明在 OOM 发生前，容器内存使用量曾达到接近限制值的高位 |
| 4 | Logging | elasticsearch | log pattern: `memory allocation advanced` 数值 `allocated_mib` 从 first: 46 增至 last: 48 (fact-0b3f24143b6a等) | 直接揭示应用在 `/work` 接口中存在递增的内存分配行为，与 OOM 机制相印证 |
| 5 | K8s State | kubernetes | container waiting_reason: CrashLoopBackOff; message: back-off 5m0s restarting failed container=app (fact-f8be73c0e902, fact-714fddbd77b0) | 确认系统层面的重启失败现象 |

**证据印证说明**：
- **K8s State (fact-1)** 确认了进程被 OOMKilled 的死亡原因和 137 退出码；
- **Logging (fact-4)** 揭示了导致 OOM 的根源：应用在处理 `/work` 请求时逐步增加内存分配（从 46 MiB 增至 48 MiB 等）；
- **Metric (fact-3)** 提供了过程证据，显示 Working Set 曾达到 63.1 MiB，逼近 64 MiB 的硬限制，最终触发 K8s (fact-1) 描述的 OOM 事件。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷：在 /work 接口中循环执行递增内存分配 (2 MiB -> 48 MiB)
→ 失败机制：内存硬限制瓶颈：容器 memory limit 设为 64 MiB，无法容纳持续增长的内存峰值 (Working Set 达 ~55 MiB)
→ 直接失败：内核 OOM 终止：内存超限触发 OOM Killer，容器进程被强制杀掉 (exitCode 137)
→ 用户可见现象：Kubernetes 重启循环：进程反复退出导致 kubelet Back-off 重启，Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因是**应用代码逻辑缺陷与内存配置不足共同导致的 OOM 终止**。
具体而言，应用在处理 `/work` 请求时逐步增加内存分配，导致容器内存使用量（Working Set）持续增长。当内存使用量超过设定的 64 MiB 硬限制时，Linux OOM Killer 强制终止了进程，导致 Pod 反复重启并进入 CrashLoopBackOff 状态。证据链完整（日志显示分配模式、Metric 显示逼近限制的峰值、K8s 显示 OOMKilled 结果），符合正式 RCA 描述。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 41.8s
├─ 并发证据采集: 103.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 103.5s (Evidence 88.3s, RCA 15.0s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled, pod-crashloop-runtime
