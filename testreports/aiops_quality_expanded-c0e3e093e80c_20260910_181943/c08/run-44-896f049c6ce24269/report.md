## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-391770bf4e95) | 确认进程被内核 OOM Killer 终止的确切原因。 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-9ff2174a3ccc) | 提供系统触发 OOMKilled 的资源硬限制边界。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1` (`reason: OOMKilled`) (fact-5a86bcff9b18) | 从监控维度验证容器被 OOMKilled 的事实。 |
| 4 | Logging | Elasticsearch | 日志模式 `memory allocation advanced`，`allocated_mib` 在 12Mi 至 38Mi 间变化 (fact-id: fact-0e830ea38b9b~14115bed0d4c) | 证明应用在处理 `/work` 请求时会分配大量内存，逼近容器限制。 |
| 5 | Tracing | DeepFlow/Tempo | Flow: `GET /work`, `http.response.status_code: 200`, `aiops.observed_mode: oom_growth` (fact-3264a37936db) | 关联应用行为，确认在 `/work` 接口处理期间内存呈增长趋势。 |
| 6 | K8s State | Kubernetes | `pod.status.phase: Running`, `pod.status: CrashLoopBackOff` (fact-51f31f9113ea, fact-f86d04113adf) | 展示 Pod 当前因反复崩溃而处于不健康状态的现象。 |

**证据综合：**
容器明确死于 `OOMKilled` (证据 1, 3)，且受限于 `64Mi` 内存硬限制 (证据 2)。日志与追踪数据 (证据 4, 5) 共同构建了故障发生的上下文：应用处理 `GET /work` 时发生内存增长（最高观察到 38Mi），最终耗尽容器允许的全部内存空间并触发 OOM Killer。虽然日志中未记录完整的 64Mi 内存峰值，但进程确被该限制杀死这一事实已确凿无疑。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置为 64Mi → 处理 /work 请求发生内存分配（最高达 38Mi 以上） → 内存使用耗尽限制，内核触发 SIGKILL (OOMKilled) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：**容器内存限制设置过低，无法承载应用处理 `/work` 请求时的内存增长。**

应用服务在处理特定请求时发生内存分配（证据 4, 5），其内存消耗迅速逼近并触发了 Kubernetes 设置的 `64Mi` 硬限制（证据 2）。这一行为直接导致内核 OOM Killer 介入终止进程（证据 1, 3），进而引发 Pod 不断重启的 `CrashLoopBackOff` 现象（证据 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 49.3s
├─ 并发证据采集: 103.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 103.6s (Evidence 94.8s, RCA 8.7s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
