## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l NotReady, readiness probe持续返回HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 确证 Probe 探测阶段发生 TCP 连接拒绝，应用进程可能未启动或处于阻塞状态 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` | 确证应用进程已响应但业务层持续返回 503 错误状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值为 `0` | 排除因 OOMKilled 或 CrashLoopBackOff 导致的容器频繁重启 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 当前值为 `1` (Running) | 确认 Pod 底层运行状态为 Running，非 Pending 或 Evicted |
| 5 | Logging | elasticsearch | `dependency unavailable` (503, GET /work), 连续记录 8 条 | 业务层日志证实应用因下游依赖不可用而主动拒绝请求，返回 503 |
| 6 | Tracing | tempo | `GET /work` span, `http.response.status_code: 503`, 耗时约 4us | 追踪数据佐证 503 响应在应用层快速返回，非外部超时导致 |
| 7 | Tracing | deepflow | HTTP Flow: `GET /work`, `dst_ip: 172.16.104.35`, `response_code: 503`, 连续 9 次 | 流量拓扑证实目标 Pod 接收请求后持续返回 503 |

**证据分析：**
Pod 的 `Running` 状态与 `restart_count=0` 排除了容器启动失败或崩溃重启的可能。Kubernetes Events 中 `connection refused` 到 `HTTP 503` 的现象，结合 Logging 中大量的 `dependency unavailable` 错误日志，共同指向应用进程已启动，但因无法连接下游依赖（如数据库、API 或缓存）而持续返回 503。这种状态导致 Readiness Probe 判定 Pod 不健康，进而 Pod 进入 `NotReady` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用业务逻辑拒绝请求并返回 HTTP 503 → Readiness Probe 持续收到 503 → Pod 状态变为 NotReady
```

### 根因结论

**已确认根因：**
应用容器（`app`）因连接下游依赖失败（Logging 证据 #5），主动在业务层返回 `HTTP 503` 错误。该行为导致 Kubernetes Readiness Probe（探测地址 `http://172.16.104.35:8080/ready`）不断收到非成功状态码，进而将 Pod 标记为 `NotReady`（Evidence #1, #2）。

**未确认细节：**
日志中记录的错误为“依赖不可用”，但未能查明是哪一个具体的下游依赖服务（如数据库、配置中心或第三方 API）不可用，也未查明该依赖不可用的根本原因（是网络分区、配置错误还是服务宕机）（Unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 12.9s
├─ 并发证据采集: 102.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 102.2s (Evidence 92.9s, RCA 9.1s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
