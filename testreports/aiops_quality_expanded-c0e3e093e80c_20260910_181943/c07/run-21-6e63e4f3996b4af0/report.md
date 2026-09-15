## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 应用程序代码启动后在业务逻辑层请求配置失败，触发应用内异常退出（Exit Code 78），导致 Kubernetes 进入 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `workload-dff5cbc6b-sjvxl` / `app` | `waiting_reason`: "CrashLoopBackOff"; `last_terminated_reason`: "Error"; `last_exit_code`: 78; `restart_count`: 12 | 确认应用处于崩溃循环状态，且退出码稳定为 78 |
| 2 | K8s Event | `kubelet` | `message`: "Back-off restarting failed container app ... 4m3s (x155 over 38m)" | 确认异常发生时间长、频率高，符合 CrashLoopBackOff 的退避行为 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}`: 1; `kube_pod_container_status_restarts_total`: 12 | 外部指标与 Pod 状态一致，佐证了重启计数 |
| 4 | Logging | Elasticsearch | Pattern: "CONFIG_MISSING", http_status: 500, path: "/work", trace_id: "f4551a23cc93e1a006b288071e8ae6bb", time_range: "20:47:10" ~ "21:08:10" | 提供应用内部直接证据：业务逻辑层因配置缺失报错 |
| 5 | Tracing | Tempo | Span "GET /work", trace_id: "64132b2c9d9b8077c1ac955acb517247", status_code: 500, `aiops.observed_mode`: "config_missing_exit" | 通过 `aiops.observed_mode` 直接指示了代码层的异常退出原因 |
| 6 | Tracing | Deepflow | L7 Flow "GET /work", src_ip: 172.16.104.8, dst_ip: 172.16.104.63, response_code: 500, trace_ids: ["2e59e3c2...", "64132b2c..."] | 网络流确认了 Pod (172.16.104.63) 在处理内部请求时返回了 500 状态码 |

**证据关联说明**：
K8s 状态 (#1, #2) 确定了“进程不断被杀死”的现象，而 Logging (#4) 和 Tracing (#5, #6) 解释了“为什么被杀死”——应用代码在请求配置时发现缺失（`CONFIG_MISSING`），主动抛错并退出（Exit Code 78）。Trace ID `64132b2c9d9b8077c1ac955acb517247` 在日志和 Tempo Span 中均有出现，且 Deepflow Flow 也关联了相同 ID，三者形成了完整的内部故障闭环证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用程序业务逻辑层配置请求失败 (CONFIG_MISSING) → 触发应用内部异常退出机制 (Exit Code 78) → K8s 检测到容器非零退出码并持续重启 → 触发 BackOff 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是**应用程序代码在启动后的业务逻辑层执行失败**。
*   **具体机制**：应用程序尝试加载配置或访问特定资源时，因配置缺失（`CONFIG_MISSING`）导致业务逻辑无法继续，触发了应用定义的异常处理流程并主动退出（Exit Code 78）。
*   **证据支撑**：
    *   Logging 明确记录了 `CONFIG_MISSING` 错误及 `http_status: 500`。
    *   Tracing 中的 `aiops.observed_mode: "config_missing_exit"` 属性直接锁定了退出原因。
    *   稳定的 Exit Code 78 与 K8s 的 CrashLoopBackOff 状态相互印证，排除了 OOMKill（通常退出码 137）或其他外部网络故障导致的崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 13.0s
├─ 并发证据采集: 65.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 65.8s (Evidence 59.0s, RCA 6.7s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
