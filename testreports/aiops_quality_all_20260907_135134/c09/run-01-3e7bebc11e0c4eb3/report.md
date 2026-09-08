## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (多次) | 确认 Readiness Probe 探测到目标端点返回 503 错误 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (首次) | 确认探针最初遭遇连接拒绝，随后转为 503 错误 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi; `resource_request.cpu`: 20m; `resource_limit.cpu`: 200m | 资源配额配置，当前重启次数为 0，暂无资源超限特征 |
| 4 | Logging | elasticsearch | `log.message`: "dependency unavailable", `http_status`: 503, `path`: "/work", `occurrence_count`: 8 | 记录到应用频繁请求后端依赖失败并返回 503，支撑应用端异常判断 |
| 5 | Tracing | tempo | `http.request.method`: GET, `http.response.status_code`: 503, `http.route`: "/ready", `trace_id`: e992d73994b485a984d6ad845214d8e0 | 追踪到具体 Readiness Probe 探测请求在 `/ready` 路由被拒绝并返回 503 |
| 6 | K8s State | kubernetes | `pod.status`: "Running"; `pod.condition.Ready`: "False" (ContainersNotReady: app) | 确认容器进程存活但健康检查未通过 |

**证据总结：**
1. **K8s Event (1, 2)** 与 **Tracing (5)** 直接证明应用侧 `/ready` 端点持续返回 `HTTP 503`，导致 Readiness Probe 失败；
2. **Logging (4)** 提供了应用内部视角的 503 记录，确认故障发生在应用尝试连接后端依赖时；
3. **K8s State (3)** 中的重启计数为 `0`，结合资源限制，排除了因资源耗尽导致容器 OOMKilled 频繁重启的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用后端依赖不可用 → /ready 端点持续返回 HTTP 503 → Readiness Probe 连续探测失败 → Pod 状态 NotReady (ContainersNotReady)
```

### 根因结论

已确认根因为：**应用后端依赖不可用**。

应用进程 `/ready` 端点因为无法连接或访问其依赖的后端服务，持续返回 `HTTP 503` 错误。这直接导致 Kubernetes Readiness Probe 探测失败，Pod 被标记为 `NotReady` 并移出 Service 负载均衡池。

- **支撑证据**：
  - `fact-171ea59b73c7` 等 K8s 状态记录显示 `Ready` 条件为 `False`，`ContainersNotReady`；
  - `fact-0bb73cc66881`、`fact-0df8dee1397b` K8s 事件记录探针失败及 503 状态码；
  - `fact-6d5fd7218d3f` 等日志记录应用报出 `dependency unavailable` 错误；
  - `fact-0d0416ee3286` Trace 追踪到 `/ready` 路由返回 `503`。

- **缺失的决定性事实**：
  - 日志中未体现具体是哪个依赖服务不可用（如 IP 或域名）；
  - 缺乏 `INFO/DEBUG` 级别日志以进一步分析应用启动初期的连接建立过程或重试行为。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 32.7s
├─ 并发证据采集: 76.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 76.1s (Evidence 69.4s, RCA 6.5s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
