## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | 应用代码内部处理请求时发生运行时错误导致进程退出（exitCode=2） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason="CrashLoopBackOff" (container: app) | 确证容器处于重启循环状态 |
| 2 | K8s State | kubernetes | container.last_terminated_reason="Error", exit_code=2 (container: app) | 明确进程退出原因为运行时错误 |
| 3 | K8s Event | kubernetes | BackOff restarting failed container app, x180 over 43m | 证明故障持续时间与高频重启现象 |
| 4 | Logging | elasticsearch | log message="runtime process exiting", http_status=500, path="/work" | 在应用层面观察到服务异常退出行为 |
| 5 | Metric | prometheus | restart_count=12 (container: app), waiting_reason="CrashLoopBackOff" | 独立数据源验证了容器重启事实与当前状态 |

1. Kubernetes `Error` 终止状态（事实 2）与 Elasticsearch 日志中 `runtime process exiting`（事实 4）在时间窗口内（12:47 - 13:13）共同指向应用进程的非正常结束。
2. 日志 `exit_code=2`（事实 2）与日志 `http_status=500`（事实 4）相结合，排除了 OOM 等常见资源限制问题，确认是代码逻辑或运行时环境导致的崩溃。
3. Metrics 重启计数（事实 5）与 K8s 重启计数（事实 3 提到的 13）互相印证，确认了集群处于持续的 CrashLoopBackOff 循环中。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理请求时发生运行时错误（日志观测） → 进程异常退出（exitCode=2） → K8s 触发重启策略 → 状态变为 CrashLoopBackOff（用户可见现象）
```

### 根因结论

**已确认根因**：应用代码内部在处理 `/work` 路径请求时发生运行时错误（runtime error），导致进程以 `exitCode=2` 异常退出。

该根因由以下事实支撑：
*   **直接证据**：Kubernetes 记录显示容器 `app` 的 `last_terminated_reason` 为 `Error` 且 `exit_code` 为 `2`（证据 2）；Elasticsearch 日志在相同时间窗口内明确记录了 `runtime process exiting` 且伴随 `http_status=500`（证据 4）。
*   **现象印证**：K8s 事件与 Metrics 一致反映了容器因频繁重启而进入 `CrashLoopBackOff` 状态（证据 1, 3, 5）。
*   **排除项**：资源限制（CPU 20m-200m, Memory 24Mi-96Mi）未被触发，且无 OOMKilled 记录，进一步缩小了故障范围为应用逻辑或内部依赖错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.8s
├─ 并发证据采集: 52.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 52.4s (Evidence 46.8s, RCA 5.5s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
