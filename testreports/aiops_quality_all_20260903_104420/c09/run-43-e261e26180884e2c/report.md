## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | workload-5f4fb9ff45-cfzz6 status NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 状态为 `Running`，重启次数 `0` | 确认应用进程仍在运行，非崩溃重启导致的 NotReady |
| 2 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (发生 2494 次，持续 121m) | 直接证明就绪探针持续失败，是 Pod 变为 NotReady 的机制 |
| 3 | K8s Config | Kubernetes | Pod IP `172.16.104.26/32`；内存 Request 24Mi / Limit 96Mi；CPU Request 20m / Limit 200m | 提供网络和资源配置上下文，非资源限制导致 OOM 或驱逐 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `0` (样本 1) | 独立验证应用未发生重启，与 K8s 状态事实一致 |
| 5 | Logging | Elasticsearch | 日志模式 `dependency unavailable`，HTTP `503` 访问 `/work`，连续 8 次记录 (19:54:02-19:54:28)，内存分配量始终为 0 | 揭示应用业务逻辑返回 503 的核心原因是下游依赖不可用 |
| 6 | Tracing | Deepflow/Tempo | Flow: `GET /work` from `172.16.104.19` to `172.16.104.26`，返回 `503` (出现 9 次)；Span `5a23e0c80f2d1e117abdc6c429c94edd` 记录 `observed_mode=readiness_fail` | 追踪链路证实外部请求与探针均遭遇同一 503 响应，且与日志时间窗口关联 |

**证据印证说明：**
Kubernetes Event 记录了探针 503 失败的状态（#2），而 Logging（#5）和 Tracing（#6）的原始事实揭示了 503 的具体业务逻辑根源为“dependency unavailable”。Metric 重启计数为 0（#4）与 K8s State（#1）一致，排除了因应用频繁重启导致的不稳定性。日志中内存分配为 0 且无 CPU 瓶颈记录，进一步支持结论指向依赖问题而非资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖不可用 → 应用返回 HTTP 503 → Kubelet Readiness Probe 判定失败 → Pod 状态 NotReady
```

### 根因结论

已确认根因：**应用依赖不可用导致就绪探针持续返回 HTTP 503 失败**。

根据事实证据，Pod 本身处于 `Running` 状态且未重启，但 Kubelet 的健康检查探针（Readiness Probe）在 `/health` 或类似端点收到了 HTTP 503 响应。日志和链路追踪（#5, #6）均明确指向业务层面的“dependency unavailable”错误，直接触发了探针机制判定应用未就绪，从而将 Pod 标记为 `NotReady`。

缺失的决定性事实：日志和探针未能识别具体的**下游依赖服务标识**（unknowns: "Specific identity of the unavailable dependency causing 503"），导致无法进一步定位是哪个依赖组件引发了 503。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 25.3s
├─ 并发证据采集: 556.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 556.8s (Evidence 548.4s, RCA 8.1s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
