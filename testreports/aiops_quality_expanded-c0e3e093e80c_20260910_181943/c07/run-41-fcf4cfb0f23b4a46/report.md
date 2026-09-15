## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 应用容器启动后依赖配置缺失（CONFIG_MISSING），导致请求处理返回 HTTP 500 并触发进程退出（exitCode 78），引发 Kubernetes 频繁重启形成 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` `last_terminated_reason` = `Error` | 证明容器进程最近一次以异常状态退出 |
| 2 | K8s State | Kubernetes | Container `app` `last_exit_code` = 78 | 明确进程退出码，指向业务逻辑层级的特定失败 |
| 3 | K8s State | Kubernetes | Container `app` `waiting_reason` = `CrashLoopBackOff` | 反映 Kubernetes 重启退避状态，直接表现为服务不可用 |
| 4 | Logging | Elasticsearch | `CONFIG_MISSING` (http_status: 500, path: `/work`)，发生时间 21:18:32 ~ 21:39:52 | 捕获到应用业务报错，直接揭示退出原因为配置缺失 |
| 5 | Tracing | Tempo | Span `GET /work` 返回 `http.response.status_code: 500`，attribute `aiops.observed_mode: config_missing_exit` | 验证了日志中业务错误的具体来源路径与上下文 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值 = 18 | 量化了因退出导致的高频重启事实 |
| 7 | K8s Config | Kubernetes | Container `resource_limit.memory` = 96Mi, `resource_request.memory` = 24Mi | 排除资源超限 (OOM) 引发退出的可能性 |

**证据印证说明：**
日志 (证据 4) 提供了“配置缺失 (CONFIG_MISSING)”这一直接的业务原因；追踪 (证据 5) 将该原因与具体的 API 路径 (`/work`) 和异常模式 (`config_missing_exit`) 绑定。这两者共同解释了为何容器会收到 HTTP 500 并以退出码 78 (证据 2) 崩溃。由于存在频繁的业务失败 (证据 4 & 5)，导致了 Kubernetes 层面观察到的高频次重启 (证据 6) 与最终的 CrashLoopBackOff 状态 (证据 3)。资源限制 (证据 7) 排除了基础设施资源耗尽的可能。

## 🎯 根因分析 · g1

### 因果链
```text
应用容器依赖配置缺失 (CONFIG_MISSING) → 处理请求 /work 时触发 500 错误 → 进程以 exitCode 78 异常退出 → 容器反复崩溃形成 CrashLoopBackOff
```

### 根因结论
**根因已确认。**
异常组 `g1` 的直接原因是应用代码或运行环境缺少必要的配置项，导致服务在请求处理阶段（路径 `/work`）发生逻辑错误（`CONFIG_MISSING`），进而主动退出进程（exitCode 78）。Kubernetes 根据该退出状态持续尝试重启容器，最终陷入 `CrashLoopBackOff` 循环。
诊断支持：日志维度明确记录了 `CONFIG_MISSING` 业务错误 (fact-32ac7a93bc60 等)，追踪维度确认了该错误发生在 HTTP 500 响应中 (fact-1475da77a435)，K8s 状态与 Metrics 一致证实了进程异常退出及高频重启现象 (fact-07ad001a469d, fact-44e3bfc28ee7, fact-3bef78811c44)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 15.6s
├─ 并发证据采集: 65.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 65.5s (Evidence 57.8s, RCA 7.5s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
