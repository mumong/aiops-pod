## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 下游依赖服务不可用导致应用层HTTP 503响应 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `Running`，但 `Ready`、`ContainersReady` 状态均为 `False`，原因 `ContainersNotReady` | 确认 Pod 运行正常但因应用层问题导致健康检查失败 |
| 2 | K8s Event | Kubernetes | `Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (发生 2493 次) | 提供健康检查失败的直接证据 |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存限制 `96Mi`，请求 `24Mi` | 排除因资源硬限制导致 OOM 的可能 |
| 4 | K8s Event | Kubernetes | CNI 网络状态显示 Pod IP `172.16.104.16` | 确认 Pod 网络配置正常 |
| 5 | Logging | Elasticsearch | 日志模式 `dependency unavailable`，HTTP 状态 503，路径 `/work` (8 次观测，时间窗 `02:35:09 - 02:35:42`) | 确认下游依赖服务不可用导致应用层返回 503 |
| 6 | Tracing | Deepflow | HTTP L7 Flow：`GET /work` 状态码 `503`，源 IP `172.16.104.62` -> 目标 IP `172.16.104.16` (9 次观测，耗时约 18ms-21ms) | 证实流量确实抵达 Pod 且由 Pod 返回 503，网络链路正常 |
| 7 | Tracing | Tempo | Span `GET /work` 响应 503，标注 `aiops.observed_mode: readiness_fail` (trace_id: `98f2342...`) | 独立于日志的追踪证据，确认应用行为 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 确认应用进程未发生重启，排除了 CrashLoopBackOff 类问题 |

证据表明，Pod 运行且网络可达（`Deepflow` 显示流量到达），但未通过 `Readiness Probe`。`Elasticsearch` 日志与 `Tempo` 追踪均一致记录应用因“下游依赖服务不可用”在 `/work` 路径返回 503。由于内存限制充足且无重启记录，判定该问题非资源或稳定性故障，而是应用逻辑层面的外部依赖问题。

## 🎯 根因分析 · g1

```text
下游依赖服务不可用 → 应用返回 503 → 就绪探针（Readiness Probe）检测到 503 返回码 → Pod 被标记为 NotReady
```

### 根因结论
**已确认的根因：下游依赖服务不可用导致应用层返回 HTTP 503。**

应用逻辑中调用下游依赖失败（证据 #5、#6、#7），导致服务无法正常响应就绪探针（证据 #2）。由于就绪探针配置预期返回 200 类成功状态码，503 响应直接导致 Kubernetes 将 Pod 状态标记为 `NotReady`（证据 #1）。

该结论得到了多维度的事实交叉验证：Kubernetes 探针事件确认了失败现象，日志确认了 503 的根本原因（依赖不可用），追踪系统确认了 503 是由 Pod 自身返回且网络可达。目前证据充分，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.4s
├─ 并发证据采集: 66.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 66.7s (Evidence 60.6s, RCA 5.9s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
