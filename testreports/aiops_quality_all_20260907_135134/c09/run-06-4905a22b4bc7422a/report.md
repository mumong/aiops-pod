## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod NotReady, Readiness probe fails with HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-ba8cf48689ee) | 确证就绪探针失败的具体状态码为 503 |
| 2 | K8s Event | kubernetes | `dial tcp 172.16.104.35:8080: connect: connection refused` (fact-e6fd512cace9) | 记录历史连接拒绝事件，用于区分当前的网络连通性问题 |
| 3 | K8s State | kubernetes | Pod `Running`，重启次数 `0` (fact-05a6639c7ede, fact-f9be02c90be8) | 排除因 OOMKilled 或 CrashLoopBackOff 导致的应用进程终止 |
| 4 | K8s Config | kubernetes | CPU limit `200m`, Memory limit `96Mi` (fact-a80b79fa52c1, fact-d672c6bc477d) | 排除资源硬限制导致应用无法启动的迹象 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 为 `0` (fact-1a5c8bdd52df) | 确认应用自启动以来未发生过异常重启 |
| 6 | Logging | elasticsearch | `dependency unavailable` (HTTP 503, path: `/work`) 模式重复 8 次，窗口：`19:05:43 - 19:06:21` (fact-490f3420ea8b...) | 确认应用自身因依赖不可用而主动返回 503 错误 |
| 7 | Tracing | deepflow | `GET /work` 流量 9 次，响应码 `503` (fact-60b7eebd7ea4...) | 网络层流量证实了应用对外提供的服务持续返回 503 |
| 8 | Tracing | tempo | Span `GET /work`，Trace `25758edb4a1fd369a0ec6286ba8e08d4`，耗时 3us (fact-3d0b989c1cf8) | 应用本地处理极快但立即返回 503，符合逻辑拒绝特征 |

**证据关联说明：**
证据 1、5 与 6、7 共同指向同一现象：应用进程处于运行状态（未重启、无资源瓶颈），但持续向外界返回 HTTP 503 状态码。证据 6（应用日志）提供了 503 的语义解释（依赖不可用），证据 8（Tracing）证实了该请求并未深入处理业务逻辑（极短耗时），符合本地依赖检查失败的典型特征。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖不可用 → 应用内部依赖检查失败 → 应用主动返回 HTTP 503 (path: /work) → 就绪探针 GET /ready 收到 503 失败 → Pod 状态 NotReady
```

### 根因结论

**已确认根因**：应用因内部依赖不可用（日志记录 "dependency unavailable"）导致对外提供服务时持续返回 HTTP 503。

**分析**：
- 证据 6 和 7 证实应用进程存活且处理请求，但响应均为 503。
- 证据 1 确认 Pod 状态变为 NotReady 的原因是就绪探针（GET /ready）收到了 503 响应。
- 缺失决定性事实：日志和追踪仅展示了“依赖不可用”这一结果，未揭示具体是哪个外部组件（如数据库、缓存或第三方 API）导致了此状态（unknowns: 外部依赖故障的具体来源在 Pod 日志/追踪中不可见）。

因此，当前现象的直接根因为**应用因依赖问题主动返回 503**，但具体的**依赖故障根源证据不足**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.7s
├─ 并发证据采集: 64.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 64.8s (Evidence 57.3s, RCA 7.3s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
