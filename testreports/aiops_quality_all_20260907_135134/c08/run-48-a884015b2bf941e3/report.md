## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: OOMKilled | 核心异常信号，确认为内存硬限制导致的被杀 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: `back-off 5m0s restarting failed container=app pod=...` | 确认处于重启循环中的等待状态 |
| 3 | K8s State | Kubernetes | `Exit Code: 137` | 标准 Linux OOM 终止信号，佐证 OOMKilled 事实 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: 64Mi | 确认内存硬限制极低，为触发 OOM 的边界条件 |
| 5 | Logging | Elasticsearch | 日志模式 `[http_request, memory allocation advanced]`；内存分配值从 10 MiB 增长至 42 MiB | 证明 `/work` 请求在处理过程中消耗了大量内存，逼近 64Mi 硬限制 |
| 6 | Tracing | Deepflow/Tempo | HTTP GET `/work` 请求成功返回 200，伴随 `oom_growth` 模式，部分关联日志 trace_id | 说明请求本身正常完成，但执行路径触发了上述内存分配行为 |

**证据互证关系：**
Kubernetes 的 OOMKilled 与日志中 `/work` 请求的内存分配增长模式（10MiB → 42MiB）高度吻合，表明在 64Mi 的硬限制下，请求处理过程中的正常内存分配即已逼近崩溃边缘，直接导致了容器的反复终止（退出码 137）。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制配置为 64Mi → 处理 GET /work 请求时内存分配量持续增长（最大达 42MiB） → 内存使用量突破硬限制触发 OOMKilled (Exit Code 137) → 容器被 K8s 重启，陷入 CrashLoopBackOff
```

### 根因结论

**已确认根因：** Pod 内存硬限制配置过低（64Mi）。
容器内的 `app` 在处理 `/work` 接口请求时，内存分配需求随处理过程递增。由于 42MiB 的内存分配已经极大挤压了 64Mi 的可用上限，导致容器运行过程中不可避免地突破硬限制，触发 OOMKilled（证据 #1, #3）。Kubernetes 重启策略随后将其拉入 CrashLoopBackOff 状态（证据 #2, #4）。

**未知项：** 现有的日志与追踪数据（证据 #5, #6）仅证实了该请求会消耗大量内存，但未能区分这是应用在高负载下的“正常高内存需求”，还是由于存在“内存泄漏”导致的不合理增长。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.9s
├─ 并发证据采集: 51.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 51.0s (Evidence 40.9s, RCA 9.9s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
