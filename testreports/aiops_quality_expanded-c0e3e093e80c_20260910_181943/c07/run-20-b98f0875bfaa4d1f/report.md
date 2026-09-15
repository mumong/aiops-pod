## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，重启 11 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Warning BackOff ... Back-off restarting failed container app` (155次) | 确认容器频繁重启，直接体现 CrashLoopBackOff 状态 |
| 2 | K8s State | K8s State | `last_terminated_reason: Error`, `exit_code: 78` | 确认应用进程因异常退出码终止，排除 OOMKilled 或信号终止 |
| 3 | K8s Config | K8s Configuration | `cpu.request: 20m`, `memory.limit: 96Mi` | 资源限制配置，非 CrashLoopBackOff 的直接致病源 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 11` | 独立确认重启次数，与 K8s 状态一致 |
| 5 | Logging | Elasticsearch | 8 次 `CONFIG_MISSING` 错误日志，HTTP 状态 `500`，`path: /work` | 揭示应用退出前的业务逻辑失败原因 |
| 6 | Tracing | Deepflow | HTTP Flow: `GET /work`, `src_ip: 172.16.104.8`, `dst_ip: 172.16.104.63`, `response_code: 500` | 对应日志中的错误模式，证实 Pod 在收到请求后处理失败 |
| 7 | Tracing | Tempo | Span `dedb33c8328961d6c4921bf52e1d587a`: `attributes: aiops.observed_mode: config_missing_exit`, `span_end: 21:02:57.860Z` | 关联 TraceID `dedb33...` 确认退出状态为配置缺失，时间戳晚于日志首条，形成连续故障窗口 |

**证据关联说明：**
Kubernetes 状态（#1, #2）与 Prometheus 指标（#4）共同证实了 Pod 的 CrashLoopBackOff 现象。Elasticsearch 日志（#5）提供了业务层面的根因（`CONFIG_MISSING`），而 Tempo/Deepflow 追踪数据（#6, #7）通过时间戳和 TraceID 进一步确认了应用是在 HTTP 服务运行期间收到请求并处理失败后退出，且日志与追踪数据在时间和事件模式上完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的配置缺失（触发） → HTTP 服务启动后处理 /work 请求时检测到 CONFIG_MISSING（机制） → 应用主动抛出 500 错误并 Exit 78 终止进程（直接失败） → Kubelet 检测到进程退出，进入 CrashLoopBackOff 状态（现象）
```

### 根因结论

已确认根因为**应用配置缺失导致的应用进程主动退出**。

1.  **现象确证**：Pod `aiops-case-07/workload-dff5cbc6b-sjvxl` 处于 `CrashLoopBackOff` 状态，已重启 11 次（证据 #1, #4）。
2.  **退出机制明确**：容器最后一次退出的原因是 `Error` 且退出码为 `78`（证据 #2），这表明是应用内部逻辑触发的退出，而非被 Kubernetes 或系统强制杀死。
3.  **失败原因定位**：日志显示应用在处理 `/work` 请求时报告 `CONFIG_MISSING` 错误（证据 #5）；Tracing 数据进一步确认了应用内部的运行模式为 `config_missing_exit`（证据 #7）。
4.  **因果关系链**：应用启动成功并监听端口，但在接收到请求时，由于缺失必要配置，主动选择退出并返回 500 错误，导致 Kubelet 反复重启容器。

现有证据已充分覆盖从现象到根因的链条。待确认项仅为 `ConfigMap workload-code` 的具体数据内容或挂载路径，但不影响“配置缺失导致进程退出”这一根因事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.8s
├─ 并发证据采集: 59.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 59.4s (Evidence 49.4s, RCA 9.8s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
