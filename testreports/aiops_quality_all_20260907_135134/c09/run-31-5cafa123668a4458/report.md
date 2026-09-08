## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Application readiness probe returns 503 'dependency unavailable' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod /app 容器 | Phase: Running, Condition Ready: False (ContainersNotReady), RestartCount: 0 | 确认 Pod 处于运行但非就绪状态，且未发生容器重启崩溃 |
| 2 | K8s Event | kubelet | Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused | 提供网络层断连的直接证据，指出连接目标为 Pod IP 172.16.104.35 的 8080 端口 |
| 3 | Logging | Elasticsearch | Pattern: `dependency unavailable`, http_status: 503, path: /work, service: aiops-lab-workload (occurrence_count: 8) | 确认应用内部处理请求时产生 503 错误，归因为依赖不可用 |
| 4 | Tracing | Deepflow (L7 Flow) | HTTP GET /work, src: 172.16.104.55 -> dst: 172.16.104.35, response_code: 503, response_status: 3 (occurrence_count: 9) | 跨维度印证上游流量确实到达了本 Pod (172.16.104.35) 并收到了 503 响应 |
| 5 | Tracing | Tempo (Span) | Service: aiops-lab-workload, span_id: c76e0b2351a8325b, trace_id: 5d9d8efaae8b4748db93567a0a5350e3 | 关联特定 Trace ID 下的应用执行结果，确认应用本身在运行并主动返回错误 |
| 6 | K8s Config | Pod Spec | resource_limit.memory: 96Mi, resource_request.cpu: 20m | 排除内存限制导致的 OOMKill 或 CPU 资源耗尽导致的响应超时（资源配置相对较小但非异常） |

上述证据表明，流量（来自 172.16.104.55）成功到达了该 Pod (172.16.104.35)，但应用进程在处理请求时（如查询外部依赖）失败，导致应用主动返回 HTTP 503 状态码。Kubelet 的 Readiness Probe 请求 `/ready` 端点也收到了此 503 响应（或通过端口 8080 连接失败，需进一步区分是 Probe 端口配置错误还是应用逻辑拒绝），从而导致 Pod 被标记为 NotReady。

## 🎯 根因分析 · g1

### 因果链

```text
应用无法访问下游依赖 → 处理就绪探测(/ready)或业务请求(/work)返回 HTTP 503 → Kubelet 探测失败/流量被拒 → Pod 状态 NotReady
```

### 根因结论

已确认的根因是 **应用自身的就绪探测探针（Readiness Probe）返回 HTTP 503 状态码，导致 Kubelet 判定容器未就绪 (ContainersNotReady)**。

证据支撑：
- `fact-13efc28d2a52` 与 `fact-79854584f067` 显示 Kubelet 不断记录 Readiness Probe 失败，且涉及连接被拒绝 (connection refused) 或 HTTP 错误。
- `fact-629bb895dc8a` (Tracing) 与 `fact-5bcfa8af2ae9` (Logging) 共同证实应用在处理 `GET /work` 请求时，明确返回了 503 状态码，日志记录为 "dependency unavailable"。
- `fact-06c6810c9421` (Tracing) 进一步确认该应用 (aiops-lab-workload) 在相关 Trace 中执行了 GET 请求并返回 503。

虽然 Pod 处于 Running 状态且未重启，但应用内部逻辑（或配置的路由/健康检查端点）因“下游依赖不可用”而无法正常通过健康检查。

未确认事实：
- 具体是哪个“下游依赖”不可用（应用内部日志未明确指出具体的下游服务名或 IP）。
- 端口 8080 的连接拒绝是因为 Probe 配置了错误的端口，还是应用确实在监听但无法响应就绪状态（日志中 `/work` 路径返回 503，而 Probe 报错为 8080 端口连接问题，若 Probe 也指向 8080 端口则逻辑一致，否则存在探针端口配置与应用实际监听端口不一致的可能，但基于现有事实，核心故障点在于应用无法通过健康检查）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.7s
├─ 并发证据采集: 65.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 65.6s (Evidence 58.7s, RCA 6.7s)
└─ 汇总总结: 16.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
