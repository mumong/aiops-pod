## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8处于CrashLoopBackOff状态，表现为容器反复以错误退出码2终止，伴随BackOff事件。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` 终止原因为 `Error`，最后退出码 `exit_code=2` (`fact-6ccafcc91e84`, `fact-deed8e45f770`) | 确认容器异常终止的直接状态与退出码，是故障现象的确凿证据 |
| 2 | K8s Event | Kubernetes | `Warning BackOff` 事件 (`fact-e22dd5d563e1`) 及 `CrashLoopBackOff` 状态 (`fact-99b1284baa94`) | 证实 Kubelet 因重启失败而触发退避机制，Pod 进入 CrashLoopBackOff 模式 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=1` (reason: Error) (`fact-c8d46b0c2f96`) | 独立于 K8s API 的指标确认，与 K8s State 的 Error 终止原因一致 |
| 4 | Logging | Elasticsearch | 错误模式 `runtime process exiting` 出现 5 次，伴随 `http_status=500` 与 `allocated_mib=0` (`fact-7b9116e549d2`) | 记录进程主动退出的关键日志信息，表明应用层触发了退出逻辑 |
| 5 | Tracing | Tempo/Deepflow | Trace `a8998d5b3775eef8729a5088fc6da07d` 显示 `GET /work` 请求返回 HTTP 500 (`fact-1809957b7788`, `fact-37cfe359aa41`) | 将错误日志中的 `/work` 请求与 HTTP 层响应关联，证实请求在到达应用逻辑后触发失败 |

**证据关系说明：**
Kubernetes 的 `exit_code=2` 和 `Error` 终止原因 (证据1) 与 Prometheus 指标 (证据3) 交叉验证了容器异常终止。Elasticsearch 日志中的 `runtime process exiting` (证据4) 和 Tempo/Deepflow 追踪的 HTTP 500 响应 (证据5) 共同解释了进程退出的直接原因——应用处理 `/work` 请求时主动退出，这与 K8s 观察到的重启失败和 BackOff (证据2) 形成完整的因果闭环。

## 🎯 根因分析 · g1

### 因果链
```text
应用配置进入'runtime_exit'测试模式 → 处理/work请求时主动执行退出逻辑 → 返回HTTP 500并退出进程(exitCode 2) → Kubelet重启失败触发BackOff，Pod进入CrashLoopBackOff
```

### 根因结论
已确认根因为**应用被人为配置的测试模式 `runtime_exit` 触发主动退出**。Kubernetes 层面的异常终止状态 (`exitCode=2`) 和应用层日志 (`runtime process exiting`) 以及追踪数据 (HTTP 500 响应) 相互印证，表明故障并非由于资源限制、依赖超时或网络问题，而是应用内部特定逻辑导致的主动终止。

---

## 📊 性能统计

```text
├─ 总耗时: 11.6m
├─ 问题定位: 28.3s
├─ 并发证据采集: 653.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 653.8s (Evidence 642.6s, RCA 11.1s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
