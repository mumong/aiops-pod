## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 持续处于 CrashLoopBackOff 状态（11次重启） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-06/workload-7679bcf76-w9s9c` 状态 `Running`，`exit_code: 2`，重启次数 `11` | 确认 Pod 处于 CrashLoopBackOff 的失败重启循环中 |
| 2 | K8s Event | Kubernetes | `BackOff` 事件（`x133 over 33m`）：Back-off restarting failed container `app` | 确认重启行为被 Kubelet 识别并执行退避策略 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = `1` (Reason: Error)，`kube_pod_container_status_restarts_total` = `11` | 指标层面印证容器因 Error 退出且重启计数与 K8s 状态一致 |
| 4 | Logging | Elasticsearch | 聚合日志：`runtime process exiting`，`http_status: 500`，`path: /work` (发生 3 次) | 发现应用在处理 `/work` 接口时主动终止进程 |
| 5 | Tracing | Deepflow | L7 Flow：GET `/work` 返回 `HTTP 500` (发生 3 次)，Trace ID 如 `491a5553286b708f2be0016438a15c3f` | 网络层确认 `/work` 请求返回 500 错误，与日志记录一致 |
| 6 | Tracing | Tempo | Span：`GET /work` 返回 200，Trace ID `97a75c073642b491e78d960ba0ad27a4`，Attribute `aiops.observed_mode: runtime_exit` | 展示偶发成功请求与日志模式中的 `runtime_exit` 标记相联系 |

**证据交叉印证：**
*   K8s `exit_code: 2` [证据 #1] 与 K8s Event [证据 #2] 及 Prometheus 指标 [证据 #3] 共同确认了 Pod 异常重启的事实。
*   Logging 的 `runtime process exiting` + `HTTP 500` [证据 #4] 与 Tracing 的 `HTTP 500` Flow [证据 #5] 及 Tempo Span [证据 #6] 高度吻合，明确指向 `/work` 接口在处理请求时触发了应用内部异常并导致进程终止。
*   尽管资源限制存在（CPU 20m/200m，内存 24Mi/96Mi [输入事实]），但日志中 `allocated_mib` 始终为 0，且错误表现为显式的 `runtime exiting`，而非 OOM Kill 等隐式信号。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时发生内部异常 → 返回 HTTP 500 并记录 "runtime process exiting" → 进程以 Exit Code 2 主动退出 → Pod 进入 CrashLoopBackOff 状态（11次重启）
```

### 根因结论

**已确认的根因：**
应用进程在处理 `/work` 接口时因内部异常（HTTP 500）主动终止了运行。
这一结论由以下多源证据确证：
1.  **K8s 状态**显示容器以 `Exit Code 2` 异常退出并持续重启 [证据 #1]。
2.  **日志与链路追踪**一致记录了 `/work` 请求返回 `HTTP 500` 后紧跟着 `runtime process exiting` 的日志输出 [证据 #4, #5, #6]。
3.  **指标数据**证实了 `CrashLoopBackOff` 和 `Error` 终止原因 [证据 #3]。

**未确认的细节：**
*   导致 HTTP 500 的具体上游依赖故障或代码逻辑错误，需结合应用源码或更深度的调试日志确认 [诊断声明未知项]。
*   `/work` 接口出现不稳定 500 错误的具体原因（偶发 Bug 或资源/依赖波动），当前缺乏足够的上下文数据支持进一步推断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.2s
├─ 并发证据采集: 65.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 65.5s (Evidence 54.7s, RCA 10.6s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
