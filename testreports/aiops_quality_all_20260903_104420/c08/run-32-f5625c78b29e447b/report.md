## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | RecentRestart | Pod aiops-case-08/workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器 app 反复终止并重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: OOMKilled (fact-2f2eff040885) | 确定异常终止的直接原因是 OOM Kill。 |
| 2 | K8s State | Kubernetes | container.waiting_reason: CrashLoopBackOff (fact-67a75b1fc606) | 确认应用因频繁崩溃进入重启循环。 |
| 3 | K8s State | Kubernetes | container.last_exit_code: 137 (fact-09a1a5d8fb62) | 提供操作系统级的致命信号佐证（OOMKilled）。 |
| 4 | K8s Config | Kubernetes | container.resource_limit.memory: 64Mi (fact-11d1008cb755) | 定义导致终止的容器内存硬性上限。 |
| 5 | K8s Event | Kubernetes | Exit Code: 137, Reason: OOMKilled (fact-336facecf876) | 事件日志中的直接现象描述。 |
| 6 | Metric | Prometheus | container_memory_working_set_bytes 在多次重启生命周期中持续逼近 64Mi (51Mi/55Mi/63Mi) (fact-68cb5d8dbf9d, fact-95fb3a8a0b82) | 证实应用内存持续增长，并在接近硬限制时崩溃。 |
| 7 | Logging | Elasticsearch | pattern="memory allocation advanced", allocated_mib: 16 → 34 (fact-4168da624b6b) | 揭示应用存在内存递增分配的业务模式。 |
| 8 | Tracing | Tempo/Deepflow | GET /work 响应状态 200, 属性 "oom_growth" (fact-1a887c66a13d) | 确认导致内存分配的具体请求路径。 |

**证据综合说明：**
Kubernetes 层面明确记录了容器因 OOMKilled（退出码 137）触发 CrashLoopBackOff。底层 Metrics 证实应用内存在使用量逼近 64Mi 硬限制时崩溃。Logging 日志中 "memory allocation advanced" 模式以及 Tracing 中标记为 "oom_growth" 的 `/work` 接口，共同锁定了造成内存泄漏的具体应用行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑在 /work 接口中持续进行内存分配 (Memory Allocation Advanced) → 内存使用量累积触及 64Mi 硬限制 → 容器被 OOM Killer 强制终止 (Exit Code 137, OOMKilled) → Kubelet 观察到容器崩溃并触发 BackOff 重启机制 (CrashLoopBackOff)
```

### 根因结论

已确认根因为：**应用业务逻辑导致内存持续增长并最终超出容器限制**。

具体表现为：应用在处理 `GET /work` 请求时持续进行内存分配（日志记录显示内存分配量递增，如从 16Mi 增至 34Mi），导致容器内存使用量持续增长。当内存触及容器配置的硬性上限 64Mi 时，Linux OOM Killer 终止了应用进程（返回 Exit Code 137），从而导致 Pod 进入 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 16.8s
├─ 并发证据采集: 129.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 129.2s (Evidence 118.7s, RCA 10.4s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
