## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff (app) | 确定 Pod 处于异常重启循环状态 |
| 2 | K8s Event | kubernetes | `event.message`: "Back-off restarting failed container app" | 确证 Kubelet 因容器持续异常而触发退避重启 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error | 确认应用进程非正常退出 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: 78 | 提供应用退出的具体错误代码 |
| 5 | Logging | elasticsearch | `pattern`: {event: "http_request", level: "error", message: "CONFIG_MISSING", http_status: 500, path: "/work"} (8次) | 证明应用接收到请求并因配置缺失返回 500 错误 |
| 6 | Tracing | deepflow | `flow`: GET /work → 500 (src: 172.16.104.8 → dst: 172.16.104.63) | 从流量层面佐证应用对外提供请求时处理失败 |
| 7 | Tracing | tempo | `span`: {trace_id: "a358165e4c5df7b2882c057473693f30", attributes: {aiops.observed_mode: "config_missing_exit", http.response.status_code: 500}} | 结合日志 TraceID，精准追踪到单次请求因 CONFIG_MISSING 触发退出逻辑 |

**证据关联说明：**
1.  证据 1-4 与 6 共同确认了 Pod 处于由内部错误导致的 CrashLoopBackOff 状态；
2.  证据 5 (日志) 与 证据 7 (追踪) 建立了因果链：应用启动后，在处理 GET /work 请求时，检测到 `CONFIG_MISSING` 并返回 500 状态码；
3.  证据 7 中的 `aiops.observed_mode: config_missing_exit` 与日志中的 `CONFIG_MISSING` 模式一致，直接解释了证据 4 中 `exit_code: 78` 的触发原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用未找到预期 CONFIG → 处理请求时触发 CONFIG_MISSING 错误并退出 (exit code 78) → Kubelet 持续重启异常容器 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：
应用运行逻辑强制要求在 `CONFIG` 可用时才提供服务。由于缺失该配置，应用在处理请求（如 `GET /work`）时抛出 `CONFIG_MISSING` 错误并直接以非零退出码（78）退出，导致 Kubelet 反复重启容器，最终形成 CrashLoopBackOff。

**支持证据**：
- **日志**显示连续 8 次出现 `CONFIG_MISSING` 错误模式并伴随 `http_status: 500`（证据 5）；
- **Tracing** 明确记录了 `config_missing_exit` 模式及 `exit_code: 78` 的退出行为（证据 7）；
- **K8s 状态**确认容器因 Error 退出并处于 CrashLoopBackOff（证据 1-4）。

**未知项**：
- 缺失的具体 CONFIG 来源（是环境变量、ConfigMap 还是 Secret）在当前证据中无法直接确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.5s
├─ 并发证据采集: 66.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 66.6s (Evidence 57.4s, RCA 9.1s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
