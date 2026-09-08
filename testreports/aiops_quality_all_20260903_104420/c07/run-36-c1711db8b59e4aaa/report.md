## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器 app 每次启动后立即以 exitCode 78 退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `last_terminated_reason` | `Error` | 确认应用非正常退出 |
| 2 | K8s State | `container.last_exit_code` | `exit_code: 78` | 提供具体的退出码，用于关联应用内部异常码 |
| 3 | K8s State | `container.waiting_reason` | `CrashLoopBackOff` | 描述当前处于的重启状态 |
| 4 | Metric | `kube_pod_container_status_last_terminated_reason` | `Error` | 监控视角确认终止原因为 Error，与 K8s 状态一致 |
| 5 | Logging | `CONFIG_MISSING` | `pattern: {"event": "http_request", "level": "error", "message": "CONFIG_MISSING", "http_status": 500, "path": "/work"}` | **决定性证据**：日志中 8 次重复出现配置缺失错误，并伴随 500 状态码 |
| 6 | Tracing | `application_span` | `attributes.aiops.observed_mode: config_missing_exit`, `http.response.status_code: 500`, `trace_id: 65684c8c074b2b13bde640e742613caa` | 链路数据确认了请求因模式 `config_missing_exit` 被拒绝，且关联的 trace_id 与日志聚合中的一致 |

上述证据形成闭环：日志记录了应用明确抛出的 `CONFIG_MISSING` 错误，Tracing 链路确认了应用在处理请求时因该模式返回了 500，且进程随即以 exitCode 78 退出。Metrics 数据仅作为当前崩溃状态的辅助确认。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置文件缺失 (CONFIG_MISSING) → 应用处理请求时主动终止进程 (exitCode 78) → K8s 触发重启策略失败并进入等待 (CrashLoopBackOff) → Pod 处于非就绪状态
```

### 根因结论

已确认的根因为**应用配置缺失**（Fact 5, 6）。
- 日志中出现的 `CONFIG_MISSING` 明确指出了应用层面的具体异常原因；
- `Tracing` 结果中的 `aiops.observed_mode: config_missing_exit` 与日志错误相互印证，确认了应用进程在检测到该条件后主动退出，并直接导致了 `exitCode 78`（Fact 2）和随后的 `CrashLoopBackOff`（Fact 3）。

目前证据不足以确定具体缺失的是哪一个配置文件（如 `config.yaml` 或 `server.conf`）以及其挂载路径。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 23.5s
├─ 并发证据采集: 64.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 64.3s (Evidence 55.8s, RCA 8.3s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
