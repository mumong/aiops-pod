## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod配置缺失(CONFIG_MISSING)导致应用启动失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `pod.phase: Running`, `container.restart_count: 17` | 确认为 CrashLoopBackOff 状态，存在持续的启动失败循环。 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (x264 over 63m) | 提供 Kubernetes 控制面的重启事件佐证。 |
| 3 | K8s Config | Kubernetes | `resource_request.cpu: 20m`, `resource_limit.cpu: 200m`, `resource_request.memory: 24Mi`, `resource_limit.memory: 96Mi` | 排除资源配额（CPU/Memory）不足导致的 OOMKill 或限制。 |
| 4 | Logging | Elasticsearch | 日志模式聚合 8 次：`http_request`, `level: error`, `message: CONFIG_MISSING`, `path: /work`, `http_status: 500`, `trace_ids` 覆盖多个调用 | 应用层暴露了配置缺失错误，导致启动或初始化失败。 |
| 5 | Tracing | Deepflow/Tempo | L7 Flow 聚合 9 次：`HTTP GET /work`, `response_code: 500`, `src_ip: 172.16.104.8`, `dst_ip: 172.16.104.63`；Trace ID 包含 `78c5df7615a0195018d603083f8c6f4b` (Tempo) | 外部请求因应用返回 500 错误被阻断，与日志错误直接关联。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason(Error): 1`, `kube_pod_container_status_waiting_reason(CrashLoopBackOff): 1`, `kube_pod_container_status_restarts_total: 16` | 监控指标验证了终止原因为 Error 以及当前处于 CrashLoopBackOff 等待状态。 |

**证据关系说明：**
Kubernetes 事实（#1, #2）和 Metric 事实（#6）共同锁定了 Pod 处于 CrashLoopBackOff 且终止原因为 Error。日志事实（#4）与 Tracing 事实（#5）互相印证，均指向应用因 `CONFIG_MISSING` 导致请求返回 500 错误，从而解释了为何容器反复启动失败。资源配置（#3）正常，排除了资源维度干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置缺失(CONFIG_MISSING) → 应用启动/初始化逻辑报错(Http 500) → 容器进程退出(Error) → Pod CrashLoopBackOff
```

### 根因结论

**已确认的根因**：
异常组 `g1` 的核心问题是由 **Pod配置缺失 (CONFIG_MISSING)** 导致的。

*   **证据支撑**：
    *   Elasticsearch 日志（证据 #4）明确记录了 8 次 `CONFIG_MISSING` 错误，伴随 HTTP 500 状态码。
    *   Tracing 流量（证据 #5）确认了对应路径 `/work` 的请求持续返回 500 错误。
    *   Kubernetes 状态（证据 #1, #2）和 Prometheus 指标（证据 #6）证实了应用因此反复终止（终止原因 Error）并进入 CrashLoopBackOff 循环。
    *   资源限制配置（证据 #3）表明这不是由 OOM 或 CPU 限制引起的容器崩溃。

该故障链完整解释了 Pod 持续重启和对外服务不可用的现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 37.1s
├─ 并发证据采集: 50.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 50.2s (Evidence 44.6s, RCA 5.5s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
