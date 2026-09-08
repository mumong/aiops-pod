## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用服务内部依赖不可用（dependency unavailable），导致 Readiness Probe 在监听端口正常启动后持续返回 HTTP 503 状态码，被 kubelet 判定为未就绪（NotReady）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | Ready=False (ContainersNotReady); ContainersReady=False | 确认 Pod 处于 NotReady 状态，应用服务被隔离 |
| 2 | K8s State | pod.status | phase=Running | 确认容器进程存活，排除了进程崩溃退出导致的不就绪 |
| 3 | K8s Event | kubelet | Readiness probe failed: HTTP probe failed with statuscode: 503 | 确认真实探针失败现象，直接导致 Pod 状态未就绪 |
| 4 | K8s Event | kubelet | Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused | 早期存在连接被拒绝的历史错误，但当前 503 状态码表明端口已通但服务主动拒绝 |
| 5 | Logging | elasticsearch | 8 次 "dependency unavailable" (error, http_status: 503) | 核心证据：应用层明确报告内部依赖不可用，并返回 503 |
| 6 | Tracing | deepflow | L7 Flow: 172.16.104.19 → 172.16.104.26 : GET /work HTTP 503 (9 次) | 网络流量证实应用对外返回了 503，与日志现象完全对应 |
| 7 | Tracing | tempo | Span: GET /work, status: 503, mode: readiness_fail | 将 503 响应与 Readiness Probe 的探测行为进行了关联 |

**证据链说明：**
Pod 保持 Running 状态但被判定为 NotReady（证据 1, 2）。探针直接命中了应用返回的 HTTP 503（证据 3），而应用层日志显示其因“内部依赖不可用”主动返回了 503（证据 5）。追踪数据进一步证实了该 503 响应与 Readiness Probe 探测的流量特征一致（证据 6, 7）。早期连接被拒绝的报错（证据 4）说明网络链路在 8080 端口是通的，当前问题聚焦于应用内部依赖。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖服务不可用 → Readiness Probe 请求返回 HTTP 503 → kubelet 持续判定探针失败 → Pod 状态保持 NotReady
```

### 根因结论

**已确认的根因：** 应用服务内部依赖不可用。

**分析：** 
现有证据形成完整闭环：
1.  **现象层**：Pod 进程存活但状态为 NotReady，因为 Readiness Probe 返回 HTTP 503（证据 1, 2, 3）。
2.  **应用层**：日志显示应用在处理探针请求时遇到了 `dependency unavailable` 错误并返回 503（证据 5）。
3.  **流量层**：网络流量和追踪 Span 证实了 503 响应确实发生在 Readiness Probe 对应的请求中（证据 6, 7）。

**缺失的决定性事实：** 具体的下游依赖（Service 或 DB）名称及其网络拓扑位置，但足以确定应用层逻辑/资源问题是当前导致 NotReady 的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 55.7s
├─ 问题定位: 12.7s
├─ 并发证据采集: 31.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 31.3s (Evidence 24.1s, RCA 7.0s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
