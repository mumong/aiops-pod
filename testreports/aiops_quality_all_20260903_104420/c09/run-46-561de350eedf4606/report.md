## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 上游依赖不可用导致应用持续返回 HTTP 503，进而触发 Readiness 探针失败使 Pod 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `status: Running` (持续运行中，无重启) | 排除进程 CrashLoop 或 OOMKilled 导致的重启现象 |
| 2 | K8s Event | Kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (频率: 2598次/126m) | 直接观测到探针失败的根本原因：应用层持续返回 503 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 与 Pod 重启次数为 0 的状态吻合，佐证未发生容器级故障 |
| 4 | Logging | Elasticsearch | `dependency unavailable` (503, path: /work, 连续发生 8 次, trace_ids: 0db5... 等) | 揭示 503 的来源：应用内部尝试访问上游依赖时失败 |
| 5 | Tracing | Deepflow | L7 Flow: `GET /work`, `src_ip: 172.16.104.19 -> dst_ip: 172.16.104.26`, `response_code: 503` | 提供网络层面的事实，确认应用接收到的请求因 503 被终止，验证上游不可用导致本地响应失败 |

**证据印证说明：**
Kubernetes 探针捕获的 503 错误（证据 #2）与日志记录的 `dependency unavailable`（证据 #4）及 Tracing 的 Flow 状态（证据 #5）完全一致。三者共同指向一个事实：应用自身存活但未就绪，原因是依赖调用失败，进而引发探针持续失败。未发生容器重启（证据 #1, #3）进一步排除了容器自身资源或稳定性问题。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖不可用 → 应用内部调用返回 503 并记录错误日志 → Readiness 探针检测到 503 → Pod 被 Kubernetes 置为 NotReady 状态
```

### 根因结论

**已确认的根因：上游依赖不可用。**

*   **现象解释**：应用持续因依赖不可用而返回 HTTP 503。由于 Readiness 探针将 503 视为不健康，Kubernetes 不断将 Pod 状态更新为 `NotReady`。
*   **证据支撑**：
    *   **现象层**：K8s Event 显示探针持续失败，原因明确为 `HTTP probe failed with statuscode: 503`（证据 #2）。
    *   **机理层**：应用日志明确报错 `dependency unavailable` 且伴随 HTTP 503 状态（证据 #4）；网络流量追踪证实该 503 是由接收请求后返回（证据 #5）。
    *   **状态层**：Pod 未发生重启（证据 #1, #3），证明 503 是由业务逻辑（依赖链断裂）导致的，而非资源耗尽或代码崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 24.0s
├─ 并发证据采集: 93.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 93.6s (Evidence 85.6s, RCA 7.8s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
