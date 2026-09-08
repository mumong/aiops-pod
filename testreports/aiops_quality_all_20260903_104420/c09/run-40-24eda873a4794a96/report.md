## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` Ready=False (ContainersNotReady)；`restart_count`: 0 (fact-1328ee3decf5, fact-1c5235786caa) | 确认异常状态及无重启迹象，排除启动循环或重启导致的不稳定 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy 30s` Readiness probe failed: HTTP probe failed with statuscode: 503 (fact-2dfbdf61ea75) | 直接指向就绪探针因 HTTP 503 错误而持续失败 |
| 3 | Logging | Elasticsearch | Pattern `http_request` (level: error, message: "dependency unavailable", http_status: 503, path: "/work") 发生 8 次 (fact-6fa585aefa61) | 应用侧日志记录了具体的业务层错误和请求路径 |
| 4 | Tracing | Deepflow | HTTP GET `/work` 返回 `response_code`: 503，耗时 min: 19047us，与日志关联的 trace_ids 存在 (fact-5b0f71b7b356) | 流量观测证实了 503 状态码及该端点在高延迟下仍然不可用 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-7e83ee17c7f6) | 印证 K8s State，排除因 OOMKilled 或 CrashLoopBackOff 引起的重启 |

**证据分析：**
1. K8s Event (证据 2) 明确指出了 Probe 失败的直接原因是 HTTP 503。
2. Logging (证据 3) 与 Tracing (证据 4) 相互印证，确认了导致 503 的具体路径为 `/work` 且业务层错误为 `dependency unavailable`。
3. 所有证据（事件、日志、流量）在时间窗口上相互匹配，共同指向应用层依赖故障，而非基础设施层（如调度、网络插件）的问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用底层依赖不可用 (dependency unavailable) → /work 端点返回 HTTP 503 (Service Unavailable) → kubelet Readiness Probe 连续失败 (statuscode: 503) → Pod 状态变为 NotReady (ContainersNotReady)
```

### 根因结论

已确认的根因是**应用层下游依赖不可用**。

具体表现为：应用在处理 `GET /work` 请求时，由于检测到 `dependency unavailable` 而直接返回了 `HTTP 503 Service Unavailable` 状态码（见 Logging 事实 3 和 Tracing 事实 4）。这一持续的业务层错误触发了 Kubelet 发起的 Readiness 探针连续失败（见 K8s Event 事实 2），导致 Kubernetes 将该 Pod 标记为 `NotReady`（见 K8s State 事实 1）。

**缺失的决定性事实：**
日志中的错误信息 `dependency unavailable` 较为笼统，无法识别出具体是哪个下游组件（如数据库、Redis 缓存或第三方 API）出现了故障。因此，虽然可以确定根因属于应用依赖层，但具体依赖目标未知。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 33.7s
├─ 并发证据采集: 95.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 95.5s (Evidence 83.4s, RCA 11.9s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
