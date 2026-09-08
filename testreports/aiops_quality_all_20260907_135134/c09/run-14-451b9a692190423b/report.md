## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | {'type': 'PodScheduled', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (fact-211276139e55) | 确认 Kubelet 探测端点不可达，直接触发 Pod 降级 |
| 2 | K8s State | kubernetes | `Ready=False`, reason: `ContainersNotReady` (fact-685d3c61de75) | 证实 Pod 当前状态为 NotReady |
| 3 | K8s Config | kubernetes | `resource_request.cpu=20m`, `resource_limit.cpu=200m` (fact-09e4a11ae66e, fact-0472594d856d) | 资源限制极低，但重启计数为 0 (fact-65a8516c28c4)，排除 OOM/过载重启 |
| 4 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-0356d5ab8779) | 确认端点可达但应用层返回 503 错误 |
| 5 | Logging | elasticsearch | `http_status: 503`, `message: "dependency unavailable"`, path: `/work` (fact-5ca7c929d754 等 8 条) | 确认应用业务逻辑中依赖失败，返回 503 |
| 6 | Tracing | deepflow | `GET /work`, `response_code: 503`, `src_ip: 172.16.104.55`, `dst_ip: 172.16.104.35` (fact-6a90391f639c 等 9 条) | 外部流量到目标 Pod 均返回 503，且耗时稳定 10ms-19ms |
| 7 | Tracing | tempo | `aiops.observed_mode: "readiness_fail"`, `http.response.status_code: 503` (fact-d27871b75230) | 追踪上下文佐证 Pod 内部健康检查端点处于失败状态 |

**证据关联分析：**
- 证据 2 与证据 4、5 互相印证：Pod NotReady 的直接原因是 Readiness 端点连续返回 503，而日志 (fact-5ca7c929d754) 明确指出了返回 503 的原因是“依赖不可用”。
- 证据 3 排除了资源（CPU/内存）限制导致的宕机或重启可能（重启次数为 0），说明应用虽然存活但未就绪。
- 证据 1 中的 `dial tcp ... connection refused` 是 Kubelet 探测失败的具体 TCP 错误，与证据 4 中的 503 状态码共同描述了探测失败的不同表现阶段（可能探测端点未完全绑定或应用初始化期间）。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的下游服务/资源不可用 → 应用内部逻辑处理依赖失败并返回 HTTP 503 → Kubelet Readiness Probe 探测连续失败 → Pod 状态变更为 NotReady
```

### 根因结论

**已确认的根因：**
Pod 内部应用代码的逻辑依赖于某个外部服务或资源，该依赖在当前窗口内不可用（具体依赖名称未通过日志或 Trace 明确标识）。由于应用逻辑在检测到依赖失败时直接返回了 `503 dependency unavailable`（见 Logging 证据 #5 和 Tracing 证据 #6），导致 Kubernetes 配置的 Readiness Probe（探测路径 `/work` 或 `/ready`）持续收到 503 响应（见 Event 证据 #1, #4）。根据 Kubernetes 机制，连续探测失败导致 Pod 状态标记为 `NotReady`（见 State 证据 #2）。

**不确定性说明：**
虽然确定了“应用内部依赖不可用”这一层级原因，但具体的依赖服务名称（如数据库、缓存或另一微服务）以及依赖不可用的根本原因（如配置错误、服务宕机或网络隔离）在当前日志和追踪数据中未被明确标识或关联，属于未确认事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.4s
├─ 并发证据采集: 75.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 75.2s (Evidence 65.8s, RCA 9.2s)
└─ 汇总总结: 15.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
