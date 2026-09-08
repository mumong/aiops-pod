## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 容器运行时的内存硬限制(64Mi)不足以支撑应用在执行HTTP请求时持续增长分配的内存(FAILURE_MODE=oom_growth)，导致Linux内核触发OOM Killer终止进程。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | BackOff restarting failed container app (x277 over 73m) | 证实容器处于反复崩溃重启的异常状态 |
| 2 | K8s State | Kubernetes | Reason: OOMKilled, Exit Code: 137 | 确认进程因内存超限被系统强制终止 |
| 3 | K8s Config | Kubernetes | container resource limit: 64Mi, request: 24Mi | 确认应用拥有极低的硬限制内存 |
| 4 | Metric | Prometheus | container_memory_working_set_bytes: max=66236416.0, first=245760.0 (61 samples, trend_evaluable=true) | 观测内存实际使用从 245KB 持续攀升逼近并突破 64MB 阈值 |
| 5 | Logging | Elasticsearch | Pattern: `memory allocation advanced` (8 occurrences, trace_ids: 30cc..., 5a3a...), allocated_mib: first=12.0, last=42.0 | 日志明确记录 HTTP 请求期间内存从 12MB 分配至 42MB 的行为，与指标增长趋势一致 |
| 6 | Tracing | Deepflow/Tempo | Flow/Span: GET /work (response_code: 200, sample_count: 9), Tempo observed_mode: oom_growth | 追踪链路确认导致内存分配的业务入口及内存持续增长模式 |

**证据关联说明：**
证据 1 和 2 共同构成了“容器崩溃”的直接现象；证据 3 揭示了导致崩溃的资源边界条件（64Mi 限制）。证据 5（日志中的内存分配行为）与证据 4（内存使用指标的增长趋势）形成了闭环，证实了应用在处理请求时实际消耗远超限制；证据 6 则进一步通过链路追踪定位了具体的业务操作（GET /work），明确了故障触发路径。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置为内存持续增长模式(FAILURE_MODE=oom_growth)且在请求中分配内存 → 容器累积内存使用(最高66Mi)超过设定的64Mi硬限制 → Linux内核OOM Killer强制终止容器进程(Exit Code 137) → Kubernetes检测到进程崩溃并不断重启，导致CrashLoopBackOff
```

### 根因结论

**已确认的根因：** 容器 `aiops-case-08/workload-5c9c7b6489-wmjhr` 的内存硬限制配置过低（64Mi），无法容纳应用在 HTTP 请求期间持续增长分配的内存。

证据链（证据 3、4、5、6）明确显示，应用在处理请求（如 `allocated_mib` 从 12MB 增至 42MB）时的工作集内存持续扩张，并最终突破了 64Mi 的系统硬性上限，导致内核 OOM Killer 介入终止进程（证据 2）。该行为引发了 Kubernetes 的自动重启机制，从而造成了当前的 CrashLoopBackOff 状态（证据 1）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 22.9s
├─ 并发证据采集: 109.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 109.3s (Evidence 101.0s, RCA 8.2s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
