## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Application dependency unavailable causing health check endpoint (/ready) to return HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `phase: Running`, `restart_count: 0` | 证明应用容器未发生 OOMKilled 或 CrashLoopBackOff，排除了容器级稳定性问题 |
| 2 | K8s Event | K8s Readiness Probe | `connection refused` (172.16.104.16:8080); `HTTP statuscode: 503` | 确认应用进程存活但拒绝连接，且健康检查端点 `/ready` 返回失败 |
| 3 | Logging | Elasticsearch Logs | `http_status: 503`, `path: /work`, `message: dependency unavailable` (8次) | 提供应用层根因，确认应用因内部依赖不可用而主动返回 503 |
| 4 | Tracing | Tempo/DeepFlow | `GET /work` Span: `http.response.status_code: 503`; `duration: 12ms~99ms` | 链路追踪证实请求在应用层直接响应 503，非基础设施网络故障 |

日志（#3）明确指出“dependency unavailable”是应用返回 503 的直接原因，该响应状态被 K8s Readiness Probe（#2）捕获并判定为 `NotReady`，导致探针报错。追踪数据（#4）与日志和事件在时间线上一致，进一步排除了底层资源不足（#1）或重启问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用 → /ready 端点返回 HTTP 503 → Kubelet 探针判定失败 (NotReady) → Pod 状态为 NotReady
```

### 根因结论

已确认的根因是**应用内部依赖不可用导致健康检查端点返回 HTTP 503**。

日志记录（证据#3，fact_id: `fact-2fff8f68125d` 等）明确记录了 `dependency unavailable` 的错误模式，证实应用自身因依赖问题无法提供正常服务。这一行为直接触发了 Kubernetes 探针（证据#2，fact_id: `fact-1b12ba35522f`）的 `connection refused` 和 `HTTP statuscode: 503` 失败。结合 Pod 运行状态稳定且无重启（证据#1），故障被精确定位在应用逻辑依赖层面，而非基础设施或资源问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.7s
├─ 并发证据采集: 70.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 70.0s (Evidence 64.4s, RCA 5.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
