## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，持续 42 分钟反复重启，HTTP 服务不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，最后终止原因为 `Error`，退出码 `78` (fact-913d92ff981e, fact-97bd02ad7187, fact-15968b810c77) | 确认应用进程以特定异常状态码退出，且 K8s 正在执行重启策略 |
| 2 | K8s Event | kubernetes | `BackOff` 事件：`Back-off restarting failed container app ... (x177 over 42m)` (fact-47215e8ae51c) | 确认重启行为是持续且被限流的，直接反映了 CrashLoopBackOff 的持续时间 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason: CrashLoopBackOff)；`kube_pod_container_status_restarts_total=12` (fact-58d3df83f231, fact-9e1561dd7236) | 独立观测确认当前等待原因与重启计数，与 K8s 状态一致 |
| 4 | Logging | elasticsearch | 重复错误模式：`http_request level: error message: CONFIG_MISSING http_status: 500 path: /work` (出现 8 次) (fact-49733d275ab8 等) | 直接指出应用逻辑层面的失败原因（配置缺失）及触发的错误码 |
| 5 | Tracing | deepflow+tempo | HTTP 500 响应：`GET /work`，trace_id `64132b2c9d9b8077c1ac955acb517247` (fact-018605175103)；关联日志中同样包含此 trace_id | 通过 trace_id 关联日志与追踪数据，确认请求在应用内部处理配置时失败并返回 500 |

日志中反复出现 `CONFIG_MISSING` 且伴随 HTTP 500 错误，追踪数据证实了具体请求 `/work` 的失败链路。日志模式与追踪跨度通过相同的 `trace_id` 直接交叉印证，排除了网络或基础设施层面的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺失关键配置 (CONFIG_MISSING) → server.py 处理请求时返回 HTTP 500 并主动以 exitCode 78 退出 → kubelet 检测到容器非正常终止 (Error) → Pod 进入 CrashLoopBackOff 状态，应用不可用
```

### 根因结论

已确认的根因为**应用启动或运行时缺失关键配置项**，导致应用代码抛出异常（HTTP 500 且 exitCode 78），进而触发 Kubernetes 的 CrashLoopBackOff 机制。

该结论由以下证据链闭环支撑：
1.  **现象确认**：K8s 状态与指标共同证实容器处于 `CrashLoopBackOff`，重启次数为 12 次（fact-913d92ff981e, fact-9e1561dd7236）。
2.  **失败机制**：日志明确记录应用内部逻辑报错 `CONFIG_MISSING`，且返回 HTTP 500 状态码（fact-49733d275ab8 等）。
3.  **退出原因**：容器最后一次终止退出码为 `78`（fact-15968b810c77），结合日志中的 `CONFIG_MISSING`，可推断是应用层在发现配置缺失后主动非正常退出。
4.  **链路关联**：Tracing 数据中的 trace_id `64132b2c9d9b8077c1ac955acb517247` 同时存在于日志报错记录和 HTTP Flow 中，确认了该配置缺失导致的具体是 `/work` 接口的处理失败（fact-018605175103）。

**未确认事项**：
-   ConfigMap `workload-code` 中具体缺失了哪个键名（日志仅上报通用错误）。
-   是 ConfigMap 挂载错误导致完全不可见，还是 ConfigMap 本身内容不完整。

现有事实已足以认定根因为应用配置缺失导致的 CrashLoop，但缺乏 ConfigMap 内容的细节以进一步区分是运维配置错误还是应用代码逻辑错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.1s
├─ 并发证据采集: 63.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 63.2s (Evidence 51.4s, RCA 11.7s)
└─ 汇总总结: 15.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
