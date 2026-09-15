## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Liveness Probe configured on '/health' path consistently returns HTTP 500, causing kubelet to kill the container (Exit Code 137) and restart it, resulting in CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 29m (x8 over 31m) kubelet Liveness probe failed: HTTP probe failed with statuscode: 500` | 确认 Liveness Probe 持续返回 500，是导致 Pod 被杀的核心事件 |
| 2 | K8s State | kubernetes | `reason: CrashLoopBackOff`；`container.last_terminated_reason: Error`；`exit_code: 137` | 确认 Pod 处于崩溃重启循环中，且因 OOMKill (137) 被终止 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi`；`container.resource_limit.cpu: 200m` | 限制容器资源上限，需验证是否触发 OOM |
| 4 | K8s Config | kubernetes | `container.resource_request.memory: 24Mi`；`container.resource_request.cpu: 20m` | 提供资源调度基准，证明 96Mi 限制相对宽松 |
| 5 | Logging | elasticsearch | `HTTP 500 on path /health` (occurrence_count: 6) | 确认应用层 `/health` 端点故障，非基础设施层不可用 |
| 6 | Metric | prometheus | `container_memory_working_set_bytes` (max: 15425536, min: 3510272) | 内存波动在 3MB-15MB 之间，远低于 96Mi 限制，排除 OOM |
| 7 | Tracing | deepflow | `GET /health` 请求响应状态 `500` (occurrence_count: 3) | 网络层观测到 Liveness Probe 请求确实收到 500 响应 |

证据链自洽：Tracing 和 Logging 确认应用服务 `/health` 端点返回 500；K8s Event 确认 kubelet 接收此 500 后判定探针失败；K8s State 确认探针失败导致容器被 Kill (Exit 137)；Metric 证明该 137 退出并非由内存超限引起，而是应用自身逻辑或资源分配导致的崩溃。

## 🎯 根因分析 · g1

```text
应用 /health 端点异常 (返回 500) → Liveness Probe 持续失败 → kubelet 杀容器 (Exit Code 137) → CrashLoopBackOff 循环
```

### 根因结论
**已确认根因：应用 Liveness Probe 端点故障。**

容器 `app` 的 `/health` 路径持续返回 HTTP 500 错误，导致 Liveness Probe 探测失败。根据 K8s 机制，探针失败会触发容器被杀并重启。

尽管容器以 `Exit Code 137` (OOM Kill) 终止，但 Memory 指标 (max 15MB) 远低于 `96Mi` 限制，排除了资源不足导致的 OOM。因此，应用自身在 `/health` 路径处理时的异常（如分配失败或逻辑错误）导致其崩溃被系统 Kill，并引发了后续的 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 3.7m
├─ 问题定位: 32.9s
├─ 并发证据采集: 179.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 179.0s (Evidence 171.1s, RCA 7.5s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-config-error, pod-crashloop-runtime
