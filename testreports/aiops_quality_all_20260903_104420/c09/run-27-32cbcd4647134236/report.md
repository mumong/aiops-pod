## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 处于 NotReady 状态，Readiness Probe 持续报 HTTP 503。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | ContainersReady: False (ContainersNotReady: app); Readiness Probe failed: HTTP probe failed with statuscode: 503 | 明确当前 Pod 处于 NotReady 状态，直接原因为健康检查失败 |
| 2 | Metric | Prometheus | `kube_pod_container_status_ready` = 0 (container: app) | 从指标侧确认应用容器状态持续为未就绪 |
| 3 | Logging | Elasticsearch | 日志模式 `dependency unavailable` (http_status: 503, path: /work)，在 `19:11:59` 至 `19:12:36` 期间连续发生 8 次，`allocated_mib` 稳定为 0 | 说明应用代码在 `/work` 端点请求中因依赖缺失主动返回 503，导致健康检查失败 |
| 4 | Tracing | Deepflow/Tempo | Deepflow 捕获 9 次 `GET /work` 的 L7 Flow 返回 HTTP 503 (响应状态 3)，Tempo 记录对应 Trace (trace_id: `1d6f8dd45b2ef15147da083fe3943a40`) | 链路数据从网络请求和应用跨度层面，独立印证了 `/work` 接口持续返回 503 错误 |

证据间形成了完整的因果闭环：K8s 事件和指标确认了 Pod 的 NotReady 状态（事实 1, 2）；日志（事实 3）揭示了应用自身在 `/work` 端点持续返回 503 错误的原因是底层依赖不可用；Tracing 数据（事实 4）则通过应用跨度和网络流，精确追踪了该 503 响应的具体来源和链路特征，证实了应用侧是故障的直接发起方。

## 🎯 根因分析 · g1

### 因果链

```text
应用底层依赖不可用 (dependency unavailable) → 应用代码在 GET /work 接口主动返回 HTTP 503 → Kubelet Readiness Probe 接收 503 判定为失败 → Pod Ready 状态转为 False (ContainersNotReady)
```

### 根因结论

已确认根因为应用代码因底层依赖不可用，主动向 Kubelet 的 Readiness Probe (GET /work) 返回 HTTP 503 状态码，导致 Pod 健康检查持续失败并进入 NotReady 状态。证据编号 3 和 4 分别从应用日志和全链路追踪维度证实了 `/work` 端点 503 响应的存在及成因。

需指出，日志中仅笼统提示 `dependency unavailable` 但未指明具体是数据库、缓存还是第三方 API，属于未确认项，这妨碍了直接修复该底层依赖。此外，日志中的 `allocated_mib: 0` 数值异常也可能反映了资源隔离或监控记录层面的问题，但这不影响对当前应用层面返回 503 这一直接根因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 29.1s
├─ 并发证据采集: 85.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 85.2s (Evidence 72.9s, RCA 12.1s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
