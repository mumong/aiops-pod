## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason=Error`, `exit_code=2` | 确认容器异常终止状态，排除 OOMKill |
| 2 | K8s Event | Kubernetes | `Warning BackOff` 60s (x315 over 70m) | 证实 CrashLoopBackOff 现象持续存在 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory=96Mi`, `resource_request.memory=24Mi` | 资源限制配置，结合 ExitCode 2 辅助排除 OOM |
| 4 | Logging | Elasticsearch | 模式 `runtime process exiting`, `http_status=500` (4次) | 应用层日志显示 HTTP 请求处理失败并退出进程 |
| 5 | Tracing | Tempo | `span: GET /work`, `http.response.status_code=500`, `aiops.observed_mode: runtime_exit` | 追踪数据将 500 错误与进程退出模式关联 |
| 6 | Tracing | Deepflow | L7 Flow `GET /work` -> `response_code: 500` (5次) | 独立流数据印证 HTTP 500 响应特征 |

**证据关联说明：**
Kubernetes 的 `exit_code=2` 与 Elasticsearch 日志中记录的应用“runtime process exiting”相互印证，说明进程是应用逻辑崩溃而非被系统资源杀手终止。Tempo 追踪数据（`aiops.observed_mode: runtime_exit`）与 Deepflow 流数据共同锁定了 `GET /work` 为触发该崩溃的具体请求，形成了从“应用层 500 报错”到“进程退出”再到“K8s 重启”的完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理 /work 请求时触发未捕获异常 → 进程记录 runtime process exiting 并返回 HTTP 500 → 容器以 Exit Code 2 异常退出 → Kubelet 检测终止并触发 CrashLoopBackOff 重启
```

### 根因结论

**已确认的根因**：应用在处理 `/work` 路径 HTTP 请求时发生未捕获的运行时异常（Exit Code 2），导致容器反复崩溃重启。

**证据支撑**：
1.  **异常触发**：Tempo 和 Deepflow 证据（#5, #6）一致显示 `GET /work` 请求返回 `HTTP 500`，且 `aiops.observed_mode` 指示为 `runtime_exit`。
2.  **异常表现**：Elasticsearch 日志（#4）捕获到同一模式的 `runtime process exiting` 错误。
3.  **系统响应**：Kubernetes 状态（#1, #2）证实容器以 `exit_code=2` 终止，并因频繁重启进入 `CrashLoopBackOff` 状态。

**局限性**：具体的 Python 异常类型（如 `KeyError` 或 `ValueError`）及完整错误堆栈细节缺失（无法获取崩溃前的最后几行日志），但现有事实已足以确认根因为应用代码层面的运行时异常。

---

## 📊 性能统计

```text
├─ 总耗时: 3.8m
├─ 问题定位: 18.6s
├─ 并发证据采集: 198.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 198.3s (Evidence 188.1s, RCA 10.0s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
