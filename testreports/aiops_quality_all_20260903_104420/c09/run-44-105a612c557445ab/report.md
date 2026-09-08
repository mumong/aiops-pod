## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 is NotReady due to continuous Readiness Probe failures (HTTP 503) on path /ready. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running`; `ContainersReady: False`; `Ready: False` | 确认应用容器已启动（Phase 为 Running）但未被 Kubelet 标记为可用 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (持续 122 分钟，发生 2494 次) | 确认 Readiness Probe 因持续收到 503 响应而长期失败 |
| 3 | K8s Event | Kubernetes | `cni.projectcalico.org/podIP: 172.16.104.26/32` | 确认 Pod 网络层正常分配了 IP，排除网络层未就绪导致的探测失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 确认应用进程未发生重启，排除因进程崩溃重启导致的问题 |
| 5 | Logging | Elasticsearch | 日志模式：`http_request [error] dependency unavailable [status: 503, path: /work]` (出现 8 次，连续记录) | 确认应用内部逻辑主动返回 503 并明确报错“dependency unavailable”，且错误发生在工作请求路径上 |
| 6 | Tracing | Deepflow | L7 Flow: `GET /work` 从 `172.16.104.19` 到 `172.16.104.26`，`response_code: 503` (持续约 21 分钟，发生 9 次) | 确认外部流量到 Pod 内部确实收到 503 响应，日志与链路数据交叉印证了内部服务不可用的事实 |
| 7 | Tracing | Tempo | Span: `GET /work` 返回 503，属性 `aiops.observed_mode: readiness_fail` | 确认探针路径 `/ready` 与工作路径 `/work` 处于相同的错误上下文，证实应用整体处于依赖不可用状态 |

**证据关系说明：**
Kubernetes 状态与事件（#1, #2）记录了外部探针失败的表象；日志（#5）与深度链路数据（#6, #7）深入到了应用内部，揭示了应用进程因“依赖不可用”主动拒绝服务并返回 503 的机制；重启计数（#4）排除了应用频繁重启的可能性，表明这是一个持续的服务状态异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的后端服务或组件不可用 → 应用进程返回 HTTP 503 (消息: "dependency unavailable") → Kubelet 探针检测失败，Pod 持续处于 NotReady 状态
```

### 根因结论

**已确认的根因：**
应用工作负载进程因依赖的后端服务或组件不可用，导致其 Readiness Probe 探测路径及工作请求路径均返回 HTTP 503 错误，Kubelet 因此判定容器不健康，Pod 长期处于 NotReady 状态。该结论由 K8s 探针事件（#2）、应用日志模式（#5）及 L7 链路追踪（#6, #7）高度印证。

**证据不足/未决事实：**
目前证据仅能证实应用进程主动报错“依赖不可用”，但未能通过日志或链路追踪中的上游追踪标识（trace_id）进一步下钻定位到**具体是哪一个后端依赖**导致了此失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 24.8s
├─ 并发证据采集: 60.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 60.1s (Evidence 50.6s, RCA 9.3s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
