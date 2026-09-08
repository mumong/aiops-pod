## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l 处于 NotReady 状态，就绪探针持续返回 HTTP 503。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5f4fb9ff45-7b77l` 状态 `ContainersReady=False`，Reason=`ContainersNotReady`，信息包含 `app` 容器 | 确认 Pod 业务侧就绪状态为异常 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 揭示就绪探测的直接失败原因：连接被拒绝 |
| 3 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 确认应用层探测长期返回 503 错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 对容器 `app` 值为 `0` | 排除因应用崩溃重启导致的就绪失败 |
| 5 | Logging | Elasticsearch | 日志聚合 `http_request error`，pattern: `dependency unavailable`, `http_status: 503`, `path: /work`, `allocated_mib` 始终为 `0` | 证明应用内部在处理请求时故意返回 503，且未发生 OOM |
| 6 | Tracing | Deepflow | L7 Flow 聚合 `GET /work`，`dst_ip: 172.16.104.35`，`response_code: 503`，共出现 9 次 | 网络层观测到对 Pod IP 的访问持续返回 503，印证应用层行为 |
| 7 | Tracing | Tempo | Span `GET /work`，`trace_id: cd230732dd175914a43aa596f86fcfed`，`aiops.observed_mode: readiness_fail`，耗时极短 (4微秒) | 确认该异常模式由系统内部故意触发（readiness_fail），且非超时导致 |

证据表明 Pod 处于正常运行状态（未重启、非 OOM），但其就绪探针探测失败。事件日志显示探针既遇到过连接拒绝，也长期收到 HTTP 503 响应。深度追踪（Deepflow 和 Tempo）及日志记录均指向应用内部主动返回 503 错误，且 Tempo 中的 Span 明确记录了 `readiness_fail` 的触发模式，证明应用层因配置原因持续不响应就绪状态。

## 🎯 根因分析 · g1

```text
应用配置 FAILURE_MODE=readiness_fail → 应用故意在 /ready 端点返回 503 (或拒绝连接) → Kubernetes 就绪探针连续失败 (HTTP 503 或 Connection Refused) → Pod 状态变为 NotReady
```

### 根因结论

已确认根因为：应用层处于故意故障注入模式。
具体而言，应用配置 `FAILURE_MODE=readiness_fail` 导致业务逻辑在 `/ready` 端点返回 `503` 错误（如日志中的 `dependency unavailable` 所示），从而直接触发 Kubernetes 就绪探针探测失败（`Readiness probe failed`）。Tempo 追踪 Span 中的 `aiops.observed_mode: readiness_fail` 属性进一步证实了这一行为是由应用逻辑控制而非资源不足或崩溃所致。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 19.5s
├─ 并发证据采集: 136.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 136.7s (Evidence 127.0s, RCA 9.5s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
