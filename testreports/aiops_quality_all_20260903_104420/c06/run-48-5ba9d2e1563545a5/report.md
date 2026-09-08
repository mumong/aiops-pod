## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | Error | Pod aiops-case-06/workload-7679bcf76-w9s9c 容器 app 处于 CrashLoopBackOff 状态，退出码为 2 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff (`fact-22af6f3c3f0f`) | 确认 Pod 处于应用崩溃后的重启等待状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error, `last_exit_code`: 2 (`fact-4a92ed99d36e`, `fact-019737e1500e`) | 确认容器非正常退出，符合应用内部崩溃特征 |
| 3 | K8s Event | kubernetes | `BackOff` Warning 3m11s x519 over 118m (`fact-d74ce34108c4`) | 确认故障持续时间长且重启频率高 |
| 4 | Logging | elasticsearch | `runtime process exiting`, HTTP 500 (`fact-250ccba47c01` 等) | 应用层日志显示进程因运行时异常主动终止 |
| 5 | Tracing | deepflow | Flow: `GET /work` -> HTTP 500, Duration 11ms-29ms (`fact-082e305b4471`) | 网络侧确认失败请求与日志中的 500 错误直接对应 |
| 6 | Metrics | prometheus | `last_terminated_reason`: Error (`fact-39755d5a8796`) | 监控数据验证容器最近终止原因确认为 Error |

**证据印证：**
K8s 记录的 `Exit Code 2` 和 `CrashLoopBackOff` 状态与日志中的 `runtime process exiting` 以及 Tracing 中的 `HTTP 500` 响应相互印证，共同指向应用进程在处理 `/work` 请求时发生了未捕获的运行时异常并主动退出，导致容器反复重启。

## 🎯 根因分析 · g1

### 因果链

```text
代码逻辑存在未捕获异常 → HTTP 请求 /work 触发应用崩溃（exit_code 2, HTTP 500） → 容器频繁重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：应用程序在处理 `/work` 接口时发生未捕获的运行时异常并主动退出。
这一根因得到了以下事实的支持：
- 应用日志中明确记录了 `runtime process exiting` (`fact-4`) 且伴随 HTTP 500 错误；
- 对应的网络流量数据确认了 `GET /work` 请求均返回了 500 状态码 (`fact-5`)；
- K8s 侧记录的容器退出码为 2 且触发 `CrashLoopBackOff` (`fact-1`, `fact-2`)。

**未知数**：导致 `runtime process exiting` 的具体 Python 异常类型（如 `IndexError` 或 `ValueError`）未直接出现在当前采样日志中，无法确定具体的代码错误行。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 36.3s
├─ 并发证据采集: 140.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 140.3s (Evidence 130.2s, RCA 10.0s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled
