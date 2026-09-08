## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod `app` 容器通过 Readiness Probe 检测自身 `/ready` 端点，但应用逻辑依赖外部下游服务可用性；下游服务持续返回 HTTP 503，导致应用自身 `/ready` 接口也返回 503，从而触发 Kubelet 判定容器为 Unhealthy (NotReady)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 41m (x830 over 41m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-64264209ad3d) | 证实 Kubelet 检测到 Readiness Probe 持续返回 503，导致 Pod 状态异常 |
| 2 | Logging | Elasticsearch | `dependency unavailable, http_status: 503, path: /work` (聚合 8 次, fact-27176789e09f) | 证实应用业务日志显示因依赖不可用主动返回 503，与 Probe 失败现象吻合 |
| 3 | Tracing | Tempo / Deepflow | `GET /work` 返回 HTTP 503 (tempo span fact-4bb0924f9d77)；src_ip `172.16.104.19` 到 `172.16.104.26` 的 L7 Flow 返回 503 (deepflow flow fact-0a7bb9f9ece3, 聚合 12 次) | 从流量视角确认对 Pod (`172.16.104.26`) `/work` 接口的请求持续被拒，排除了网络连通性本身的问题（Dial 失败为另一现象或历史） |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory: 24Mi` (fact-40227ab148f3); `container.resource_limit.cpu: 200m` (fact-68735600c540) | 资源限制正常，日志中 `allocated_mib` 均为 0，排除因内存不足导致的 OOM 或响应变慢 |

**证据互证分析**：
Kubernetes 事件 (1) 与日志 (2) 在现象（503 错误）和时间段上高度一致，证明 Pod 内部应用正常运行但主动拒绝服务。Tracing 数据 (3) 进一步证实了对 Pod 端点的请求确实是收到了 503 响应，而非网络不通。结合日志中提到的“依赖不可用 (dependency unavailable)”，共同指向应用层面的外部依赖故障，而非容器自身崩溃或配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 (返回 HTTP 503) → 应用逻辑因依赖失败而拒绝服务 (Readiness 端点返回 503) → Kubelet Readiness Probe 检测到非 2xx 状态码失败 → Pod 状态变为 NotReady
```

### 根因结论

**已确认的根因**：Pod `workload-5f4fb9ff45-cfzz6` 的 `/ready` 端点依赖外部下游服务，而该下游服务目前处于不可用状态（持续返回 HTTP 503）。这导致应用自身的健康检查端点也返回 503，从而触发 Kubelet 的 Readiness Probe 失败，使 Pod 失去流量并标记为 `NotReady` (证据 1, 2, 3)。

**不确定性**：当前证据足以确认应用层面的故障现象，但 Tracing 数据显示上游请求直接到达目标 Pod，日志也仅显示“依赖不可用”，未明确指明具体是哪个下游组件或网络链路（如 Service、Ingress 或特定后端 Pod）导致了最初的 503 错误（unknowns 字段所述）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.4s
├─ 并发证据采集: 98.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 98.2s (Evidence 88.9s, RCA 9.1s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
