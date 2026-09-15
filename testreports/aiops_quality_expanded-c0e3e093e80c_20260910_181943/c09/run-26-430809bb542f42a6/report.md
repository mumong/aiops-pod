## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc 处于 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy ... Readiness probe failed: HTTP probe failed with statuscode: 503` | 记录探针持续失败的具体状态码 |
| 2 | K8s State | Kubernetes | `ContainersReady: False` / `Ready: False` (ContainersNotReady) | 确认 Pod 未就绪状态由容器未就绪导致 |
| 3 | Logging | Elasticsearch | `dependency unavailable` (error level, HTTP 503, path: /work) | 应用自身日志确认因依赖不可用主动返回 503 |
| 4 | Tracing | Deepflow / Tempo | Flow: `GET /work` 返回 503 (src: 172.16.104.62 → dst: 172.16.104.16) | L7 流量直接证实 Pod 在处理请求时返回了服务不可用错误 |
| 5 | K8s State | Kubernetes | Pod 处于 `Running` 阶段，无重启记录 (restart_count: 0) | 排除容器崩溃重启导致的 NotReady，确认是业务逻辑故障 |

证据间相互印证：Kubernetes 探针报告 503 状态码 [1]，而应用日志 [3] 解释了产生该状态码的根本原因（依赖不可用）。Tracing 数据 [4] 从网络层面对日志和事件进行了交叉验证，确认是目标 Pod (172.16.104.16) 针对特定请求主动返回了错误，并非网络连通性或基础设施故障。

## 🎯 根因分析 · g1

### 因果链

```text
外部依赖不可用 → 应用健康检查端点返回 HTTP 503 → 探针判定失败 → Pod 处于 NotReady 状态
```

### 根因结论

根因已确认：应用内部依赖不可用导致健康检查端点持续返回 HTTP 503 错误。
Kubernetes 探针 [1] 明确检测到探针请求失败，应用日志 [3] 直接归因于 `dependency unavailable`。Tracing [4] 佐证了该 503 响应是由 Pod 业务逻辑生成。因此，Pod 的 `NotReady` 状态是应用因依赖问题主动拒绝服务的直接表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.6s
├─ 并发证据采集: 70.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 70.1s (Evidence 61.2s, RCA 8.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
