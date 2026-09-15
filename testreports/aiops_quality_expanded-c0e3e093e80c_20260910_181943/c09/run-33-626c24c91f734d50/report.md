## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (x1662 over 82m) | 直接证实就绪探针因业务侧返回 503 而持续失败 |
| 2 | K8s State | Kubernetes | Pod phase=Running, Ready=False, ContainersReady=False, container[app] restart_count=0 | 证实容器进程存活且未重启，故障发生在应用逻辑层而非启动或崩溃层 |
| 3 | Logging | Elasticsearch | error log: "dependency unavailable" (http_status: 503, path: /work), 8 occurrences (first: 01:55:52.159Z - last: 01:56:20.300Z) | 证实应用侧明确因依赖缺失返回 503，且资源占用未变 |
| 4 | Tracing | Tempo | Span trace_id=3cfa8efe6e08de7a7e38cde3bae0f417: GET /work returns 503, mode=readiness_fail | 将探针的 503 失败绑定到具体的 HTTP 业务路径 `/work` |

**证据关联与冲突分析**：
- 证据 1 与证据 3 高度一致：探针因 503 失败，日志同时记录 503 并指出 "dependency unavailable"。
- 证据 3 与证据 4 互相印证：日志记录的路径与追踪到的 Span 路径一致，确认故障点位于业务处理链路中。
- 证据 2 排除了资源超限导致 OOM 重启的可能，说明故障属于外部依赖或配置层面的逻辑错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用下游依赖项不可用 → 业务逻辑返回 HTTP 503 "dependency unavailable" → Readiness Probe 持续失败 → Pod 状态标记为 NotReady
```

### 根因结论

**已确认的根因**：工作负载 `workload-5f4fb9ff45-5mlnc` 的应用逻辑无法处理请求，因为其依赖的某个服务、数据库或资源不可用，导致内部返回 HTTP 503 状态码。这直接触发了 Kubernetes 就绪探针（Readiness Probe）的持续失败，使 Pod 从可用状态转为 `NotReady`。

**支持事实**：
- `fact-7796b8d8307e`：探针日志记录状态码 503。
- `fact-0cf21e769a08` 等：应用日志明确记录 `dependency unavailable` 且伴随 HTTP 503。

**缺失的决定性事实**：
现有证据仅能确认“依赖不可用”这一表象，未能识别具体的下游依赖对象（如数据库、缓存或外部 API）以及不可用的底层原因（如网络隔离、配置错误或服务宕机），这些在 `unknowns` 中标记。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 10.7s
├─ 并发证据采集: 72.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 72.5s (Evidence 62.7s, RCA 9.6s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
