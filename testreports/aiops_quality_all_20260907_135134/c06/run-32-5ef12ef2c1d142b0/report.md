## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | {'message': 'k8s.v1.cni.cncf.io/network-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`<br>`container.waiting_message=back-off 5m0s restarting failed container=app...` | 描述应用持续重启且被 Kubelet 主动推迟，确认为当前主要异常状态 [fact-2e15c3f63ecf, fact-5e54cbebab19] |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason=Error`<br>`container.last_exit_code=2` | 证明进程非正常退出且非 K8s 主动管理，属于应用侧异常 [fact-af98f95652b3, fact-099c988c09b8] |
| 3 | K8s Event | Kubernetes | `event.message=Warning BackOff 11s (x406 over 89m) kubelet Back-off restarting failed container app...` | 提供异常持续时间（89分钟）与高频重启（406次）的时间线上下文 [fact-e2bfafaa787a] |
| 4 | Logging | Elasticsearch | `pattern: runtime process exiting`<br>`http_status: 500, path: /work, level: error`<br>`time_range: 13:34:04 - 13:49:50` | 明确应用进程在 `/work` 请求时抛出 500 错误并主动退出，是引发 K8s 重启的直接触发点 [fact-58d660c9944a] |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1 (CrashLoopBackOff)` | 以监控视角验证当前容器处于 CrashLoopBackOff 的等待状态 [fact-3462c306b56c] |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=1 (Error)` | 监控端确认上次容器终止原因为 Error，与 K8s State 一致 [fact-6a1aa6e6350d] |
| 7 | Logging | Elasticsearch | `pattern: request completed`<br>`http_status: 200, path: /work`<br>`trace_id: 44525bd28a17a8eff3638b29447eec5c` | 存在应用处理 `/work` 成功返回 200 的案例，表明应用逻辑并非永久不可用，而是间歇性/偶发性故障 [fact-2af31d4b64dc] |
| 8 | Tracing | Deepflow | `HTTP GET /work`<br>`response_code: 500`<br>`duration_us: 4416 - 8760` | 网络流数据独立佐证了 500 错误的存在，且处理耗时较短，暗示故障发生在应用处理内部而非后端依赖慢 [fact-8370ded3b5ce] |

日志中 `/work` 路径下“500 错误并退出”与“200 成功”的现象共存，表明应用进程状态不稳定（可能是资源竞争、偶发异常或内部条件依赖未满足）；Tracing 与 K8s 日志互相印证了导致容器崩溃的触发机制为“应用内部 runtime error 并主动 exitCode 2”。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程内部存在缺陷或状态异常（未确认） → 处理 /work 请求时触发运行时错误（http_status 500） → 应用记录 'runtime process exiting' 并以 exitCode 2 主动退出 → 容器崩溃进入 CrashLoopBackOff
```

### 根因结论

**已确认现象**：应用 `workload-7679bcf76-jwr8b` 在处理 `GET /work` 请求时，因内部运行时错误（`runtime process exiting`）主动终止（`exitCode 2`），导致 Kubernetes 触发重启并陷入 `CrashLoopBackOff`（由 [fact-1, 2, 4, 7, 8] 等证实）。

**证据不足的根因**：现有日志仅记录了“进程退出”和“HTTP 500”，缺乏导致该 500 错误的根本技术原因（如具体的代码异常堆栈、依赖服务故障、配置缺失或 OOM 等）。同时，缺乏对“为何部分请求（如 `trace_id 44525bd28a17a8eff3638b29447eec5c`）能返回 200 成功”的决定性区分证据。因此，正式根因（RCA）发布条件未满足，诊断状态为 `inconclusive`。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 44.0s
├─ 并发证据采集: 76.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 76.8s (Evidence 66.2s, RCA 10.4s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- 未调用 Runbook
