## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | OOMKilled | Container memory limit (64Mi) is insufficient for the application's linear memory growth pattern (/work endpoint allocating +2MiB per request, reaching 48MiB), causing OOMKilled (exit 137) and CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Back-off restarting failed container app in pod workload-5c9c7b6489-wmjhr` (Over 64m) | 证实容器反复崩溃与重启现象 |
| 2 | K8s State | Container | `last_terminated_reason`: OOMKilled; `last_exit_code`: 137 | 确定直接导致崩溃的系统级原因是内存超限 |
| 3 | K8s Config | Container Limits | `container.resource_limit.memory`: 64Mi | 提供容器被杀死的硬性阈值边界 |
| 4 | K8s State | Container Status | `container.waiting_reason`: CrashLoopBackOff | 证实应用因反复 OOM 进入退避重启循环 |
| 5 | Logging | Application Logs | `GET /work` 请求中内存分配量从 `first: 14` MiB 线性增长至 `last: 48` MiB | 证实应用存在线性内存泄漏行为 |
| 6 | Metric | Container Usage | `container_memory_working_set_bytes`: 196608 bytes (容器 Pause 进程) | 辅助证明当前内存占用，因工具调用失败，未获取到应用容器当前实时使用量 |
| 7 | Tracing | HTTP Spans | `GET /work` 路由标记 `aiops.observed_mode: oom_growth` | 从分布式追踪层面证实了请求处理期间的异常增长模式 |

证据 2（OOMKilled）和证据 3（64Mi Limit）确立了崩溃的物理原因；证据 5（日志显示内存增至 48MiB）和证据 7（追踪确认 oom_growth 模式）解释了为何应用会触碰该边界，证据 1 则记录了这一机制导致的持续运行异常。

## 🎯 根因分析 · g1

```text
应用 /work 接口线性内存增长 (日志+追踪证实) → 内存使用触及 64Mi 限制 → OOMKilled (退出码 137) → CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因为**应用容器内存限额（64Mi）低于其实际运行时的线性内存增长需求**。
应用在处理 `/work` 请求时表现出持续的内存累积行为（日志记录分配量最高达 48MiB），当累积内存触及 `resource_limit.memory` 设定的 64Mi 硬限制时，Kubernetes OOM Killer 强制终止了容器进程（证据 2），进而触发 CrashLoopBackOff（证据 4）。正式 RCA 与观测到的指标和日志模式完全一致，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 7.6m
├─ 问题定位: 15.8s
├─ 并发证据采集: 427.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 427.8s (Evidence 420.9s, RCA 6.6s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled
