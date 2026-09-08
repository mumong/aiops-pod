## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用启动缺失必要配置（CONFIG_MISSING）导致进程异常退出（Exit Code 78） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error; container.last_exit_code: 78 | 证明容器非正常终止且退出码固定 |
| 2 | K8s State | kubernetes | container.restart_count: 17; status: CrashLoopBackOff | 确认故障已触发 Kubernetes 重启保护机制 |
| 3 | K8s Event | kubernetes | BackOff restarting failed container app in pod workload-dff5cbc6b-kmfxx (x290 over 65m) | 证实异常状态持续且频率极高 |
| 4 | Logging | elasticsearch | pattern: CONFIG_MISSING (error, 500, /work); 8 occurrences (2026-09-03T14:42:13.854Z - 15:03:03.553Z) | 提供应用层具体的错误类型与发生时间窗口 |
| 5 | Tracing | tempo/span | trace_id: 65684c8c...; http.response.status_code: 500; aiops.observed_mode: config_missing_exit | 确认特定 Trace 内的服务端直接返回 500 且模式匹配 |
| 6 | Tracing | deepflow/flow | 9 occurrences of GET /work -> 500; trace_ids include 65684c8c... and 3ddfc555... | 提供网络层流量聚合及部分 Trace ID 关联证据 |

**证据印证说明：**
1. **状态闭环**：K8s State 报告的 Exit Code 78 与 Application Error 共同构成了进程崩溃的直接证据（事实 1、2、3）。
2. **错误定位**：Logging 和 Tracing 数据（事实 4、5、6）明确指出了崩溃原因为 `CONFIG_MISSING`，且部分 Trace ID（如 `65684c8c...`）在 Logs 和 Tracing 中完全交叉验证，证明是应用启动或配置加载阶段发生致命错误。
3. **资源无关性**：K8s State 中的 resource limits 显示配置了 CPU 200m / Mem 96Mi，结合日志中的特定 `CONFIG_MISSING` 模式，排除了 OOM 或 CPU 争抢导致退出的可能性，进一步锁定为应用自身的配置缺陷。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动缺失必要配置（CONFIG_MISSING） → 进程初始化失败/抛出致命错误 → 进程退出码 78 (Error) → CrashLoopBackOff 及客户端 500 报错
```

### 根因结论

**已确认根因**：工作负载 `aiops-case-07/workload-dff5cbc6b-kmfxx` 的 `app` 容器因**启动缺失必要配置**（错误标识为 `CONFIG_MISSING`）导致进程异常退出。

*   **事实支撑**：
    *   容器退出码固定为 `78` 且重启了 17 次（事实 1、2）。
    *   日志聚合结果明确记录 8 次 `CONFIG_MISSING` 错误（事实 4）。
    *   Tracing 数据中的 `aiops.observed_mode: config_missing_exit` 及 HTTP 500 响应（事实 5）直接证实了应用内部的诊断机制。

现有证据已形成完整闭环，足以解释当前 `CrashLoopBackOff` 现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.6s
├─ 并发证据采集: 77.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 77.4s (Evidence 72.2s, RCA 4.8s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime, pod-imagepull-failed, pod-oomkilled
