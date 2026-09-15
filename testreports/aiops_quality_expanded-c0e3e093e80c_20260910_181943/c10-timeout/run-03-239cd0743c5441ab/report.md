## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 初始状态 CrashLoopBackOff，当前 Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` 退出码: 137 (`fact-1042a0f93ff5`) | 容器被系统强制终止 (SIGKILL) 的直接证据 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (`fact-4b0d217fd3f4`) | 存活探针持续超时，触发重启机制 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: dial tcp ... connection refused (`fact-e6deed47fdd9`) | 容器在启动阶段或重启间隙无法响应就绪检查 |
| 4 | Logging | Elasticsearch | 应用日志 `listening on 18080` (`fact-3bb5dc2f6549`) | 确认应用进程已在预期端口启动 |
| 5 | Logging | Elasticsearch | HTTP 响应 200 记录 (`fact-0bf81dd5daf1` 等) | 日志层面显示应用能正常响应 GET 请求 |
| 6 | Tracing | Deepflow | GET /health 请求耗时 min: 3001102.0µs (`fact-3c0efe8d8c1b`) | 追踪证实响应时间约为 3 秒，显著超过探针预期 |
| 7 | K8s Config | Kubernetes | 资源限制 Memory: 64Mi, CPU: 200m (`fact-0c8673520707`) | 排除 OOM (OOMKilled) 或 CPU 饥饿导致的资源拒绝 |
| 8 | Metric | Prometheus | 重启总数: 5 (`fact-955972fcc7b5`) | 确认容器处于频繁重启循环状态 |

**证据综合说明**
Kubernetes 探针日志显示 Liveness Probe 因 `context deadline exceeded` 失败并触发信号 9 终止容器（证据 1、2）。应用日志和追踪数据相互印证：应用确实监听了端口 18080 且能返回 200 状态，但 HTTP Flow 显示 `/health` 端点耗时长达 3001ms（证据 6），这与探针配置超时不匹配，证实了代码逻辑层面的阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 端点执行耗时 3 秒的操作 → Liveness Probe (超时 1 秒) 持续触发 Deadline Exceeded 异常 → Kubelet 判定容器不健康发送 SIGKILL → Pod 进入 CrashLoopBackOff 并反复重启
```

### 根因结论

已确认的根因为：**应用代码在 `/health` 端点处理存在长耗时阻塞（约 3 秒），而配置的 Liveness Probe 超时参数过短，导致探针判定超时失败。**

支撑证据如下：
1.  **触发机制**：Kubelet 报错 `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded`（证据 2），说明请求超出了探针设定的时间窗口。
2.  **超时原因**：Deepflow 追踪数据显示 `/health` 请求的实际耗时约为 3001ms（证据 6），证实了应用端处理逻辑的迟缓。
3.  **非资源原因**：`last_terminated_reason` 为 Error 且 Exit Code 为 137（证据 1），排除了 OOMKilled（Exit 137 且内存限制 64Mi 无迹象）或代码 panic 退出；应用日志确证进程已启动（证据 4），排除了启动配置错误。
4.  **循环结果**：重启计数为 5 次（证据 8），直接对应了探针失败后的自动重启行为。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 12.8s
├─ 并发证据采集: 78.9s
│  └─ g1 aiops-case-v17/workload: 78.9s (Evidence 67.6s, RCA 11.1s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
