## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Readiness Probe 持续返回 503 导致 Pod 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | prometheus | `kube_pod_status_phase` = 1 (Running) / `restarts` = 0 | 确认 Pod 存活且未重启，排除了容器崩溃重启导致的暂时不可用。 |
| 2 | Metric | prometheus | `kube_pod_status_phase` (Succeeded) = 0 | 进一步确认 Pod 持续处于运行状态，非短暂任务结束。 |
| 3 | Logging | elasticsearch | 8 次 `http_request` 错误：`status=503`, `path=/work`, `message=dependency unavailable` (04:02:24 - 04:03:00) | 确认服务在请求路径 `/work` 上持续返回 503，并指向具体的业务错误“依赖不可用”。 |
| 4 | Tracing | deepflow | 9 次等效 L7 流：`GET /work`, `response_code=503`, `src=172.16.104.55`, `dst=172.16.104.35` | 从网络流层面证实了读探针发出的健康检查请求均收到了 503 响应。 |
| 5 | Tracing | tempo | `GET /work` Span 确认 `http.response.status_code=503`, `observed_mode=readiness_fail` | 提供单次请求的详细上下文，明确 503 状态被探针机制捕获。 |

**证据互证说明：**
1.  **现象确认**：日志中的 `503 dependency unavailable` (证据 3) 与 Tracing 中的 `response_code=503` (证据 4, 5) 高度一致，证实了 Pod 对外部健康检查请求的响应确实是 503 错误。
2.  **状态关联**：Metrics 证明 Pod 容器本身未发生崩溃 (证据 1, 2)，结合探针返回 503 (证据 3, 4, 5)，直接对应了“探针持续返回 503 导致 Pod 处于 NotReady 状态”的诊断事实。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用 (dependency unavailable) → GET /work 请求返回 503 → Readiness Probe 连续失败 → Pod 被标记为 NotReady
```

### 根因结论

已确认的根因是 **应用层依赖不可用导致健康检查接口持续返回 503 状态码**。

具体证据支持如下：
*   **直接机制**：Log 事实 `fact-5e0955e4ee66` 等显示，在 `/work` 路径上持续发生 `http_status: 503` 错误，且错误信息明确为 `dependency unavailable`。
*   **探针结果**：Tracing 事实 `fact-2ed9cb687744` 和 `fact-180c1ddb06b3` 等确认了探针请求最终收到的响应码为 503，且系统观测模式为 `readiness_fail`。
*   **状态表现**：Metrics 证实容器仍在运行且未重启，说明问题并非容器进程崩溃，而是业务层逻辑（依赖故障）导致的健康检查失败。

现有的多维度数据（K8s 状态、Metrics、Log、Tracing）已互相印证，充分支持该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 54.0s
├─ 问题定位: 14.5s
├─ 并发证据采集: 28.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 28.0s (Evidence 22.8s, RCA 5.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
