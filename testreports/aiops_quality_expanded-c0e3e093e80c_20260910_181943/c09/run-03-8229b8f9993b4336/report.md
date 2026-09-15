## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Application dependency unavailable causes /ready endpoint to return HTTP 503, failing Readiness Probe |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused | 确认探针初始阶段的网络/连接拒绝异常 |
| 2 | K8s Event | kubelet | Readiness probe failed: HTTP probe failed with statuscode: 503 | 确认探针后续阶段的 HTTP 503 服务端错误，导致 Readiness 条件转为 False |
| 3 | Metric | prometheus | kube_pod_container_status_ready{container="app"} = 0 (timestamp: 2026-09-11T00:39:22Z) | 独立于 Kubernetes API 的外部观测，确认容器处于未就绪状态 |
| 4 | Logging | elasticsearch | pattern: dependency unavailable, http_status=503, path=/work (count: 8, trace_ids: a3eefc3e054e4370268ed7434903578b...) | 日志明确记录业务层因内部依赖不可用导致 /work 接口返回 503，印证了应用自身报错逻辑 |
| 5 | Tracing | deepflow | GET /ready -> dst_ip=172.16.104.16, response_code=503 (count: 7, time_range: 08:33:37 - 08:38:28) | 流量日志证实针对就绪探针端点的请求频繁收到 503 响应 |
| 6 | Tracing | tempo | GET /work (span_id: 21bc66249905df27, http.response.status_code: 503, aiops.observed_mode: readiness_fail) | 单条 Span 明确标记了请求模式为 "readiness_fail"，且返回 503 |

证据表明，就绪探针（/ready）和业务接口（/work）均因应用返回 503 错误而导致失败。Kubernetes 事件从最初的“连接拒绝”演变为明确的“503 状态码失败”，Metric 和外部的 L7 流量日志一致证实了 503 的持续发生。日志与 Trace 关联指出，该 503 错误源于应用内部依赖不可用，但具体是哪个内部依赖（如数据库、缓存或下游服务）在输入事实中未提供。

## 🎯 根因分析 · g1

### 因果链

```text
内部依赖不可用 → 应用就绪检查（/ready）及业务接口（/work）返回 HTTP 503 → Kubelet 探针失败 → Pod Ready=False
```

### 根因结论

已确认根因为：**应用内部依赖不可用导致应用服务返回 503 错误，进而触发 K8s 就绪探针失败，使 Pod 持续处于 NotReady 状态。**

证据链闭环：
1. **现象验证**：K8s 事件记录探针连续失败（connection refused 及 statuscode: 503），Metric 确认容器 `status.ready` 为 0。
2. **机制定位**：Deepflow 流量日志显示 `/ready` 路径频繁收到 503 响应；应用日志（pattern: dependency unavailable）与 Tempo Span 明确记录了因内部依赖问题导致 `/work` 路径返回 503，且该错误模式被系统标记为 `readiness_fail`。

**未确认项**：导致 503 的**具体内部依赖身份**（如具体的下游服务名或资源名）在输入事实中缺失，无法进一步下沉。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 13.2s
├─ 并发证据采集: 125.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 125.7s (Evidence 116.4s, RCA 9.1s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
