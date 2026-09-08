## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器 app 频繁退出 (exitCode=137) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: OOMKilled (Container: app) | 证明进程被内核强制终止的直接原因 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 137 | 验证 OOMKilled (SIGKILL) 的标准退出码 |
| 3 | K8s State | kubernetes | `container.resource_limit.memory`: 64Mi | 确立容器内存硬限制阈值 |
| 4 | K8s Event | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 描述应用频繁重启导致的最终服务状态 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` 观测值: 59637760 (~57Mi) | 证实应用运行时内存峰值接近 64Mi 的限制 |
| 6 | Logging | elasticsearch | `numeric_fields`: `allocated_mib` 从 12 增至 46 (观察窗口: 16:34:30 ~ 16:35:04) | 展示应用内存分配的持续增长趋势 |

**证据印证：**
K8s 状态（证据 1-4）直接确认了 OOMKilled 导致的 CrashLoopBackOff 现象。Prometheus 指标（证据 5）显示容器实际使用的内存（约 57 MiB）极度接近 64 MiB 的硬限制，与日志（证据 6）中观察到的内存分配持续增长（达到 46 MiB + 系统开销）相互印证，共同指向资源不足是崩溃的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行时持续分配内存（allocated_mib 增长） → 内存使用触及并超过 64Mi 容器硬限制 → 内核 OOMKiller 触发 SIGKILL (Exit 137) → CrashLoopBackOff
```

### 根因结论

**已确认根因：容器内存硬限制配置过低。**

容器 `app` 被配置的内存硬限制为 `64Mi`（证据 3）。监控数据显示，该应用在运行过程中内存使用量持续增长，峰值接近 `60Mi`（证据 5），且日志记录显示其内部内存分配在崩溃前已达到 `46Mi`（证据 6）。这种持续的内存增长触发了容器的内存硬限制，导致 Linux 内核 OOMKiller 强制终止进程（证据 1, 2），从而引发 Kubernetes 的重启循环（证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 20.3s
├─ 并发证据采集: 170.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 170.0s (Evidence 158.7s, RCA 11.1s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
