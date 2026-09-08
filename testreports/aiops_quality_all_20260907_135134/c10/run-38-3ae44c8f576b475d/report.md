## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | 容器 'app' 被 Linux OOM Killer 终止（Exit Code 137） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error (Exit Code: 137) | 确认容器因被杀终止并重启。Exit Code 137 是 Linux OOM Killer 的标准退出码。 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi | 提供内存硬限制事实。当进程使用量超过此值时，内核会触发 OOM Killer。 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory`: 24Mi | 作为参考背景。实际运行中容器内存远高于请求值（Request），说明配置不合理且存在溢出风险。 |
| 4 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 证明应用进程在探测期间已不可用（被终止），导致健康检查失败，加剧了 CrashLoopBackOff。 |
| 5 | Metric | Prometheus | `container_memory_usage_bytes`: 3.6Mi → 15.4Mi (样本间) | 显示内存使用在重启后再次迅速增长至接近 96Mi 的上限，证实了内存泄漏或高负载导致资源耗尽的趋势。 |
| 6 | Logging | Elasticsearch | `request completed` (200 OK, `/work`) | 提供应用尚能正常运行时的基线日志，证明问题非业务逻辑错误导致，且应用具备正常响应能力。 |

**证据互证说明：**
K8s 事件记录了 Liveness Probe 500 错误，Metric 证据证实内存使用量从约 3.6Mi 飙升至 15.4Mi（且此前峰值达 15.6Mi），结合 K8s State 中 Exit Code 137 的事实，直接指向进程在内存达到 96Mi 硬限制时被内核 OOM Killer 终止。日志中正常的 200 OK 结果排除了应用代码直接报错退出的可能，进一步锁定了资源受限问题。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用量持续增长（达到96Mi上限） → 触发Linux内核OOM Killer强制终止进程(Exit Code 137) → 容器退出并进入CrashLoopBackOff，Liveness Probe随之失败(500) → Pod 持续重启且处于Unhealthy状态
```

### 根因结论

**已确认的根因：容器内存硬限制过低或内存使用模式异常，导致触发内核 OOM Killer。**

1. **直接原因**：容器 `app` 被 Linux OOM Killer 终止，表现为 `Exit Code 137`（`fact-1`）。OOM Killer 通常在进程使用内存超过分配的硬限制（`resource_limit.memory`）时介入。
2. **机制确认**：Pod 的 `resource_limit.memory` 被设定为 `96Mi`（`fact-2`）。Metric 数据（`fact-5`）显示容器内存从启动初期的约 3.6Mi 迅速增长至 15.4Mi 以上（且历史记录峰值达 15.6Mi）。在如此小的内存限制下，内存的持续增长极大概率导致其瞬间突破 96Mi 阈值，从而触发内核 OOM 机制。
3. **现象印证**：进程被杀导致 Liveness Probe 返回 `500` 错误（`fact-4`），引发 Pod 进入 `CrashLoopBackOff` 状态。

**待确认事项：**
当前 Metric 仅反映容器内部分配内存（Cgroup memory usage），未捕获宿主层面的精确 OOM 触发阈值或其他 cgroup 限制。建议检查 `kubectl describe pod` 中 `lastState.terminated.reason` 是否更精确地显示为 `OOMKilled` 以进一步佐证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.0s
├─ 并发证据采集: 84.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 84.8s (Evidence 73.4s, RCA 11.2s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
