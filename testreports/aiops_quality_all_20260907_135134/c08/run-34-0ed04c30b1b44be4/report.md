## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 3m30s (x334 over 91m)` 持续触发重启警告 | 确认 Pod 处于 CrashLoopBackOff 异常循环状态 |
| 2 | K8s State | Kubernetes | 终止原因 `OOMKilled`，退出码 `137` | 判定进程被操作系统强制终止，直接指向资源限制溢出 |
| 3 | K8s Config | Kubernetes | 容器内存限制 `64Mi` (硬限制)，请求 `24Mi` | 定义容器合法内存使用的边界，证实资源配额极低 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 在最近一次重启窗口内从 `3366912.0` 升至 `49106944.0` | 观测到内存呈单方向持续累积，确认内存异常增长趋势 |
| 5 | Logging | Elasticsearch | 模式 `memory allocation advanced`，`allocated_mib` 从 `18` 增至 `46` | 揭示应用逻辑层正在发生不可控的内存分配行为 |

**证据印证说明：**
*   **内存与终止的闭环**：日志中 `allocated_mib` 的持续增加（事实 5）驱动了实际内存使用量的飙升（事实 4），最终触发了 Kubernetes 的 `OOMKilled` 机制（事实 2）。
*   **循环现象解释**：低内存硬限制（事实 3）加速了OOM的发生，导致应用频繁重启并在重启后重现内存分配问题，从而产生大量的 `BackOff` 事件（事实 1）。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码内存分配持续累积（事实5） → 内存使用量突破 64Mi 硬限制（事实4, 3） → 内核 OOM Killer 终止容器进程（事实2） → Pod CrashLoopBackOff 频繁重启（事实1）
```

### 根因结论

根因为 **容器进程在处理业务请求时发生内存分配累积（内存泄漏）**。
具体的内存分配行为由日志证实（事实 5），其导致的内存持续增长直接触发了 Kubernetes 在容器突破 `64Mi` 硬限制时的强制终止机制（事实 2、4），进而导致 Pod 陷入频繁的 CrashLoopBackOff 重启循环（事实 1、3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.1s
├─ 并发证据采集: 84.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 84.7s (Evidence 74.5s, RCA 10.1s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
