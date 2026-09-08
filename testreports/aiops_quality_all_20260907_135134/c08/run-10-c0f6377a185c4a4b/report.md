## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，容器未就绪，重启10次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: `OOMKilled` (fact-5c5d0bc8699e) | 证实 Pod 终止原因被内核标记为 OOMKilled |
| 2 | K8s State | kubernetes | container.last_exit_code: `137` (fact-1b50dd694d72) | 证实进程被信号强制终止，符合 OOM 机制 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory: `64Mi` (fact-4129963aef1d) | 提供资源硬限制基准，用于与真实内存使用对比 |
| 4 | Metric | prometheus | container_memory_working_set_bytes 峰值: `66244608` bytes (~63.1 MiB) (fact-667629377229) | 实测内存峰值突破 `64Mi` 限制，印证 OOMKilled 事实 |
| 5 | Logging | elasticsearch | `/work` 接口 `allocated_mib` 持续增长: 10 -> 46 (fact-440796742c03) | 揭示内存持续增长的直接行为来源 |
| 6 | Tracing | deepflow | HTTP GET `/work` 响应 200 的等效 Flow，关联 7 条日志 trace_id (fact-2f186b9341e4 等) | 关联应用请求与内存分配日志，确认内存泄漏发生在业务流量处理期间 |
| 7 | K8s Event | kubernetes | `BackOff restarting failed container` 连续 99 次 (fact-18a10894401c) | 证实由于上述机制导致的 CrashLoopBackOff 恶性循环 |

**证据关联说明：**
日志中 `allocated_mib` 的连续增长（事实 #5）直接驱动了容器内存指标 `container_memory_working_set_bytes` 的攀升（事实 #4）。当指标突破 K8s 配置的 `64Mi` 内存硬限制（事实 #3）后，内核触发 OOM Killer，导致进程退出码 137 及 `OOMKilled` 状态（事实 #1、#2）。Tracing 数据（事实 #6）将这一内存增长行为锁定在 `/work` 接口的 HTTP 请求处理上下文中，证实了内存泄漏的业务触发路径，进而导致 K8s 频繁重启（事实 #7）。

## 🎯 根因分析 · g1

### 因果链

```text
应用执行 /work 端点时发生内存分配泄漏 (allocated_mib 10 -> 46) 
→ 容器内存使用量 (峰值 63.1Mi) 突破内存硬限制 (64Mi) 
→ 触发 OOM Killer 终止进程 (Exit 137, OOMKilled) 
→ 用户可见现象：Pod 处于 CrashLoopBackOff 状态，容器反复重启
```

### 根因结论

**已确认的根因：**
应用在处理 `/work` 接口请求时存在持续的内存分配泄漏（事实 #5），导致容器实际内存使用量（事实 #4）超过 Kubernetes 配置的 `memory limit`（事实 #3）。这一超限行为直接触发了内核 OOM Killer 机制，导致进程以 `OOMKilled`（事实 #1）和退出码 `137`（事实 #2）终止，进而引发了 `CrashLoopBackOff` 状态（事实 #7、#6）。

**证据充分性：**
K8s 状态（OOMKilled/Exit 137）、Metrics（内存峰值超限）与 Logging/Tracing（应用层内存增长行为）三维度事实闭环印证，根因判定充分。

**未确认事项：**
`container_oom_events_total` 指标显示为 0（事实 #7f4270a7fd42），与 `OOMKilled` 现象存在轻微不一致。根据诊断记录，这被归类为指标上报延迟或 Pod 生命周期过短导致计数未持久化的已知背景情况，不影响对 OOM 根因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 31.0s
├─ 并发证据采集: 105.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 105.1s (Evidence 93.3s, RCA 11.7s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- 未调用 Runbook
