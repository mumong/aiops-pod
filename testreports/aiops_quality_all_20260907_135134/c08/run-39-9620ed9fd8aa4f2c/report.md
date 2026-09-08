## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，容器 app 反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137, Reason: OOMKilled (fact-0106d6283054, fact-ff708ca55369) | 证明进程被 OOM Killer 强制终止 |
| 2 | K8s State | Kubernetes | container.last_terminated_reason: OOMKilled (fact-110eb8f6b7c9) | 确认最近一次终止原因为内存超限 |
| 3 | K8s Config | Kubernetes | container.resource_limit.memory: 64Mi (fact-01538f75d563) | 提供硬限制上下文，解释为何发生 OOM |
| 4 | K8s State | Kubernetes | container.restart_count: 22 (fact-a2b4be2d56c1) | 确认反复重启导致 CrashLoopBackOff |
| 5 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (reason=OOMKilled) (fact-b8d3726fd61c) | 独立验证容器最后终止原因 |
| 6 | Logging | Elasticsearch | Pattern: "memory allocation advanced", allocated_mib: 12 → 48 (fact-582d25832db4 等) | 展示内存使用随请求增长直至耗尽硬限制 |
| 7 | Tracing | Deepflow | L7 Flow: GET /work (src=172.16.104.47, dst=172.16.104.42) (fact-51283e0b11f6 等) | 确认触发内存分配的具体请求路径 |

**证据互证：**
1. 触发器关联：Logging 显示内存分配（`allocated_mib`）增长，Tracing 显示具体触发该行为的请求路径（`GET /work`），两者结合明确了内存消耗的来源。
2. 机制与现象印证：Kubernetes 和 Prometheus 的指标均一致报告 `OOMKilled` 和退出码 137，结合 64Mi 的硬限制配置，证实了因内存使用超过硬限制而被系统终止的因果链。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制仅 64Mi → 应用处理 /work 请求时内存线性增长至 48Mi+ → 触发 Linux OOM Killer 终止进程 (Exit Code 137) → Kubernetes 执行退避重启策略导致 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存限制过低（64Mi）**。

证据表明，应用在处理 `GET /work` 请求时存在内存增长现象（日志显示分配量从 12Mi 增至 48Mi），当内存使用接近或触及 64Mi 的硬限制时，触发 Linux OOM Killer 终止容器进程（退出码 137）。随后 Kubernetes 启动 CrashLoopBackOff 机制，导致 Pod 反复重启，表现为应用不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 19.2s
├─ 并发证据采集: 140.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 140.8s (Evidence 132.1s, RCA 8.5s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
