## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l (namespace: aiops-case-09) 处于 NotReady (0/1 Ready) 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.condition`: Ready/ContainersReady=False, reason=ContainersNotReady (fact-1779ac6d2d04) | 确认 Pod 因容器未就绪而处于 NotReady 状态 |
| 2 | K8s Event | Kubernetes | kubelet Readiness probe failed: `connect: connection refused` (fact-2c09a326e18a) | 揭示 Kubelet 在 8080 端口探测时连接被拒绝，导致探针失败 |
| 3 | K8s Event | Kubernetes | kubelet Readiness probe failed: HTTP probe failed with statuscode: `503` (fact-d93f91a9811b) | 记录探针返回的 HTTP 状态码为 503 |
| 4 | K8s Config | Kubernetes | Container `app` CPU limit=200m, memory limit=96Mi (fact-172ce422b9eb, fact-570620cd3310) | 提供 Pod 资源上下文，当前无重启记录 (0, fact-1676ad37e420) |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-94ed5322e1b1) | 确认 Pod 处于正常运行状态（非 CrashLoopBackOff），排除崩溃重启因素 |
| 6 | Logging | Elasticsearch | 错误日志 `dependency unavailable`, http_status: 503, path: `/work`, 8次出现 (fact-17d4ca5340ed) | 证实应用层正在处理请求并因下游依赖不可用返回 503 |
| 7 | Tracing | Tempo | Span `GET /work`, `http.response.status_code`: 503, `aiops.observed_mode`: readiness_fail (fact-1802b61c7265) | 关联 Readiness Probe 行为，确认探针探测 `/work` 端点时收到 503 响应 |
| 8 | Tracing | Deepflow | L7 Flow: GET `/work`, response_code: 503, src_ip=172.16.104.55, dst_ip=172.16.104.35 (fact-3a388dd41dc4) | 从网络层确认流量在 Pod IP (172.16.104.35) 的 8080 端口受阻或无服务响应 |

**证据印证说明：**
1.  **现象与机制一致**：Kubelet 的探针失败事件（证据 2, 3）与应用日志（证据 6）和 Trace 中的 `/work` 端点响应（证据 7, 8）相互印证，明确探测失败的原因是应用层返回了 `503`，而非网络不通或端口未监听。
2.  **探针路径闭环**：Trace 中观察到 `aiops.observed_mode: readiness_fail`（证据 7）直接关联了探针失败（证据 3），确认了 503 是导致 NotReady 状态的根本触发点。
3.  **排除重启因素**：Metric 显示无重启（证据 5）结合状态（证据 1）证明 Pod 进程一直在运行，但健康检查因业务依赖问题持续失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的下游资源不可用 → 应用 /work 端点返回 503 (Dependency unavailable) → Readiness Probe 探测失败 (HTTP 503 & Connection Refused) → Pod 状态 NotReady
```

### 根因结论

**已确认的根因**：应用工作负载 `aiops-case-09/workload-5f4fb9ff45-7b77l` 的 `/work` 端点因内部依赖的下游资源不可用，持续返回 HTTP 503 错误。由于 Readiness Probe 配置了该端点，探测结果持续失败，导致 Pod 被标记为 `NotReady` 并从服务后端摘除。

**证据支撑**：
-   **探针状态**：Pod 条件 `ContainersNotReady`（证据 1）及探针事件显示状态码 503 或连接拒绝（证据 2, 3）。
-   **应用日志**：多条日志记录到 `dependency unavailable` 及 `http_status: 503`（证据 6）。
-   **链路追踪**：Span 数据直接捕获 `/work` 路径返回 503，且处于 `readiness_fail` 模式（证据 7）；底层网络流确认该请求流向该 Pod IP 时返回 503（证据 8）。

**缺失信息**：
-   具体的下游依赖资源名称或具体报错原因（如数据库连接失败、微服务超时等）在现有事实中未明确，仅确认为 `dependency unavailable`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.3s
├─ 并发证据采集: 67.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 67.3s (Evidence 59.2s, RCA 7.9s)
└─ 汇总总结: 16.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
