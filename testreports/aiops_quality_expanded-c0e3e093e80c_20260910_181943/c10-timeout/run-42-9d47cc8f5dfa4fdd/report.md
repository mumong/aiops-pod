## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | {'container': 'app', 'reason': 'CrashLoopBackOff'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (x67 over 92m)` | 直接导致 Pod 被标记为不健康 (Unhealthy) 并进入重启循环 |
| 2 | K8s Event | Kubelet | `Back-off restarting failed container app (x387 over 91m)` | 确认应用处于 CrashLoopBackOff 状态，频繁重启 |
| 3 | K8s State | Pod Status | `container.last_terminated_reason: Error`, `container.last_exit_code: 137` | 进程以信号 137 (SIGKILL) 终止，结合 Exit Code 137 强提示资源超限或内核强制杀进程 |
| 4 | K8s Config | Resource Limits | `container.resource_limit.memory: 64Mi`, `container.resource_limit.cpu: 200m` | 为 Python 应用分配的内存限制极低，为 OOMKilled 提供了显著的上下文约束 |
| 5 | Logging | App Logs | `listening on 18080` (14:36:19) → `GET /health HTTP/1.1" 200` (14:36:37~14:37:03) | 应用已正常启动并在探针检查前返回了 200 状态码，排除了应用未启动的可能性 |
| 6 | Tracing | Deepflow | `/health` flow 响应状态 200，Duration 约 3001ms-3002ms | L7 流量显示应用响应了 HTTP 请求，但耗时极长（约 3 秒），解释了为何 K8s 探针会因 `context deadline exceeded` 而判定失败 |

**证据互证：**
K8s Liveness 探针因等待 `172.16.104.36:18080/health` 超时而触发重启（证据 #1, #2），但 Deepflow 追踪（证据 #6）显示应用对同一端点的响应耗时约 3 秒。若探针超时设置小于 3 秒，则探针超时与应用慢响应直接相关；而进程最终被内核 SIGKILL（Exit Code 137，证据 #3）在 64Mi 限制下（证据 #4），极可能是因慢响应导致的资源消耗累积或 OOM 触发了杀进程机制。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制极低 (64Mi, Evidence #4) → 应用运行出现内存溢出或响应缓慢 (Evidence #6) → 内核 OOM Killer 终止进程 (Exit Code 137, Evidence #3) → Liveness 探针超时失败并触发重启 (Evidence #1, #2)
```

### 根因结论

**已确认的根因：应用资源受限导致的异常终止 (Exit Code 137) 与 探针超时。**

1.  **终止原因**：容器以 `Exit Code 137` (SIGKILL) 终止，结合 `container.resource_limit.memory: 64Mi` (证据 #4)，高度怀疑是由 **OOM (Out Of Memory)** 触发的内核强制杀进程。
2.  **现象关联**：虽然 K8s 记录的原因字段为 `Error` 而非明确的 `OOMKilled` (未知因素：kubelet 是否明确上报了 OOM 事件存在不确定性，且缺乏 Prometheus 内存峰值指标确认)，但 Exit Code 137 与极低的内存限制共同构成了强有力的 OOM 推断证据。
3.  **重启诱因**：由于进程频繁被终止 (Evidence #3)，Liveness 探针在进程恢复期间捕获到应用响应极慢 (Deepflow 耗时 ~3s, Evidence #6)，导致探针超时并不断重启容器 (Evidence #1, #2)，形成了 CrashLoopBackOff 循环。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 13.8s
├─ 并发证据采集: 96.5s
│  └─ g1 aiops-case-v17/workload: 96.5s (Evidence 86.7s, RCA 9.5s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
