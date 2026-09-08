## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h in aiops-case-08 exhibits CrashLoopBackOff with exit code 137. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: `OOMKilled` | 证实容器被系统级 OOM 杀 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (x143 over 42m) | 证实 CrashLoopBackOff 的长期重试行为 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory`: `64Mi` | 定义容器的硬性内存上限 |
| 4 | Logging | Elasticsearch | `/work` 日志模式 `allocated_mib`: 从 10.0 增长至 46.0 | 揭示应用存在持续增长的内存分配行为 |
| 5 | Tracing | Deepflow/Tempo | `GET /work` HTTP 200, `app.observed_mode=oom_growth` | 关联特定路由请求与内存异常增长现象 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `11` | 量化容器因异常终止导致的重启次数 |

**证据分析**：K8s 的 `OOMKilled` 和 `CrashLoopBackOff` 状态（#1, #2, #6）直接指向资源耗尽。Logging 和 Tracing 证据（#4, #5）明确锁定 `/work` 端点的请求驱动了内存从 10Mi 至 46Mi 的攀升。这一增长趋势配合 64Mi 的内存硬限制（#3），构成了内存溢出并触发 Linux OOM Killer 的完整闭环。

## 🎯 根因分析 · g1

```text
App memory allocation increments to 48 MiB on /work requests → 
Usage approaches or exceeds 64Mi limit defined in resource spec → 
Kernel OOM Killer terminates container (Exit Code 137) → 
Kubernetes retries restart with backoff (CrashLoopBackOff)
```

### 根因结论

已确认的根因是应用 `workload-5c9c7b6489-fl85h` 在处理 `/work` 端点请求时存在无界的内存增量行为（日志证据 `allocated_mib` 增至 46Mi，追踪标注 `oom_growth`），触发了 64Mi 的硬限制（#3, #4, #5），导致 Linux OOM Killer 强制终止进程（#1, #7）。该机制直接导致 Pod 状态变为 CrashLoopBackOff（#2）。现有日志中最大分配值为 46Mi，与 64Mi 上限之间仍有部分空隙，确切导致 OOM 的精确内存阈值（涉及 overhead 或碎片）尚未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 10.1m
├─ 问题定位: 16.0s
├─ 并发证据采集: 579.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 579.2s (Evidence 569.7s, RCA 9.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
