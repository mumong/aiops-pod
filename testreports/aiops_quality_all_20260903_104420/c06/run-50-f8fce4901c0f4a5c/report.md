## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器进程异常退出（exitCode=2）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `reason=CrashLoopBackOff`, `last_terminated_reason=Error`, `restart_count=28`, `exit_code=2` | 证实容器异常退出并进入重启退避机制 |
| 2 | K8s Event | K8s BackOff Event | `Back-off restarting failed container app in pod ...` (x541 over 122m) | 提供长周期持续崩溃的时间跨度证据 |
| 3 | K8s Config | K8s Resource Config | `cpu_request=20m`, `cpu_limit=200m`, `memory_request=24Mi`, `memory_limit=96Mi` | 确认资源分配合理，非资源耗尽所致 |
| 4 | Metric | Prometheus State | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}=1` | 独立验证当前的异常状态 |
| 5 | Logging | Elasticsearch (Error) | `pattern="runtime process exiting"`, `http_status=500`, `path="/work"`, `occurrence_count=5` | 捕获应用崩溃前的最后日志，表明进程主动退出 |
| 6 | Logging | Elasticsearch (Info) | `pattern="request completed"`, `http_status=200`, `path="/work"`, `occurrence_count=3` | 提供崩溃前的成功请求基线，证实崩溃是近期突发状态 |
| 7 | Tracing | Tempo Span | `GET /work` -> `200`, `trace_id=44d82bffd1cff720d7ba7f132cc91772` | 确认应用此前曾成功处理 `/work` 请求 |
| 8 | Tracing | Deepflow Flow | `GET /work` -> `500`, `src_ip=172.16.104.21`, `dst_ip=172.16.104.17`, `occurrence_count=2` | 关联日志 `500` 错误，证实崩溃前发生了导致应用拒绝服务的请求 |

证据表明，应用在运行于 `20m-200m CPU` 和 `24Mi-96Mi Memory` 的环境中时，处理 `/work` 请求发生内部异常（HTTP 500），随后进程主动执行退出逻辑 (`exitCode=2`)。K8s 依据重启策略进行 28 次重启，最终因退避触发而处于 `CrashLoopBackOff` 状态。Tracing 中的 500 错误 Flow 与 Logging 中的 `runtime process exiting` 记录高度对应。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work HTTP 请求时触发内部错误 → 进程主动执行退出逻辑 (exitCode=2) → Kubelet 检测到容器异常终止并触发重启策略 → Pod 状态进入 CrashLoopBackOff，持续处于未就绪
```

### 根因结论

**已确认的根因**：应用进程在处理 `GET /work` 请求时触发内部运行时错误并主动退出，导致 K8s 持续重启且无法就绪。

- 事实支撑：
  - K8s 侧证实容器最后终止原因为 `Error`，退出码为 `2`，Pod 进入 `CrashLoopBackOff` 状态（事实 1, 2, 4）；
  - 日志侧记录到 5 次 `runtime process exiting` 伴随 HTTP 500 响应，证实是应用侧主动退出而非 OOM 或外部终止（事实 5）；
  - Tracing 侧观测到针对 `/work` 的 500 错误请求流，与日志模式吻合（事实 8）；
  - 资源限制（事实 3）排除了资源争抢导致系统杀进程的可能。

- 待确认项：
  - 具体的 Python 异常类型或堆栈信息（日志未捕获，无相关 Fact 支撑）；
  - 导致 `/work` 内部错误的代码逻辑或配置缺陷详情。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.9s
├─ 并发证据采集: 69.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 69.3s (Evidence 58.2s, RCA 11.0s)
└─ 汇总总结: 14.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
