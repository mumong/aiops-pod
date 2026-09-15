## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 应用程序在启动后尝试访问 /work 路径时因缺少关键配置 (CONFIG_MISSING) 而返回 HTTP 500 错误，随后应用进程以退出码 78 主动终止进程，触发 Kubernetes 的重启策略并导致 Pod 进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff; `last_exit_code`: 78 | 确认应用进程异常退出并触发 Pod 重启循环 |
| 2 | K8s Event | Kubernetes | `BackOff`: 3m5s (x332 over 77m) restarting failed container app | 证实 Pod 长期处于频繁重启的故障状态 |
| 3 | Logging | ElasticSearch | 日志模式: `CONFIG_MISSING` (http_status: 500, path: /work, service: aiops-lab-workload); 时间范围: 2026-09-10 21:18:32 - 21:45:10 | 确认应用因配置缺失主动报错并终止 |
| 4 | Tracing | Deepflow | 聚合 L7 Flow: 9 次 `GET /work` 返回 `500` (dst_ip: 172.16.104.63); 关联 trace_id: 193f8205c4db895a18b774984e1e0867 等 | 证实 HTTP 请求路径 `/work` 的持续失败 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: 1 (reason: Error); `restart_count`: 19 | 独立监控源确认容器因 Error 退出并重启 |

**证据关联说明：**
1. **代码层报错与系统层重启的闭环**：日志 (证据 #3) 和追踪 (证据 #4) 均指向应用对 `/work` 路径请求返回 `HTTP 500` 且内部报 `CONFIG_MISSING`；这与 K8s 状态 (证据 #1) 中容器以 `exit_code=78` 退出并进入 `CrashLoopBackOff` 直接吻合，证实应用进程在收到配置错误后主动终止了自身。
2. **多维度观测的一致性**：日志与追踪共同覆盖了故障的时间窗口（2026-09-10 晚间），指标 (证据 #5) 确认了异常持续存在（重启已达 19 次）且未恢复，排除了瞬时网络抖动导致 500 的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码中关键配置缺失 (CONFIG_MISSING) → 应用启动后处理 /work 请求返回 HTTP 500 并以退出码 78 退出 → Kubernetes 检测到容器异常退出 (exitCode=78) 并频繁重启 → Pod 进入 CrashLoopBackOff 状态 (restarts=19)
```

### 根因结论

**已确认根因：应用程序因缺失关键配置（日志明确标识为 `CONFIG_MISSING`）导致启动/运行失败。**

该配置缺失导致应用在处理 `/work` 路径的请求时返回 `HTTP 500` 并触发 `exit_code=78` 主动退出（证据 #3, #4, #1）。这一异常退出行为被 Kubernetes 捕获，进而触发 Pod 的重启策略，最终表现为 `CrashLoopBackOff` 状态且持续 77 分钟未恢复（证据 #2, #5）。证据链完整闭合，确认了配置缺失为导致 Pod 无法稳定运行的根本原因。

*(注：具体的 ConfigMap 中缺失的确切 Key 名及退出码 78 的选择逻辑在现有观测中未确认，但不影响对“配置缺失引发应用主动退出”这一根因的判定。)*

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.2s
├─ 并发证据采集: 65.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 65.1s (Evidence 54.4s, RCA 10.6s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
