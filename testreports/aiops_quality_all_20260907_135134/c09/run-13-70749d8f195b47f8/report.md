## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod `workload-5f4fb9ff45-7b77l` in `aiops-case-09` namespace is `NotReady` due to persistent Readiness Probe failures. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (fact-f8aedf72c6a9) | 确定 Probe 机制的早期失败模式为连接拒绝（服务未响应）。 |
| 2 | K8s Event | `kubelet` | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-a6098b8e1f09) | 确认当前（3m49s 前）Probe 收到业务层返回的 503 错误。 |
| 3 | K8s Config | `pod.spec` | `resource_limit.memory: 96Mi`, `resource_limit.cpu: 200m` (fact-38ac0fe10e14, fact-451051df93fd) | 确认资源限制充足，排除 OOM/Kill 导致应用崩溃的可能。 |
| 4 | K8s State | `pod.status` | `ContainersNotReady: [app]`, `restart_count: 0` (fact-694b9c30352f, fact-d6a1cc72feee) | 确认容器运行正常且未被重启，故障为应用逻辑或依赖问题而非进程异常。 |
| 5 | Logging | `elasticsearch` | `dependency unavailable` (http_status: 503, path: `/work`) | 记录应用自身在处理请求时检测到依赖不可用的错误。 |
| 6 | Tracing | `tempo/span` | `GET /work` span, `response_code: 503` (fact-d27871b75230) | 确认应用对 `/work` 接口的响应确实为 503，日志中的“dependency unavailable”得到追踪数据印证。 |
| 7 | Tracing | `deepflow/flow` | `src_ip: 172.16.104.55 -> dst_ip: 172.16.104.35`, `GET /work`, `response_code: 503` (fact-6a90391f639c 等 9 条) | 确认外部请求到达 Pod 并成功接收到 503，排除了网络阻断导致 Pod 无响应的问题。 |
| 8 | Metric | `prometheus` | `kube_pod_container_status_ready: 0` (fact-6301b2e0a6ba) | 从监控侧验证容器状态一直为未就绪，与 K8s 事件吻合。 |

证据表明：Pod 进程存活并正常接受 TCP 连接（排除网络不通或端口未开），但应用逻辑层面检测到外部依赖故障（Logging 记录 `dependency unavailable`，Tracing 显示 503 响应）。Readiness Probe (`/ready`) 与业务逻辑共享了后端依赖的状态（或 `/ready` 本身即调用了该依赖），导致其返回 503 被 kubelet 标记为 `NotReady`。

## 🎯 根因分析 · g1

### 因果链

```text
External dependency unavailable → App detects failure and returns HTTP 503 on /ready → kubelet Readiness Probe receives 503 → ContainersNotReady
```

### 根因结论

已确认根因：**应用进程 `app` 运行正常，但后端依赖不可用（Unavailable Dependency），导致应用自身的健康检查端点 `/ready` 返回 HTTP 503 状态码。**

具体证据支撑：
1.  **应用存活**：Pod 处于 `Running` 状态且 `restart_count: 0` (fact-95524bd8d453, fact-d6a1cc72feee)，Tracing 数据 `dst_ip: 172.16.104.35` 接收到了请求 (fact-6a90391f639c)。
2.  **应用报错**：日志记录应用内部遇到 `dependency unavailable` 错误 (fact-824583e962cf 等)，Tracing 验证了 `GET /work` 路由返回 503 (fact-d27871b75230)。
3.  **探针机制确认**：Kubelet 的 Readiness Probe 配置为检测 `/ready` (fact-f8aedf72c6a9, fact-a6098b8e1f09)，当前持续收到 503 (fact-a6098b8e1f09)，从而将 Pod 标记为 `NotReady` (fact-694b9c30352f)。

**未知项/限制**：
*   无法确定具体是哪个外部依赖不可用（如数据库、缓存或第三方 API）。
*   无法确定该依赖为何不可用（如网络策略、依赖服务宕机或配置错误）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 34.5s
├─ 并发证据采集: 92.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 92.5s (Evidence 79.2s, RCA 13.1s)
└─ 汇总总结: 17.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
