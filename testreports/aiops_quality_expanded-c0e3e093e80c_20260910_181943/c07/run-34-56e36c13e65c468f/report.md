## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，应用进程在启动并响应HTTP请求后直接退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 54s (x264 over 60m) kubelet Back-off restarting failed container app` | 确认 Pod 进入 CrashLoopBackOff 状态并持续重试重启。 |
| 2 | K8s State | kubernetes | `exit_code: 78` | 指示应用进程以特定非零码异常终止，需结合日志确定原因。 |
| 3 | Logging | elasticsearch | `pattern: {event: "http_request", level: "error", message: "CONFIG_MISSING", http_status: 500, path: "/work"}` (发生 8 次) | 直接定位失败原因为配置缺失 (CONFIG_MISSING)，发生在业务请求路径。 |
| 4 | K8s Event | kubernetes | `message: "ContainersNotReady status: [app]"` | 证实容器因异常退出导致 Pod 状态处于非就绪 (Ready=False)。 |
| 5 | Tracing | tempo | `span: {"name": "GET /work", "attributes": {"aiops.observed_mode": "config_missing_exit", "http.response.status_code": 500}}` | 关联日志与 Trace，确认异常由应用内部配置缺失导致并直接返回 HTTP 500。 |

**证据链说明**：
Kubernetes 事件 (Fact 1) 确认了重启现象，Exit Code 78 (Fact 2) 与 ELK 日志 (Fact 3) 的 `CONFIG_MISSING` 模式互为印证，说明应用非系统资源受限退出，而是业务逻辑层面的配置缺失。Tracing 记录 (Fact 5) 进一步将这一错误锁定在应用处理请求的具体路径上，证实了退出是由应用主动抛出异常引起的。

## 🎯 根因分析 · g1

### 因果链

```text
应用初始化/运行检查缺失必要配置 (Fact 3, Fact 5)
	↓
应用抛出 CONFIG_MISSING 致命异常
	↓
进程以退出码 78 终止 (Fact 2)
	↓
Kubernetes 判定 CrashLoopBackOff 并持续重启 (Fact 1)
```

### 根因结论

已确认根因为**应用因缺少必要配置（触发 `CONFIG_MISSING` 错误）而退出**。

应用代码在执行过程（如初始化或处理请求 `/work`）中检测到配置缺失，主动抛出异常并返回 HTTP 500，随后进程以退出码 `78` 终止。Kubernetes 检测到容器异常退出后，触发 `CrashLoopBackOff` 机制并不断进行重启，导致了 Pod 的持续不健康状态。

目前已知缺失的 ConfigMap 为 `workload-code`，但尚无法确认其中具体缺失的键名或内容（受限于未获取到的 ConfigMap 详情），仅能确认是此应用侧配置缺失导致了异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.6s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 55.2s (Evidence 44.9s, RCA 10.1s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
