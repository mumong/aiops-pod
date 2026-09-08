## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器 app 反复以 exitCode 2 异常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes Pod `workload-7679bcf76-jwr8b` | 状态 `Running`, 容器重启计数 15, 上次退出码 2, 状态 `CrashLoopBackOff` | 确认应用进程反复启动失败并被 kubelet 强制重启的事实。 |
| 2 | K8s Event | Kubernetes Event | `Back-off restarting failed container app` (累计发生 226 次) | 佐证容器持续异常退出，触发 Kubernetes 退避重启机制。 |
| 3 | K8s Config | Kubernetes Pod Spec | CPU limit `200m`, Memory limit `96Mi` | 排除内存或 CPU 硬限制被突破导致 OOMKilled 的可能性。 |
| 4 | Logging | Elasticsearch | 模式 `http_request` (status 500, message: `runtime process exiting`, path: `/work`), 累计 4 次 | 直接捕获到进程在 `/work` 处理时发生内部异常并主动退出的日志证据。 |
| 5 | Tracing | Deepflow | HTTP Flow: 路由 `/work`, 响应状态码 500, 持续时间 4128us - 5361us | 从网络层证实了 `/work` 路径请求均返回了 500 内部错误，与日志中进程退出的时间点高度吻合。 |
| 6 | Tracing | Tempo | Span: `GET /work` (trace_id: `153a0cf5dbb515dfd465bf9e213cee91`), 响应状态码 200, 结束时间 `13:08:11.003523Z` | 与日志 `153a0cf5...` 一致的成功请求记录，证明应用在某些 `/work` 请求中运行正常，排除了全局不可用或网络不通问题。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (`CrashLoopBackOff`) = 1 | 从指标侧独立观测到容器正处于反复重启等待状态，与 Kubernetes 事件相互印证。 |

证据分析：
1. **异常定位一致**：Kubernetes 日志、应用层日志与 Tracing 深度流（Deepflow）共同指向唯一的故障入口 `/work` 路径。
2. **现象互证**：PromQL 的 `CrashLoopBackOff` 状态（证据 #7）与 Kubernetes 事件中的 BackOff 记录（证据 #2）相互印证，表明该故障具有连续性而非单次偶发。
3. **排除资源瓶颈**：尽管容器不断重启，但资源限制（CPU 200m, Mem 96Mi）极低且并未触发 OOMKilled（证据 #3），结合 exitCode 2 与 `runtime process exiting` 日志（证据 #4），可确认为应用内部逻辑异常或错误触发的强制退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑内部异常 → 处理请求 /work 时触发强制退出(Exit Code 2) → 容器进程非正常终止并触发重启机制 → CrashLoopBackOff
```

### 根因结论

**已确认的根因**：
集群 Pod `aiops-case-06/workload-7679bcf76-jwr8b` 中的容器 `app` 在处理 HTTP 请求路径 `/work` 时，触发了应用内部的异常退出逻辑（exitCode 2）。

**证据支撑**：
1. **退出原因明确**：应用层日志 `runtime process exiting`（证据 #4）和 Deepflow 网络日志中的 HTTP 500 响应（证据 #5）直接证明了容器进程在收到 `/work` 请求后主动崩溃，而非因资源耗尽或外部中断。
2. **故障持续性**：容器已重启 15 次（证据 #1），且 Kubernetes 指标与事件持续报告 `CrashLoopBackOff`（证据 #2, #7），表明该问题导致应用处于无限重启循环中。
3. **局部可用性**：Tracing 成功记录了一次 `/work` 的 200 成功响应（证据 #6），说明应用代码并非全局崩溃，而是特定条件下（具体为触发退出逻辑的某个条件）才出现异常，故障完全由应用自身代码逻辑引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 31.1s
├─ 并发证据采集: 66.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 66.5s (Evidence 56.9s, RCA 9.4s)
└─ 汇总总结: 14.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled
