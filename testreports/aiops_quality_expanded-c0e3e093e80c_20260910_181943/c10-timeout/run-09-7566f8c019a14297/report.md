## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container app: status=CrashLoopBackOff, waiting_message=back-off 5m0s restarting failed container | 描述应用当前处于重启退避状态的现象事实 |
| 2 | K8s Event | kubernetes | kubelet 报告 Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (Client.Timeout exceeded while awaiting headers) | 确认导致容器被杀（Killing）的直接原因是探针超时，而非连接失败 |
| 3 | K8s State | kubernetes | Container app: exit_code=137, last_terminated_reason=Error | 提供关键的退出事实：137 通常对应 OOMKilled，但 K8s 记录的终止原因却是 Error，存在矛盾 |
| 4 | K8s Config | kubernetes | resource_request.memory=8Mi, resource_limit.memory=64Mi | 提供判断内存压力的资源背景，应用被允许使用上限 64Mi |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 显示 reason=Error (value=1, sample_count=1) | 独立验证了 K8s State 中记录的原因为 Error，排除了 OOMKilled 指标 |
| 6 | Logging | elasticsearch | 10.2.0.50 ... "GET /health HTTP/1.1" 200 - (时间戳 13:19:53 至 13:20:18) | 确认应用在探针报错的时间窗口内，`/health` 端点实际响应了 200，支持探针配置存在偏差的假设 |
| 7 | Tracing | deepflow | L7 Flow (GET /health): src=10.2.0.50 -> dst=172.16.104.36, response_code=200, duration_us min=3001102 (约 3s) | 证实 `/health` 请求实际耗时约 3 秒，显著超时（通常探针默认或配置超时为 1 秒），是触发 Kill 的直接诱因 |

证据关联说明：
- 编号 6、7 的日志与 Tracing 数据高度一致，均证实 `/health` 端点耗时在 3 秒左右并成功返回 200。
- 编号 2（探针超时事件）与编号 7（实际 3 秒响应）互为因果：实际耗时 3 秒导致探针超时，探针超时触发 K8s 杀死容器（编号 2）。
- 编号 1 和 5 确认了当前的异常状态和终止原因为 Error，而编号 3 进一步指出退出码 137 与该原因存在逻辑冲突。

## 🎯 根因分析 · g1

### 因果链

```text
探针超时配置(<3s) < 业务接口响应耗时(~3s) → 容器因 Liveness 探测失败被 K8s 杀死 (Kill/Signal 9) → 退出码 137 但 terminated_reason 记录为 Error → 应用进入 CrashLoopBackOff 循环
```

### 根因结论

**证据不足**，无法确认根本原因是 OOM 还是配置偏差。

1.  **关于探针超时（高度可信）**：Tracing 和 Logging 明确显示，`/health` 接口实际耗时约 3 秒，这导致 Liveness Probe 发生 `context deadline exceeded`（事实 2, 6, 7）。这是导致容器被周期性重启的直接机制。
2.  **关于异常根因（冲突/未确认）**：容器退出码为 137（事实 3）。在 Linux 标准中，137 通常意味着进程收到了 Signal 9 (SIGKILL)，常见原因为 OOMKilled 或人为 `kill -9`。然而，K8s State（事实 3）和 Prometheus Metric（事实 5）均明确记录 `terminated_reason=Error`，而非 `OOMKilled`。

**缺失的决定性事实**：
要区分是 OOM 还是非预期 Kill，需要查看具体的 `container_last_terminated_exit_code` 以及是否存在伴随 `Terminating` 阶段的其他错误日志或 `systemd`/`dmesg` 层面的 OOM 记录。目前的证据在“超时导致被杀”与“被杀的原因记录”之间存在事实冲突，无法直接下结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 18.2s
├─ 并发证据采集: 142.0s
│  └─ g1 aiops-case-v17/workload: 142.0s (Evidence 131.9s, RCA 9.8s)
└─ 汇总总结: 15.1s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
