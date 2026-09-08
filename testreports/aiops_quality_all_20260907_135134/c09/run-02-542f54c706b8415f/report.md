## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | {'type': 'PodScheduled', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `type: Ready, status: False, reason: ContainersNotReady` (fact-1637c907260c) | 证实 Pod 处于 NotReady 状态，且容器未就绪。 |
| 2 | K8s Event | kubelet | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-55a0100edb74) | 证明就绪探针因业务逻辑返回 503 而判定失败。 |
| 3 | K8s Event | kubelet | `Warning Unhealthy Readiness probe failed: ... connect: connection refused` (fact-b26f1e67bc2e) | 记录早期连接拒绝现象，反映网络或进程状态的历史波动。 |
| 4 | Logging | elasticsearch | `event: http_request, level: error, message: dependency unavailable, http_status: 503, path: /work` (fact-1b4f99237430 等) | 证实业务路径 `/work` 存在“依赖不可用”错误，导致服务返回 503。 |
| 5 | Tracing | Tempo/Deepflow | `GET /work`, `http.response.status_code: 503`, `aiops.observed_mode: readiness_fail` (fact-0d0416ee3286) | 确认业务流量 `/work` 返回 503，且时间线上与探针故障观察模式一致。 |
| 6 | K8s Config | container.resource | `cpu request: 20m, limit: 200m`; `memory request: 24Mi, limit: 96Mi` (fact-323e12eb7029 等) | 资源配额极低，但当前未触发 OOMKill 或 CPU Throttling 日志，排除资源耗尽的直接导致。 |

**证据说明：**
Pod 的 `Ready` 状态为 `False`，直接由 Kubelet 读取到探针返回 `503` 引起（证据 2）。追踪数据（证据 5）和日志（证据 4）均指向业务端点 `/work` 因“依赖不可用”而拒绝服务。由于 Kubelet 报出的是 `statuscode: 503`，而非 `connection refused`（证据 3 为早期或网络层异常），说明应用进程正在运行且能响应 HTTP 请求，只是业务逻辑返回了错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑依赖不可用（未确认具体上游） → 业务端点 /work 返回 HTTP 503 → Readiness Probe 路径 /ready 同样返回 503 → Pod 被判定为 NotReady
```

### 根因结论

**证据不足，诊断状态为 inconclusive。**

现有证据确凿地表明 Pod 处于 `NotReady` 状态的原因是 **Readiness Probe 失败**。探针持续探测到 `HTTP 503` 响应（证据 2），同时业务侧日志与追踪确认端点 `/work` 存在 `dependency unavailable` 导致的 503 错误（证据 4、5）。

然而，正式根因分析的发布受阻，主要原因如下：
1. **路径解耦未证实**：虽然探针和业务接口均返回 503，但缺乏 `/ready` 端点的具体实现逻辑（如是否直接复用 `/work` 的依赖检查），无法断定是“/ready 复用了 /work 的失败依赖”还是“探针本身触发了独立的未知错误分支”。
2. **上游依赖缺失**：日志中提到的“dependency unavailable”缺乏具体的依赖对象（如数据库、外部 API 或 DNS），无法追溯至具体的基础设施故障（如网络分区、DNS 故障或第三方服务宕机）。

因此，无法给出唯一的、确定的业务级根因，仅能确认应用层返回 503 是导致当前 NotReady 状态的直接机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.5s
├─ 并发证据采集: 60.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 60.7s (Evidence 51.9s, RCA 8.7s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
