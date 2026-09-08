## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | Error | Pod workload-dff5cbc6b-kmfxx 持续 CrashLoopBackOff 重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 app 退出码 exit_code: 78 | 支撑直接失败机制 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (BackOff, Warning) | 证实 CrashLoopBackOff 现象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (last_reason: Error) | 确认最近一次终止原因为非 0 退出 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 3 | 确认重启计数 |
| 5 | Logging | Elasticsearch | 错误日志模式 `CONFIG_MISSING` (8次) | 支撑根本原因 (Root Cause) |
| 6 | Tracing | Tempo | 错误日志关联 Trace ID: `da9999ae734835080b2f252e105e1ce7` | 关联日志与追踪 |
| 7 | Tracing | Tempo | Flow/Span `GET /work` (http.response.status_code: 500) | 确认应用逻辑层产生内部错误 |

**证据关联说明：**
1. **根本原因确认**：日志维度显示 8 次 `CONFIG_MISSING` 错误（事实 #5），这是导致应用退出和 500 错误的直接逻辑原因。
2. **失败机制确认**：追踪维度确认了具体的内部调用链路 `GET /work` 返回了 `500` 状态码（事实 #7），日志中的 Trace ID `da9999ae...` 与追踪数据一致（事实 #6）。
3. **现象确认**：退出码 78（事实 #1）配合 K8s Event（事实 #2）和 Metric 重启计数（事实 #4），证实了容器进程因内部错误反复退出并触发 K8s 的 BackOff 机制。

## 🎯 根因分析 · g1

### 因果链

```text
关键配置缺失 (CONFIG_MISSING) → 应用请求处理失败并返回 HTTP 500 → 容器进程非正常退出 (Exit Code 78) → kubelet 触发 CrashLoopBackOff 重启
```

### 根因结论

**已确认根因**：应用启动或运行过程中缺失关键配置（`CONFIG_MISSING`）。
- **证据支持**：日志聚合事实显示 8 次 `CONFIG_MISSING` 错误，且关联的追踪 Span 显示应用请求 `GET /work` 返回 500 错误；Kubernetes 状态和 Metric 证实容器因此反复退出（Exit Code 78）并触发重启。
- **机制说明**：应用因配置缺失无法处理请求，进程以 78 退出码终止，导致 Kubelet 的指数退避重启机制（CrashLoopBackOff）生效。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.2s
├─ 并发证据采集: 64.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 64.9s (Evidence 57.0s, RCA 7.6s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-config-error
