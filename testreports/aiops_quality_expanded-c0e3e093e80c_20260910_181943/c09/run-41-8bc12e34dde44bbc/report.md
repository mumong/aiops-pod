## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod NotReady (Readiness Probe failed: HTTP 503) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接症状，确认 Kubelet 检测到的就绪失败原因是 503 状态码 |
| 2 | K8s State | kubernetes | `pod.condition: ContainersReady=ContainersNotReady(app), Ready=ContainersNotReady(app)` | 确认 Pod 实际状态与探针结果一致，容器未就绪 |
| 3 | Logging | elasticsearch | `dependency unavailable` (HTTP 503, path: `/work`) | 提供应用层日志，将 503 状态码归因于“依赖不可用”这一具体应用错误 |
| 4 | Tracing | tempo | `http.response.status_code: 503`, `attributes.aiops.observed_mode: readiness_fail` | 确认探针请求链路返回 503，且被标记为探针失败模式 |
| 5 | Tracing | deepflow | `dst_ip: 172.16.104.16` -> `response_code: 503` | 确认 Pod 自身 IP 的入站流量持续被拒绝，且与日志时间窗吻合 |
| 6 | K8s Config | kubernetes | `resource_limit.memory: 96Mi` | 作为环境背景，确认资源限制配置情况 |

日志中记录的 `dependency unavailable` 错误（fact-2880df2fde51 等）与 Tempo 追踪中记录的探针 503 响应（fact-b7f784fdb898）相互印证，明确指向应用代码在 `/work` 路径返回失败是由于内部依赖问题，而非网络连通性或资源耗尽问题。

## 🎯 根因分析 · g1

```text
Application dependency unavailable → Readiness probe /work returns HTTP 503 → Kubelet marks container unready → Pod enters NotReady state
```

### 根因结论
已确认根因为：**应用探针端点 `/work` 因依赖不可用（dependency unavailable）返回 HTTP 503 状态码**。

*   **直接原因**：应用代码在探针检查时未能访问其依赖资源（证据编号 3、4、5）。
*   **机制**：Kubelet 执行就绪探针（Readiness Probe）时，收到 HTTP 503 响应，判定容器不健康，从而导致 Pod 状态标记为 `ContainersNotReady`（证据编号 1、2）。
*   **缺失事实**：当前证据无法确认导致“依赖不可用”的具体下游服务或资源名称（unknowns: Specific identity of the unavailable dependency）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.2s
├─ 并发证据采集: 58.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 58.1s (Evidence 51.7s, RCA 6.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
