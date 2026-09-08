## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 app 退出码: 137 | 证实容器因 OOM 被系统强制杀死 |
| 2 | K8s Event | Kubernetes | Killing (33m): Container app failed liveness probe, will be restarted | 证实 Liveness 探针失败导致 Pod 重启 |
| 3 | K8s Event | Kubernetes | Unhealthy (20m): Liveness probe failed with statuscode: 500 | 证实健康检查接口返回具体的 500 错误 |
| 4 | K8s State | Kubernetes | Container restarts: 15 | 证实故障具有持续性及循环特征 |
| 5 | K8s Config | Kubernetes | 资源限制: Memory 96Mi / CPU 200m | 提供触发资源争用或 OOM 的环境配置约束 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total = 14 (2026-09-03T20:44:42Z) | 独立观测验证容器存在高频重启状态 |
| 7 | Logging | Elasticsearch | 模式: http_request completed, HTTP 200 (窗口: 20:38:54 - 20:44:37) | 证实观察窗口内存在正常业务流量，无对应故障日志 |
| 8 | Tracing | Tempo | Span: GET /work, HTTP 200 (Trace: 7c45d99e320355c055b463208ccf66f2) | 证实业务路径正常，且未发现导致 500 的异常 Span |

**证据互证与冲突说明：**
- **事实印证**：K8s 事件与 Metrics 双重证实容器经历了因 Liveness 探针失败导致的循环重启（#2, #3, #6）；K8s 状态指出底层机制为 Exit 137（OOM 信号）（#1）。
- **证据冲突/局限性**：日志（#7）和链路追踪（#8）均未捕获导致探针失败的 500 报错记录，仅观察到正常 200 响应。这表明故障发生时刻的异常上下文在日志冲刷前可能已丢失，或该 500 错误发生于未记录日志的底层逻辑/探针拦截路径。

## 🎯 根因分析 · g1

### 因果链

```text
应用实例资源受限/逻辑异常(未确认具体点) → Liveness 探针(/health) 返回 500 → Kubelet 触发 Kill(Exit 137) → 容器崩溃进入 Restart/BackOff 循环
```

### 根因结论

**诊断结论：证据不足 (inconclusive)**

**详细说明：**
1.  **已确认的表象与机制**：确凿事实表明容器 `workload-79d9f8fd88-sbqvc` 因 Liveness 探针（返回 HTTP 500）失败而触发容器被操作系统杀死（Exit Code 137），并导致 15 次重启（引用证据 #2, #3, #1, #4）。
2.  **根因缺失**：未能捕获导致探针返回 500 的根本应用层原因。日志（#7）和 Tracing（#8）仅呈现正常业务流（HTTP 200），未能记录故障瞬间的堆栈、依赖超时或报错信息。因此，无法断定是内存不足（96Mi Limit）、代码缺陷、内部依赖超时还是其他应用逻辑错误导致了探针的 500 响应。
3.  **缺失事实**：需要获取 500 错误发生时的**应用层错误日志**、探针失败时刻的**详细 Trace 链路**或**应用内部调用堆栈**。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 19.1s
├─ 并发证据采集: 166.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 166.0s (Evidence 152.6s, RCA 13.2s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
