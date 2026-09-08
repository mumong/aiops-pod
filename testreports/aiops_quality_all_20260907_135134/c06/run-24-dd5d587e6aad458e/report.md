## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，主容器 app 反复退出（重启 17 次），事件记录持续报警。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | container `app` last_terminated_reason: `Error`, last_exit_code: `2` | 确定容器异常终止且代码非 0 |
| 2 | K8s Event | `kubernetes` | `Warning BackOff`: `Back-off restarting failed container app` (x293 over 68m) | 确认容器反复重启进入 CrashLoopBackOff 状态 |
| 3 | Metric | `prometheus` | `kube_pod_container_status_last_terminated_reason` (reason: Error): `1` | 从指标维度印证容器最后终止原因为 Error |
| 4 | Logging | `elasticsearch` | Pattern: `runtime process exiting` (error, 500), first: `13:13:21` to last: `13:34:04` | 确认进程收到显式退出信号 |
| 5 | Tracing | `tempo` | `GET /work` span: `aiops.observed_mode: "runtime_exit"` (trace_id: `684a53ea...`) | 确认当前活跃请求处理过程中进程直接退出 |

证据表明 Pod 的 `app` 容器在运行期间反复发生非 OOM 的 `Exit Code 2` 异常终止（事实 #1, #3）。日志显示进程在 68 分钟内持续触发 `runtime process exiting` 错误（事实 #4）。Tracing 记录 `runtime_exit` 模式发生在正常的 HTTP 请求处理期间（事实 #5）。综合来看，进程是在接收处理请求（包括可能的业务流量或探针）的过程中被外部或内部逻辑立即终止，导致 Kubelet 重启失败并最终触发 BackOff（事实 #2）。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务启动 → 接收/处理外部请求（如探针或业务流量） → 进程收到终止信号立即退出 (Exit Code 2) → Kubelet 重启容器并触发 BackOff 机制
```

### 根因结论

**根因：应用进程在启动后，于处理外部请求（如健康检查探针或业务流量）时，收到终止信号（Exit Code 2）而主动退出。**

已确认的事实支撑如下：
*   **退出性质**：K8s 状态与 Prometheus 指标均明确显示 `last_terminated_reason` 为 `Error`，且退出码为 `2`（事实 #1, #3），排除了 OOMKilled（通常伴随 exit code 137 或 143）。
*   **触发场景**：Tracing 记录 `GET /work` 返回 200 的同时伴随 `aiops.observed_mode: "runtime_exit"`（事实 #5），结合日志中大量 `runtime process exiting` 记录（事实 #4），证明进程是在处理请求的上下文中被终止。
*   **现象表现**：Kubelet 的 `BackOff` 事件表明进程反复重启失败（事实 #2）。

**未知数（需进一步确认）：**
*   具体是哪种上游探针（如 Readiness/Liveness Probe）或业务逻辑导致了该终止信号（Exit Code 2）。
*   Exit Code 2 在特定应用代码中的具体业务含义（例如，是配置错误、依赖连接失败，还是显式的 `return 2;`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.3s
├─ 并发证据采集: 75.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 75.9s (Evidence 63.7s, RCA 12.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled
