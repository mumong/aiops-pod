## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | application logic error causing 500 error and process exit |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `wait_reason=CrashLoopBackOff`, `last_terminated_reason=Error`, `exit_code=2` | 直接确认应用进程异常退出及 Kubernetes 的重试状态。 |
| 2 | K8s State | K8s | `pod.status=Running` (但 `ContainersNotReady`), `restart_count=21` | 证实 Pod 处于调度运行中但容器持续重启失败的状态。 |
| 3 | K8s Config | K8s | `resource_limit.cpu=200m`, `resource_limit.memory=96Mi` | 提供资源限制上下文，排除硬限制导致的 OOMKilled 可能性。 |
| 4 | K8s Event | K8s | `Warning BackOff ... Back-off restarting failed container app` | 记录了kubelet层面长时间的重启退避现象（持续88分钟）。 |
| 5 | Logging | Elasticsearch | `http_request` `error` `http_status=500` `message="runtime process exiting"` (5次) | 确认应用内部发生未捕获的 500 错误并导致进程立即退出。 |
| 6 | Logging | Elasticsearch | `http_request` `info` `http_status=200` `message="request completed"` (3次) | 表明应用逻辑本身有成功运行的记录，故障非持续性状态。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total=21`, `waiting_reason=CrashLoopBackOff`, `last_terminated_reason=Error` | 独立指标确认了重启次数与 K8s 状态的一致性。 |
| 8 | Tracing | Deepflow | HTTP Flow: `GET /work` `response_code=500` `response_status=3` (4次, duration 5-9ms) | 确认了引发故障的具体流量路径与 HTTP 响应代码。 |
| 9 | Tracing | Tempo | Span: `GET /work` `status_code=200`, `observed_mode=runtime_exit`, trace_id=`160828fdbc068f8fae2f2c59ecad1f1b` | 证实部分请求虽然完成返回，但随后触发 runtime exit；与日志 trace_id 吻合。 |

**证据关联说明：**
- **K8s 状态** (1, 2, 4) 提供了宏观的故障表现，即进程反复退出。
- **日志** (5) 揭示了退出机制：HTTP 500 后进程退出；**成功日志** (6) 说明代码逻辑存在偶发性崩溃。
- **Tracing** (8, 9) 提供了中间层证据，确认了 500 状态码与“runtime exit”观察模式的直接关联，且 Trace ID 在日志和 Tracing 中形成闭环。
- **Metric** (7) 从时序角度确认了重启行为的累积结果。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑缺陷（未处理特定条件） → 内部 HTTP 500 错误 → 进程直接退出 (exit code 2) → Kubernetes 重启策略触发 CrashLoopBackOff
```

### 根因结论

**已确认根因**：应用逻辑错误导致 500 内部服务器错误并直接终止进程。

证据链如下：
1. **异常触发**：日志中记录了 5 次 `http_status=500` 且伴随 `runtime process exiting` 的明确错误信息（证据#5）；Tracing 数据显示了 4 次 `response_code=500` 的 HTTP 流（证据#8），且跨度时间较短（5-9ms），表明是在处理请求时发生的逻辑崩溃而非超时。
2. **进程终止**：Kubernetes 状态显示容器退出码为 `2`（证据#1），通常表示程序执行错误；且没有 OOMKilled 等系统级终止特征，符合应用主动报错退出的特征。
3. **结果与状态**：进程退出直接导致 Kubernetes 触发重启，并在短时间内（观察窗 88 分钟）重启了 21 次（证据#1, #7, #2），最终进入 CrashLoopBackOff 退避状态（证据#1, #4）。

综上，非基础设施或资源限制（CPU/Memory 限制未被触发）问题，而是应用本身处理 `/work` 端点时发生了逻辑错误导致退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.2s
├─ 并发证据采集: 59.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 59.9s (Evidence 53.5s, RCA 6.3s)
└─ 汇总总结: 15.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
