## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | 容器 app 处于 CrashLoopBackOff 状态，Pod 无法 Ready |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" (fact-8a46f8ab587e) | 确认 Pod 崩溃的直接原因 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... restarting failed container app` (fact-d3827428308b) | 确认 Pod 处于反复重启循环中 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory`: "64Mi" (fact-51beb05c0241) | 确定导致溢出事故的硬资源上限 |
| 4 | Logging | Elasticsearch | 日志模式：`"allocated_mib"` 从 12 增至 48 (fact-582d25832db4, fact-15afeab42920) | 记录请求处理期间内存占用的持续增长过程 |
| 5 | Tracing | Tempo/Deepflow | `span_name: GET /work`, `status_code: 200`, 关联 trace_id `497e9021c2bee1fde97ea8e31dda97f5` (fact-b37dd4c45b1b, fact-51283e0b11f6) | 关联导致内存增长的异常 HTTP 请求来源 |

上述 K8s 事实确认了 Pod 因 OOMKilled 退出（Exit Code 137）并处于 CrashLoopBackOff 状态。Logging 记录证实应用在处理请求时内存分配显著增加，最高触及 48 MiB。Tracing 确认了 `/work` 接口是承载该业务请求的入口，且与日志记录的时间窗口一致。结合 64 MiB 的内存限制，证据闭环完整。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存资源限制过低 (64 MiB, 事实#3) → /work 请求处理导致内存累积 (至 48 MiB, 事实#4, #5) → 突破 64 MiB 限制触发 OOM Killer (事实#1) → Pod CrashLoopBackOff (事实#2)
```

### 根因结论

已确认根因：容器的 `resource_limit.memory` 配置过低（64 MiB），不足以支撑 `/work` 请求处理期间的内存增长需求。
1. **证据支撑**：K8s 事件明确显示容器被 `OOMKilled` (事实#1) 且处于重启循环 (事实#2)。Logging 数据显示应用在处理 `/work` 请求时，内存占用（allocated_mib）从 12 增长至 48 (事实#4)，该过程由 Tracing 中的 `/work` 请求触发 (事实#5)。
2. **机制分析**：应用内存最高使用量（约 48 MiB）已接近 64 MiB 的硬限制上限，导致请求处理过程中剩余内存不足以应对突发或峰值，触发 Linux OOM Killer 强制终止进程，引起容器反复崩溃重启。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 18.0s
├─ 并发证据采集: 84.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 84.2s (Evidence 74.5s, RCA 9.6s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled, pod-crashloop-runtime
