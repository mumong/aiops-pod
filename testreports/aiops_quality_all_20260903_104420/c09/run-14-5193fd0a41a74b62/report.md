## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 持续处于 NotReady 状态，Readiness 探针持续返回 HTTP 503 错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-5f4fb9ff45-cfzz6` phase=Running，但 PodReady=False (ContainersNotReady: app) | 确立 Pod 正在运行但被标记为不可用的事实 |
| 2 | K8s Event | kubernetes | Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused | 提供探针失败的最初网络层原因（连接拒绝） |
| 3 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 | 确认探针在后续观测中接收到了业务逻辑层面的 503 响应 |
| 4 | Logging | elasticsearch | Pattern: `dependency unavailable` (HTTP 503, Path: /work)，连续 13 条记录 (18:20:32 - 18:21:32)，内存分配为 0 | 证实应用代码主动返回 503，原因是检测到依赖不可用 |
| 5 | Tracing | deepflow | Flow: src=172.16.104.19 → dst=172.16.104.26, HTTP GET /work, status=503, trace_ids=[d42e475060387b31724366bb7c734d2b, ...] | 关联日志中的 503 请求，展示外部流量访问该 Pod 被拒的确切证据 |
| 6 | Tracing | deepflow | DNS: src=172.16.104.26 → dst=172.30.0.10, AAAA lgtm.monitor.svc.svc.cluster.local, response_status=4 (NXDOMAIN) | 暴露应用尝试解析自身监控地址失败，属于内部网络/配置故障 |

**证据分析：**
Kubernetes 事件记录了探针从早期的“连接拒绝（connection refused）”到后期稳定的“HTTP 503”的转变（证据 2、3），说明 Pod 进程存活（Running），但其服务端口无法提供正常响应。日志聚合（证据 4）明确将 HTTP 503 归因为“dependency unavailable”，结合追踪流量（证据 5）证实该 503 是应用针对 `/work` 接口主动返回的业务错误。此外，DNS 解析失败（证据 6）暗示应用内部存在针对 `lgtm.monitor` 的严重网络或配置问题，这可能正是应用代码无法连接下游依赖的具体表现，但日志和流量未追踪到具体的外部数据库或缓存连接失败细节。

## 🎯 根因分析 · g1

### 因果链

```text
应用检测到外部依赖不可用(日志显示dependency unavailable) → 应用代码逻辑主动返回 HTTP 503 状态码 → Kubernetes Readiness Probe (GET /ready) 接收 503 响应判定失败 → Pod 状态标记为 NotReady (ContainersNotReady)
```

### 根因结论

**已确认根因：** 应用 `workload-5f4fb9ff45-cfzz6` 内部依赖不可用导致业务层返回 HTTP 503，直接引发 Kubernetes Readiness Probe 失败，从而将 Pod 标记为 NotReady。

**证据支持：**
1.  **探针失败归因**：K8s 事件显示探针最终接收到了 503 状态码（证据 3），而非持续的网络拒绝，证明应用进程在运行但服务不可用。
2.  **业务逻辑确认**：Elasticsearch 日志明确记录了 `dependency unavailable` 且伴随 HTTP 503 错误（证据 4），直接证实了 503 是应用主动返回的业务错误，而非系统崩溃。
3.  **现象吻合**：Pod 保持 `Running` 状态（证据 1），但 `Ready` 条件为 `False`，与探针失败的现象完全一致。

**已知未知（Evidence Insufficient）：**
目前无法确定“依赖不可用”的具体实体身份。日志中仅记录了通用的 `dependency unavailable` 错误模式，虽然追踪中发现了 DNS 解析 `lgtm.monitor.svc` 失败的线索（证据 6），但这可能只是监控链路的一部分，并未提供核心业务依赖（如数据库、缓存等）的连接层错误信息。因此，依赖实体的具体身份和底层故障原因（网络隔离、配置错误或服务宕机）证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 22.4s
├─ 并发证据采集: 108.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 108.1s (Evidence 97.6s, RCA 10.2s)
└─ 汇总总结: 15.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
