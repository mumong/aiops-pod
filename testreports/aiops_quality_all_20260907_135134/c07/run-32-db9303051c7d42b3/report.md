## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器持续以非零退出码退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-07/workload-dff5cbc6b-fkzvn` 容器 `app` 状态 `CrashLoopBackOff`，最后一次终止原因 `Error` (fact-5fd590a77def) | 确认异常实体及状态 |
| 2 | K8s Event | Kubernetes | `Warning BackOff 4m33s (x288 over 69m)` kubelet 频繁重启失败容器 (fact-f053e09875b4) | 证实重启循环已持续较长时间 |
| 3 | K8s State | Kubernetes | 容器退出码 `78` (fact-3ca66fd3cb09)；重启计数 `18` 次 (fact-6e6196f755cf) | 提供进程终止的具体退出码 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 值为 `1` (labels: `reason=Error`, fact-0da696424a3d) | 从监控侧独立确认终止原因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (labels: `reason=CrashLoopBackOff`, fact-8d9c6f11c833) | 从监控侧独立确认 Pod 等待状态 |
| 6 | Logging | Elasticsearch | 日志模式 `CONFIG_MISSING` (http_status: 500, path: /work)，出现 11 次，时间跨度 `14:57 - 15:44` (fact-1dc34210d4bd) | 提供应用层面的错误上下文 |
| 7 | Tracing | Tempo | Span `GET /work` 返回 HTTP 500，属性 `aiops.observed_mode: config_missing_exit`，trace_id `50a6abba43d3322e8431773d1f1331d3` (fact-15f649b57edf) | 链路追踪与日志模式及关联的 trace_id 一致 |

**证据链说明**：
1-5 号证据在 K8s 和 Metrics 层面共同确立了 `CrashLoopBackOff` 及 `Error` 终止状态，且提供了退出码 `78`。
6 号日志证据引入了 `CONFIG_MISSING` 模式，解释了错误性质。
7 号 Tracing 证据中的 `trace_id` 与日志聚合中的 trace_id 一致，证实了应用确实以 HTTP 500 返回并标记了 `config_missing_exit` 模式，从而将进程级终止码（证据 3）与配置缺失（证据 6）关联起来。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置项缺失 → 应用启动/请求处理抛出 CONFIG_MISSING 异常并退出 (code 78) → 容器崩溃 → 触发 Back-off 重启
```

### 根因结论

**已确认根因：应用配置缺失 (CONFIG_MISSING)**

证据链（证据 6、7）明确显示应用在处理请求或启动时抛出了 `CONFIG_MISSING` 错误，并返回 HTTP 500 状态码及 `config_missing_exit` 标记；证据 3 显示的退出码 78 证实了进程的致命终止。这些应用层面的错误直接导致了 K8s 层面容器以 `Error` 终止并进入 `CrashLoopBackOff`（证据 1-2、4-5）。

**缺失事实**：具体缺失的配置项名称或键值（unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.4m
├─ 问题定位: 20.8s
├─ 并发证据采集: 590.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 590.6s (Evidence 581.5s, RCA 9.0s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
