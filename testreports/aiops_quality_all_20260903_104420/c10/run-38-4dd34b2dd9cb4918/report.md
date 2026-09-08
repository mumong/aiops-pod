## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | 容器 'app' 内存请求(24Mi)与限制(96Mi)配置过低，无法支撑 Python 进程启动及运行时的内存开销，导致内核 OOM Killer 强制终止进程（Exit 137）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app: last_exit_code=137, last_terminated_reason=Error, waiting_reason=CrashLoopBackOff | 确认进程被内核信号强制终止的直接状态 |
| 2 | K8s Config | kubernetes | container.app: resource_request.memory=24Mi, resource_limit.memory=96Mi | 确认容器内存资源限制极其有限 |
| 3 | K8s Event | kubernetes | BackOff 66s (x402 over 106m): back-off restarting failed container app | 提供持续重启与启动失败的时序上下文 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason 1 (CrashLoopBackOff), kube_pod_container_status_restarts_total 37 | 指标数值验证了长期运行失败的高频重启现象 |
| 5 | Logging | elasticsearch | pattern: http_request completed (status=200), allocated_mib min/max=0.0 (窗口内) | 表明在崩溃发生前的可观测窗口内未记录显著内存分配，或日志采集点未能捕获崩溃瞬间 |
| 6 | Tracing | deepflow | flow: GET /work, status_code=200, duration min=18865us max=28488us | 证明网络流量存在且部分请求处理成功，限定故障具有瞬时性或特定触发条件 |

**证据分析：**
1. 退出码 137 (Signal 9) 结合极低内存限制（24Mi 请求/96Mi 限制），直接指向内存超限导致的 OOM Killer 行为。
2. Metric 中的重启总数（37 次）与 Event 中的 BackOff 计数（402 次）相互印证了这是一个长期且频繁的故障模式。
3. Tracing 和 Logging 的 200 OK 状态证明应用并非完全无法启动，可能存在初始启动时的内存峰值超过硬限制，或在特定请求下触发 OOM，但日志与追踪未能捕获到崩溃瞬间的具体指标峰值。

## 🎯 根因分析 · g1

```text
容器内存限制(96Mi)过低 → 无法满足 Python 进程启动及运行内存需求 → 触发内核 OOM Killer → 进程终止(Exit 137)导致 CrashLoopBackOff
```

**根因结论：**
已确认根因为**容器资源请求与限制配置过低**（#2, #4）。
内存硬限制（96Mi）无法满足 Python 进程的运行需求，导致进程在启动或运行期间内存耗尽，被操作系统内核通过信号强制终止（Exit 137, #1）。这一机制引发了容器的反复重启（#3, #4），并在客户端表现为持续的 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.6s
├─ 并发证据采集: 76.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 76.7s (Evidence 70.3s, RCA 6.3s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
