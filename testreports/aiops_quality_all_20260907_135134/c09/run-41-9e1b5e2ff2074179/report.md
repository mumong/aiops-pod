## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` 状态为 `Running`，但 `ContainersReady` 为 `False` (reason: `ContainersNotReady`) | 确认 Pod 容器进程存活但探针判定失败，未发生重启或 Crash |
| 2 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (累计触发 1662 次，持续 83 分钟) | 直接确认存活探针接收到的错误码，是造成 Pod 状态异常的直接原因 |
| 3 | K8s Config | kubernetes | 资源 Request: 20m CPU, 24Mi Memory；资源 Limit: 200m CPU, 96Mi Memory；重启次数: 0 | 排除因资源超限导致的 OOM 或重启，确认资源处于合理范围 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值为 `0` | 佐证该异常非突发宕机，而是持续的服务内部错误 |
| 5 | Logging | elasticsearch | 错误日志聚合：`dependency unavailable`，伴随 HTTP `503`，路径 `/work`；内存占用在观测窗口内稳定为 `0 MIB` | 确认错误源于应用自身依赖，且排除了内存资源受限的可能 |
| 6 | Tracing | deepflow + tempo | L7 Flow 聚合：9 次请求 `GET /work` 返回 `503` (耗时 11ms-20ms)，关联 Trace ID `eb7a9bb83a0876aedc988acf5fef61f9` | 链路数据与日志、探针结果高度一致，确认特定路由 `/work` 存在稳定的下游不可用问题 |

**证据小结**：
Kubernetes 探针与 Metrics 证实了持续性的 503 错误及无重启状态。Logging 聚合明确指出故障点在于应用内部的“依赖不可用”，且内存稳定无异常。Tracing 聚合的独立观测证实了 `GET /work` 请求返回 503 的事实。多维度数据共同锁定根因为应用自身服务逻辑或依赖项不可用。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用 → 工作负载 /work 端点持续返回 HTTP 503 → K8s Readiness Probe 检测到 503 判定失败 → Pod 状态转为 NotReady (ContainersNotReady)
```

### 根因结论

**已确认的根因**：应用工作负载 `aiops-case-09/workload-5f4fb9ff45-7b77l` 的服务内部依赖不可用，导致其提供的 `/work` 端点持续返回 HTTP 503 错误。

**证据支撑**：
- **K8s 探针与状态**：探针因持续接收 503 错误而失败，导致 Pod 状态标记为 `NotReady`（证据编号 1, 2）。
- **应用日志与指标**：日志明确聚合显示 `dependency unavailable` 错误，且内存占用稳定为 0 MIB，重启次数为 0，证实是应用内部的持续性逻辑或依赖问题，而非环境资源限制（证据编号 4, 5）。
- **分布式追踪**：独立采集的 L7 Flow 聚合数据证实了针对 `/work` 端点的 503 响应，与探针捕获的错误码完全一致（证据编号 6）。

**未知项**：
- 具体是哪个底层“依赖”（如数据库、外部 API 或微服务）导致不可用。
- 该依赖不可用的具体原因（是下游宕机、配置错误还是限流）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.7m
├─ 问题定位: 23.5s
├─ 并发证据采集: 184.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 184.7s (Evidence 175.2s, RCA 9.4s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
