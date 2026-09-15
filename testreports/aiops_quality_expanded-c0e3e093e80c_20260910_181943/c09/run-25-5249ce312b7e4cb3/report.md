## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc is NotReady due to Readiness Probe failing with HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status` = Running, `Ready` = False, reason: `ContainersNotReady` [fact-2a9fb476e902, fact-d402df370c15] | 确认 Pod 进程正在运行但健康检查失败，导致服务未就绪 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` [fact-26f7671c494f] | 确认直接故障机制为端点返回 503，且已持续 65 分钟 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory` = 96Mi, `container.resource_request.memory` = 24Mi [fact-c1c26807515f, fact-4f14c7ba71b6] | 排除资源限制（Limit/Request）导致容器被杀或 OOM 的可能 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 [fact-1cfb938f7f0f] | 确认应用在观察窗口内未发生重启，排除启动失败 |
| 5 | Logging | Elasticsearch | 16 次 `dependency unavailable` (HTTP 503, path: /work), trace_ids: `99d36b...`, `39df9f...` [fact-logging-pattern] | 确认应用自身报告下游依赖不可用，且时间跨度与探针失败窗口一致 |
| 6 | Tracing | Deepflow/Tempo | Flow: 172.16.104.62 -> 172.16.104.16 (GET /work), response_code=503, trace_id: `3cfa8efe...` [fact-tracing-flow] | 网络层面确认 `/work` 接口确实返回 503，关联的 Trace ID 与日志记录相符 |

**证据总结：**
1. **状态与现象印证**：K8s 层面 `Pod Running` 但 `Ready=False`，直接原因是 Readiness 探针请求 `/work` 返回 503 (fact-1, fact-2)。
2. **故障机制确认**：应用日志明确记录“dependency unavailable”并返回 503，网络流量 Deepflow 记录同样捕获到该端点的 503 响应，证明故障发生在应用处理逻辑层（无法访问依赖），而非应用自身崩溃 (fact-4) 或资源不足 (fact-3)。
3. **关联性**：Tracing 中的 trace_id `3cfa8efe...` 同时出现在日志聚合和 Flow 聚合中，将 HTTP 请求、应用日志和网络流量紧密关联，确认了 `/work` 路径下的依赖调用失败。

## 🎯 根因分析 · g1

### 因果链

```text
Application dependency unavailable → /work endpoint returns HTTP 503 → Readiness probe fails (status=503) → Pod status NotReady
```

### 根因结论

**已确认的根因：应用依赖不可用导致就绪探针失败。**

1. **现象归因**：Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` 处于 `Running` 状态且 `restart_count=0` (fact-4)，排除了应用 Crash 或 OOM。
2. **直接原因**：Kubelet 对 `/work` 路径的健康检查持续返回 HTTP 503 (fact-2)。
3. **根因定位**：应用日志 (fact-5) 和分布式追踪 (fact-6) 一致表明，该 503 响应是由“dependency unavailable”引起的。即应用代码正在尝试访问某个下游依赖服务/资源，但该依赖当前不可用。
4. **缺失事实（Unknowns）**：当前事实仅确认“依赖不可用”，未明确标识该“Dependency”的具体身份（例如：具体的下游服务名、数据库或外部 API 接口）。需要额外的拓扑或详细调用链日志来明确是哪一个依赖导致了故障。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 18.5s
├─ 并发证据采集: 103.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 103.9s (Evidence 94.7s, RCA 9.0s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
