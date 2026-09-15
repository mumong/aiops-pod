## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用服务依赖组件不可用导致健康检查持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Phase: Running; Condition Ready: False (reason: ContainersNotReady, message: containers with unready status: [app]) | 确认 Pod 虽存活但服务入口不可用 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused | 提供健康检查失败的确切原因：端口 8080 拒绝连接 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (over 40m) | 提供健康检查失败的替代/后续模式：503 状态码持续存在 |
| 4 | K8s Config | Kubernetes | resource_limit.cpu: 200m, resource_limit.memory: 96Mi; restart_count: 0 | 排除 OOMKilled 或资源耗尽导致的重启可能性 |
| 5 | Logging | Elasticsearch | pattern: `dependency unavailable`, `http_status: 503`, `path: /work` (8 occurrences) | 确认应用内部依赖服务不可用，产生 503 错误 |
| 6 | Tracing | Tempo/Deepflow | Span: `GET /work`, `http.response.status_code: 503`, `aiops.observed_mode: readiness_fail` (Flow count: 9, min_duration: 15ms) | 链路观测证实请求被应用以 503 拒绝，耗时极短 |

**证据说明：**
1. **应用内部逻辑与外部暴露一致**：Trace 数据显示应用处理 `GET /work` 请求直接返回了 `503` 状态码（证据 #5, #6），这与 K8s 健康检查收到的 `503` 信号完全匹配（证据 #3）。
2. **连接拒绝与 503 的关系**：存在 `dial tcp ... 8080: connection refused`（证据 #2），但同时也存在 `HTTP probe failed with statuscode: 503`（证据 #3）。考虑到应用日志明确报错 `dependency unavailable`（证据 #5），且 Trace 显示应用内部产生了 `503` 响应（证据 #6），这表明 Pod 进程是存活且可监听的（非单纯的进程挂掉导致 refused），`connection refused` 可能是针对特定内部依赖端点的探测失败，或者是探测逻辑中特定路径（如 `/ready`）依赖了不可用的子组件。核心故障在于应用自身的 `/ready` 端点或依赖组件返回了不可用状态。
3. **资源非主因**：重启计数为 0 且资源限额正常，排除了进程崩溃重启导致的不稳定（证据 #4）。

## 🎯 根因分析 · g1

### 因果链

```text
依赖组件不可用 → 应用返回 HTTP 503 → Readiness Probe 接收 503 失败 → Pod 状态 NotReady
```

### 根因结论

**已确认的根因**：应用服务依赖组件不可用（`dependency unavailable`），导致应用自身健康检查端点返回 HTTP 503 状态码，进而触发 K8s Readiness Probe 持续失败，最终使 Pod 被标记为 `NotReady` 并从服务流量中摘除。

- **证据支撑**：
  - 日志显示应用内部明确报错 `dependency unavailable` 并返回 `http_status: 503`（证据 #5）。
  - 追踪数据证实应用处理请求直接返回了 `503` 状态码（证据 #6）。
  - K8s 事件记录了健康检查因收到 `503` 状态码而失败，并持续了 40 分钟（证据 #3）。
  - 尽管存在 `connection refused` 事件（证据 #2），但结合应用内部产生 503 日志的事实，主因是应用层依赖失败，而非单纯的容器网络崩溃或 OOM。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.4s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 41.3s (Evidence 34.6s, RCA 6.5s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
