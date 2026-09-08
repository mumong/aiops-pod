## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器 app 反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-7679bcf76-w9s9c` 状态 `CrashLoopBackOff`，Container `app` 退出码 `2`，重启次数 `22` 次 | 确认 Pod 处于异常重启循环状态 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app`，持续 `95m` | 证实 Kubelet 观察到反复重启且退避 |
| 3 | Logging | Elasticsearch | `error` 日志：`http_request` 请求 `/work` 返回 `http_status: 500`，`message: "runtime process exiting"` (4 次) | 揭示应用层发生 500 错误并导致进程退出 |
| 4 | Tracing | Deepflow | HTTP Flow `GET /work` 返回 `response_code: 500`，持续时间 `4511-9849 us` (5 次) | 网络侧观测到与日志时间窗口一致的业务层 500 错误 |

**证据印证与关联：**
日志中 `500` 错误且伴随 `"runtime process exiting"`，直接解释了 Tracing 中观测到的 `500` 响应状态（证据 #3 和 #4），以及 K8s 侧观察到的容器异常终止和 CrashLoopBackOff（证据 #1 和 #2）。时序上，日志错误窗口与 500 响应窗口高度重合。

## 🎯 根因分析 · g1

### 因果链
```text
应用内部运行时错误 → 处理 /work 请求抛出 500 异常 → 进程异常终止 (exitCode=2) → Kubernetes 重启导致 CrashLoopBackOff
```

### 根因结论
已确认根因为应用在处理 `/work` 端点时发生运行时异常，抛出 500 错误并导致进程退出。
证据 `fact-41145b75929d` (Tracing 500 错误) 和 `fact-41d82ae5b969` (Logging 错误日志) 明确指出了故障发生在应用逻辑层。Kubernetes 的 `CrashLoopBackOff` 状态是由于应用进程意外退出后被系统不断重启造成的。

缺失决定性事实：无，应用层错误证据充足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.0s
├─ 并发证据采集: 69.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 69.4s (Evidence 61.0s, RCA 8.2s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
