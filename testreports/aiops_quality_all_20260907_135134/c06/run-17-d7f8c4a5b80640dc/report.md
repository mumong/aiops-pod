## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，应用容器 `app` 持续非正常退出 (exitCode=2)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app` (3m23s over 48m) | 证实容器已陷入重启退避循环 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error`, `exit_code: 2` | 提供确切的终止原因与退出码 |
| 3 | K8s Config | kubernetes | `resource_limit.memory: 96Mi`, `resource_limit.cpu: 200m` | 排除资源超限被 Kill 的可能 |
| 4 | Logging | elasticsearch | `runtime process exiting` (HTTP 500, path: /work) 3次 (trace_ids: 658..., 18e..., f01...) | 直接捕获应用内部主动退出行为 |
| 5 | Tracing | deepflow | HTTP GET /work → `response_code: 500`, 2次 (trace_ids: 658..., 18e...) | 关联日志，确认失败发生在特定请求期间 |
| 6 | Tracing | deepflow | HTTP GET /work → `response_code: 200`, 3次 (trace_ids: 3fa..., 684...) | 证明该服务接口本身具备可用性 |

日志中的 `runtime process exiting` (trace_id: 658...) 与 Deepflow 追踪中的 HTTP 500 错误 (trace_id: 658...) 严格匹配，证明应用在处理 `/work` 请求时因内部逻辑异常主动退出了进程（Exit Code 2）。由于 K8s 配置的内存上限为 96Mi 且日志显示初始内存分配为 0，未观察到 OOM Kill 迹象。Kubernetes 检测到进程异常退出后执行了重启策略，当前因重启频率过高进入了 `CrashLoopBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑异常（未捕获） → 应用进程捕获严重错误主动终止 (exitCode=2) → K8s 容器运行时自动重启容器失败 → CrashLoopBackOff (应用不可用)
```

### 根因结论

**已确认的根因：** 应用代码在处理 `GET /work` 请求时发生未捕获的业务逻辑异常（Internal Error），导致应用程序进程主动终止。

*   **证据支撑：**
    *   **应用侧事实**：Elasticsearch 日志显示 3 次 `runtime process exiting`，均关联 HTTP 500 状态码（Fact #4）；Deepflow 追踪数据显示相同时间段内存在 2 次 HTTP 500 响应（Fact #5）。
    *   **系统侧事实**：Kubernetes 事件与状态反映容器以 `Error` 终止并反复重启，最终进入 `CrashLoopBackOff`（Fact #1, #2）。
    *   **排除其他因素**：Pod 拥有足够的资源限制（96Mi 内存，200m CPU），且 K8s 状态为 `Exit Code 2`（通常为应用逻辑错误），而非 OOMKilled。

*   **未知项（需进一步调查）：**
    *   导致该 `500` 错误的具体业务代码异常详情（如 Java Stack Trace 或 Python 报错堆栈）。
    *   触发该业务异常的具体前置条件或输入数据特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 34.2s
├─ 并发证据采集: 58.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 58.7s (Evidence 49.0s, RCA 9.5s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
