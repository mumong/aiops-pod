## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx (aiops-case-07) 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod phase: Running, last_terminated_reason: Error, exit_code: 78 | 确认 Pod 运行中但容器进程异常终止 |
| 2 | K8s State | Kubernetes | container.waiting_reason: CrashLoopBackOff, back-off 5m0s | 确认 Kubelet 持续重启行为及当前状态 |
| 3 | K8s Event | Kubernetes | Warning BackOff x335 over 78m | 观察窗口内持续的高频重启与退避记录 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}`: 1 | 独立观测确认等待状态，与 K8s 事实一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason{reason="Error"}`: 1 | 独立观测确认终止原因为 Error |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 19 | 确认重启累计次数，佐证长期故障 |
| 7 | Logging | Elasticsearch | `CONFIG_MISSING` (HTTP 500), path: `/work`, allocated_mib: 0, trace_ids: ["6568...", ...] | 核心故障日志，显示请求处理失败原因 |
| 8 | Tracing | Deepflow | L7 Flow: GET /work -> 500, duration: 5796.0us-47772.0us, trace_ids overlap with Logs | 独立链路数据确认应用接口返回 500，与日志聚合时间范围一致 |
| 9 | Tracing | Tempo | Span: "GET /work", aiops.observed_mode: "config_missing_exit" | 追踪详情直接映射日志中的配置缺失模式 |

**证据关联说明：**
- **日志 (7) 与 Tracing (8, 9)**：日志聚合的 trace_ids 与 Tracing 数据中的 trace_ids 完全重叠。Log 显示 `/work` 路径返回 500 且 `aiops.observed_mode` 为 `config_missing_exit`，Tracing 确认了该请求的 HTTP 状态码与持续时间，两者在“配置缺失导致服务拒绝”这一核心故障机制上高度吻合。
- **K8s 状态 (1-3) 与 Metrics (4-6)**：Metric 中的 `reason="Error"` 与 `restarts_total=19` 独立印证了 K8s 状态中的 `exit_code: 78` 与 `CrashLoopBackOff`。这表明应用并非因资源限制被 Kill，而是因为业务逻辑错误退出后进入重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
配置加载失败 (CONFIG_MISSING) → 进程异常退出 (Exit Code 78) → 容器重启 (19 times) → 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：应用配置加载失败（CONFIG_MISSING）**

应用容器 `app` 在启动或处理请求时，因缺少必要的配置文件（日志显示路径 `/work` 请求返回 `CONFIG_MISSING` 及 HTTP 500 错误），导致业务进程以 `Exit Code 78` 退出。Kubelet 检测到容器退出后触发持续重启机制，当前累计重启 19 次并已进入 BackOff 退避阶段（等待时间 5m0s）。

**证据支撑：**
- **应用层故障**：日志（事实 7）和 Tracing（事实 9）明确记录 `CONFIG_MISSING` 错误模式；
- **系统层反馈**：K8s 事实（1）确认退出码为 78，Tracing（事实 9）的 `aiops.observed_mode: config_missing_exit` 提供了直接的行为映射；
- **循环状态**：K8s 状态（2, 3）和 Metric（6）证实了由于上述退出行为导致的 CrashLoopBackOff 现象。

现有证据链完整，足以确认根因为配置缺失导致的应用进程退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.4s
├─ 并发证据采集: 66.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 66.0s (Evidence 58.2s, RCA 7.7s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
