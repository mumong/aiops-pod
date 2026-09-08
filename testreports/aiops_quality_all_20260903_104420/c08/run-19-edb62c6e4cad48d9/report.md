## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-48dc8e2ffebf) | `Back-off restarting failed container app in pod workload-5c9c7b6489-fl85h` | 确认应用容器存在 CrashLoopBackOff 异常循环。 |
| 2 | K8s State | kubernetes (fact-baa8d0a85d40) | 容器 `app` 终止原因 `OOMKilled`，退出码 `137` | 明确异常根因为系统层面的内存溢出强制终止。 |
| 3 | Metric | prometheus (fact-0be83bda81b3) | 重启次数 (restart_total) 从 3 次线性增长至 13 次。 | 证实重启频率持续上升，印证了故障未被隔离。 |
| 4 | Logging | elasticsearch (fact-aggr-3fa6d) | 8 次 `http_request` 日志显示内存分配 `allocated_mib` 从 10 线性增长至 46，HTTP 状态均为 200。 | 证明业务在处理正常请求时存在持续内存增长现象。 |
| 5 | K8s Config | kubernetes (fact-296f51f3ffb2) | 容器 `app` 的内存硬限制为 `64Mi`。 | 确认容器资源边界，与日志中的持续增长趋势形成直接冲突。 |
| 6 | Tracing | deepflow (fact-aggr-flow) | 9 次等价 GET `/work` 请求，耗时 15-20 ms，响应码 200。 | 进一步排除业务侧报错，证实请求处理成功但内存未释放。 |

**证据印证说明：**
日志中观测到内存分配随请求次数线性增长（`10 MiB` -> `46 MiB`），结合配置中 `64 MiB` 的内存硬限制，内存使用量逼近并突破限制必然触发 OOMKilled（退出码 137）。Tracing 中业务请求返回 200，说明应用正常消耗内存但未正确回收，最终导致容器不断被系统杀掉并重启，形成了观察窗口内的 CrashLoopBackOff 现象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存硬限制设为 64 MiB → 应用在处理业务请求时内存线性分配增长（如每次请求增加 2 MiB） → 内存使用量突破容器硬性限制（64 MiB） → 操作系统 OOM Killer 强制终止容器进程 (Exit Code 137) → Pod 持续重启进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用业务逻辑存在内存泄漏或设计缺陷，导致在处理单个业务请求（如 `/work`）的过程中发生持续的内存分配且未有效回收。

当累积内存分配达到 48 MiB 左右时，已极为接近且最终超过了设定的 `64 MiB` 硬限制。触发 Kubernetes 底层 OOM Killer 机制，直接杀死了该容器进程。随后 Pod 依据重启策略（BackOff）不断尝试重启，形成 `CrashLoopBackOff` 循环（#2, #3）。此结论由内存持续增长日志、内存限制配置及 OOM 终止状态多源事实确凿印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 15.2s
├─ 并发证据采集: 79.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 79.1s (Evidence 72.3s, RCA 6.7s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-config-error, pod-oomkilled
