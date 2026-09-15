## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Warning Unhealthy ... Liveness probe failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers)` | 确认应用健康检查严重超时。 |
| 2 | K8s State | Kubelet | `container.last_exit_code: 137` | 确认容器进程被强制终止。 |
| 3 | K8s Event | Kubelet | `Warning BackOff ... Back-off restarting failed container app` | 确认因进程终止导致指数退避重启循环。 |
| 4 | K8s Config | K8s Spec | `CPU Limit: 200m` / `Memory Limit: 64Mi` | 提供资源限制的边界上下文。 |
| 5 | Logging | Elastic | `GET /health HTTP/1.1 200` (14:36:38 - 14:37:03) | 证明在 CrashLoopBackOff 发生前，应用仍具备正常的请求处理能力。 |
| 6 | K8s Event | K8s Status | `reason: Exit Code: 137` (伴随 CNI/Network 状态日志) | 辅助确认终止时的系统状态，但日志本身不包含 137 的成因。 |

日志显示 14:36:38 至 14:37:03 期间应用能够正常响应 `/health` 请求，但随后kubelet的 Liveness Probe 记录到超时报错。Exit Code 137 在 Linux 中表示进程收到了 `SIGKILL` 信号，通常由 OOM-killer、节点驱逐或外部强制指令触发。由于 `context deadline exceeded` 表明探针无法获取响应，而日志显示应用此前响应良好，两者之间的断裂点缺乏决定性的监控数据（如真实的 64Mi 内存峰值记录或 CPU Throttling 指标）来支撑根因结论。

## 🎯 根因分析 · g1

### 因果链

```text
资源使用突破限制或节点出现压力 → 进程被强制终止 (Exit Code 137) → Liveness Probe 因进程不可用而超时 → CrashLoopBackOff 循环重启
```

### 根因结论

**证据不足**。

现有的 Kubernetes 事实仅能确认应用进入了 `CrashLoopBackOff` 状态，其直接机制是 **Liveness 探针超时 (fact-2d671e924d1a)** 后触发了 **进程终止与退避重启 (fact-f0413425855b)**，终止原因为 **Exit Code 137 (fact-32efa01d7695)**。

然而，确认导致 137 的根本原因（如内存是否突破 64Mi 触发 OOM-kill，或 CPU 耗尽导致探针阻塞）的**决定性事实缺失**。缺少以下维度的观测：
1.  **Memory Metrics**：确认应用进程在 14:37 左右是否真实触及 64Mi 的物理内存上限。
2.  **CPU Metrics**：确认是否存在严重的 CPU CFS Throttling 导致探针逻辑无法在限期内完成。

在缺乏这些硬性监控数据支持的情况下，无法断定是资源限制、代码死锁还是节点底层驱逐导致了 137 信号。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.5s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-v17/workload: 53.1s (Evidence 40.1s, RCA 12.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
