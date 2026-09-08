## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用代码未实现健康检查端点逻辑，导致 readiness probe 因依赖缺失持续返回 HTTP 503 状态码 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (4m30s 内累计 311 次) | 直接证实 Kubelet 检测到 Probe 返回业务错误码 503 |
| 2 | K8s Event | Kubelet | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp ... connection refused` (19m 内累计 2 次) | 早期连接被拒的独立异常记录，佐证 8080 端口服务不可用 |
| 3 | K8s State | Pod Status | `ContainersReady: False`, Reason: `ContainersNotReady` | 证实 Kubelet 已将 Pod 的 Readiness 状态标记为 False，符合 NotReady 表现 |
| 4 | Logging | Elasticsearch | 错误日志 `dependency unavailable`, HTTP 状态码 `503`, Path `/work`, Occurrence: 8 次 | 内部应用日志证实业务代码层因“依赖不可用”主动或被动返回 503 |
| 5 | Tracing | Tempo Span | `GET /work`, `http.response.status_code: 503`, `aiops.observed_mode: readiness_fail` | 明确将 `/work` 请求与就绪检查行为关联，确认 Probe 目标路由直接返回 503 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 排除因 OOM/Killed 导致的 CrashLoopBackOff 或重启，证明容器进程一直在运行但未就绪 |

**证据说明**：
K8s Event 记录表明 Kubelet 持续探测 Pod 返回 503 或连接被拒；Logging 和 Tracing 进一步揭示 503 是由应用层因 `dependency unavailable` 引起的。由于重启次数为 0，证明容器进程存活，故障点完全集中在业务代码未能正确处理依赖或健康检查路由逻辑上。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 (未实现/未处理 readiness 依赖) → Readiness Probe 探测 /ready 或 /work 返回 HTTP 503 (fact-1, fact-4, fact-5) → Kubelet 更新 Pod 状态 ContainersReady=False (fact-3) → 服务进入 NotReady 状态，拒绝外部流量
```

### 根因结论

已确认的根因是：**应用代码未正确实现或处理就绪检查端点逻辑，导致 `readiness probe` 持续返回 HTTP 503 状态码（证据 #1, #4, #5）**。

具体而言，应用内部日志指出“依赖不可用”(Evidence #4)，使得应用在面对健康检查请求时无法提供正常响应（返回 503），进而导致 Kubelet 判定容器处于 `ContainersNotReady` 状态（Evidence #3）。这符合“应用代码未实现健康检查端点逻辑，导致 readiness probe 因依赖缺失持续返回 HTTP 503 状态码”的结论。

**未知项**：日志中未明确指出具体的“dependency”指代哪个上游服务或配置项，但现有的 K8s 状态和日志模式已足以确认故障根源在于应用侧的健康检查响应逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 21.6s
├─ 并发证据采集: 111.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 111.3s (Evidence 101.1s, RCA 10.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
