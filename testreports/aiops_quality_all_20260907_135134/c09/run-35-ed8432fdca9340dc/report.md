## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Service readiness check consistently returning HTTP 503 (dependency unavailable) prevents kubelet from marking the container Ready. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (x1350 over 69m) | 直接证明就绪探针持续失败，是导致 Pod 状态异常的直接原因 |
| 2 | K8s State | Kubernetes | `ContainersReady: False`, `Ready: False`, reason: `ContainersNotReady` | 确认应用容器 `app` 未就绪，Pod 整体处于 NotReady 状态 |
| 3 | Logging | Elasticsearch | 8 次聚合日志显示 `event: http_request`, `error: dependency unavailable`, `http_status: 503` | 揭示应用逻辑层面的具体错误信息，将探针失败归因于“依赖不可用” |
| 4 | Tracing | Deepflow/Tempo | HTTP GET /work 返回 503 (src_ip: 172.16.104.55 -> dst_ip: 172.16.104.35); Trace ID: `19d91041c588289dbde79a42192f2e1e` | 从流量维度确认 `/work` 接口持续返回 503，与日志和探针结果形成闭环 |

**证据关联说明**：Kubernetes 事件（#1, #2）记录了系统层面的探针失败和状态异常；日志（#3）和链路追踪（#4）提供了应用层面的归因（HTTP 503 "dependency unavailable"）。Trace ID 将 L7 流量与应用日志关联，确认了 `/work` 端点因依赖问题持续返回 503，直接导致了 K8s 就绪探针的持续失败。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖故障或配置错误 → 应用 /work 接口返回 HTTP 503 "dependency unavailable" → 就绪探针（Readiness probe）持续返回 503 失败 → Pod 状态变为 NotReady
```

### 根因结论

**已确认根因**：应用容器内部调用依赖组件失败，导致应用 `/work` 接口持续返回 HTTP 503 状态码（“dependency unavailable”）。这一应用层错误直接触发了 K8s 就绪探针的连续失败，从而阻止了 Pod 标记为 Ready 状态。

**证据支持**：
- 日志明确记录了 "dependency unavailable" 错误（证据 #3）。
- 链路追踪和探针事件均捕获了相同的 HTTP 503 响应（证据 #1, #4）。

**未确认/证据不足**：
- 具体是哪个“上游依赖”（如数据库、缓存或第三方服务）发生故障，以及该依赖故障的具体原因，当前证据链中未体现，属于“dependency unavailable”的确切所指，暂无法定位。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 19.6s
├─ 并发证据采集: 77.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 77.8s (Evidence 70.4s, RCA 7.3s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
