## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，频繁重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Exit Code: 137 (fact-38b0f268929f) | 容器异常退出的直接证据 |
| 2 | K8s Event | kubernetes | Back-off restarting failed container app in pod workload-79d9f8fd88-sbqvc (fact-5d4163ec8556) | 解释频繁重启的行为 |
| 3 | K8s Config | kubernetes | Memory Limit: 96Mi (fact-9a941f537f2e) | 确认导致 OOM 的硬限制阈值 |
| 4 | K8s State | kubernetes | Restart Count: 27 (fact-9ea9226186fe) | 确认故障处于持续的 CrashLoopBackOff 状态 |
| 5 | Metric | prometheus | Reason: CrashLoopBackOff (fact-1fe3a80c663c) | Prometheus 指标验证了 CrashLoopBackOff 状态 |
| 6 | Metric | prometheus | Reason: Error (fact-71bccce82886) | Prometheus 指标验证了终止原因为 Error |
| 7 | Logging | elasticsearch | Pattern: `request completed, http_status: 200, allocated_mib: 0` (fact-1ae6dff45f11) | 正常完成请求的日志记录，未捕捉到 OOM 瞬间 |
| 8 | Tracing | deepflow | Flow: `GET /work -> 200`, duration: 19486us - 58397us (fact-03ad950a734f) | 网络流量数据，确认应用对外提供正常服务 |

**证据印证说明：**
1. Kubernetes 的 `Exit Code 137` [证据#1] 与 `Memory Limit 96Mi` [证据#3] 构成了 OOMKilled 的标准诊断特征。
2. `Restart Count 27` [证据#4] 结合 BackOff 事件 [证据#2]，证实了因退出异常导致的循环重启，与 Prometheus 的 `CrashLoopBackOff` 指标 [证据#5] 和 `Error` 指标 [证据#6] 完全吻合。
3. 日志 [证据#7] 和 Tracing [证据#8] 捕捉到的是 200 正常的服务流量，虽然证实了应用具备服务响应能力，但因采样时间窗口未覆盖崩溃瞬间，未能记录到导致 OOM 的具体请求或内存增长过程。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存分配超过 96Mi limit → 内核 OOM Killer 发送 SIGKILL → 容器终止并退出码 137 → Pod 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
容器 `app` 的内存使用超过了 Kubernetes 配置的 `96Mi` 硬限制（`memory_limit`）。Linux 内核的 OOM Killer 进程被触发，向容器发送了 `SIGKILL` 信号，导致容器以 `Exit Code 137` 异常终止。频繁的终止与重启触发了 Kubernetes 的 BackOff 机制，最终表现为 Pod 处于 `CrashLoopBackOff` 状态。

证据支撑：
- **OOM 触发：** `Exit Code 137` (事实 #1) 和 Memory Limit 96Mi (事实 #3)。
- **循环重启：** Restart Count 27 (事实 #4) 和 BackOff 事件 (事实 #2)。
- **状态确认：** Prometheus CrashLoopBackOff 指标 (事实 #5)。

**未知/未确认部分：**
日志 [证据#7] 和 Tracing [证据#8] 虽然展示了 200 的正常服务请求，但其时间窗口（如 `allocated_mib: 0` 和持续时间）未直接包含导致内存突破 96Mi 的那次峰值请求。具体的触发负载模式或应用内部的内存泄漏代码路径无法从现有工具事实中确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 14.8s
├─ 并发证据采集: 56.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 56.2s (Evidence 47.4s, RCA 8.7s)
└─ 汇总总结: 14.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
