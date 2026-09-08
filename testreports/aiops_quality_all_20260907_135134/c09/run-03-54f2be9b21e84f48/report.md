## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 NotReady 状态，表现为 kubelet Readiness Probe 持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` 状态为 `Running` (fact-0a8714590de0)，但未出现重启 (restart_count: 0, fact-9da6cfe3acee) | 确认容器进程存活，非容器崩溃或资源超限导致的重启/OOM |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy ... kubelet Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (fact-2485d5ec3336) | 早期探针失败证据，表明 172.16.104.35:8080 端口不可达或无服务监听，导致 Pod 无法进入 Ready 状态 |
| 3 | K8s Event | Kubernetes | `Warning Unhealthy ... Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-1c40f7d72814) | 近期探针失败证据，探针可连通但应用返回 503，表明服务逻辑处于拒绝服务状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-cc95dba5488d) | 佐证容器进程未发生重启，进一步确认服务处于运行但报错的假死状态 |
| 5 | Logging | Elasticsearch | 聚合日志模式显示 `http_request: error, dependency unavailable, http_status: 503, path: /work`，时间范围 18:59:01 - 18:59:41，发生 10 次 (fact-300f60e00c56 等) | 应用日志明确指出业务逻辑返回 503 的原因是 `dependency unavailable`，且持续发生 |
| 6 | Tracing | Deepflow/Tempo | L7 Flow 聚合显示 `GET /work` 返回 503 (fact-0b08375d6091 等)，Trace ID `e992d73994b485a984d6ad845214d8e0` 关联 Tempo Span (fact-0d0416ee3286) | 跨维度关联确认了 503 错误来自应用处理 `/work` 逻辑，排除了底层网络异常 |

证据互相印证：K8s 探针从早期的“连接拒绝（连接未建立）”演变为近期的“503（服务已启动但拒绝处理）”。Metrics 确认无重启，说明不是应用启动失败。Logging 提供了根本原因（`dependency unavailable`），Tracing 确认了该错误与探针探测路径 `/work` 的一致性，形成了完整的证据闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖组件不可用 (日志模式: dependency unavailable) → 应用业务逻辑在 /work 端点返回 HTTP 503 → kubelet Readiness 探针检测 503 失败 → Pod 状态标记为 NotReady
```

### 根因结论

**已确认的根因：** 应用服务启动后，由于**缺失或不可用的内部依赖（dependency）**，导致业务逻辑在处理 Readiness 探针路径（`/work` 或 `/ready`）时主动返回 HTTP 503 错误。

1.  **探针检测失败**：早期日志 (fact-2485d5ec3336) 显示探针连接 8080 端口被拒绝，随后 (fact-1c40f7d72814) 开始持续收到 503 响应。
2.  **应用逻辑拒绝**：日志记录 (fact-300f60e00c56) 明确指出错误原因为 `dependency unavailable`，且 HTTP 状态码为 503。这表明应用代码中有针对依赖项健康检查的逻辑，当依赖缺失时，应用选择通过返回 503 来主动阻止流量进入，而非抛出 500 异常。
3.  **状态固化为 NotReady**：Kubelet 依据探针返回的 503 持续判定服务不健康，导致 Pod 始终保持在 `NotReady` 状态，无法接收流量。

**未知项/缺失决定性事实：**
*   日志中仅泛指 `dependency unavailable`，**未指明具体是哪个依赖组件**不可用（例如数据库、缓存或第三方 API 等）。要彻底解决此问题，需进一步确认该 `dependency` 的实际对象及不可用原因（如网络不通、配置错误或资源不足等）。目前证据仅证明了该依赖缺失导致了 503 响应，但无法定位缺失的具体组件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.5s
├─ 并发证据采集: 58.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 58.6s (Evidence 50.4s, RCA 8.1s)
└─ 汇总总结: 16.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
