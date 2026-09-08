## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | {'type': 'Warning', 'reason': 'Unhealthy', 'message': 'Warning  Unhealthy       4m35s (x519 over 29m)  kubelet            Readiness probe failed: HTTP probe failed with statuscode: 503'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-1c282b6e24f0) | 确证就绪探针持续失败的现象 |
| 2 | K8s State | Kubernetes | `Ready`: `False` / `ContainersReady`: `False` (fact-1a7a09dfb807) | 反映 Pod 当前 NotReady 状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `0` (fact-d5fdc63723d1) | 排除容器频繁重启导致启动异常的可能 |
| 4 | Logging | Elasticsearch | `dependency unavailable`, `http_status`: 503, `path`: `/work` (fact-5d4bbbece160) | 确认应用进程自身在响应内部依赖请求时的逻辑失败 |
| 5 | Tracing | Tempo | `GET /work` 503 (trace_id: `cd230732dd175914a43aa596f86fcfed`) (fact-1802b61c7265) | 提供特定失败时刻的 L7 请求级证据 |
| 6 | Topology | DeepFlow | `src_ip`: 172.16.104.55 -> `dst_ip`: 172.16.104.35 (HTTP 503) (fact-858f043c6099) | 仅证明应用容器是 503 响应的发起者，未捕获出网目标 |

证据说明：
1. **现象一致性**：K8s 探针 (证据1)、Pod 状态 (证据2)、应用日志 (证据4) 及 Tracing 链路 (证据5) 高度一致，共同指向应用容器在 `/work` 请求中因内部依赖不可用返回 503。
2. **网络路径断点**：DeepFlow 数据 (证据6) 确认了源端 IP，但由于缺乏完整的出站流量记录或拓扑数据，无法进一步定位导致该 503 的下游目标 IP 或域名。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖 unavailable（未确认下游实体） → /work 路径返回 503 → Readiness 探针检查失败 → Pod 被标记为 NotReady
```

### 根因结论

已确认的直接故障现象是应用容器 `aiops-case-09/workload-5f4fb9ff45-7b77l` 因无法获取内部依赖（`dependency unavailable`），导致健康检查端点持续返回 503。
但现有证据不足以确定**根本原因（Root Cause）**，因为缺乏拓扑数据来揭示该内部依赖的具体目标（例如具体的 DB 实例、缓存服务或其他下游微服务）。由于无法确定依赖不可用的具体底层原因（是目标宕机、网络不通还是认证失败），当前结论停留在业务层面，证据不足以判定系统级故障根因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 30.0s
├─ 并发证据采集: 76.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 76.5s (Evidence 65.6s, RCA 10.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
