## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl处于CrashLoopBackOff状态，无法就绪 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-sjvxl` (x110 over 25m) | 证明应用持续处于崩溃重启循环中 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.last_terminated_reason`: Error | 确认当前 Pod 运行状态及上一次容器终止原因 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 78 | 确定容器异常退出的具体错误码，指向应用层配置问题 |
| 4 | Logging | elasticsearch | Pattern `CONFIG_MISSING` 出现 8 次，时间窗口 20:31:25 ~ 20:52:25，均关联 `/work` 路径且 `http_status: 500` | 直接记录应用层检测到的根本错误类型 |
| 5 | Tracing | tempo | Trace ID `c6ffc9838e9b589ff9c084aa2ea07c2f` 显示 `aiops.observed_mode: config_missing_exit`，状态码 500 | 提供请求级轨迹证据，与日志模式在语义上完全一致 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (CrashLoopBackOff) 和 `restarts_total` 均为 1 和 9 (单次快照) | 从监控指标侧印证 Pod 持续等待与高重启频率 |

上述证据相互印证：K8s 状态（#1, #2）确认了容器反复退出的事实，错误码 78（#3）提供了退出性质的线索。日志中明确的 `CONFIG_MISSING` 错误（#4）以及带有相同语义标识 `config_missing_exit` 的 Tracing Span（#5）共同锁定了应用因配置缺失而主动终止的具体原因。监控指标（#6）进一步从宏观层面确认了异常状态的存在。

## 🎯 根因分析 · g1

### 因果链

```text
容器应用启动后无法找到必需配置（CONFIG_MISSING） → 检测到配置错误并返回 HTTP 500 终止请求 → 容器以退出码 78 异常退出 → 触发 K8s 重启策略并进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：**应用启动后无法找到必需配置项或环境变量（标识为 CONFIG_MISSING），导致应用以非零退出码（78）主动终止。**

该根因由以下事实支撑：
1. 日志与 Trace 明确记录了 `CONFIG_MISSING` 错误（对应证据 #4, #5）；
2. 容器退出码为 78（对应证据 #3），与日志模式相符；
3. K8s 层面的 `CrashLoopBackOff` 状态和 `Error` 终止原因（对应证据 #1, #2）是上述应用层异常导致的直接结果。

**未知信息**：日志和 Tracing 仅指明了缺失配置的通用类型（CONFIG_MISSING），未能提供具体缺失的是哪个具体的配置项键名或环境变量名称。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.6s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 55.2s (Evidence 44.4s, RCA 10.6s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
