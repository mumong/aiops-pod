## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | {'message': 'Reason:       CrashLoopBackOff'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 确认异常退出的直接状态，排除了 OOMKilled 信号 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app`; Pod IP: 172.16.104.52 | 确认 K8s 层面已识别并正在执行重启策略 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory`: 96Mi; `resource_limit.cpu`: 200m | 提供资源限制上下文，虽未触发 OOMKilled 但仍可能制约进程运行 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: Error (last_terminated_reason 非 OOMKilled) | 侧面印证非由容器内存超限被 Kill 引起，进一步指向业务或系统错误 |
| 5 | Logging | Elasticsearch | Pattern: `http_request | error | message: "runtime process exiting"` (HTTP 500); Pattern: `http_request | info | message: "request completed"` (HTTP 200) | 日志模式模糊，仅指出进程在请求路径上退出，缺乏具体异常堆栈 |
| 6 | Tracing | Deepflow/Tempo | 关联 `18e0338801b5ff20f216241e4c442d1e` 的 HTTP 500 Flow; 关联 `684a53ea2d51690cdbba709bce8303a0` 的 HTTP 200 Flow | 追踪证实异常期间确实产生了 500 响应，但应用侧未向下游传递具体的错误信息 |

证据 1、2 与 4 共同确认了 Pod 处于由于容器非正常退出（Exit Code 2 且非 OOMKilled）导致的 CrashLoopBackOff 状态。日志（证据 5）与追踪（证据 6）仅能证明在 `/work` 路径上发生了错误并返回了 500，且进程终止时仅打印了通用消息。由于缺乏具体的错误堆栈（Stack Trace）或配置报错信息，目前的工具事实互相印证的是“异常发生”这一现象，但无法提供导致该异常的明确业务或系统级原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器 `app` 启动并处理请求（Trigger） → 进程在运行时以 Exit Code 2 异常退出（机制，未确认具体错误） → Kubernetes 触发 CrashLoopBackOff 重启策略（直接失败） → Pod 状态变为 CrashLoopBackOff（用户可见现象）
```

### 根因结论

证据不足以确定导致容器异常退出（Exit Code 2）的根本原因。
现有事实（K8s 状态、Metrics、Logs、Traces）一致证实了容器发生了非 OOM 的异常终止（Exit Code 2, terminated_reason=Error），并触发了 K8s 的重启机制。然而，日志中仅记录了模糊的 `runtime process exiting` 错误，且未提供具体的错误堆栈（Stack Trace）或配置解析失败的证据，导致无法将异常归因于具体的业务逻辑错误、资源受限（尽管未达到 OOM 阈值）或外部依赖调用失败。

---

## 📊 性能统计

```text
├─ 总耗时: 9.3m
├─ 问题定位: 20.0s
├─ 并发证据采集: 525.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 525.2s (Evidence 515.0s, RCA 10.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
