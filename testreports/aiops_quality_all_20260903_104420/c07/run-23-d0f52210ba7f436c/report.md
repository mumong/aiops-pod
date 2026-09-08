## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，重启次数为 12，退出码为 78。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 78` | 终止状态：应用进程非正常退出（错误码 78 通常表示配置错误） |
| 2 | K8s Event | Kubernetes | `BackOff 5m0s restarting failed container=app pod=...` | 故障现象：Kubelet 频繁重启失败，已进入退避等待阶段 |
| 3 | Logging | Elasticsearch | `http_request error CONFIG_MISSING path=/work status=500` (Pattern, 发生 8 次, 2026-09-03T14:10:55 至 14:31:43) | 故障原因：应用在处理请求时明确报出“配置缺失”错误 |
| 4 | Tracing | Tempo | `GET /work response_code=500` (trace_id: `9e99fbd922a97ca99308339b3fbad526`, observed_mode: `config_missing_exit`) | 故障原因：通过分布式追踪确认 500 错误由应用逻辑层因配置缺失主动返回 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=Error`, `restarts_total=12` | 故障规模：确认应用因 Error 状态被重启，累计次数 12 |
| 6 | K8s State | Kubernetes | `container.last_terminated_reason: Error` | 终止原因：与 Metrics 数据一致，证实应用层报错退出 |

**证据印证说明：**
- **Kubernetes 状态 (事实 #1, #2, #6)** 证实容器反复异常退出，退避行为（#2）表明重启未解决根本问题。
- **日志与追踪 (事实 #3, #4)** 直接指向应用内部逻辑故障，具体表现为请求处理时检测到配置缺失并返回 HTTP 500。
- **Metrics (事实 #5)** 提供了全局视角的佐证，其反映的 `Error` 退出原因与 K8s 事件及应用日志完全对应。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺少必要配置文件 → 启动后接收请求检测缺失返回 500 → 应用进程以 exitCode 78 终止 → Pod 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用程序因**缺失必要的配置文件（CONFIG_MISSING）**导致启动失败或无法正常运行。

证据链支撑：
1.  **直接证据**：Elasticsearch 日志（事实 #3）明确显示 `CONFIG_MISSING` 错误模式，且伴随 HTTP 500 响应。
2.  **应用行为佐证**：Tempo 追踪（事实 #4）展示了 `GET /work` 请求返回 500，且应用特征标记为 `config_missing_exit`，证实该 500 错误并非后端异常，而是应用因配置问题主动终止服务。
3.  **系统结果匹配**：Kubernetes 记录退出码为 78（事实 #1），该退出码在容器应用中常用来指示配置或参数错误，与 `CONFIG_MISSING` 的根因逻辑一致。
4.  **持续性**：Kubelet 的 BackOff 事件（事实 #2）表明尽管容器不断重启，但配置缺失的问题始终未解决，导致持续失败。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 23.5s
├─ 并发证据采集: 97.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 97.6s (Evidence 88.2s, RCA 9.3s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
