## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 处于 NotReady 状态，Readiness Probe 持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` (fact-b83591e8cf55) | 明确读取探针的连接拒绝错误，证实探测目标不可达 |
| 2 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-580ad9b6941a) | 确认探针接收到 503 响应并判定失败 |
| 3 | K8s State | pod condition | `Ready=False (ContainersNotReady)` (fact-00b5e8eef077) | 证实 Pod 当前处于 NotReady 状态 |
| 4 | Logging | elasticsearch | `dependency unavailable, http_status: 503, path: /work` (pattern: fact-0641de6fb0f0...) | 确认业务代码因依赖不可用显式返回 503 状态码 |
| 5 | Tracing | deepflow | `HTTP GET 172.16.104.19 -> 172.16.104.26 /work response_code: 503` (occurrence: 15, fact-1da588602fd7) | L7 流量统计与日志模式完全一致，证实应用返回 503 具有持续性 |
| 6 | Tracing | tempo | `GET /work status_code: 503, span: 1958329029c7c0fd` (fact-0dac21718955) | 提供特定 Trace 实例的上下文佐证，证实错误发生在 `/work` 路径 |

**证据分析：**
K8s Event 直接记录了探针（Probe）的失败细节，包括连接拒绝和收到 503 状态。Logging 中的 `dependency unavailable` 与 HTTP 503 状态解释了探针返回 503 的内部原因。Tracing 数据在流量层和 Span 层分别确认了目标端点（172.16.104.26）对外部请求的拒绝行为。日志中的业务错误（fact-0641de6fb0f0）与探针事件（fact-580ad9b6941a）相互印证了“返回 503”这一事实，但日志中的依赖路径 `/work` 与探针路径 `/ready` 不同，说明应用因内部依赖问题无法启动正常业务（返回 503），同时也导致健康检查探针无法获得正常响应。

## 🎯 根因分析 · g1

### 因果链

```text
外部服务不可用 (依赖服务故障) → 应用内部业务逻辑返回 HTTP 503 (dependency unavailable) → 应用未处理 503 或 /ready 端点同样受影响 → 探针接收 503 响应判定失败 → Pod 进入 NotReady 状态
```

*注：日志显示的依赖错误路径为 `/work`，探针路径为 `/ready`，中间“应用未处理 503”或“两者共享依赖”的具体映射环节未确认。*

### 根因结论

已确认的根因是 **应用依赖的外部服务不可用**。
该原因导致应用无法提供正常服务，向探针（Readiness Probe）返回了 HTTP 503 状态码（证据：日志 fact-0641de6fb0f0、探针事件 fact-580ad9b6941a、L7 流 fact-1da588602fd7），从而触发 Pod 的 `NotReady` 状态（证据：Pod 状态 fact-00b5e8eef077）。

关于 `dependency unavailable` 的具体外部服务名，现有日志和追踪数据不足以直接确定，仅能从日志模式（fact-0641de6fb0f0）中观察到该现象。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 16.0s
├─ 并发证据采集: 116.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 116.7s (Evidence 107.4s, RCA 9.2s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
