## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 NotReady 状态，Readiness Probe 持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.condition`: Ready=False, reason=ContainersNotReady; Pod Phase=Running; Restart Count=0 (fact-69065d9e157a, fact-878fc492a3e0, fact-0fab99f63755) | 确认应用进程存活，但健康检查未通过，排除了容器崩溃退出。 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy`: Readiness probe failed: HTTP probe failed with statuscode: 503 (fact-52511f1d57b4) | 直接证明 Readiness Probe 接收到了 HTTP 503 响应。 |
| 3 | K8s Event | kubernetes | `Warning Unhealthy`: Readiness probe failed: dial tcp 172.16.104.35:8080: connect: connection refused (fact-92fbd1e1ca48) | 早期记录表明探针曾遭遇连接拒绝，确认应用服务端口存在服务失败历史。 |
| 4 | K8s Config | kubernetes | Pod IP=172.16.104.35, CPU Limit=200m, Memory Limit=96Mi (fact-2ef83ec8976e, fact-5aceb4b2f2e7, fact-1442aadb11ee) | 提供异常实体的网络与资源基准配置。 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-99a0e306615e) | 验证容器未发生过重启。 |
| 6 | Metric | prometheus | `container_cpu_usage_seconds_total`: 4.46s, `container_memory_failcnt`: 0, `cluster:namespace:pod_cpu:active`: 0.02 core (fact-3dc0cdb06e23, fact-64ed5b0eacc5, fact-0d2ae4c3857c) | 资源使用量极低，排除因 CPU 饥饿或 OOM 导致服务无法响应的可能。 |
| 7 | Logging | elasticsearch | `dependency unavailable`, `http_status`: 503, `path`: /work (8 occurrences, fact-0cff474a2831) | 日志明确记录业务逻辑因下游依赖不可用而返回 503 状态码。 |
| 8 | Tracing | deepflow | HTTP GET /work, `response_code`: 503, `src_ip`: 172.16.104.55 → `dst_ip`: 172.16.104.35 (fact-6a90391f639c) | 流量数据证实了从其他实例（或外部）到异常 Pod 的读端点请求持续失败。 |

**证据印证说明：**
- Pod 状态（事实 1, 5, 6）显示容器运行正常且资源未耗尽，排除了基础设施层面的故障。
- K8s 事件（事实 2, 3）与 Tracing 流量（事实 8）均捕获到针对 `/ready` 或 `/work` 路径返回 HTTP 503 的信号。
- 日志（事实 7）揭示了 503 的根本诱因：业务逻辑层面的“dependency unavailable”，与 K8s 探针失败直接对应。

## 🎯 根因分析 · g1

### 因果链
```text
上游依赖 unavailable → 应用判定失败 → Readiness Probe 持续返回 HTTP 503 → Pod 保持 NotReady 状态
```

### 根因结论
**已确认的根因**是应用业务逻辑异常，具体表现为应用在检测到下游依赖不可用时，选择返回 HTTP 503 状态码，直接导致 Kubernetes Readiness Probe 持续失败。
- 证据（日志 fact-0cff474a2831 中的 `dependency unavailable`）提供了 503 响应的具体业务原因。
- 证据（K8s Event fact-52511f1d57b4 和 Tracing fact-6a90391f639c）一致证实了探针及实际请求均收到了 503 响应。

**证据不足的未知项**：
- **依赖组件身份不明**：日志中仅记录 `dependency unavailable`，未指明具体的数据库、缓存或其他服务。
- **上游根源未查明**：缺乏 Topology 数据（已规划采集失败）及 L7 链路跟踪，无法确认上游依赖不可用的根本原因是网络分区、下游服务宕机还是配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 19.9s
├─ 并发证据采集: 83.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 83.7s (Evidence 73.1s, RCA 10.5s)
└─ 汇总总结: 16.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
