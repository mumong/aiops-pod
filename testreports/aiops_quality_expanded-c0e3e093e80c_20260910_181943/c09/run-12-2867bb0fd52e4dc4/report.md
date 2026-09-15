## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc 状态 NotReady，Readiness Probe 持续返回 HTTP 503。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-66852b3824b7) | 确认 Kubelet 判定探针失败，Pod Ready 状态异常 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: dial tcp 172.16.104.16:8080: connect: connection refused` (fact-2b33c3c08ae4) | 早期探针失败记录，反映应用服务不可达状态 |
| 3 | K8s State | Kubernetes | Pod `Running`，但 `Ready=False`，`ContainersReady=False` (fact-7e993f41b6f0, fact-4510392821db) | 确认 Pod 容器已启动但未通过就绪检查 |
| 4 | Logging | Elasticsearch | 模式：`dependency unavailable`, `http_status: 503`, `path: /work`，出现 8 次 (fact-359e6551f275) | 提供直接应用日志证据，确认为下游依赖问题 |
| 5 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 `503`，源 IP `172.16.104.62` -> 目标 IP `172.16.104.16` (fact-45c3bcf6a861) | 跨维度观测确认 Pod 对外服务持续返回 503 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `0` (fact-03c66cba0ab4) | 排除应用频繁重启导致的不稳定因素 |

- **证据印证**：Kubernetes 探针持续报 503 (E1) 与日志 (E4) 及 Trace (E5) 中的 503 错误直接对应，形成“探针失败 -> 应用报错 -> 流量失败”的闭环。
- **维度互补**：Trace 数据 (E5) 与日志数据 (E4) 虽未直接关联 Trace ID，但一致指向 `/work` 端点的 503 故障，且无重启记录 (E6)，表明故障持续发生。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的服务不可用 → 应用 /work 端点返回 HTTP 503 ("dependency unavailable") → Kubelet 探针判定失败 → Pod Ready 状态转 False
```

### 根因结论

- **已确认的根因**：应用因下游依赖服务不可用（日志记录 `dependency unavailable`），导致自身的就绪检查端点返回 HTTP 503。
- **证据支撑**：该结论由 Kubernetes Readiness Probe 的 503 失败事件、应用日志中的 `dependency unavailable` 错误以及外部流量对 `/work` 路径持续返回 503 的跨维度观测共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.0s
├─ 并发证据采集: 65.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 65.9s (Evidence 57.8s, RCA 8.0s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
