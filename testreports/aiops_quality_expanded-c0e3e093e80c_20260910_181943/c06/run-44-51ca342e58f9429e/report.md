## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIPs: 172.16.104.6/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-37bbd078e6e2` | `waiting_reason: CrashLoopBackOff` (container: app) | 确认应用容器当前处于因反复失败而被 K8s 延迟重启的终止状态 |
| 2 | K8s State | `fact-14f26dbe7502` | `last_terminated_reason: Error` (container: app) | 标识出导致重启的直接原因是容器应用进程以非零代码退出 |
| 3 | K8s State | `fact-08253df51fbc` | `last_exit_code: 2` (container: app) | 提供具体的进程退出代码，对应通常的应用内部逻辑错误或参数错误 |
| 4 | K8s Event | `fact-3fcc32a3b420` | `BackOff` 事件：`Back-off restarting failed container app` (已发生 452 次) | 量化崩溃频率，表明问题具有持续性而非瞬时干扰 |
| 5 | Logging | `fact-66a6759ddad4` | `http_status: 500`, `message: runtime process exiting`, `path: /work` (时间窗口 19:51-20:12) | 在崩溃前捕获到明确的 HTTP 500 业务错误及进程退出的日志模式 |
| 6 | Tracing | `fact-37cfe359aa41` | `GET /work`, `response_code: 500` (流量记录 2 次) | 网络流层面佐证了应用在处理 `/work` 路由时确实返回了内部错误 |
| 7 | Metric | `fact-c337d56e8b2d` | `restarts_total: 24` (container: app) | 指标层面确认了容器已经被强制重启了 24 次 |

**证据印证说明：**
K8s 状态（#1, #2, #3）明确指出了 `CrashLoopBackOff` 及其底层触发因素（`exit code 2`），这与 Prometheus 指标显示的持续重启（#7）及 K8s 事件（#4）相互印证。Logging 层（#5）提供了关键的因果链条片段：应用进程在处理 `/work` 请求并返回 HTTP 500 后记录“runtime process exiting”。Tracing 记录（#6）从流量侧证实了 HTTP 500 的发生，但缺乏对应的崩溃日志 Trace ID 匹配，无法直接证明 500 错误导致了当次特定的进程退出，二者在时间窗口上具有高度重叠。

## 🎯 根因分析 · g1

### 因果链

```text
应用在处理 /work 请求时发生内部错误(HTTP 500) → 应用进程记录错误并主动退出(exitCode 2) → 容器生命周期终止触发 K8s 重启策略 → CrashLoopBackOff 状态
```

### 根因结论

已确认的根因机制是：应用进程在处理 `GET /work` 请求时遭遇未捕获的运行时错误，导致返回 `HTTP 500` 并记录 `runtime process exiting` 后以 `exit code 2` 退出，进而触发 Kubernetes 的 `CrashLoopBackOff` 重启机制。

**但正式 RCA 无法发布且决定性事实不足**，因为：
1. 缺乏导致 `HTTP 500` 的具体原因：日志中仅有 `runtime process exiting` 的通用报错，缺失导致该状态的具体 Python 异常堆栈（如 `KeyError`、`AttributeError` 或 `Timeout`）。
2. 缺失崩溃前的上下文：工具 `query_pod_logs` 执行失败（输入验证错误），导致未能获取上一容器崩溃瞬间（exit code 2 发生前）的详细业务日志或堆栈信息。
3. 无法排除外部输入或依赖故障：由于缺乏详细日志，无法确认是否由特定输入数据或上游依赖瞬时故障引发。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 15.8s
├─ 并发证据采集: 95.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 95.1s (Evidence 86.1s, RCA 8.8s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
