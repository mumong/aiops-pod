## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用内部依赖服务不可用，导致应用进程在处理请求时返回 HTTP 503 状态码，进而使得 Kubernetes Readiness Probe 持续失败，Pod 保持在 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 处于 `Running` 阶段，但 Pod 状态为 `NotReady`（`ContainersNotReady`） | 确认应用容器正在运行但被 K8s 标记为不可用，直接对应“应用内部依赖不可用”的假设 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (x519 over 29m) | 证明 K8s 对 Pod IP `172.16.104.26` 的 `:8080/ready` 探针持续收到 503 错误，排除了网络不通（如 connection refused）作为当前唯一原因 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused (x2 over 29m) | 提供早期或偶发的网络拒绝证据，但当前主要表现为 503，说明连接建立成功但应用层拒绝服务 |
| 4 | Logging | Elasticsearch | 8 条重复日志：`event="http_request"`, `level="error"`, `message="dependency unavailable"`, `http_status=503` (18:22:53 - 18:23:25) | 证实应用代码在处理请求时，因下游依赖不可用而主动返回了 503 状态码，与探针失败原因一致 |
| 5 | Tracing | Tempo | Span `GET /work` 记录：`http.response.status_code=503`, `aiops.observed_mode=readiness_fail` (trace: d42e475060387b31724366bb7c734d2b) | 将 HTTP 503 响应与具体的业务路由 `/work` 和探针失败模式关联 |
| 6 | Tracing | Deepflow | 9 个 L7 Flow：`GET /work` 请求至 Pod IP `172.16.104.26:8080`，返回 `response_code=503` | 跨网络层面确认了请求成功到达 Pod 且 Pod 返回了 503，而非请求未到达 |

上述证据相互印证：K8s 探针（#2, #3）持续收到 503 导致 Pod 标记为 `NotReady`（#1）。日志（#4）和追踪（#5, #6）从应用内部确认了该 503 并非由于网络故障或服务未启动，而是应用在处理请求时因 `dependency unavailable` 主动抛出的业务错误。资源配置（Memory 96Mi, CPU 200m）正常且未触发重启，排除资源耗尽导致的崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务或资源不可用 (dependency unavailable) → 应用处理请求时抛出 503 错误 → Kubernetes Readiness Probe 持续收到 503 状态码 → Pod 被标记为 NotReady
```

### 根因结论

**已确认的根因**：应用内部依赖的下游服务或资源不可用（`dependency unavailable`）。

该根因通过以下事实链确证：
1. **应用层行为**：日志（#4）和追踪（#5）一致表明，应用在 `/work` 等业务端点因依赖不可用主动返回了 HTTP 503 状态码。
2. **探针层响应**：K8s Readiness Probe（#2）持续探测 `/ready` 端点并收到相同的 503 响应（519次），导致探针判定应用不健康。
3. **最终状态**：探针失败导致 Pod 状态由 `Ready` 转为 `NotReady`（#1），表现为服务不可用。

当前证据完整，无需进一步猜测。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.0s
├─ 并发证据采集: 64.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 64.8s (Evidence 56.7s, RCA 7.9s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
