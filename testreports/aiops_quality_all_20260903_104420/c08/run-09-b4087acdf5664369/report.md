## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod `aiops-case-08/workload-5c9c7b6489-fl85h` 处于 CrashLoopBackOff 状态，容器 `app` 反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-5c9c7b6489-fl85h` 状态 Running，但容器 `app` 状态 CrashLoopBackOff，最后退出码 137 (Exit Code 137) | 确认容器反复崩溃并被 OOM Kill 的直接现象 |
| 2 | K8s State | kubernetes | 容器 `app` 内存限制 (resource_limit.memory) 为 64Mi | 确定容器资源硬限制阈值 |
| 3 | Metric | prometheus | `container_memory_working_set_bytes` 在最近一次运行中从 30Mi 攀升至 62Mi (59.75Mi)，逼近 64Mi 限制 | 证实内存使用量在单次运行中持续增长并逼近上限 |
| 4 | Logging | elasticsearch | 请求路径 `/work` 连续记录中，`memory allocation advanced` 日志的 `allocated_mib` 字段从 10 累积增加至 34 | 证实应用代码在处理 `/work` 请求时存在不释放的内存累积行为 |
| 5 | Tracing | deepflow | 7 次 HTTP GET `/work` 请求响应 200，关联 Deepflow Span 与 Tempo Span 记录 | 证实 `/work` 接口被正常调用且响应成功，排除请求侧网络阻断 |

证据 1 的 OOMKilled (Exit Code 137) 与证据 2 的 64Mi 限制直接对应，确立了内存超限导致的系统级杀进程事实。证据 3 从监控维度记录了内存使用量在 Pod 生命周期内呈阶梯式攀升并逼近限制。证据 4 则从日志维度揭示了 `/work` 接口调用时，应用内部 `allocated_mib` 随请求次数增加而不断累积的具体行为。这三者共同印证了应用代码在处理该请求时存在内存分配不释放（内存泄漏）的问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码存在内存泄漏（处理 /work 请求时累积分配且未释放） → 内存使用量持续攀升触及 64Mi 容器限制 → 容器被 OOMKilled (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是**应用代码存在内存泄漏（Memory Leak）**。

在 `aiops-case-08/workload-5c9c7b6489-fl85h` 中，应用在处理 `/work` 请求时，日志记录显示每次请求的内存分配量（`allocated_mib`）会持续增加（从 10M 累积至 34M），且未进行释放。这种累积行为导致 `container_memory_working_set_bytes` 指标在容器运行期间迅速增长（接近 62M），最终触及并超过了配置文件中设定的 `64Mi` 硬限制（证据 1, 2, 3, 4）。由于内存耗尽，Linux 内核 OOM Killer 强制终止了容器进程（退出码 137），导致 Pod 陷入重启循环（CrashLoopBackOff）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 18.4s
├─ 并发证据采集: 105.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 105.3s (Evidence 95.0s, RCA 10.1s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
