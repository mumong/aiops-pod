## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用容器内的依赖服务不可用，导致HTTP就绪探针在/ready端点持续返回503错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady=False` ([fact-623c37b41415]) | 容器在 Running 状态下未就绪 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` ([fact-fe9f42d4f4cf]) | 就绪探针因 HTTP 503 状态码持续失败 |
| 3 | Logging | elasticsearch | `dependency unavailable` (HTTP 503, `/work`) ([fact-40b5bbd840c7]等) | 应用日志确认为外部依赖不可用导致的服务异常 |
| 4 | Tracing | deepflow | HTTP `GET /work` 返回 `503` ([fact-0a1673ec942d]等) | 流量数据印证了 503 错误的高频重复模式 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` ([fact-4e411be39169]) | 排除因容器频繁重启导致的临时性故障 |
| 6 | K8s Config | kubernetes | CPU Limit `200m`, Memory Limit `96Mi` ([fact-03634624b47c], [fact-3c6980ea124c]) | 资源限制极低，但重启次数为 0，暂无 OOM/Kill 证据 |

Kubernetes 事件与日志深度互证：探针探测的是应用暴露的 HTTP 端点，而应用日志 `[fact-40b5bbd840c7]` 明确报出 "dependency unavailable"，直接解释了 `[fact-fe9f42d4f4cf]` 中探针为何会收到 503 错误。Tracing 数据 `[fact-0a1673ec942d]` 进一步从网络层面证实了 503 响应的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用 (事实：日志报错 dependency unavailable) → 应用逻辑处理失败，HTTP 端点 /ready 和 /work 返回 503 (事实：app日志、Flow流量) → 就绪探针持续检测 HTTP 503 失败 (事实：kubelet Event) → 容器状态 NotReady (事实：ContainersReady=False)
```

### 根因结论

已确认根因为**应用依赖服务不可用**。

这一外部依赖问题导致应用自身的 HTTP 端点（如 `/ready` 和 `/work`）无法提供正常服务，持续返回 503 状态码。Kubernetes 就绪探针（Readiness Probe）基于 HTTP 状态码进行探测，因此检测到 503 错误后判定容器未就绪，进而将 Pod 标记为 `NotReady` 状态。该结论由应用日志的直接报错（`dependency unavailable`）、HTTP 流量追踪的 503 响应以及 K8s 探针事件的失败原因三重事实闭环支撑，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.6s
├─ 并发证据采集: 69.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 69.5s (Evidence 63.7s, RCA 5.7s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
