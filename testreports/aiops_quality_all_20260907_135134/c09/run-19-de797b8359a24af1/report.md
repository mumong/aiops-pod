## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用内部依赖不可用 (dependency unavailable) 导致服务返回 HTTP 503，使得 kubelet 的 Readiness 探针持续失败（statuscode: 503），最终导致 Pod 状态为 NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.phase: Running, status.conditions[type=ContainersNotReady].status: False | 确认 Pod 正在运行但应用容器未就绪，未发生 CrashLoopBackOff |
| 2 | K8s Event | Kubernetes | Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused (35m前) | 提供初始根因线索，表明 35 分钟前存在网络层面的连接阻断 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (近 5 分钟) | 描述当前探针状态，从连接拒绝转为应用显式返回 503 错误 |
| 4 | Logging | Elasticsearch | error log: 'dependency unavailable', http_status: 503, path: /work, trace_ids: ["41737e9f9d059aad03199a8d4344e2b0", ...] | 证实服务正在业务层显式返回 503，原因是“上游依赖不可用” |
| 5 | Tracing | Tempo | Application Span: GET /work, http.response.status_code: 503, observed_mode: readiness_fail, trace_id: cd230732dd175914a43aa596f86fcfed | 追踪应用内部逻辑，确认在特定 Trace ID 下应用确实处于 Readiness 失败模式并返回 503 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total: 0 | 排除容器频繁重启（如内存超限或进程崩溃）导致的周期性故障 |

**证据互证分析：**
- **现象一致**：K8s 探针从早期的 `connect: connection refused` 演变为当前的 `statuscode: 503`，表明网络底层连通性已恢复或探针路径改变，但应用服务本身处于失败状态。
- **根因印证**：Logging 中明确的 `dependency unavailable` 错误及 503 状态码，直接解释了 K8s 探针为何收到 503 响应（证据 #2、#3 与证据 #4 一致）。
- **链路闭环**：Tracing 数据（证据 #5）在 `GET /work` 路径下观察到 `observed_mode: readiness_fail` 且状态码为 503，验证了日志中“依赖不可用”并非偶发，而是导致服务进入 `NotReady` 状态的确定性机制。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖服务不可用 → 应用检测到依赖故障显式返回 HTTP 503 → Kubelet Readiness Probe 探测接口（/ready 或 /work）持续收到 503 → Pod 状态由 Running 变为 NotReady
```

### 根因结论

**已确认根因：应用内部依赖不可用（dependency unavailable）导致 Readiness 探针持续失败。**

1. **直接原因**：Pod 内的应用在处理请求（如 `GET /work`）时，因无法访问上游依赖服务，主动返回了 `HTTP 503` 状态码（证据 #4, #5）。
2. **状态形成机制**：Kubelet 配置的 Readiness 探针探测该服务接口时，接收到 `503` 响应。探针判定失败，导致容器被标记为不健康，进而 Pod 进入 `ContainersNotReady` 和 `NotReady` 状态（证据 #1, #3）。
3. **证据排除**：
   - Pod 运行阶段为 Running 且重启次数为 0（证据 #1, #6），排除了容器崩溃或启动失败。
   - 早期事件显示过 `connection refused`（证据 #2），但最新现象已转化为应用层的 503 拒绝，说明当前瓶颈在于应用对不可用依赖的处理逻辑，而非纯粹的网络端口不通。

**已知缺失信息**：
日志和链路均未指明具体是哪一个上游依赖（如数据库或缓存服务）不可用，缺乏具体的连接错误细节。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 14.4s
├─ 并发证据采集: 74.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 74.2s (Evidence 64.1s, RCA 9.9s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
