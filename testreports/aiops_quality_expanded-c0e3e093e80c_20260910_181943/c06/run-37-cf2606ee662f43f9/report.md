## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod `workload-7679bcf76-n5vp8` 持续处于 CrashLoopBackOff，容器频繁重启，最近重启次数达 19 次（累计 338 次），退出码为 2。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` 状态 `CrashLoopBackOff`, `exit_code=2`, `restart_count=19` | 确认应用进程已退出并触发集群自动重启机制 |
| 2 | K8s Event | Kubernetes | Warning BackOff: `Back-off restarting failed container app in pod workload-7679bcf76-n5vp8` (重复 338 次) | 证实容器处于持续崩溃循环中，重启间隔正在拉长 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 计数为 `19` | 独立验证应用发生了多次重启行为 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值达 `17,158,144 Bytes`，资源限制为 `96Mi` (约 100MB) | 显示内存使用存在波动，但未见突破 96Mi 硬限制的 OOM 迹象 |
| 5 | Logging | Elasticsearch | 日志模式：`"http_status": 500, "message": "runtime process exiting"` (3 次) | 直接捕获应用崩溃前最后一刻的日志行为：HTTP 500 后进程退出 |
| 6 | Tracing | Deepflow/Tempo | Flow 记录显示请求 `GET /work` 返回 `response_code=500` 且 `aiops.observed_mode="runtime_exit"` | 将具体的 API 请求与进程终止机制关联，确认是在处理该路由时崩溃 |

证据分析：
Kubernetes 状态与 Metric 共同证实了容器反复因异常退出（Exit Code 2）而陷入 CrashLoopBackOff。Logging 与 Tracing 数据精确锁定了崩溃发生的上下文：应用在处理 `GET /work` 请求时，先记录了 HTTP 500 状态，随后应用进程终止。内存监控数据排除了资源硬限制（Memory Limit）导致崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码存在未捕获的运行时异常（具体类型不明） → 异常被捕获并记录 'runtime process exiting' (HTTP 500) → 进程以 Exit Code 2 退出 → Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认的根因为**应用内部逻辑异常导致的进程退出**。

证据 `[#5, #6]` 显示应用在处理 `GET /work` 路由时触发了未处理的错误，并在日志中留下了 `runtime process exiting` 的记录，随后进程以非零状态码退出。这一直接失败被 K8s 检测为容器非正常退出，从而触发重启逻辑。

目前证据不足以定位具体的根本代码错误：
1. 日志中缺失导致 `runtime process exiting` 的底层异常堆栈（如 Python Stack Trace）。
2. 资源指标排除了内存溢出（OOM）或 CPU 过载的常见外部因素。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 20.2s
├─ 并发证据采集: 150.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 150.1s (Evidence 135.9s, RCA 13.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
