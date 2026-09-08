## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Back-off restarting failed container app in pod workload-5c9c7b6489-fl85h` (fact-3e4fee1d6945) | 描述 CrashLoopBackOff 的症状，表明容器持续重启。 |
| 2 | K8s Event | `kubelet` | `Exit Code: 137` (fact-ea6d5b837703) | 提供确切的容器终止原因，137 通常为 SIGKILL 信号。 |
| 3 | K8s Event | `kubelet` | `Reason: OOMKilled` (fact-e12832997114) | 确认容器是被 OOMKilled 机制杀死的。 |
| 4 | K8s State | `container` | `Reason: OOMKilled` (fact-6b7f03ffa5cf) | 提供容器最终退出的状态事实。 |
| 5 | K8s Config | `container` | `limit.memory: 64Mi`, `request.memory: 24Mi` (fact-b4044217999d, fact-64355e9c104d) | 提供容器硬内存限制配置，为判断是否超限提供基准。 |
| 6 | Logging | `app` | `memory allocation advanced` (HTTP 200), allocated_mib 从 10 增至 48 (fact-447f946c3ecc 聚合) | 显示应用在执行正常的 /work 请求过程中，逐步申请了高达 48 MiB 的内存。 |
| 7 | Tracing | `app` | `GET /work`, status 200, `aiops.observed_mode: oom_growth` (fact-485a9212a4e5) | 提供了完整的 HTTP 调用上下文，确认该请求在应用内部触发并观察到了 OOM 增长。 |
| 8 | Metric | `prometheus` | `container_memory_working_set_bytes` max: 66318336 (~63.2 MiB), limit: 64 MiB (fact-3075231fc151) | 通过容器工作集内存监控证实内存峰值逼近了 64 MiB 的硬限制。 |

**证据印证：**
1. **现象与状态确认**：K8s 事件明确指出容器因 `OOMKilled`（退出码 137）被终止，这与 Metric 监控到的内存工作集（Max 63.2 MiB）逼近配置硬限制（64 MiB）完全吻合。
2. **因果链路闭环**：日志记录显示请求正常返回（HTTP 200）但 `allocated_mib` 在单轮/连续周期内从 10 MiB 激增至 48 MiB；Tracing 同样捕获到该路径且标注为 `oom_growth`。这一过程证实了应用逻辑导致的内存增长是触发内核 OOM Killer 的直接原因，进而导致 Pod 陷入重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用请求周期内持续申请内存（日志：alloc 10->48Mi） → 内存消耗逼近/触及容器硬限制 64Mi → Linux OOM Killer 强制终止进程（Exit 137） → Pod 触发 CrashLoopBackOff 重启
```

### 根因结论

已确认的根因为：**应用内存在缺陷的内存分配模式导致单次或累积请求的内存使用量超过容器设定的硬限制。**

具体机制为：应用在处理 `GET /work` 请求时，内存分配呈增长态势（从 10 MiB 增长至 48 MiB），结合容器自身的基线内存占用，使得整体工作内存峰值（约 63.2 MiB）触达了配置的 `64Mi` 硬限制。随后内核 OOM Killer 介入强制终结容器，导致 Kubernetes 反复尝试重启但持续失败，最终表现为 `CrashLoopBackOff`。

---

## 📊 性能统计

```text
├─ 总耗时: 10.5m
├─ 问题定位: 33.9s
├─ 并发证据采集: 581.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 581.1s (Evidence 569.6s, RCA 11.3s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
