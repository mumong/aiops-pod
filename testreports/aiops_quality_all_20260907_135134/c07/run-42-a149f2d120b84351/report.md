## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Application configured with FAILURE_MODE=config_missing_exit causes the HTTP server (server.py) to log CONFIG_MISSING error, return HTTP 500 on /work requests, and exit with code 78, triggering Kubelet restart loop (CrashLoopBackOff). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: "CrashLoopBackOff"`, `restart_count: 21`, `container.last_terminated_reason: "Error"` | 确认 pod `workload-dff5cbc6b-fkzvn` 处于反复重启的故障状态。 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-fkzvn_aiops-case-07(bffd1771-cb0a-4bea-96ed-0a46e5b3a923)` | Kubelet 正在实施指数退避重启策略，佐证崩溃循环正在发生。 |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 78` | 容器以退出码 78 异常终止，该非零退出码直接触发了重启逻辑。 |
| 4 | Logging | Elasticsearch | `pattern: CONFIG_MISSING, http_status: 500, path: /work`, 出现 8 次 (如 `fact-3cad91ff2a13`) | 应用日志明确记录由于配置缺失 (`CONFIG_MISSING`) 导致内部报错，并返回 HTTP 500。 |
| 5 | Tracing | Deepflow/Tempo | `flow: GET /work -> 500 (occurrence: 9)`, `app_span: aiops.observed_mode: config_missing_exit`, `trace_id: 7ed664affe6fdd8e75610015d3c8e3a3` | 流量与链路数据证实应用接收到 `/work` 请求后直接返回 500 并退出，且运行模式确认为 `config_missing_exit`。 |
| 6 | Metrics | Prometheus | `kube_pod_container_status_last_terminated_reason=Error`, `kube_pod_container_status_waiting_reason=CrashLoopBackOff` | 监控指标从系统层面确认了异常终止原因为 Error，等待原因为 CrashLoopBackOff。 |

**证据印证说明：**
应用代码因配置缺失 (`config_missing_exit`) 主动处理请求失败并返回 500，随后以退出码 78 退出进程（证据 3, 4, 5）。Kubernetes 侦测到非零退出码后触发重启（证据 1），并在达到重试限制后进入 `CrashLoopBackOff` 状态（证据 1, 2, 6）。日志中记录的 `CONFIG_MISSING` 与追踪中的 `config_missing_exit` 模式完全一致，形成了从应用层行为到容器层状态的完整因果闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行模式配置为 FAILURE_MODE=config_missing_exit → 处理请求时抛出 CONFIG_MISSING 错误并返回 500 → 进程主动以退出码 78 终止 → Kubelet 检测非零退出码触发重启，最终导致 Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：应用 `workload-dff5cbc6b-fkzvn` 被显式配置为 `FAILURE_MODE=config_missing_exit` 模式。在此模式下，应用代码在接收到 `/work` 请求时，因检测到配置缺失主动触发 `CONFIG_MISSING` 错误，返回 HTTP 500 状态码，并随后以退出码 `78` 终止进程。这种设计导致容器不断异常退出，进而引发 Kubernetes 的指数退避重启机制，使得 Pod 持续处于 `CrashLoopBackOff` 状态 [证据 3, 4, 5, 1]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 22.7s
├─ 并发证据采集: 68.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 68.6s (Evidence 58.0s, RCA 10.4s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
