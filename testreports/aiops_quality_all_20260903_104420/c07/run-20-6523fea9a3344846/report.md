## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器 app 因持续非零退出码重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` reason: `CrashLoopBackOff`; last terminated reason: `Error`; Exit Code: `78` | 定义故障现象：容器因错误退出被 Kubelet 反复重启并退避。 |
| 2 | K8s Event | Kubernetes | Event `BackOff`: `back-off 5m0s restarting failed container=app` | 证实重启频率受指数退避限制，确认处于 CrashLoopBackOff 稳定态。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (CrashLoopBackOff): 1; `...last_terminated_reason` (Error): 1 | 从指标侧独立验证 Pod 等待状态与上次终止原因。 |
| 4 | Logging | Elasticsearch | Log Pattern: `CONFIG_MISSING`, HTTP Status: `500`; Occurrences: 8 | 暴露应用崩溃的直接原因：代码逻辑因配置缺失主动抛出 500 并退出。 |
| 5 | Tracing | Deepflow/Tempo | Span `GET /work`: 500, `aiops.observed_mode: config_missing_exit`; Flow 9次，Trace IDs 与日志聚合一致 | 链路观测确认请求在应用层因相同错误被拒绝，且跨日志、Trace 的 Trace ID 关联一致。 |

**证据关联说明：**
*   K8s 事实 (Fact 1, 2) 与 Prometheus 指标 (Fact 3) 互相印证了容器处于 CrashLoopBackOff 且因 Error 终止的状态。
*   日志 (Fact 4) 提供了退出码 78 背后的业务逻辑（HTTP 500 + CONFIG_MISSING）。
*   追踪数据 (Fact 5) 不仅复现了 HTTP 500 错误，还通过 `aiops.observed_mode` 进一步确认了 `config_missing` 模式，且部分 Trace ID 与日志聚合中的 ID 重叠，形成了完整的观测闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 应用捕获错误并返回 HTTP 500 及退出码 78 → Kubelet 检测到容器异常退出 (exitCode=78) 并触发重启 → Pod 进入 CrashLoopBackOff 状态 (back-off 5m0s)
```

### 根因结论

已确认根因：**应用进程启动/请求处理时因缺失关键配置（`CONFIG_MISSING`）主动终止。**

具体表现为 `aiops-lab-workload` 服务的 `GET /work` 接口在处理时，因检测到配置缺失而返回 HTTP 500 并调用退出逻辑（Exit Code 78）。Kubelet 监听到该非零退出码后，按照 CrashLoopBackOff 策略反复重启容器，导致 Pod 持续处于不可用状态。证据主要来源于 Elasticsearch 中的重复报错日志、Deepflow/Tempo 中关联的 500 错误 Span 以及 K8s 侧的终止状态记录。

缺失决定性事实：ConfigMap `workload-code` 的具体内容未展示，无法确认缺失的具体 Key 名称。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 20.8s
├─ 并发证据采集: 90.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 90.3s (Evidence 78.5s, RCA 11.6s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
