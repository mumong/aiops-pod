## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 2` (`fact-0fe582d15ed9`) | 确认应用进程非正常退出 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (`fact-73ac384e0152`) | 确认容器反复重启，当前处于 CrashLoopBackOff |
| 3 | K8s State | Kubernetes | `last_terminated_reason: Error` (`fact-2f2d95a3cd48`) | 进一步印证退出原因归类为 Error |
| 4 | Logging | Elasticsearch | `runtime process exiting` (HTTP 500) (`fact-1b5987cca1f8` 等) | 捕捉到应用层面的致命错误日志 |
| 5 | Tracing | Tempo | `GET /work` `200 OK` (`fact-3b54a2f16f21`, `b2c74bd...`) | 证明应用曾正常处理请求，故障非全局宕机 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 17` (`fact-615cb8559a92`) | 量化验证了高频率重启现象 |

**证据互证说明：**
K8s Event (`#2`) 和 Metric (`#6`) 客观描述了 CrashLoopBackOff 的现象；Logging (`#4`) 明确指出了应用侧的异常行为 `runtime process exiting` 并伴随 HTTP 500，与 K8s State 记录的 `Error` (`#3`) 和 `exit_code: 2` (`#1`) 逻辑一致。Tracing (`#5`) 确认了该实例具备服务能力且故障发生于特定请求处理中，排除了基础设施或网络层面的持续性阻断。

## 🎯 根因分析 · g1

### 因果链

```text
App runtime exception during request processing → Application logs 'runtime process exiting' with HTTP 500 → Container exits with code 2 (non-zero) → Pod aiops-case-06/workload-7679bcf76-n5vp8 in CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用程序在处理请求时发生了未捕获的异常（Uncaught Exception），导致进程直接退出（Exit Code 2）。

该根因由以下事实共同支撑：
1.  **应用层日志** (`fact-1b5987cca1f8` 等)：记录明确显示 `runtime process exiting`，表明进程在异常状态下被终止。
2.  **容器退出状态** (`fact-0fe582d15ed9`, `fact-2f2d95a3cd48`)：Kubernetes 观察到容器以非零退出码 2 退出，且终止原因为 `Error`。
3.  **重启行为** (`fact-73ac384e0152`, `fact-615cb8559a92`)：Kubelet 触发 BackOff 机制，且重启计数已达 17 次，符合未处理异常导致进程立即退出的特征。

**未确认事项**：日志中缺乏具体的堆栈跟踪（Stack Trace）或异常类型信息（如 NullPointer），因此无法确定导致异常的业务逻辑根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 22.7s
├─ 并发证据采集: 78.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 78.2s (Evidence 70.0s, RCA 8.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
