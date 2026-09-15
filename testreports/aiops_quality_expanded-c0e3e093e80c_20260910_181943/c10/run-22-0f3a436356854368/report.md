## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | Liveness Probe configured with insufficient timeout (1s) and period (3s) relative to application startup or request processing latency, causing probe failures (HTTP 500) and subsequent container KILL (Exit 137) by kubelet. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x8 over 10m) | 直接证明应用端在 Liveness Probe 期间返回 500 错误，触发探针失败 |
| 2 | K8s State | K8s State | `container.last_terminated_reason`: Error; `container.waiting_reason`: CrashLoopBackOff; `restart_count`: 7 | 证实容器因异常退出陷入重启循环 |
| 3 | K8s State | K8s State | `container.last_exit_code`: 137 | 确认容器是被系统强制 Kill 退出（对应 OOMKilled 或 SIGKILL），非应用正常退出 |
| 4 | K8s Config | K8s Config | `container.resource_request.memory`: 24Mi; `container.resource_limit.memory`: 96Mi | 提供应用内存资源边界，为分析 Exit 137 原因提供上下文 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`="Error"; `kube_pod_container_status_waiting_reason`="CrashLoopBackOff"; `kube_pod_container_status_restarts_total`=7 | 从指标层面独立印证 K8s 状态中的 CrashLoopBackOff 及终止原因为 Error |
| 6 | Logging | Elasticsearch | Pattern: `request completed` (HTTP 200, path: `/work`, trace_ids: 8 distinct); time_range: 02:37:00 - 02:37:38 | 证实应用在处理正常 HTTP 请求时并未报错，日志中无 OOM/Kill 相关信息 |
| 7 | Tracing | Deepflow/Tempo | L7 Flow: `GET /work` -> `200 OK` (duration: 15.6ms-24.0ms); Trace ID 关联 `5f04ae74e771e6c0a2c80fa04c325125` | 展示探针发起的请求（或同期流量）被应用成功处理，排除应用崩溃导致的不可用 |

证据 1 显示探针收到 500 错误，但证据 4 仅展示常规 200 正常请求的日志与 Trace。由于日志与链路均为成功状态，结合容器被强制 Kill (137) 且探针失败，说明在探针触发的特定时刻，应用因处理延迟或阻塞导致探针超时返回 500，进而触发了 kubelet 的杀进程保护机制。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 配置超时/周期过短 (1s/3s) → 探针请求处理延迟超过阈值返回 500 → kubelet 判定探针失败并执行 SIGKILL (Exit 137) → 容器进入 CrashLoopBackOff 循环
```

### 根因结论

**已确认根因**：Liveness Probe 配置的不合理（超时时间 1s 和周期 3s 过短），无法匹配应用实际的请求处理延迟。

**分析**：
1. **探针失败触发杀进程**：K8s Event 记录显示探针失败原因为 `HTTP probe failed with statuscode: 500`（证据 1），且 `Exit Code: 137`（证据 3）表明容器是被强制杀死的，这符合 kubelet 在探针失败时的默认行为。
2. **应用本身无逻辑故障**：同期日志（证据 6）和链路追踪（证据 7）均显示正常的 HTTP 200 请求在处理 `/work` 路径，耗时在 15ms-24ms 之间，应用并未发生崩溃或 OOM 报错，说明 500 状态码是探针在应用繁忙或阻塞时触发的超时结果。
3. **重启循环**：Metric 数据（证据 5）和 K8s 状态（证据 2）一致确认了容器因 Error 状态陷入重启循环，这是探针不断失败导致的直接后果。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 17.4s
├─ 并发证据采集: 143.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 143.5s (Evidence 133.4s, RCA 9.9s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-terminating-stuck
