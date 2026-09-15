## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc 处于 NotReady 状态，kubelet 持续报告 Readiness probe failed (503) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` (1454次) | 确认探针机制：应用层 HTTP 503 导致 kubelet 判定不健康 |
| 2 | K8s Config | kubernetes | `Readiness probe` 配置：`http-get /work` (推测基于错误信息) | 明确探针检查的具体路径与协议 |
| 3 | K8s Config | kubernetes | `cni.projectcalico.org/podIP`: `172.16.104.16` | 网络拓扑证据，与 Tracing 中目标 IP 一致 |
| 4 | K8s Config | kubernetes | `container.resource_request.cpu`: `20m`, `memory`: `24Mi`; `limit`: `cpu` `200m`, `memory` `96Mi` | 资源规格正常，排除资源超限（OOM/CPU Throttling） |
| 5 | K8s State | kubernetes | `ContainersReady`: `False`, `Ready`: `False`, `phase`: `Running` | 容器存活但应用层不健康，非内核或容器级故障 |
| 6 | Logging | elasticsearch | `dependency unavailable`, `http_status`: `503`, `path`: `/work` (13次, 00:59-01:44) | 应用日志证实 503 源于上游依赖不可用 |
| 7 | Tracing | deepflow | `L7_Flow`: HTTP GET `/work`, `response_code`: `503`, `src`: `172.16.104.62`, `dst`: `172.16.104.16` (9次) | 网络流证据：请求成功到达 Pod IP 并获 503 响应 |
| 8 | Tracing | tempo | `Span`: `aiops.observed_mode`: `readiness_fail`, `http.response.status_code`: `503`, `route`: `/work` | 应用侧跟踪确认就绪失败时的响应状态 |

**证据关联：**
- 日志 (fact-6) 中的 `dependency unavailable` 解释了 Tracing (fact-7) 和 Kubelet (fact-1) 中的 HTTP 503 根本原因。
- Tracing 数据 (fact-7) 确认了 `172.16.104.16` (fact-3) 上的 `/work` 端点确实收到了外部请求并返回了 503。
- K8s 状态 (fact-5) 与探针事件 (fact-1) 完全对应，无资源瓶颈干扰。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖不可用 (未确认具体组件) → 应用 /work 端点返回 HTTP 503 → Kubelet 就绪探针连续失败 (1454次) → Pod 状态 NotReady
```

### 根因结论

已确认根因：应用端点 `/work` 因**上游依赖不可用**持续返回 HTTP 503 错误。

1. **应用层异常确认**：Elasticsearch 日志明确记录 `dependency unavailable` (事实 6)，且 Temp/DLF 跟踪显示 HTTP GET `/work` 始终返回 `status_code: 503` (事实 7, 8)。
2. **Kubelet 判定结果**：由于探针路径 `/work` 持续收到 503，Kubelet 判定就绪探针失败 (事实 1)，导致容器虽运行 (`Running`) 但状态为 `NotReady` (事实 5)。
3. **缺失环节**：日志中仅提及“dependency unavailable”，未明确具体是哪个上游服务或组件故障，该部分原因未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.0s
├─ 并发证据采集: 76.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 76.0s (Evidence 65.8s, RCA 9.9s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
