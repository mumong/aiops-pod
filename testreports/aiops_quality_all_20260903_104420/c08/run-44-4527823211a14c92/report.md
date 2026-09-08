## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 容器内存限制配置过低（64 MiB）导致进程在内存分配过程中因超出限制被内核 OOM Killer 终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" | 直接证明进程是被内核 OOM Killer 终止的 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 137 | 退出码 137 进一步确认进程被信号 9 (SIGKILL) 终止 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: "64Mi" | 确定容器的内存硬限制为 64 MiB |
| 4 | Logging | Elasticsearch | `memory allocation advanced` 日志，`allocated_mib` 从 10 增长到 48 | 显示应用在崩溃前内存持续分配，逼近 64 MiB 限制 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=OOMKilled`, `value`: 1 | 监控数据侧面印证容器状态 |

- **证据关联**：K8s 状态明确进程因内存超限被杀 (事实 1, 2)，且配置了极低的 64 MiB 限制 (事实 3)。日志 (事实 4) 提供了应用视角的内存分配过程，显示其分配量已持续增加至 48 MiB（接近限制的 75%），证实了内存耗尽的触发机制。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置过低 (64 MiB) → 内存分配请求超限触发内核 OOM Killer → 容器进程被强制终止 (Exit 137) → 用户可见现象: CrashLoopBackOff
```

### 根因结论

已确认的根因为：**容器内存硬限制（64 MiB）配置过低**。
该限制导致应用在处理请求时发生内存分配增长（日志显示分配量从 10 MiB 增长至 48 MiB），当分配行为接近或触及 64 MiB 上限时，被 Linux 内核的 OOM Killer 终止进程（退出码 137，终止原因 OOMKilled）。这直接引发了容器的反复崩溃和重启循环。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 35.6s
├─ 并发证据采集: 81.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 81.5s (Evidence 74.9s, RCA 6.4s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
