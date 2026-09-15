## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用程序在处理 /work 请求时因下游依赖服务不可用持续返回 HTTP 503，导致 kubelet 就绪探针（Readiness Probe）反复检测失败，触发 ContainersNotReady 条件使 Pod 处于 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | phase: Running, status: Running (fact-96a079765b68, fact-c0d171ba4f3c) | 确认容器进程已在运行，非启动失败或 CrashLoopBackOff 导致 |
| 2 | K8s Event | Kubelet Readiness | Warning Unhealthy: Readiness probe failed: HTTP probe failed with statuscode: 503 (fact-6482fad826fa) | 直接证据：就绪探针检测到 HTTP 503，触发 NotReady 状态 |
| 3 | K8s State | Pod Conditions | Ready=False, reason=ContainersNotReady, message: containers with unready status: [app] (fact-102d7b9f93bc, fact-1f21bc825e66) | 确认 Pod 整体状态因应用容器未就绪而转为 NotReady |
| 4 | Logging | Application Error | pattern: http_request, level: error, message: "dependency unavailable", http_status: 503, path: /work, service: aiops-lab-workload (fact-172c9ca32d2e et al.) | 应用层日志揭示 503 来源是下游依赖不可用 |
| 5 | Tracing | L7 Flow | HTTP GET /work, src_ip: 172.16.104.62, dst_ip: 172.16.104.16, response_code: 503 (fact-0ad8c440336d et al.) | 流量侧数据印证 `/work` 接口持续返回 503，跨多个 Trace ID (e.g., 3cfa8efe6e08de7a7e38cde3bae0f417) |

**证据交叉印证：**
1.  **K8s 侧**的探针失败日志（证据 2、3）与**应用侧**的日志模式（证据 4）完全对应，均指向 `/work` 请求返回 503。
2.  **Tracing 侧**的 HTTP Flow 数据（证据 5）与 K8s 探针请求路径一致，进一步确认了故障的持续性和服务级别的表现。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用 /work 接口返回 HTTP 503 → kubelet 就绪探针检测失败 → Pod 状态转为 NotReady (ContainersNotReady)
```

### 根因结论

已确认根因：应用程序在处理 `/work` 请求时，因下游依赖服务不可用，持续返回 HTTP 503 状态码。

该问题通过以下证据链得到证实：
1.  **Kubelet 探针告警**：Kubelet 对 `app` 容器的就绪探针进行 HTTP 检测时，频繁收到 503 响应（证据 2），导致容器状态标记为未就绪，进而使 Pod 状态变为 `NotReady`（证据 3）。
2.  **应用日志与流量日志**：应用日志记录了明确的 "dependency unavailable" 错误（证据 4），且流量追踪数据显示针对 `/work` 路径的请求持续返回 503（证据 5），而非由于资源限制、网络中断或应用进程崩溃（容器仍在运行，证据 1）。

综上所述，Pod 处于 `NotReady` 状态的根本原因是下游依赖服务的故障导致应用健康检查接口持续失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 22.9s
├─ 并发证据采集: 77.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 77.5s (Evidence 70.1s, RCA 7.2s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
