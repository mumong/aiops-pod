## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用依赖不可用导致Readiness Probe持续返回503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 98m`: Readiness probe failed: HTTP probe failed with statuscode: 503 | 明确 Readiness Probe 探测到 HTTP 503 响应，触发 Pod 状态异常 |
| 2 | K8s State | Kubernetes | `Pod.condition`: type=Ready, status=False, reason=ContainersNotReady | 确认 Pod 已转为 NotReady 状态 |
| 3 | K8s Config | Kubernetes | `container.resource_request.cpu`: 20m; `container.resource_limit.memory`: 96Mi | 排除资源限制导致的容器异常 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 排除因容器频繁重启导致的应用不可用 |
| 5 | Logging | Elasticsearch | 日志模式 `dependency unavailable` (HTTP status 503, path /work)，首次 `2026-09-07T20:32:57`，连续 8 次出现 | 证实应用自身在 `/work` 接口返回了 503 |
| 6 | Tracing | Deepflow/Tempo | L7 Flow: 172.16.104.55 -> 172.16.104.35, GET /work, status 503; Tempo Span: `aiops.observed_mode=readiness_fail` | 关联底层网络请求与应用日志，确认 Readiness Probe 路径返回了 503 |

**证据印证说明**：
Kubernetes 侧的 Readiness 探测失败（证据1、2）与 Elasticsearch 侧的应用 503 报错（证据5）完全吻合。Tracing 维度（证据6）进一步确认了这些 503 响应发生在 `/work` 接口，并明确标注为 `readiness_fail` 模式。Pod 重启计数为 0（证据4）排除了应用自身崩溃的可能，确认为应用处理请求时的业务或依赖逻辑错误。

## 🎯 根因分析 · g1

### 因果链
```text
应用依赖组件不可用 → 应用HTTP服务对Readiness Probe请求返回503 → Kubelet持续检测Readiness失败 → Pod状态转为NotReady
```

### 根因结论
已确认根因为**应用依赖不可用**。
应用对 Readiness Probe 请求（`/work` 路径）持续返回 503 状态码，导致 Kubelet 判定应用不健康，进而将 Pod 状态设为 NotReady。Tracing 数据确认该 503 响应与 Readiness 探针模式一致（证据 #6）。虽然确认为“应用依赖不可用”，但底层的具体依赖组件名称及其故障原因（如网络、配置或下游服务问题）在当前事实中未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.9s
├─ 并发证据采集: 97.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 97.2s (Evidence 88.0s, RCA 9.0s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
