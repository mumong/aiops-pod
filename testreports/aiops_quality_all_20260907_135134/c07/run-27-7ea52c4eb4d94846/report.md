## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用代码因缺少必需配置项抛出 CONFIG_MISSING 错误，触发 HTTP 500 响应并导致进程以退出码 78 终止，进而引发 Kubernetes 持续的 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `last_terminated_reason`: "Error", `last_exit_code`: 78 | 证明容器因应用错误（非资源超限）被 K8s 终止 |
| 2 | K8s Event | kubernetes | `Back-off restarting failed container app` (持续 52 分钟, x221 次) | 记录 CrashLoopBackOff 状态的长期持续性 |
| 3 | K8s Config | kubernetes | `resource_limit.memory`: "96Mi", `resource_limit.cpu`: "200m" | 排除 OOMKilled 或 CPU Throttling 作为直接终止原因 |
| 4 | Logging | elasticsearch | 8 条 `CONFIG_MISSING` 错误日志，HTTP 状态码 500，路径 `/work` | 定位终止的直接诱因：应用层配置缺失 |
| 5 | Tracing | deepflow | 9 个等效 Flow，GET `/work` 返回 500，耗时 4.9ms-20ms | 验证终止状态与异常请求之间的因果关系 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 持续为 1 (`reason: Error`)，`restarts_total` 从 2 升至 14 | 量化重启频次与异常终止状态 |

证据链表明：`LOGGING` 维度的 `CONFIG_MISSING` 错误与 `TRACING` 维度的 500 响应直接吻合，解释了应用为何以 `exit_code: 78` 退出；`K8s STATE` 的 `Error` 状态排除了资源耗尽，而 `K8s EVENT` 和 `METRIC` 证实了这一逻辑错误触发了 Kubernetes 持续的重启与退避机制。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码缺少必需配置项 (Logging/Tracing) → 抛出 CONFIG_MISSING 并返回 HTTP 500 → 进程以退出码 78 终止 (K8s State) → 触发 K8s CrashLoopBackOff 机制 (K8s Event/Metric)
```

### 根因结论

已确认的根因是应用代码因缺失必需配置项抛出 `CONFIG_MISSING` 错误，导致业务请求失败（HTTP 500）并引发进程异常退出（退出码 78）（见证据 #1, #4, #5）。这一状态被 Kubernetes 识别为失败（`Error`），进而触发了观察到的 CrashLoopBackOff 现象（见证据 #2, #3, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 23.4s
├─ 并发证据采集: 59.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 59.9s (Evidence 51.0s, RCA 8.8s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-oomkilled, pod-crashloop-runtime
