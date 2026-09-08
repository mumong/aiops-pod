## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用依赖不可用（dependency unavailable）导致 /work 端点持续返回 HTTP 503，使 kubelet Readiness Probe 校验失败，Pod 进入 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (x1558 over 78m, fact-9edadb42c96b) | 直接证实 Readiness 探针因业务 HTTP 错误而持续失败。 |
| 2 | K8s State | pod condition | `Ready=False, ContainersNotReady: [app]` (fact-0174b3200f6c) | 记录 Pod 最终状态为 NotReady，由应用容器状态引起。 |
| 3 | Logging | elasticsearch | `dependency unavailable` (HTTP 503, path: /work, service: aiops-lab-workload, 16 occurrences, fact-3864ff82e0a6) | 证明业务逻辑在 /work 端点遇到上游依赖不可用，主动返回 503。 |
| 4 | K8s Config | container resource | memory_limit: 96Mi, memory_request: 24Mi, cpu_limit: 200m (fact-017e1a961e37) | 确认资源限制范围，内存硬限制 96Mi。 |
| 5 | Metric | prometheus | `container: app, metric: prometheus_sample, value: 30.85` (fact-87be1e940c44) | 提供应用侧的单一资源使用快照。 |
| 6 | Tracing | Tempo | Span `GET /work` returned `status_code: 503` (trace_id: dd70455af090da47e572b9dafcc763eb, fact-00691e3fbd03) | 链路追踪证实请求在目标端点返回 503。 |
| 7 | Tracing | Deepflow | L7 Flow: `GET /work` response_code: 503 (dst_ip: 172.16.104.35, occurrence: 9, fact-5217c546588b) | 网络流数据佐证该 Pod IP 的 /work 端点持续返回 503。 |

**证据关联说明：**
日志 (E3) 记录了具体的根因 `dependency unavailable`，该错误直接对应 K8s Event (E1) 和 L7 Flow (E7) 中的 HTTP 503 状态码。Tempo Span (E6) 进一步在应用层确认了 `/work` 端点的 503 响应。这组证据互相印证了“应用层返回 503 -> 探针失败 -> Pod NotReady”的因果关系。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖服务不可用 → 应用 /work 端点返回 HTTP 503 (dependency unavailable) → kubelet Readiness Probe 持续失败 (statuscode: 503) → Pod 进入 NotReady 状态
```

### 根因结论

**已确认的根因：**
应用内部依赖的服务不可用（`dependency unavailable`），导致 `aiops-case-09/workload-5f4fb9ff45-7b77l` 上的 `app` 容器在处理 `/work` 端点请求时，连续向 kubelet 的 Readiness Probe 返回 `HTTP 503` 状态码。

**证据支撑：**
1.  **日志 (fact-3864ff82e0a6)**：明确记录了 `dependency unavailable` 错误模式，且伴随 HTTP 503 状态码，指出了具体的错误原因。
2.  **K8s Event (fact-9edadb42c96b)**：kubelet 报告探针连续失败，原因是接收到 `HTTP 503` 响应。
3.  **Tracing (fact-00691e3fbd03, fact-5217c546588b)**：Span 和 L7 Flow 数据在链路和网络层分别证实了请求在 `aiops-lab-workload` 处获得了 503 响应。

综上，Pod 的 `NotReady` 状态并非由资源耗尽（如 OOM）或调度失败引起，而是由于应用代码层面的依赖错误，触发了探针机制导致的“假死”隔离状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 29.2s
├─ 并发证据采集: 131.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 131.0s (Evidence 123.6s, RCA 7.1s)
└─ 汇总总结: 15.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
