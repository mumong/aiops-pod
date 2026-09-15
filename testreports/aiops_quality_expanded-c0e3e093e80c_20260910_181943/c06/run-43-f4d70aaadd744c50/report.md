## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-n5vp8处于CrashLoopBackOff状态，容器app反复以Exit Code 2异常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 确认容器异常退出及退出码 |
| 2 | K8s State | kubernetes | `pod.status`: Running; `container.restart_count`: 24 | 确认 Pod 当前处于重启恢复状态 |
| 3 | K8s Event | kubernetes | `Warning BackOff 48s (x452 over 100m)` kubelet 重启失败容器 app | 确认 K8s 频繁重启容器的控制面状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 23 | 验证重启次数与 K8s State 事实互相印证 |
| 5 | Logging | elasticsearch | `level: error`, `message: "runtime process exiting"`, `http_status: 500`, `path: /work`, `occurrence_count: 5` | 确认应用在处理特定请求时发生运行时错误退出 |
| 6 | Tracing | deepflow | HTTP GET /work, `response_code: 500`, `occurrence_count: 4`, `dst_ip: 172.16.104.6` | 从网络流层面确认应用层返回了 500 错误 |
| 7 | Tracing | tempo | Trace: `53808a44ebb4efd9bdbfb4220cbdacbf`, Span: `aiops.observed_mode: runtime_exit`, `http.response.status_code: 500` | 通过链路追踪确认应用内部观察到了运行时退出模式 |

证据表明，容器异常退出是由应用层在处理 `GET /work` 请求时，故意抛出一个 HTTP 500 错误并触发“运行时退出模式（runtime_exit）”导致的。Kubernetes 检测到进程退出后，按照策略不断重启该容器。Metrics 与 K8s State 中的重启计数一致，Logging 和 Tracing 分别证实了异常退出的日志和链路模式。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置了受控故障注入模式 (FAILURE_MODE=runtime_exit) → 应用在处理 /work 请求时触发受控退出逻辑 → 进程抛出 HTTP 500 错误并执行退出命令 (Exit Code 2) → 容器异常终止导致 K8s 不断重启 (CrashLoopBackOff)
```

### 根因结论

根因已确认：容器反复进入 `CrashLoopBackOff` 状态是因为应用本身配置了受控故障注入逻辑。在 `FAILURE_MODE=runtime_exit` 的配置下，应用在处理 `/work` 请求时会故意返回 HTTP 500 并终止进程。

- **Kubernetes 证据**：容器退出码为 2，事件记录显示频繁重启 [证据 1, 2, 3]。
- **应用日志证据**：记录到带有 `runtime process exiting` 的 500 错误请求 [证据 5]。
- **追踪与流证据**：链路与网络流均观察到 `http.response.status_code: 500` 且观测模式为 `runtime_exit` [证据 6, 7]。

现有的日志、链路和网络流事实一致指向受控故障注入是导致异常的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 4.0m
├─ 问题定位: 23.3s
├─ 并发证据采集: 206.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 206.1s (Evidence 195.6s, RCA 10.3s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
