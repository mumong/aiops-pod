## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | RecentRestart | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 退出码 `137`；最近终止原因 `Error` | 直接指示进程被系统异常终止，存在资源限制触发的物理可能 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 证明应用虽然未崩溃（或重启后），但健康检查端点 `/work` 处于不可用状态 |
| 3 | K8s Config | Kubernetes | 内存限制 `96Mi`；内存请求 `24Mi`；CPU 限制 `200m` | 提供资源上限约束，`96Mi` 限制是推测 OOM 的依据 |
| 4 | K8s State | Kubernetes | Pod 重启次数 `44`；状态 `Running` | 证实容器经历了持续的 CrashLoopBackOff 循环，但当前时刻处于运行中 |
| 5 | Metric | Prometheus | 重启总数 `44`；`kube_pod_container_status_last_terminated_reason` 返回 `Error` | 从监控维度确认了异常终止的持续性与错误性质 |
| 6 | Logging | Elasticsearch | 8条应用日志均为 `http_status: 200`, `request completed` | 与应用层的 500 错误状态矛盾，缺乏 500 错误发生时的应用端日志证据 |
| 7 | Tracing | Deepflow/Tempo | 9个 Flow 均为 `response_code: 200`；1个 Span `aiops.observed_mode: liveness_fail` 且 `http.response.status_code: 200` | 证明流量在 L7 层均返回成功，探针检测到 500 但应用层实际记录为 200，存在探针误判或探针自身逻辑故障的可能 |

证据冲突：应用日志（#6）与链路追踪（#7）均显示 `/work` 返回 200 成功，但 K8s 事件（#2）明确记录探针接收到了 500 错误。这种“探针报错但应用成功”的矛盾，使得 500 错误的确切来源（探针配置错误、探针自身 Bug、或 K8s 探针机制误解）无法仅凭现有数据确认。同时，存在退出码 137（#1），但因缺少内存使用指标（如 `container_memory_usage_bytes`），无法确定 137 是否由突破 96Mi 限制（#3）的 OOM 引起，也可能是探针或容器运行时内部错误导致的退出。

## 🎯 根因分析 · g1

### 因果链

```text
未知（探针应用层矛盾） / 未确认的 OOM（缺内存指标） → 未确认的 500 错误 / 未确认的 137 终止 → Liveness Probe 失败 / Kubelet 终止容器 → Pod 频繁重启
```

### 根因结论

**证据不足**。

现有证据支持两个互相矛盾且无法互相排他解释的故障路径：
1. **应用层/探针配置故障**：应用日志与链路追踪均显示 `/work` 返回 200，但 Kubelet 报告 500。这表明根因可能是探针配置错误（如未正确传递 Cookie/Header）或探针内部逻辑 Bug，而非应用处理逻辑错误。
2. **资源限制导致的 OOM**：进程以 137 退出表明存在系统层面的强杀。虽然容器配置了 `96Mi` 的硬限制，但缺少 `container_memory_usage_bytes` 等指标数据，无法证实该退出是由内存超限触发的 OOM Kill 还是其他原因。

由于无法确认 500 错误的真实性来源，也无法确认 137 退出的确切物理机制，无法将根因判定为“应用内存泄漏/资源不足”或“探针配置错误”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.3s
├─ 并发证据采集: 61.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 61.4s (Evidence 49.7s, RCA 11.6s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime, pod-evicted
