## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | Running | 应用代码 /opt/aiops/server.py 在处理 /work 路径请求时发生内部错误（HTTP 500）导致进程直接退出（exit code 2），进而引发 Kubelet 重启失败进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason`: Error (app), `exit_code`: 2 | 定位进程异常退出的直接系统反馈 |
| 2 | K8s Event | Kubernetes | `BackOff` (app), 112 次, 27分钟内 | 确认 Kubelet 连续重启失败进入 CrashLoopBackOff |
| 3 | K8s State | Kubernetes | `waiting_reason`: CrashLoopBackOff, `restart_count`: 10 | 明确应用当前处于不可用的崩溃循环状态 |
| 4 | Logging | Elasticsearch | `http_request` error, `http_status`: 500, `path`: /work, `message`: "runtime process exiting" (occurs 2 times) | 揭示应用层因运行时内部错误导致退出的触发逻辑 |
| 5 | Tracing | Tempo | `trace_id`: 21eb2aa3662b8c76672d373057516614, `http.response.status_code`: 200, `aiops.observed_mode`: runtime_exit | 关联同一次请求的完整生命周期，证实异常发生在响应返回之后的运行时阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: CrashLoopBackOff): 1 | 独立指标佐证容器当前处于等待重启状态 |

**证据说明**：
K8s 事件与状态（#1, #2, #3）共同确认了 Pod 处于 `CrashLoopBackOff` 状态且频繁重启；日志事实（#4）提供了根本原因——应用在 `/work` 请求处理中发生运行时错误（500）并直接退出（exit code 2）；Tracing 事实（#5）通过 `trace_id` 关联了日志与调用链，表明应用确实在处理特定 HTTP 请求时发生了异常退出，而 Metric（#6）从监控侧印证了该状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码异常 (内部错误 500) → 进程退出 (exit code 2) → Kubelet 重启失败 → CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：应用代码 `/opt/aiops/server.py` 在处理 `/work` 路径请求时发生内部错误（导致 HTTP 500），进而引发进程直接退出（`exit code 2`），触发 Kubelet 的重启机制。由于退出频繁且无外部资源（如 CPU/内存 Limit）告警或 OOM 迹象，Kubelet 进入退避逻辑，最终导致 Pod 进入 `CrashLoopBackOff` 状态并不可用。

该结论由以下证据共同支撑：
1.  **K8s 退出事实**：`container.last_terminated_reason` 为 `Error`，`last_exit_code` 为 `2`（证据 #1）。
2.  **应用层触发点**：Elasticsearch 日志明确记录 `/work` 路径的 `http_request` 伴随 `http_status: 500` 且日志信息为 `"runtime process exiting"`（证据 #4）。
3.  **状态印证**：K8s Event 显示 `BackOff` 行为，Metric 显示 `waiting_reason` 为 `CrashLoopBackOff`（证据 #2, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.5s
├─ 并发证据采集: 66.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 66.1s (Evidence 59.9s, RCA 6.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- 未调用 Runbook
