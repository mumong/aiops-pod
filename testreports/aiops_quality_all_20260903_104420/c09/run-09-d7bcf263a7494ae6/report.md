## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用代码对就绪检查路径（/work）返回 503 且日志报错 'dependency unavailable' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Running; `pod.condition.Ready`: False (`ContainersNotReady`, `app`) | 确认应用运行中但处于未就绪状态 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` | 证明就绪探针因连接拒绝而失败，Pod 地址为 172.16.104.26 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 证明在部分探针执行时，应用显式返回了 503 错误 |
| 4 | Logging | elasticsearch | `pattern`: `error dependency unavailable http_status: 503 path: /work` (occurrence: 8) | 确认应用代码在内部依赖不可用时返回了 503 错误 |
| 5 | Tracing | deepflow | `l7_flow`: HTTP GET /work `172.16.104.19 -> 172.16.104.26`, response_code: 503 (occurrence: 9) | 独立于探针的网络层观测证实目标 IP 持续返回 503 响应 |
| 6 | Tracing | tempo | `span`: GET /work, status_code: 503, trace_id: `d882babe0b383bda1a35dd7116d979a4` | 追踪关联确认了该 HTTP 503 响应与特定 Trace 绑定 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 排除了因 OOM/Killed 导致的频繁重启（未观察到资源限制导致的重启） |

**证据分析：**
Kubernetes 探针（#2, #3）显示应用针对就绪检查返回连接拒绝或 503 错误；Logging 聚合（#4）和 Tracing 观测（#5, #6）从网络和应用代码层面独立证实了应用在处理 `/work` 请求时主动返回了 503，并伴随 `dependency unavailable` 日志。Metric 数据（#7）确认了容器处于稳定运行状态，未发生重启，将故障范围锁定在应用逻辑而非宿主或运行时资源。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖不可用 → 就绪探针（/work）HTTP 返回 503 且伴随错误日志 → Pod Ready 条件置为 False → 集群标记 Pod 为 NotReady
```

### 根因结论

已确认根因为**应用代码内部依赖不可用导致就绪检查（`/work`）返回 HTTP 503**。
- **证据支撑**：
  - `K8s Event` 显示探针连续失败，既遇到 `connection refused` 也遇到显式的 `503` 状态码（#2, #3）。
  - `Logging` 聚合明确记录了应用层在 `/work` 路径返回 503 时，消息为 `dependency unavailable`（#4）。
  - `Tracing` 数据独立证实了从客户端到该 Pod 的流量持续收到 503 响应（#5, #6）。
- **结论**：应用的健康检查端点未能通过，表明服务尚未达到可以接收流量的就绪状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.5s
├─ 并发证据采集: 60.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 60.2s (Evidence 54.6s, RCA 5.4s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
