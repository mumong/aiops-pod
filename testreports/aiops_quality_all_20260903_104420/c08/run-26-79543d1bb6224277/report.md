## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled`, `last_exit_code: 137` | 核心事实：确认容器因内存超限被内核强制终止 |
| 2 | K8s Event | Kubernetes | `BackOff 25s (x261 over 68m)` | 现象佐证：频繁重启导致指数退避延迟 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi`, `request.memory: 24Mi` | 边界确认：64Mi 硬限制与 24Mi 请求值严重不匹配 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 突增至 25956352 (约 24.7Mi)，此前稳定在 3.2~3.7Mi | 资源消耗轨迹：正常运行时极低，崩溃前出现异常跳升 |
| 5 | Logging | Elasticsearch | `log.message: "memory allocation advanced"`, `allocated_mib` 从 12 增至 46 | 应用行为：请求处理期间内存申请量逼近容器限制上限 |
| 6 | K8s State | Kubernetes | `pod.status: Running`, `restart_count: 15` | 容器状态：尽管 CrashLoopBackOff 处于等待期，最后一次尝试已处于 Running 状态 |

**证据交叉验证：**
Kubernetes 的 OOMKilled 终止原因 (1, 2) 与 Prometheus 内存跳升指标 (4) 直接对应。日志中 `allocated_mib` 增长至 46 MiB (5) 的数据，解释了为何在 64 MiB 硬限制 (3) 下会触发 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
Memory limit (64Mi) insufficient for workload → Application memory usage exceeds limit during request processing → Linux OOM Killer terminates container process (Exit Code 137) → Kubelet detects termination and retries, entering CrashLoopBackOff
```

### 根因结论

**已确认的根因**：
容器内存限制过低。应用程序在处理请求时内存需求激增（从常态约 3 MiB 跃升至接近限制值），导致进程超过配置的 64 MiB 硬性内存上限，被 Linux 内核 OOM Killer 强制终止 (Exit Code 137, fact 1, fact 6, fact 4, fact 5)。Kubelet 随后不断重启该容器，触发 BackOff 机制，表现为 CrashLoopBackOff (fact 2)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.1s
├─ 并发证据采集: 70.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 70.5s (Evidence 60.7s, RCA 9.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
