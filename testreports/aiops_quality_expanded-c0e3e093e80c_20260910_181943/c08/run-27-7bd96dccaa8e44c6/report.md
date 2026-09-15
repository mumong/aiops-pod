## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器内存资源限制(64Mi)不足以支撑应用请求处理过程中的内存增长(从2MB增至48MB)，导致容器因内存超限被操作系统OOM Killer强制终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137；OOMKilled；CrashLoopBackOff；重启 18 次 | 确认容器因资源耗尽被系统终止的终止状态与反复重启现象 |
| 2 | K8s Config | Kubernetes | Memory Limit: 64Mi；Memory Request: 24Mi | 提供内存限制基线，64Mi 为容器内存硬上限 |
| 3 | Logging | Elasticsearch | 模式 "memory allocation advanced"；窗口内 allocated_mib 从 12 增至 48 | 显示请求处理期间内存持续增长至接近硬限制，逼近 OOM 边界 |
| 4 | Tracing | Tempo/Deepflow | 12个 GET /work Flow；trace_id 如 3c85efb888a881f2f25064f5eeb9e57f；span 记录 aiops.observed_mode: oom_growth | 关联日志证据与特定业务流量，证实请求处理直接引发 OOM 增长模式 |

证据相互印证：K8s 的 `OOMKilled` 状态 (1) 与 64Mi 限制 (2) 结合，解释了重启的直接原因；Logging (3) 揭示了内存从 12Mi 激增至 48Mi 的具体过程，证实了应用对资源的不合理消耗；Tracing (4) 将这一内存增长模式 (oom_growth) 锚定在特定业务请求 (`GET /work`) 上，构成了完整的因果证据链。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制过低 (64Mi) → 请求处理内存持续增长 (12Mi→48Mi) → 触发 OOM Killer → 容器被强制终止 (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

已确认的根因是容器内存资源限制配置不足。64Mi 的硬限制无法承载业务请求处理过程中的实际内存增长（记录显示最高分配至 48Mi），导致触发操作系统的 OOM Killer 机制并强制终止容器（`OOMKilled`）。日志中观察到的内存激增模式（E#3）与 Tracing 中观测到的 `oom_growth` 模式（E#4）一致，直接支撑了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 13.1s
├─ 并发证据采集: 56.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 56.0s (Evidence 49.7s, RCA 6.2s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
