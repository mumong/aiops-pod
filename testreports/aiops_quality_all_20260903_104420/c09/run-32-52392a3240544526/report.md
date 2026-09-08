## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用依赖不可用导致 HTTP 503 响应，引发 Readiness Probe 持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `Ready: False`, `ContainersNotReady` (app), 时间 `2026-09-03T17:53:37Z` | 确认 Pod 处于非就绪状态，容器未满足条件 |
| 2 | K8s Event | `Readiness Probe` | `HTTP probe failed with statuscode: 503` (x1766 over 89m) | 提供探测失败的直接指标，确认故障持续存在且高频触发 |
| 3 | Logging | `log.pattern` | `http_request 503 dependency unavailable` (path: `/work`, service: `aiops-lab-workload`) | 揭示内部业务层返回 503 的真实原因（依赖不可用），作为探测失败的业务级证据 |
| 4 | Tracing | `Deepflow flow` | `HTTP GET /work` → `503` (src: 172.16.104.19, dst: 172.16.104.26), 9 次重现 | 网络层观测确认了从客户端到 Pod IP 的流量均收到 503，与日志和事件因果闭环 |
| 5 | K8s State | `pod.restart_count` | `0` | 排除容器崩溃重启导致的瞬时故障，确认为持续的应用层异常 |
| 6 | Tracing | `Tempo Span` | `aiops.observed_mode: "readiness_fail"`, `http.response.status_code: 503` | 链路追踪直接标记了该次请求被 K8s 视为 Readiness 失败的观察模式 |

**证据综合分析：**
K8s Event 与 Pod 状态共同确立了 `Readiness Probe 失败` 这一外部表现。内部 Logging 明确指出失败原因为 `dependency unavailable`，表明故障不在网络连通性或资源调度（Restart=0），而在应用自身的依赖逻辑。Tracing 数据通过外部 HTTP Flow (dst IP 172.16.104.26 对应 Pod IP) 和业务 Span 双重验证了 `503` 响应确实由该 Pod 发出，且被明确标记为 `readiness_fail`。所有维度的证据均指向同一个确定性原因。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 (Logging: "dependency unavailable") 
→ 应用业务逻辑返回 HTTP 503 (Tracing/Logging: "http_status: 503") 
→ K8s Readiness Probe 探测失败 (K8s Event: "probe failed with statuscode: 503") 
→ Pod Ready 状态变更为 False，不可用于接收流量 (K8s State: "Ready: False")
```

### 根因结论

已确认的根因是 **应用依赖不可用**。

该根因直接导致应用处理请求时抛出异常或拒绝处理，返回 `HTTP 503` 响应。由于 K8s 配置的 Readiness Probe 对 503 状态码判定为健康检查失败（见证据 #2），导致该 Pod 被从 Service Endpoint 中剔除（见证据 #1, #6）。

现有证据（包括 K8s 事件、Pod 状态、日志聚合、Tracing 全链路和 Flow 数据）已完全覆盖因果链的上游（依赖状态）、中游（业务返回 503）和下游（K8s 探测反馈），事实闭环完整，支持 RCA 结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.8s
├─ 并发证据采集: 70.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 70.3s (Evidence 63.8s, RCA 6.3s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
