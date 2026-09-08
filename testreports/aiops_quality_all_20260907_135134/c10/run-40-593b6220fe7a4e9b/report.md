## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | 容器内存使用量长期处于低位（峰值约 15 MiB），远低于 96 MiB 的硬限制，直接排除了 OOMKilled 作为退出码 137 的原因；结合 Liveness 探针在崩溃前持续返回 HTTP 500 且无内存飙升证据，判断根因为应用程序逻辑缺陷（或受控故障注入）导致服务内部报错、探针失败并触发强制终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `last_exit_code: 137` | 确认容器反复异常退出及退出码。 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 确认崩溃触发机制为 Liveness 探针连续失败。 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值 `16732160` Bytes (~16 MiB) | 确认运行时内存使用量极低，排除 OOM 导致退出码 137 的可能。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `36` | 证实 CrashLoopBackOff 已持续发生多次。 |
| 5 | Logging | Elasticsearch | 7 次 `request completed` 日志，`http_status: 200` | 证实应用主流量正常，Liveness 500 错误未被应用日志记录。 |
| 6 | Tracing | Deepflow/Tempo | 7 次等效 L7 Flow，`response_code: 200`，`span.aiops.observed_mode: liveness_fail` | 确认 HTTP 协议层面返回 200，探针状态受控于外部因素（如注入或侧车）。 |

**证据印证与冲突说明**：
K8s 事件指出 Liveness 探针因 HTTP 500 失败导致容器被杀（退出码 137），而 Prometheus 内存监控数据（峰值仅 16 MiB）充分证伪了 OOMKilled 的假设。Logging 与 Tracing 证据一致显示应用处理的主请求均为 HTTP 200 成功响应，这表明探针的 500 错误并非源于应用业务逻辑崩溃，而是独立的故障现象。探针模式（`liveness_fail`）与正常业务流量的并存，强有力指向应用内部逻辑缺陷或受控的故障注入。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部逻辑缺陷或受控故障注入 → Liveness 探针连续返回 HTTP 500 → Kubernetes 执行容错终止（Exit Code 137） → 容器状态 CrashLoopBackOff
```

### 根因结论

已确认根因为**应用程序逻辑缺陷或受控故障注入**。

1.  **排除 OOM**：退出码 137 通常由 OOMKilled 引起，但 Prometheus 指标（E#3）显示容器峰值内存仅为 ~16 MiB，远低于 96 MiB 的硬限制，证明内存充足。
2.  **确定触发机制**：K8s 事件（E#2）显示 Liveness 探针持续报 HTTP 500 失败，导致 kubelet 强制杀死了容器。
3.  **定位故障属性**：Tracing（E#6）和 Logging（E#5）证实应用实际处理的 HTTP 请求均返回 200，说明探针的 500 错误是应用非主流量路径的独立故障，符合“逻辑缺陷”或“故障注入”特征。

**缺少的事实**：应用代码的具体逻辑或依赖中导致 Liveness 探针返回 500 的确切原因（日志查询被拒，无法直接定位）。

---

## 📊 性能统计

```text
├─ 总耗时: 4.6m
├─ 问题定位: 13.3s
├─ 并发证据采集: 253.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 253.7s (Evidence 243.1s, RCA 10.3s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
