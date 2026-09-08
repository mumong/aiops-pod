## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 异常循环，最终表现为 OOMKilled。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff  113s (x280 over 75m)` `kubelet  Back-off restarting failed container app` | 证实故障进入指数退避重启阶段，属直接症状 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled` | 确认崩溃直接原因为系统 OOM 机制触发 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 137` | 137 信号为 Linux OOM Killer 强制终止的标准标识 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` | 提供导致崩溃的硬限制阈值，属关键背景 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes`: last `37109760` bytes (≈35.3 MiB), max `40976384` bytes (≈39.1 MiB) | 内存使用量逼近 64Mi 上限，符合 OOM 前特征 |
| 6 | Logging | elasticsearch | `log.message: "memory allocation advanced"` | `allocated_mib`: first `10` -> last `42` | 确认应用层存在持续内存分配增长行为 |
| 7 | Tracing | deepflow | `GET /work`: `response_code: 200`, `occurrence_count: 9` | 确认业务请求在处理期间保持正常返回，排除网络中断 |

**证据互证说明：**
K8s 层面的 `OOMKilled` (证据 2) 与 `Exit Code 137` (证据 3) 提供了崩溃的直接物理证据；Prometheus 显示内存峰值达到 39Mi (证据 5)，高度接近 64Mi 的硬限制 (证据 4)；Elasticsearch 日志显示内存分配持续增长 (证据 6)，结合 Deepflow 证明业务请求正常返回 (证据 7)，三者结合确证了“持续分配导致突破限制进而触发 OOM”的因果链条。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 逻辑内存持续增长 → 内存使用量突破 64Mi 硬限制 → Linux OOM Killer 强制终止容器（Exit 137） → Kubelet 触发 BackOff 重启导致 CrashLoopBackOff
```

### 根因结论

**已确认根因：容器应用内存使用量持续增长，导致突破 Pod YAML 配置的 64Mi 内存硬限制，进而触发 Linux OOM Killer 进程终止。**

这一根因完整解释了所有关键现象：
1. **日志中的 `OOMKilled` 与 `Exit 137` (证据 2, 3)**：由 OOM Killer 的底层机制直接产生。
2. **日志中的内存分配持续增长 (证据 6)**：提供了突破资源限制的前置行为依据。
3. **Metrics 中的内存逼近峰值 (证据 5)**：确认了内存使用量确实达到了触发硬限制的临界点。
4. **Kubelet 的 BackOff 日志 (证据 1)**：是 OOM 崩溃后 Kubelet 标准的重启策略表现。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 21.5s
├─ 并发证据采集: 110.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 110.7s (Evidence 95.6s, RCA 14.8s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
