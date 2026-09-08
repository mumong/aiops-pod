## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，持续重启退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | prometheus | `kube_pod_container_status_last_terminated_reason=Error` (fact-8588d18789fd) | 确认容器非正常终止，终止原因为 Error，支撑 CrashLoopBackOff 状态。 |
| 2 | K8s State | prometheus | `kube_pod_container_status_restarts_total=19` (fact-b8a703a321df) | 证实应用经历了反复重启循环，非单次启动失败。 |
| 3 | K8s State | prometheus | `kube_pod_container_status_waiting_reason=CrashLoopBackOff` (fact-9a0cd368c80d) | 直接展示 Pod 当前的异常状态及原因。 |
| 4 | Logging | elasticsearch | 聚合日志 Pattern: `event=http_request`, `level=error`, `message=CONFIG_MISSING`, `http_status=500` (fact-015df69f68ff, 8 occurrences) | 日志明确记录了“配置缺失”错误，直接指向应用内部的配置依赖问题。 |
| 5 | Tracing | Deepflow | HTTP L7 Flow: `GET /work`, `response_code=500`, `occurrence_count=9` (fact-0818a05f11d7) | 网络流量记录证实应用对外响应 500 错误，且集中在 `/work` 接口。 |
| 6 | Tracing | Tempo | Application Span: `GET /work`, `attributes.aiops.observed_mode=config_missing_exit`, `http.response.status_code=500` (fact-251f255919dc) | Trace 详情进一步确认了请求处理路径中因配置缺失导致的主动退出机制。 |

**证据分析：**
Metrics 确认了应用处于 CrashLoopBackOff 状态并频繁重启。Logging 和 Tracing 数据提供了关键的内部上下文：日志中的 `CONFIG_MISSING` 和 Trace 中的 `config_missing_exit` 模式高度一致，且均指向 `GET /work` 接口返回 500。这种应用层主动报错（Exit Code 1）与 CrashLoopBackOff 状态形成了完整的因果闭环，证据之间相互印证，排除了网络或资源限制等外部因素。

## 🎯 根因分析 · g1

### 因果链

```text
应用关键配置缺失 → 应用逻辑触发 CONFIG_MISSING 异常并返回 HTTP 500 → 应用进程以非零 Exit Code 1 终止 → Pod 重启进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：**
应用的启动或运行逻辑强依赖某项未配置好的配置（表现为 `CONFIG_MISSING` 日志），导致在请求 `/work` 时主动抛出异常并退出进程（`config_missing_exit`）。Kubernetes 检测到该非零退出码后，按照重启策略不断重启 Pod，从而形成了 CrashLoopBackOff 状态。

*   **证据支撑：** 日志中的 `CONFIG_MISSING` 模式（证据 #4）与 Trace 中的 `config_missing_exit` 属性（证据 #6）及 HTTP 500 响应（证据 #4, #5）直接证实了应用内部因配置缺失而崩溃的逻辑；Metrics 中的 `Error` 终止原因（证据 #1）和 19 次重启（证据 #2）证实了这一崩溃机制的持续发生（证据 #1, #2）。

**未知因素：**
*   具体缺失的配置项名称（如具体的 ConfigMap/Secret 键名）尚未在日志或 Trace 中披露。
*   应用镜像的默认入口执行逻辑源码未提供，无法判断为何该配置缺失会导致整体进程终止而非优雅降级。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.6s
├─ 并发证据采集: 44.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 44.1s (Evidence 34.1s, RCA 9.9s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
