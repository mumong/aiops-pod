## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用代码在访问 '/work' 端点时发生运行时崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，终止原因 `Error`，退出码 `2` | 确认进程在运行时异常终止，而非配置或拉取失败 |
| 2 | K8s Config | Kubernetes | 容器内存硬限制 `96Mi`，请求 `24Mi`；CPU 限制 `200m`，请求 `20m` | 提供资源边界上下文，用于评估是否为资源耗尽导致崩溃 |
| 3 | Logging | Elasticsearch | 访问 `/work` 时 `http_status: 500`，消息 `runtime process exiting`；出现 `5` 次，`allocated_mib` 始终为 `0.0` | 直接定位到特定端点的代码执行阶段发生了进程级崩溃 |
| 4 | K8s Event | Kubernetes | `BackOff` 警告（315次），消息 `back-off 5m0s restarting failed container=app` | 佐证应用进入频繁重启循环，系统级反馈与应用崩溃一致 |
| 5 | Tracing | Tempo/Deepflow | 关联日志的 Flow：500 响应耗时 `5-6ms` (trace `4fb6ed6bcd8851d023d8b0e47cb38cfe`)；成功响应耗时 `18-23ms` | 证明崩溃发生在请求处理的极早期（应用内部逻辑中），而非外部连接超时 |
| 6 | Metrics | Prometheus | 当前重启次数 `18` 次，`reason: CrashLoopBackOff` | 确认异常现象的持续性和规模 |

**证据关联说明：**
Kubernetes 的 `CrashLoopBackOff` 和退出码 `2` 提供了崩溃的宏观证据 [1]；日志明确指出了崩溃发生的具体位置是在处理 `/work` 端点且状态为 500 时 [3]；Tracing 数据显示请求耗时极短 [5]，说明崩溃发生在应用内部逻辑的入口处，排除了外部依赖或网络链路的问题，从而锁定了代码运行时错误。

## 🎯 根因分析 · g1

```text
应用代码在访问 '/work' 端点时触发运行时错误 → 进程以退出码 2 异常终止 → K8s 触发重启机制并进入 CrashLoopBackOff → 用户观察到 Pod 持续重启且请求返回 500
```

**根因结论：**
已确认根因：应用代码在访问 `/work` 端点时发生运行时崩溃。
该结论由以下事实支撑：
1. **现象直接对应**：日志显示在 `/work` 请求期间发生了 `runtime process exiting` 错误 [3]。
2. **排除资源限制**：虽然内存限制较低（96Mi），但日志中明确记录 `allocated_mib` 始终为 `0.0`，且请求处理时间极短（5-6ms），这排除了 OOM（内存溢出）或 CPU 耗尽导致崩溃的可能性 [2]、[5]。
3. **系统级一致**：Pod 状态表现为 `CrashLoopBackOff`，退出码为 `2`，与代码内部抛出的未捕获异常导致进程退出的行为特征完全一致 [1]。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 16.9s
├─ 并发证据采集: 110.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 110.9s (Evidence 104.1s, RCA 6.6s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
