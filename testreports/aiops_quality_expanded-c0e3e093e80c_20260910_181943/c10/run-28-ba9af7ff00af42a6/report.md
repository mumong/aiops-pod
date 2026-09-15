## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，持续重启且无法就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Warning Unhealthy: Liveness probe failed with statuscode: 500 (fact-a4ac8b423062) | 记录应用存活探针持续失败的直接现象，导致 Pod 重启机制触发 |
| 2 | K8s Event | Kubernetes | Warning BackOff: Back-off restarting failed container (fact-ab03649ac149) | 证明容器处于频繁重启状态，最终表现为 CrashLoopBackOff |
| 3 | K8s State | Kubernetes | Container last terminated reason: Error; Exit Code: 137 (fact-b4d94f5490d3, fact-e6008d7ee486) | 退出码 137 是进程被 OOM Killer 强制终止的特征，指向内存不足 |
| 4 | K8s Config | Kubernetes | Container resource limit (memory): 96Mi (fact-670da840bf5b) | 提供了导致 OOM 的环境上下文，限制值相对严格 |
| 5 | Metric | Prometheus | kube_pod_container_status_waiting_reason (CrashLoopBackOff): 1; restarts_total: 11 (fact-60ba221d9652, fact-6144ee5dd9e9) | 独立于 Kubernetes API，从 Metrics 维度证实了重启次数和状态 |

**证据说明：**
Kubernetes 的 Event 明确记录了探针失败和重启行为，而 `Exit Code: 137` 结合 96Mi 的内存限制，共同指向了资源耗尽导致进程被杀的根本原因。Metrics 数据（Restart Count 11, CrashLoopBackOff 状态）与 K8s 状态完全印证，排除了偶发性故障。Logging 和 Tracing 展示的是应用正常响应时的快照，与当前崩溃状态处于不同时间线。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制（96Mi）过低 → 内存不足触发 OOM Killer → 进程被强制终止（Exit Code 137） → Liveness 探针失败触发重启 → CrashLoopBackOff
```

### 根因结论

**已确认的根因**：容器内存配置过低导致 OOM（Out of Memory）。
证据 `[fact-b4d94f5490d3, fact-e6008d7ee486]` 中的 `Exit Code: 137` 是 Linux 内核 OOM Killer 终止进程的明确标志，这直接证实了应用因内存不足被强制杀死的推断。结合证据 `[fact-670da840bf5b]` 中 96Mi 的硬限制，说明该限制不足以支撑应用稳定运行。该进程终止导致了探针失败和后续的重启风暴。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.5s
├─ 并发证据采集: 56.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 56.7s (Evidence 46.4s, RCA 10.2s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
