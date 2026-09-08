## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用依赖不可用导致 readiness 探针持续返回 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pod` 状态 `Running`，`Ready` 状态为 `False`，原因 `ContainersNotReady`；`restart_count` 为 0 | 确认应用正在运行但未就绪，且进程未发生崩溃重启 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (7s 内连续 1974 次) | 确保持续 503 错误导致就绪探针失败，这是 Pod 不 Ready 的直接原因 |
| 3 | Logging | Elasticsearch | 模式 `http_request` [error]，日志 message `dependency unavailable`，路径 `/work`，状态 503 | 提供应用内部视角，确认 503 是由“依赖不可用”导致，而非网络或配置错误 |
| 4 | Tracing | Deepflow | L7 Flow 聚合：`GET /work` 请求到 `172.16.104.35`，响应 503 (status: 3)，耗时 12-20ms | 网络流量层证实应用正在正常处理入站请求并主动返回 503 状态码 |
| 5 | Tracing | Tempo | Span `GET /work` 的 `http.response.status_code` 为 503 | 与日志和流量数据交叉验证，确认是业务逻辑导致的 503 错误 |

**证据关联说明：**
Kubernetes 的 503 探针失败（#2）直接由应用返回 503 响应导致；应用日志（#3）和追踪链路（#4, #5）共同证实，503 是在请求处理过程中因 `dependency unavailable` 而主动返回的，排除了基础设施故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖不可用 → 业务逻辑主动返回 HTTP 503 → Readiness 探针接收 503 → Pod Ready 状态置为 False
```

### 根因结论

已确认根因：**应用依赖不可用**。

应用正在运行且未发生崩溃（`restart_count: 0`），但处理请求时因内部依赖不可用而主动返回 503 状态码。这导致 Kubernetes 的 Readiness 探针持续检查失败，Pod 始终处于 `NotReady` 状态，无法被 Service 流量接入。所有维度数据（K8s 探针、应用日志、Trace Span）均一致指向“依赖不可用导致主动 503”这一事实。

---

## 📊 性能统计

```text
├─ 总耗时: 9.5m
├─ 问题定位: 17.3s
├─ 并发证据采集: 543.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 543.8s (Evidence 538.1s, RCA 5.5s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
