## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error` | 证实应用容器非正常退出 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 证实容器因频繁重启进入等待状态 |
| 3 | Logging | Elasticsearch | `pattern: CONFIG_MISSING, http_status: 500` | 提供应用启动/请求失败的直接错误原因 |
| 4 | Tracing | Tempo | `trace_id: 64132b2c9d9b8077c1ac955acb517247, attributes: aiops.observed_mode=config_missing_exit, http.response.status_code: 500` | 通过 Trace 确认请求失败与 `config_missing_exit` 模式直接关联 |
| 5 | K8s State | Kubernetes | `container.last_exit_code: 78` | 提供进程退出的具体代码 |
| 6 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 排除资源硬限制导致的 OOM |
| 7 | Metric | Prometheus | `reason: CrashLoopBackOff, value: 1` | 交叉验证容器当前的 CrashLoopBackOff 状态 |

**证据说明：**
日志中的 `CONFIG_MISSING` 错误（#3）与 Trace 数据中 `aiops.observed_mode=config_missing_exit` 的属性（#4）相互印证，明确指向应用程序内部因缺失配置而主动终止的逻辑。Kubernetes 侧记录的 `ExitCode=78`（#5）和 `CrashLoopBackOff`（#2）是该应用终止行为在集群层面的直接体现。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺失关键配置 → HTTP 500 错误并记录 CONFIG_MISSING → 进程以 exitCode=78 终止 → CrashLoopBackOff (restarts=12)
```

### 根因结论

已确认根因为**应用程序启动或处理请求时缺失关键配置（CONFIG_MISSING）**。该问题直接导致应用抛出 HTTP 500 错误并异常退出（ExitCode 78），进而触发 K8s 的容器重启机制，最终表现为 `CrashLoopBackOff` 状态。

决定性证据链：
1. **Logging (证据 #3)** 和 **Tracing (证据 #4)** 均一致显示应用内部发生了 `CONFIG_MISSING` 错误。
2. **K8s State (证据 #1, #2, #5)** 证实了进程因错误终止（ExitCode 78）并陷入重启循环，且排除了 OOM 等资源限制因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 10.2s
├─ 并发证据采集: 83.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 83.7s (Evidence 73.5s, RCA 10.0s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
