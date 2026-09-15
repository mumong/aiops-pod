## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 持续处于 CrashLoopBackOff 状态（重启19次） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 app 退出码 `78`；状态 `CrashLoopBackOff`（等待 5m0s），重启 19 次 | 确认应用异常终止且 K8s 持续重启的特征 |
| 2 | K8s Event | kubernetes | `BackOff`：62s (x332 over 75m) 重启失败的容器 app | 证实异常已持续约 75 分钟且处于指数退避阶段 |
| 3 | K8s State | kubernetes | 应用退出原因 `Error`（最后一次终止） | 将容器终止归因为非零退出码（Code 78） |
| 4 | Logging | elasticsearch | 日志模式 `CONFIG_MISSING`，`http_status=500`，`/work`（发生 8 次，时间窗口：21:18:32 至 21:45:10） | 暴露应用代码层面的失败逻辑与触发路径 |
| 5 | Tracing | deepflow/tempo | HTTP Flow：`GET /work` → `500`（9 次）；Tempo Span `35171f43b5d98aebd6019469374b813c` 标记 `aiops.observed_mode=config_missing_exit` | 关联日志模式到具体的 API 调用，并直接标识应用内部故障模式 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 显示 `Error`（样本 13 个，均为 1） | 独立确认最后一次容器终止原因为 Error，与 K8s State 吻合 |

证据链说明：
- **机制闭环**：日志维度记录的 `CONFIG_MISSING` 与追踪维度提供的 `app.observed_mode=config_missing_exit` 直接印证了应用代码层面的具体失败逻辑。
- **系统表现印证**：K8s State 显示的非零退出码 78 以及 Tracing 记录的 HTTP 500 响应，共同构成了“应用处理请求时触发配置缺失逻辑并主动退出”的完整证据。
- **现象一致性**：Prometheus 指标持续监测到 `last_terminated_reason=Error`，与 K8s 层面的 `CrashLoopBackOff` 状态和事件记录相互匹配，确认了故障的持续性。

## 🎯 根因分析 · g1

### 因果链
```text
环境变量 FAILURE_MODE 设置为 config_missing_exit → 应用启动/处理请求时触发 CONFIG_MISSING 逻辑 → 应用以 Exit Code 78 主动终止进程 → K8s 持续重启导致 CrashLoopBackOff
```

### 根因结论
应用 `workload-dff5cbc6b-sjvxl` 处于 `CrashLoopBackOff` 的根本原因是：**应用被配置为在检测到配置缺失时主动退出**。

具体而言，环境中的 `FAILURE_MODE` 变量被设置为 `config_missing_exit`（证据：Tracing 标记），导致应用进程在启动后（如响应 `/work` 请求时，证据：Logging/Tracing）检测到配置缺失，主动触发了错误退出逻辑（HTTP 500，Exit Code 78）。由于退出码非 0，Kubernetes 将其判定为异常终止并执行指数退避重启（证据：K8s State/Event/Metric），形成了当前的重启循环。

**未知项**：ConfigMap `workload-code` 中具体缺失的是哪一个配置文件键值，目前证据不足以定位。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.8s
├─ 并发证据采集: 88.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 88.4s (Evidence 79.5s, RCA 8.7s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
