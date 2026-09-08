## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | Error | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器 `app` 反复退出 (exitCode=2)，表现为 HTTP 请求处理期间进程非预期终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `phase=Running`，但 `Ready=False` (reason: `ContainersNotReady`)，`restart_count=19` | 确认容器处于非预期的反复终止/重启循环中 |
| 2 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`，`container.last_terminated_reason=Error`，`exit_code=2` | 直接证明容器因内部错误被系统强制终止，而非资源驱逐或配置失败 |
| 3 | Logging | Elasticsearch | 出现 4 次 `http_request` 模式错误日志：`level=error, message="runtime process exiting", http_status=500, path="/work"` (时间窗: 13:23 - 13:44) | 提供应用层进程退出的确切触发时机和状态，定位故障请求路径 |
| 4 | Tracing | Tempo | Span `d37042c083146b7c0693f494aea075f8`: `GET /work` 返回 `status_code=500`，且 `aiops.observed_mode="runtime_exit"`，时间戳 13:44:33.907 | 将网络层 500 响应与进程即时退出的行为建立因果关联 |
| 5 | K8s Config | Kubernetes | CPU limit `200m` (Request `20m`)，Memory limit `96Mi` (Request `24Mi`) | 资源上限合理，无 OOMKilled 特征（配合 Metrics 事实确认） |
| 6 | Metric | Prometheus | `container_memory_usage_bytes` 当前值 `741376` bytes (~724KB)，`container_cpu_usage_seconds_total` 为 `12.24` | 实际资源使用远低于 96Mi/200m 上限，排除资源超限导致的问题 |

**证据综合说明：**
Kubernetes 状态与 Metrics 数据互相印证，排除了集群资源不足或 Pod 被 OOM Kill 的可能性；日志 (Logging) 捕获到的 `http_status=500` 与 Trace (Tracing) 中的 `status_code=500` 完全一致，且 Trace 中的 `aiops.observed_mode="runtime_exit"` 属性精准解释了为何应用日志显示 `runtime process exiting` 并直接导致容器以 `exitCode=2` 崩溃，证据链闭环指向应用层逻辑故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑异常或依赖故障 → GET /work 请求触发内部未捕获错误(500)并终止进程 → 容器 exitCode=2 退出并触发 BackOff 重启 → Pod CrashLoopBackOff (Ready=False)
```

### 根因结论

已确认根因为 **应用层逻辑异常导致进程退出**。
应用在处理 `GET /work` 请求时发生未捕获的内部错误（日志记录 `runtime process exiting`），直接导致应用进程非预期终止。由于当前采集事实中缺失具体的应用错误堆栈或异常类型（Unknowns 字段确认），无法区分是确定性代码 Bug 还是偶发性下游依赖故障，但故障的根本触发点确认为应用自身的 500 逻辑错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.8s
├─ 并发证据采集: 78.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 78.4s (Evidence 65.4s, RCA 12.8s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
