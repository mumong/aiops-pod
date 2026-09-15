## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用进程在处理 /work 请求时发生内部运行时异常导致退出 (exitCode=2)，引发 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-7679bcf76-n5vp8` 状态 `Running`，容器 `app` 处于 `CrashLoopBackOff` | 确认异常实体与当前运行状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 最后一次终止原因 `Error`，退出码 `exit_code=2` | 确认进程异常终止的直接事实 |
| 3 | K8s State | Kubernetes | 容器重启次数 `restart_count=8`；Pod 条件 `ContainersReady=False` | 反映异常导致的持续不健康状态 |
| 4 | K8s Event | Kubernetes | `BackOff` 事件：`Back-off restarting failed container app` (89次，持续20m) | 确认 Kubelet 处于重启退避阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}=1` | 独立观测到等待状态，确认事实 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason{reason="Error"}=1` | 独立观测到上一终止状态，确认事实 |
| 7 | Logging | Elasticsearch | 错误日志模式：`http_request level="error" message="runtime process exiting" path="/work" http_status=500` (3次，18:32-18:34) | 提供应用进程崩溃前的最后信号 |
| 8 | Tracing | DeepFlow/Tempo | L7 Flow 匹配 1 次 500 响应 (`dst_ip: 172.16.104.6`)，其余 8 次为 200 响应；Trace 包含 `http.response.status_code: 200` | 提供应用行为时序，确认崩溃前服务曾短暂正常响应 |

**证据说明：**
K8s 层面确认了 Pod 处于崩溃循环，且退出码 2 表明是非标准的进程内部错误。Metric 和 K8s State 交叉验证了 `CrashLoopBackOff` 和终止状态。日志提供了具体的触发点（`/work` 路径的 `runtime process exiting`），而 Trace 数据补充了崩溃发生前系统曾短暂处理成功请求的背景。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务器处理 /work HTTP 请求时发生内部运行时错误 → 进程异常终止 (exitCode=2) → Kubelet 尝试重启但失败并进入 Back-off 退避 → Pod 进入 CrashLoopBackOff 状态且无法 Ready
```

### 根因结论

**已确认的根因：** 应用容器 `app` 中的进程（根据日志显示为 Python 脚本 `/opt/aiops/server.py`）在处理 `/work` 请求时发生内部运行时异常，导致进程以 `exitCode=2` 异常退出。

*   **证据支撑：**
    *   Kubernetes 层面确认了容器的退出码为 2 (`fact-9158a3d40e28`)，且处于 `CrashLoopBackOff` 状态 (`fact-5e6d3207269e`)。
    *   Prometheus 指标独立确认了该 Pod 处于等待状态，且上一次终止原因为 Error (`fact-8c38a1867f4d`)。
    *   应用日志明确记录了在 `/work` 路径收到请求后发生 `runtime process exiting` 错误 (`fact-7f29f52b1580`)。

*   **缺失的决定性事实：** 具体导致进程退出的异常堆栈或错误类型（如内存错误、断言失败等）目前证据不足，需要进一步查看应用标准输出日志。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 22.5s
├─ 并发证据采集: 64.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 64.7s (Evidence 56.2s, RCA 8.3s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
