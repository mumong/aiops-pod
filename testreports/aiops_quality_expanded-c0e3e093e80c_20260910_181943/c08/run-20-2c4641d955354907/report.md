## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 应用代码在处理 /work 请求时存在内存分配不释放（每次增加 2 MiB）的逻辑缺陷，导致容器内存使用量持续增长，最终在 64 MiB 的限制下触发 OOMKilled，引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-68955c21334a) | 证实容器因内存超限被内核杀掉 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 137` (fact-41210c215624) | 确认进程异常终止原因 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` (fact-dda23622450b) | 描述当前 Pod 持续重启的状态 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory: 64Mi` (fact-04b3dbeec9aa) | 提供引发 OOM 的硬性资源边界 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: OOMKilled` (fact-90c37fb843c6) | 指标确认最近一次异常终止原因为 OOM |
| 6 | Logging | Elasticsearch | Pattern: `memory allocation advanced` on `/work`, allocated_mib: first=10, last=48 (fact-aggregated) | 日志显示在处理 `/work` 请求时，内存分配值在观察窗口内从 10 MiB 线性增长至 48 MiB，证实内存泄漏模式 |
| 7 | Tracing | Deepflow | L7 Flow: HTTP GET `/work`, Response: 200, Trace: `f67172f3ba46d96625b3fafa5fddc306` (fact-aggregated) | 确认业务层 `/work` 请求成功处理，但结合日志说明成功请求伴随了内存增长 |

证据表明，容器在每次处理 `/work` 请求时内存均发生约 2 MiB 的净增长（日志中 10 MiB 到 48 MiB 的线性增加证实了这一点）。由于 Pod 配置了 `64 MiB` 的硬限制，累积增长最终触发了 `OOMKilled`（退出码 137），导致 Kubernetes 将其置于 `CrashLoopBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 处理逻辑内存泄漏（每请求递增） → 内存使用量突破 64 MiB 硬限制 → 触发 OOMKilled (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用代码在处理 `/work` 请求时存在内存分配不释放的逻辑缺陷。
**证据支撑**：
1. 应用代码层面：日志（证据 6）显示在 `/work` 请求处理期间，内存分配量呈现规律性增长。
2. 系统层面：Kubernetes 状态（证据 1, 2, 3）和 Prometheus 指标（证据 5）一致确认了 OOMKilled 是导致容器不断崩溃并重启的根本原因，且硬限制被突破（证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.4s
├─ 并发证据采集: 70.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 70.6s (Evidence 62.7s, RCA 7.8s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
