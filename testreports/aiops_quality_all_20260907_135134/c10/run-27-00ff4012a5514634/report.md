## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 持续处于 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 确认健康检查机制直接判定应用不健康 |
| 2 | K8s Event | kubelet | `Back-off restarting failed container app` (245次 over 68m) | 证明异常状态已导致持续的 CrashLoopBackOff 重启循环 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 记录容器非正常退出的终止状态 |
| 4 | K8s State | kubernetes | `container.last_exit_code: 137` | 提供系统强制终止容器的明确证据（SIGKILL） |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason: 1` (reason: Error) | 独立于 K8s API 的指标确认了 Error 类型的终止原因 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason: 1` (reason: CrashLoopBackOff) | 独立于 K8s API 的指标确认了当前的崩溃回退状态 |
| 7 | K8s Event | kubernetes | `Annotations: Exit Code: 137` | 辅助确认容器被系统级强制终止 |
| 8 | Logging | elasticsearch | `HTTP 200 /work` (occurrence: 8, trace_ids: a508b8fd... etc) | 记录工作负载请求成功（200 OK），与探针失败的 500 错误形成现象矛盾 |
| 9 | Tracing | deepflow | `GET /work response_code: 200` (src: 172.16.104.39 → dst: 172.16.104.32) | 独立追踪证据显示特定端点正常，进一步缩小异常范围为仅限健康检查路径 |

**证据印证说明：**
Kubernetes Event (1, 3, 4) 与 Prometheus Metric (5, 6) 互相印证了应用健康度异常和随之产生的 CrashLoopBackOff 状态。
Exit Code 137 (4, 7) 证实了 kubelet 在 Probe 失败后执行了强制杀进程操作。
Logging (8) 与 Tracing (9) 确认 `/work` 业务请求正常返回 200，说明故障点仅限于 `/health` 探针路径，排除了整个 Pod 崩溃或网络不可用的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部 /health 端点异常返回 500 (未确认具体原因) → kubelet Liveness Probe 连续失败 → kubelet 对容器发送 SIGKILL 信号 (Exit Code 137) → Pod 进入 CrashLoopBackOff 持续重启 (245次)
```

### 根因结论

已确认根因：`/health` 端点不健康导致 Liveness Probe 失败并触发系统强制杀除进程。
依据事实：
- **直接失败证据**：Pod 处于 `CrashLoopBackOff` 状态 (Metric fact-4eafa44a2013, K8s Event fact-e244078f68e5)。
- **终止机制证据**：容器以 `Exit Code 137` (SIGKILL) 终止 (K8s State fact-5894c94fc761, Event fact-cb39cd4e935c)，且被标记为 `Error` (Metric fact-5dd22a6cabbf)。
- **触发源头证据**：明确记录了 `Liveness probe failed: HTTP probe failed with statuscode: 500` (K8s Event fact-6e3b030893d5)。

**证据不足声明**：导致 `/health` 端点返回 500 的具体应用层业务原因（如内部逻辑错误、依赖超时、资源不足等）未在现有工具事实（K8s/Metric/Logging/Tracing）中体现。日志与 Trace 仅显示业务流量（`/work`）正常，进一步证明问题隔离在健康检查逻辑本身。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.5s
├─ 并发证据采集: 73.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 73.6s (Evidence 61.7s, RCA 11.8s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
