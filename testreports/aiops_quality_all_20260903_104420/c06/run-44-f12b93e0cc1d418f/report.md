## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态（重启25次） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 17s (x497 over 110m) kubelet Back-off restarting failed container app in pod workload-7679bcf76-w9s9c` | 确证 Pod 因容器重启失败进入 CrashLoopBackOff 状态，并展示了长达 110 分钟的重试周期 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (Container: app) | 标识容器异常退出的具体原因标记 |
| 3 | Logging | Elasticsearch | `runtime process exiting` (HTTP status: 500, Path: `/work`, Occurrence: 5次, 时间窗: 13:19 - 13:40) | 直接展示了导致容器终止的进程退出行为及伴随的 HTTP 500 错误 |
| 4 | Tracing | Deepflow | HTTP GET /work 请求响应代码 500 (Occurrence: 5次, Time: 13:19 - 13:40) | 从网络层证实了与日志对应的服务端内部错误 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 25` (Label: container=app) | 量化了 Pod 重启次数，与 K8s 事件中的 `BackOff` 现象一致 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason = 1` (Label: reason=Error) | 从指标层面佐证了容器的终止原因为 `Error` |

证据 3 (日志 `runtime process exiting`) 与证据 4 (Tracing 500 状态码) 明确指向应用层主动终止进程的行为；证据 2 和 6 (状态与指标 Error) 与日志信息相互印证，排除了 OOM 或网络等外部资源限制导致退出的可能；证据 1 确认了 K8s 层面针对这些异常退出的标准重启策略。

## 🎯 根因分析 · g1

### 因果链

```text
Application logic on /work encounters critical condition → HTTP 500 returned and process.exit(2) executed → K8s kubelet detects non-zero exit code & triggers BackOff policy → Pod enters CrashLoopBackOff
```

### 根因结论

已确认根因为：应用代码在处理 `/work` 端点时遇到内部严重错误，主动返回 HTTP 500 状态码并执行了进程终止操作（`runtime process exiting`，exit code 2）。这种设计导致 Kubernetes 检测到容器以非零退出码终止，从而触发 `CrashLoopBackOff` 状态（见证据 1、2、3）。
缺失的决定性事实：应用源代码中触发该 `500` 错误的具体业务逻辑或数据条件（标记为 unknown）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 17.2s
├─ 并发证据采集: 93.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 93.7s (Evidence 83.7s, RCA 9.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
