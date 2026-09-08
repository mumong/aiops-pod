## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 Running 但 NotReady 状态，Readiness 探针连续返回 503 Service Unavailable。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5f4fb9ff45-7b77l` 状态 Running，但 `Ready=False`，Reason `ContainersNotReady` | 明确 Pod 处于业务运行但服务不可用的 NotReady 状态 |
| 2 | K8s Event | Kubernetes | 连续 Readiness probe failed：`Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused`（最新）及 `HTTP probe failed with statuscode: 503`（累积1142次） | 揭示探针检测机制：从连接被拒演变为业务端点稳定返回 503，指示应用层健康检查逻辑失效 |
| 3 | K8s Config | Kubernetes | 容器 `app` 资源配置：CPU request 20m/limit 200m，Memory request 24Mi/limit 96Mi | 排除因资源硬性限制（CPU/Memory 溢出）导致容器崩溃或 OOM 重启 |
| 4 | Logging | Elasticsearch | 错误日志模式：`error level dependency unavailable`，HTTP status 503，path `/work`，时间窗口 `2026-09-07 19:50:49` 至 `19:51:25` | 确认应用代码在 `/work` 路径因“依赖不可用”主动返回 503，解释了探针失败的具体逻辑原因 |
| 5 | Tracing | Deepflow/Tempo | 聚合 Flow：`172.16.104.55 -> 172.16.104.35` 的 `GET /work` 请求持续返回 `503`，`occurrence_count: 9` | 从流量层面印证了目标 Pod 172.16.104.35 正在持续拒绝业务请求，且流量来源为内部集群节点 |

**证据互证说明：**
Kubernetes 探针检测到 Pod 172.16.104.35 返回 503（证据 #1, #2）；Elasticsearch 日志证实该 Pod 在处理 `/work` 路径时因“dependency unavailable”主动报错（证据 #4）；Deepflow 流量日志证实了该 IP 节点确实持续向客户端吐出 503 响应（证据 #5）。三者形成闭环，证明故障原因为应用内部业务逻辑失败，而非网络连通性或 Pod 进程挂死。

## 🎯 根因分析 · g1

### 因果链

```text
上游外部依赖不可用（未确认具体来源） → 应用处理依赖请求失败，返回 HTTP 503 Service Unavailable → Readiness 探针检测到 503 状态码，判定容器不健康 → Kubernetes 将 Pod 标记为 NotReady，从 Service Endpoints 中剔除流量
```

### 根因结论

已确认根因为**应用依赖服务不可用导致业务端点返回 503，进而触发 K8s Readiness 探针失败，使 Pod 被标记为 NotReady**。
- 证据 #4 (Logging) 显示应用代码明确上报 `dependency unavailable` 错误，说明探针返回的 503 是应用业务逻辑层面的真实失败（如连接外部 DB 或下游服务超时/被拒）。
- 证据 #2 (K8s Event) 确认了探针连续失败记录，且伴随大量的 503 响应；证据 #5 (Tracing) 从网络流量侧佐证了请求在被 Pod 处理后返回了 503。

**证据不足说明：**
当前证据无法确认**具体是哪个外部依赖**（如数据库、缓存或特定微服务）不可用。日志中仅包含泛化的 `'dependency unavailable'` 错误，且未捕获到具体的下游连接超时或拒绝堆栈（如 `connect: connection refused` 在探针日志中可能指代探针本身与 8080 端口的通信，或应用探测内部依赖失败，但应用日志未细化）。若需进一步定界，需补充应用层针对该 `/work` 路径更详细的下游调用 Trace 或错误上下文。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 20.5s
├─ 并发证据采集: 85.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 85.0s (Evidence 74.7s, RCA 10.2s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
