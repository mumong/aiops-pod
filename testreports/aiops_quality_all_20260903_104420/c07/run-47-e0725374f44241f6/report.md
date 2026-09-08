## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | application configuration missing at runtime |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Back-off restarting failed container app in pod workload-dff5cbc6b-kmfxx_aiops-case-07` | 确认容器处于频繁崩溃重启循环状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff` | 证实 Kubernetes 调度器已终止重启策略并进入等待期 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 提供应用程序异常退出的直接系统级证据 |
| 4 | K8s State | kubernetes | `container.last_exit_code: 78` | 提供退出码的具体数值，指向应用层特定的错误类型 |
| 5 | Logging | elasticsearch | `pattern: "CONFIG_MISSING" | http_status: 500 | path: "/work" | service: "aiops-lab-workload"` | 揭示应用自身在运行时检测到配置缺失并返回错误响应 |
| 6 | Tracing | deepflow | `flow.response_code: 500 | request_resource: "/work" | src_ip: 172.16.104.9` | 独立捕获到针对同一端点的高频 500 错误流量 |

**证据关联说明**：
- 事实 #1、#2 共同解释了 Pod 的 `CrashLoopBackOff` 状态与高频重启现象。
- 事实 #4 的退出码 78 与事实 #5 中 `CONFIG_MISSING` 日志模式在语义上高度吻合，表明异常退出是由应用层错误处理逻辑触发。
- 事实 #5 与 #6 在相同的时间窗口与路径上互相印证，确认了导致应用崩溃及返回 500 的内部原因是配置缺失，而非网络或基础设施故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行时无法获取配置 → 触发 CONFIG_MISSING 逻辑 → 应用记录错误日志并退出(code 78) → CrashLoopBackOff
```

### 根因结论

已确认根因：**application configuration missing at runtime**。

证据显示应用进程持续因内部“配置缺失”错误（日志事实 #5）而异常终止（退出码 78，事实 #4），导致 Kubernetes 无法维持容器存活并触发 `CrashLoopBackOff`（事实 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.2s
├─ 并发证据采集: 63.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 63.3s (Evidence 53.3s, RCA 9.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
