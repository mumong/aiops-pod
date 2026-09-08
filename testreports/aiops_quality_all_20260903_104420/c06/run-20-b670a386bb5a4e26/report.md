## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container app exit_code: 2; Reason: Error | 确认容器异常退出状态 |
| 2 | K8s Event | kubernetes | Warning BackOff: Back-off restarting failed container app (x201 over 45m) | 确认 CrashLoopBackOff 症状与频率 |
| 3 | K8s Config | kubernetes | CPU Request: 20m, Limit: 200m; Memory Request: 24Mi, Limit: 96Mi | 排除资源硬性限制（Limit）导致的 OOMKilled |
| 4 | Metric | prometheus | kube_pod_container_status_last_terminated_reason = Error; restart_count = 13 | 确认退出原因为 Error 且非资源耗尽 |
| 5 | Metric | prometheus | kube_pod_status_phase = 1 (Running); kube_pod_status_phase (Failed) = 0 | 当前 Pod 处于 Running 状态但容器处于重启循环中 |
| 6 | Logging | elasticsearch | Pattern: 'runtime process exiting' at path /work, HTTP status 500; Trace IDs: 491a5553... etc. | 锁定故障触发点为 /work 接口处理时的应用层崩溃 |
| 7 | Logging | elasticsearch | Pattern: 'request completed' at path /work, HTTP status 200; 内存 allocated_mib 始终为 0 | 证明应用具备服务请求的能力，故障非内存超限导致 |
| 8 | Tracing | deepflow | L7 Flow: GET /work response_code 500; duration_us 5384-6746 | 证实 HTTP 请求在应用处理阶段即被拒绝并返回 500 |
| 9 | Tracing | tempo | Span GET /work trace_id 97a75c07... attributes: http.response.status_code 200 | 提供正常成功请求的耗时基线，辅助判断故障为瞬间崩溃 |

证据链显示 Pod 处于 CrashLoopBackOff 状态，K8s 与 Metric 确认退出原因为 Error (Exit Code 2)。Logging 与 Tracing 交叉印证表明，应用在处理 `/work` 接口时直接返回 HTTP 500 并随即发生 "runtime process exiting"，同时排除了资源超限导致的 OOM（日志内存占用为 0）。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 逻辑未捕获的异常 → HTTP 500 错误响应 → 进程记录 'runtime process exiting' (Exit Code 2) → K8s 重启失败并进入 CrashLoopBackOff
```

### 根因结论

**证据不足 (inconclusive)**。
当前事实已确凿证明故障现象：应用在 `/work` 接口处理时发生内部错误返回 HTTP 500，随后以 Exit Code 2 强制终止，引发容器 CrashLoopBackOff。

然而，导致该现象的**根本原因（Root Cause）无法确认**。现有证据中缺失应用层详细的堆栈跟踪（Stack Trace）与底层异常信息，日志仅记录了高层退出事件，无法判断具体是代码 Bug、参数校验失败还是内部依赖不可用所致。此外，正式 RCA 的发布因配置限制（RCA fact binding and publication validation disabled）被禁用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.0s
├─ 并发证据采集: 62.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 62.8s (Evidence 53.0s, RCA 9.6s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
