## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | Error | 应用进程 `python3 /opt/aiops/server.py` 运行时未捕获异常（runtime error）或关键配置缺失导致进程以 exit code 2 非正常终止，进而触发 Kubernetes 的 CrashLoopBackOff 重启机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running; `pod.condition`: Initialized=True, PodScheduled=True; `ContainersReady`: False, Ready: False (reason: ContainersNotReady) | 确认 Pod 处于运行阶段，但应用容器未通过就绪探针，处于异常状态。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 容器最后一次启动因 Error 终止，退出码为 2，是应用进程异常退出的直接证据。 |
| 3 | K8s Event | Kubernetes | `BackOff`: "Back-off restarting failed container app" (发生 8 次，跨度 116s); `restart_count`: 4 | 容器持续崩溃并触发重启退避机制，证实该状态已持续一段时间且无法自愈。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`=1 (labels: container=app, reason=Error); `waiting_reason`=1 (reason=CrashLoopBackOff); `restarts_total`=3 | 监控数据确认容器处于 CrashLoopBackOff 状态，且最近终止原因为 Error，与 Kubernetes 状态一致。 |
| 5 | Logging | Elasticsearch | `http_request` error log: `runtime process exiting`, `http_status`: 500, `path`: /work, `service`: aiops-lab-workload (发生 4 次, trace_id: e.g., 01081e5b5d57475904221bdc11916111) | 日志显示应用进程在处理请求后发生运行时错误并退出，提供了崩溃前的具体行为上下文。 |
| 6 | Tracing | Tempo/Deepflow | Trace `01081e5b5d57475904221bdc11916111` (Tempo span): HTTP GET /work returned 500; Deepflow L7 flow: GET /work dst_ip=172.16.104.17 returned 500 (occurrence_count: 3) | 追踪数据将 500 错误响应与应用进程内部处理关联，确认 HTTP 请求失败导致了应用异常。 |

**证据说明**：
Kubernetes 的 `Exit Code 2` 和 `Error` 终止原因（事实 2）与 Prometheus 中的 `CrashLoopBackOff` 状态（事实 4）相互印证，确认了崩溃的持续性。日志中的 `runtime process exiting`（事实 5）结合 Trace 中的 `500` 错误响应（事实 6），解释了容器非正常退出的直接诱因是应用层运行时错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程 `python3 /opt/aiops/server.py` 运行时未捕获异常或关键配置缺失 → 进程以 exit code 2 非正常终止 → 触发 Kubernetes 的 CrashLoopBackOff 重启机制 → 应用进程 `python3 /opt/aiops/server.py` 运行时未捕获异常（runtime error）或关键配置缺失导致进程以 exit code 2 非正常终止，进而触发 Kubernetes 的 CrashLoopBackOff 重启机制。
```

### 根因结论

**已确认的根因**：应用进程 `python3 /opt/aiops/server.py` 在运行过程中发生未捕获异常或遇到关键配置缺失，导致进程以 `exit code 2` 非正常终止。这一应用层错误直接引发了 Kubernetes 的崩溃重启循环（CrashLoopBackOff）。

**证据引用**：
- 容器非正常退出及退出码：事实 2（K8s State: `last_terminated_reason: Error`, `last_exit_code: 2`）
- 重启循环状态：事实 3（K8s Event: `BackOff`）和事实 4（Metric: `CrashLoopBackOff`）
- 应用层错误上下文：事实 5（Logging: `runtime process exiting`）和事实 6（Tracing: `HTTP 500`）

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 31.0s
├─ 并发证据采集: 67.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 67.0s (Evidence 60.0s, RCA 6.8s)
└─ 汇总总结: 14.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
