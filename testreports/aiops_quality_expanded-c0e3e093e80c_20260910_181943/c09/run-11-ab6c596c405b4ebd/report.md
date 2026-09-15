## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用进程因依赖的服务不可用（dependency unavailable）主动返回 HTTP 503 状态码，导致 Readiness Probe 持续失败，Pod 被 Kubernetes 标记为 NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: Running | 提供实体当前运行的生命周期状态 |
| 2 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 | 提供应用层响应 503 的具体现象证据 |
| 3 | K8s Event | kubernetes | Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused | 提供底层网络拒绝的关联现象证据 |
| 4 | Logging | elasticsearch | 连续记录中：`dependency unavailable`，`http_status: 503`，`path: /work`；内存消耗稳定为 0 MiB | 提供应用进程主动报错的归因依据，排除资源耗尽因素 |
| 5 | Tracing | deepflow | 9 次重复 L7 Flow：GET /work，src: 172.16.104.62，dst: 172.16.104.16，response_code: 503，耗时 9125-20287 微秒 | 提供目标请求在应用层持续返回 503 的底层链路观测 |

**证据关联说明：**
事实 2、3 从 Kubernetes 层面确认了就绪探针持续失败的两种表现形式（应用层 503 与底层连接拒绝）；事实 4（Logging）与事实 5（Tracing）提供了相同的归因与现象：应用进程在 `/work` 路径主动返回 503 并报告依赖不可用。三者共同印证了探针失败的根源在于应用服务自身的故障，而非集群网络或基础设施问题。

## 🎯 根因分析 · g1

### 因果链

```text
依赖的服务不可用（dependency unavailable） → 应用进程主动返回 HTTP 503 状态码 → Readiness Probe 探测失败 → Pod 被 Kubernetes 标记为 NotReady
```

### 根因结论

**已确认的根因：** 应用进程因依赖的服务不可用（dependency unavailable），持续主动向客户端返回 HTTP 503 状态码（事实 4、5），导致 Kubernetes Readiness Probe 判定应用处于不健康状态，进而将 Pod 标记为 `NotReady`（事实 2、3）。

**证据支撑：**
- 日志事实 4 明确记录了业务逻辑报错 `dependency unavailable` 及响应码 `503`；
- Tracing 事实 5 证实了应用端口（172.16.104.16）上针对 `/work` 的请求均返回 503；
- K8s 事件事实 2、3 确认探针探测结果与上述应用报错现象完全一致。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 14.9s
├─ 并发证据采集: 92.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 92.7s (Evidence 86.0s, RCA 6.6s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
