## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，容器 app 以 exitCode=2 异常终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason=Error` | 确认容器退出原因为错误终止，排除 OOMKill 等常见资源问题 |
| 2 | K8s State | kubernetes | `container.last_exit_code=2` | 提供具体的非零退出码，直接指向进程内部异常退出逻辑 |
| 3 | K8s Event | kubernetes | `Warning BackOff restarting failed container app` (x8 over 112s) | 验证集群控制器已观测到重启失败并进入指数退避状态，确认 CrashLoopBackOff 现象 |
| 4 | Logging | elasticsearch | `http_status: 500` 且 `message: runtime process exiting` (4次) | 揭示触发退出的直接诱因：处理 /work 请求时发生内部错误并主动调用退出 |
| 5 | Tracing | deepflow | HTTP GET `/work` 响应码 `500` (src: 172.16.104.56, dst: 172.16.104.6) | 通过流量元数据确认应用层 HTTP 500 状态码的生成路径，与日志错误模式一致 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total=3` (container: app) | 确认容器在过去观测周期内发生了多次重启，量化了故障持续性 |
| 7 | Tracing | deepflow | DNS AAAA/A `lgtm.monitor.svc.svc.cluster.local` 响应状态 `4` | 辅助观测，表明存在监控 DNS 查询失败，但与 500/exit code 2 的进程自退出无直接关联 |

**证据交叉印证：**
Kubernetes 记录的 `exit_code=2` 和 `reason=Error` 与日志中记录 `runtime process exiting` 完全对应，证明是进程内部崩溃或主动退出，而非被系统杀死（OOM/Killed）。Tracing 的 HTTP 500 响应与日志中的 `http_status: 500` 相互印证，说明应用在返回错误响应后触发了自杀逻辑。Metric 重启计数验证了该状态已持续一段时间。

## 🎯 根因分析 · g1

### 因果链

```text
应用在处理 /work 请求时发生内部错误(触发 HTTP 500) → 应用代码执行主动退出逻辑('runtime process exiting') → 容器进程以 exitCode=2 终止 → Kubernetes 检测到终止并进入 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因：**
应用服务在处理 `/work` 路径请求时发生内部逻辑错误，导致其主动调用退出函数，进程以退出码 2 终止，进而触发 Kubernetes 的 CrashLoopBackOff 机制。

**关键证据支撑：**
- **日志层**：4 条重复日志明确显示在 HTTP 请求处理期间，服务返回 500 状态码并输出 `runtime process exiting`（见证据 #4）。
- **追踪层**：Deepflow 流量数据确认了对 `/work` 的请求确实返回了 HTTP 500 响应（见证据 #5）。
- **状态层**：Kubernetes 状态直接观测到容器以非零退出码 2 终止（见证据 #1, #2）。

**未确认细节：**
导致初始 HTTP 500 的具体业务逻辑缺陷、依赖故障或代码上下文未在采集范围内（见正式 RCA 中的 `unknowns`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.1s
├─ 并发证据采集: 75.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 75.8s (Evidence 64.6s, RCA 11.1s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
