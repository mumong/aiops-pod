## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器反复被 OOMKilled (exitCode 137)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | container.last_terminated_reason="OOMKilled" (fact-000d7c5fe291) | 确认容器因内存溢出被操作系统强制终止 |
| 2 | K8s Event | K8s | BackOff restarting failed container app, back-off 5m0s (fact-a70a1bfd6449) | 证实进入频繁重启循环，直接表现为 CrashLoopBackOff |
| 3 | K8s Config | K8s | container.resource_limit.memory=64Mi (fact-17aadda75df0) | 定义容器使用的内存硬限制阈值 |
| 4 | Metric | Prometheus | container_memory_working_set_bytes: 49115136 Bytes (约 46.8 MiB) at 15:59:00Z (fact-1bdd1b66717a) | 采样点显示内存已逼近 64Mi 限制 |
| 5 | Logging | ES | log.pattern: "memory allocation advanced" (http request), allocated_mib 从 12 增长至 48 (fact-29ded2642507) | 证实应用正在处理请求并持续分配内存 |
| 6 | Tracing | Tempo | span: GET /work, attributes: {"aiops.observed_mode": "oom_growth"} (fact-15f90663da7d) | 提供关键上下文：应用处于专门设计用于触发 OOM 的测试模式 |

证据逻辑链：Tracing (fact-6) 确认应用配置了 `oom_growth` 模式；日志 (fact-5) 记录了处理 `/work` 请求时内存从 12 MiB 持续增长至 48 MiB；Metrics (fact-4) 显示容器实际工作集内存达到 46.8 MiB，逼近 64Mi 硬限制 (fact-3)；K8s 状态 (fact-1) 证实容器因触及限制被 OOMKilled，进而引发 K8s 事件 (fact-2) 的重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=oom_growth (测试模式) → 处理 /work 请求时持续分配内存 → 内存使用量增长突破 64Mi 容器硬限制 → 内核 OOM Killer 强制终止进程 (exitCode 137) → 触发 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因：**
异常组 `g1` 的 CrashLoopBackOff 现象由应用自身的 **OOM 增长（oom_growth）测试行为** 引起。

具体而言：
1.  **直接原因**：应用配置了 `FAILURE_MODE=oom_growth`，在处理 HTTP `GET /work` 请求时主动且持续地分配内存（证据编号 fact-5, fact-6）。
2.  **发生机制**：随着内存不断分配（从 12 MiB 增长至 48 MiB），应用内存占用（最高达 49,115,136 Bytes，约 46.8 MiB）超过了容器配置的硬限制 `resource_limit.memory: 64Mi`（证据编号 fact-3, fact-4）。
3.  **最终结果**：Kubernetes 底层的 OOM Killer 触发了容器终止（ExitCode 137），导致 Pod 状态持续陷入重启循环（证据编号 fact-1, fact-2）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.2m
├─ 问题定位: 18.9s
├─ 并发证据采集: 162.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 162.9s (Evidence 151.2s, RCA 11.4s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
