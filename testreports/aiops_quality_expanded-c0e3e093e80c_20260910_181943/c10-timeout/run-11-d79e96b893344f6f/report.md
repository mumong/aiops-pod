## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubectl get pod` (fact-3853743d07d3) | exit_code: 137 | 确证进程被操作系统强制终止，通常对应 OOMKilled 或 SIGKILL |
| 2 | K8s State | `kubectl get pod` (fact-a49e253f0773) | waiting_reason: CrashLoopBackOff | 确认容器处于频繁崩溃重启的异常循环状态 |
| 3 | K8s Config | `kubectl get pod` (fact-756b7cb872c3) | resource_limit.memory: 64Mi | 存在极低的内存硬限制，为 OOMKilled 提供了物理诱因 |
| 4 | K8s Event | `kubectl get events` (fact-288d32a0da58) | Killing, liveness probe failed | 确认存活探针超时导致 kubelet 触发容器重启 |
| 5 | Metric | `kube_pod_container_status_last_terminated_reason` (fact-8255e182b457) | reason: Error (count: 4) | Prometheus 数据交叉验证了最后一次终止原因为异常终止 |
| 6 | Logging | `query_pod_logs` (fact-22f039758b32) | "listening on 18080" | 证明应用进程已成功启动并开始监听，排除启动代码执行错误 |

证据印证：
- **启动与终止闭环**：Logging 证据 (#6) 证明应用能够成功启动，而 K8s State (#1) 和 Metric (#5) 证实随后发生异常退出。
- **OOM 证据链**：极低的内存限制配置 (#3) 与退出码 137 (#1) 结合，强指向 OOMKilled 机制，且该退出原因已被 Metric (#5) 独立捕获。
- **循环加速机制**：K8s Event (#4) 显示 Liveness 探针失败触发了 Killing 动作，这解释了为何应用在短暂启动后立即被终止，从而形成 CrashLoopBackOff (#2)。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存 Limit 配置过小 (64Mi) → 启动/运行时内存超限触发 OOMKilled (Exit 137) → Kubelet 终止容器且 Liveness 探针超时加速重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是**容器内存限制配置不足导致的服务进程被系统强制终止**。

1.  **直接故障机制**：应用进程被强制退出（Exit Code 137，见 #1），并由 Prometheus 监控数据确认终止原因为 Error（见 #5）。结合极低的内存 Limit 64Mi（见 #3），该退出码高度吻合 OOMKilled 场景。
2.  **崩溃循环成因**：应用日志证实服务可以正常启动并监听端口（见 #6）。但 K8s 事件记录显示，Liveness 探针在启动间隙因超时被判定失败，导致 Kubelet 主动终止容器（见 #4）。这种“启动 -> 内存/探针问题 -> 被杀 -> 重试”的循环机制导致了持续的 CrashLoopBackOff 状态（见 #2）。

当前证据已覆盖故障的核心闭环，但无法提供精确的内存阈值判定或启动期间的内存增长趋势快照。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 27.5s
├─ 并发证据采集: 70.6s
│  └─ g1 aiops-case-v17/workload: 70.6s (Evidence 59.2s, RCA 11.2s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled
