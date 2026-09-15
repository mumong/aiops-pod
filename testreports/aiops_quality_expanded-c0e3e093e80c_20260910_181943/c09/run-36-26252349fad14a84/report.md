## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc status is NotReady due to persistent Readiness probe failures. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `Ready=False`, `ContainersReady=False` (`ContainersNotReady`), 状态 `Running` 但 `restart_count=0` (fact-1611a2d75c5e, fact-4eefdf994e93, fact-ec87a212a7e0) | 确认 Pod 虽然运行但处于不健康状态，且无重启历史，排除资源超限导致的 CrashLoop。 |
| 2 | K8s Event | kubernetes | `Unhealthy` 事件: Readiness probe failed: HTTP probe failed with statuscode: 503 (fact-12a800b077d0) | 明确探针执行结果，直接触发容器未就绪判定。 |
| 3 | K8s Config | kubernetes | Container `app` CPU Limit `200m` / Memory Limit `96Mi` (fact-2a4d3cf5186d, fact-a5fee16064e7) | 资源限制处于常规范围，非 OOM 或 CPU 饱和瓶颈。 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` 为 `0` (fact-b07fd084ebc5) | 确认应用进程未发生过异常退出，进一步支持“运行中但功能异常”的判断。 |
| 5 | Tracing | deepflow+tempo | GET /work 返回 `503` (flow-58537d000141); Tempo 确认 `aiops.observed_mode: readiness_fail` (fact-2db908a120d5) | 流量观测与探针机制一致，证明请求因应用返回错误状态被拒绝，符合探针预期行为。 |
| 6 | Logging | elasticsearch | 8 次记录 `dependency unavailable`, HTTP 503, path `/work` (fact-4cfa88f5a346...) | 记录明确指向内部依赖不可用导致的错误，揭示了探针返回 503 的具体业务原因。 |

**证据说明：**
Pod 始终处于 Running 状态且重启次数为 0，排除了资源竞争或崩溃重启导致的问题。Kubernetes 探针、Prometheus 指标（重启数为 0）与 Deepflow 流量日志（GET /work 返回 503）在“容器健康”与“应用业务逻辑”两个维度上完全一致。Logging 维度进一步明确了业务逻辑失败的根源在于“内部依赖不可用（dependency unavailable）”。

## 🎯 根因分析 · g1

### 因果链

```text
内部依赖服务不可用/配置错误 → /work 端点持续返回 HTTP 503 (dependency unavailable) → 探针检测失败超过阈值 → Pod Ready=False, 进入 NotReady 状态
```

### 根因结论

已确认根因为：**应用 `/work` 端点因内部依赖不可用（dependency unavailable）而持续返回 HTTP 503 错误，导致 K8s Readiness 探针反复失败。**

- **现象解释**：K8s 探针（fact-12a800b077d0）检测到 503 状态码，将 Pod 标记为 `NotReady`。应用进程因未被资源限制杀死，保持 Running 状态且无重启（fact-4eefdf994e93, fact-b07fd084ebc5）。
- **证据支撑**：Trace/Flow 观测（fact-58537d000141, fact-2db908a120d5）确认 GET /work 的响应状态为 503；日志记录（fact-4cfa88f5a346）直接给出了错误原因为 `dependency unavailable`。
- **不确定性**：确切是哪个内部服务不可用、以及该内部服务为何不可用，因未在拓扑或日志中查明（unknowns: 内部依赖身份及故障源），属于下一步排查方向。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 21.5s
├─ 并发证据采集: 118.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 118.3s (Evidence 108.8s, RCA 9.4s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
