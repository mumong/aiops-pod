## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Application logic returning 503 due to 'dependency unavailable' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Pod phase=Running`, `status=NotReady` (ContainersNotReady)；`restart_count=0` | 确认 Pod 运行中但因应用层问题处于不可用状态，且无重启波动，排除不稳定性崩溃。 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy`: `Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接暴露就绪探针失败的具体机制，是应用进入 NotReady 状态的直接触发器。 |
| 3 | K8s Config | kubernetes | `container.app` limits: `CPU=200m`, `memory=96Mi`；requests: `CPU=20m`, `memory=24Mi` | 提供资源边界上下文，确认配置并非极端限制，非调度或资源争抢类异常。 |
| 4 | Logging | elasticsearch | 错误日志模式 `event: http_request, level: error, message: "dependency unavailable", http_status: 503`；时间窗口 2026-09-03T18:59:16 至 18:59:50；`numeric_fields.allocated_mib` 始终为 0 | 聚合的 8 次相同日志确认应用内部逻辑因依赖不可用主动抛出 503，且应用内存消耗极低（0 MiB）。 |
| 5 | Tracing | deepflow | L7 Flow: `GET /work` → 503；来源 `172.16.104.19`，目标 `172.16.104.26` (Pod IP)；持续时间 18-23ms | 独立于日志的网络流证据，复现了外部请求进入 Pod 后立刻返回 503 的行为特征。 |

**证据印证与冲突说明**：
1. K8s 事件（#2）与日志模式（#4）、Trace 流（#5）在错误代码 `503` 和异常时间上完全一致，共同证明应用逻辑在健康检查及用户请求期间均返回 `dependency unavailable`。
2. Pod 状态（#1）与 Trace 流（#5）中明确的源/目标 IP 对应关系相互印证，确认故障发生在该 Pod 的应用层而非网络层。
3. 日志（#4）中 `allocated_mib` 始终为 0 且重启次数为 0，与 K8s 配置（#3）的资源设定结合，排除了因内存不足 OOM 或资源耗尽导致的异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑缺陷（依赖不可用） → 应用层主动返回 503 → K8s Readiness Probe 失败 → Pod 变为 NotReady 状态（剔除 Service 流量，外部请求直接返回 503）
```

### 根因结论

已确认根因为 **应用逻辑错误（Application logic returning 503 due to 'dependency unavailable'）**。

具体机制如下：
应用组件 `workload-5f4fb9ff45-cfzz6` 在处理 HTTP 请求（包括 K8s 就绪探针探测及外部流量）时，因底层依赖服务不可用，主动向上游返回了 HTTP `503` 状态码。
- **证据支撑**：Kubernetes 事件（fact-48f6e1e55e6c）记录了探针连续失败及 503 状态码；Elasticsearch 日志（fact-0f3c1662d382 等聚合事实）明确记录了 `message: "dependency unavailable"` 且伴随 `http_status: 503`；Deepflow 流量记录（fact-654b0841c714 等聚合事实）也证实了该 Pod 接收到的请求被原样返回 503。
- 此行为导致 Pod 被标记为 `NotReady`（fact-4d372253b7a0），从而将流量隔离，并在用户侧表现为应用直接报错。由于内存消耗为 0 且无重启，可排除运行时故障或资源争抢。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 17.7s
├─ 并发证据采集: 82.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 82.1s (Evidence 75.5s, RCA 6.3s)
└─ 汇总总结: 14.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
