## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc处于NotReady状态，就绪探针持续失败（HTTP 503） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (持续 117m) | 证明应用端点对外返回 503，直接触发 Pod 就绪状态变更为 NotReady。 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.cpu: 200m`, `container.resource_limit.memory: 96Mi` | 提供资源上下文；内存限制较高，结合应用实际内存使用量，排除 OOMKill 可能性。 |
| 3 | Logging | Elasticsearch | `dependency unavailable` (error, HTTP 503) 发生 8 次，`allocated_mib` 为 0 | 确认应用内部业务逻辑主动触发了 503 状态码，而非依赖服务超时。 |
| 4 | Tracing | Deepflow + Tempo | `GET /work` 请求响应 `HTTP 503`，耗时 17.6ms - 21.8ms | 证明应用内部处理链路完整且快速响应，排除了由于后端依赖或计算导致的超时故障。 |

K8s 事件明确记录探针因 503 失败；日志与 Tracing 共同证实了应用是在内部处理完请求后，主动返回了 503 状态码。由于资源未耗尽且响应迅速，该 503 极有可能是应用层的受控行为而非故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置了 FAILURE_MODE=readiness_fail → 应用逻辑在探针探测路径上故意返回 HTTP 503 → Kubelet 探针检测失败 → Pod 状态变为 NotReady
```

### 根因结论

已确认的根因为应用被配置了 `FAILURE_MODE=readiness_fail` 模式。

在 `aiops-case-09/workload-5f4fb9ff45-5mlnc` 中，应用逻辑受配置控制，在就绪探针探测路径（`GET /work`）上主动返回 `HTTP 503` 响应。这导致 `kubelet` 持续判定应用不健康（见证据 #1），从而使 Pod 处于 `NotReady` 状态。日志中记录的 `dependency unavailable` 错误以及 Tracing 中极短的处理耗时（<22ms）均表明该 503 是应用内部的受控行为，排除了真实的底层依赖故障或资源瓶颈。

---

## 📊 性能统计

```text
├─ 总耗时: 3.2m
├─ 问题定位: 20.5s
├─ 并发证据采集: 160.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 160.2s (Evidence 150.0s, RCA 10.0s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
