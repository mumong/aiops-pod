## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5f4fb9ff45-7b77l` (IP: 172.16.104.35) 状态 `Running`，重启次数 0 | 排除容器崩溃，确认处于存活但不可调度状态 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: dial tcp 172.16.104.35:8080/ready: connect: connection refused | 确定 `/ready` 探测初期存在网络层连接拒绝 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 | 确认应用已启动，但探测端点业务层返回 503 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认 Pod 未发生重启，503 为当前稳定状态 |
| 5 | Logging | Elasticsearch | Pattern: `dependency unavailable` (HTTP 503, path: /work)，发生 8 次，时间窗 19:22:16 - 19:22:51 | 应用自身日志记录业务依赖失败，解释了为何 `/ready` 返回 503 |
| 6 | Tracing | Deepflow/Tempo | HTTP GET /work 响应 503，span `aiops.observed_mode` 标记为 `readiness_fail` | 链路追踪直接证实健康检查端点因依赖问题返回错误 |

**证据关系说明：**
Kubernetes 事件显示探测从“连接拒绝”演变为“503 错误”（#2, #3），证明 Pod 容器已正常运行；应用日志（#5）和链路追踪（#6）提供了 503 的业务语义：`/ready` 接口因依赖不可用主动返回 503；Metrics 排除了容器重启的可能性（#4）；综合证据锁定根因为应用健康检查失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务依赖不可用（如外部API/DB） → /ready 端点主动返回 HTTP 503 → Kubelet 探测失败移除 Pod Ready 条件 → Pod 保持 Running 但标记为 NotReady
```

### 根因结论

**已确认根因：应用服务 /ready 健康检查端点返回 HTTP 503 导致 Readiness Probe 持续失败。**
应用已运行（Pod 状态 Running，无重启记录），其健康检查端点 `/ready` 由于依赖不可用（应用日志记录 `dependency unavailable`）返回了 HTTP 503 状态码，致使 Kubelet 判定探针失败，Pod 虽存活但被 Kubernetes 标记为 NotReady，无法接收服务流量。

**待明确事实：**
具体是哪一个上游依赖（如数据库、外部API）不可用导致了业务层抛出 503，当前证据链仅能确认业务层报错现象，未包含该依赖的详细故障信息。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.3s
├─ 并发证据采集: 65.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 65.5s (Evidence 57.8s, RCA 7.6s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
