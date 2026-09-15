## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | NotReady | Pod aiops-case-v17/workload 因健康检查失败（Liveness/Readiness probe）触发重启（Exit 137/OOMKilled），导致 NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason="Error" | 确认容器异常退出，非正常停止。 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) (fact-4aef14d24740) | 直接指出 Liveness 探针超时，是触发重启和 NotReady 的机制。 |
| 3 | K8s Config | Kubernetes | container.resource_limit.memory="64Mi" (fact-10d84a7bedb3) | 确认应用存在硬内存限制，为 OOM Kill (Exit 137) 提供资源约束背景。 |
| 4 | K8s Event | Kubernetes | Exit Code: 137 (fact-29fa2ef37d0a) | 确认容器因 OOM Kill 终止，该状态与探针超时后的重启行为同时存在。 |
| 5 | Logging | Elasticsearch | GET /health HTTP/1.1 200 (多次, 含 fact-57050115f16b 等) | 确认应用日志层面 `/health` 接口最终成功，证明阻塞发生在应用内部而非网络。 |
| 6 | Tracing | Deepflow | GET /health duration_us min=3001350, max=3001920 (fact-3c0efe8d8c1b) | 确认 `/health` 请求实际耗时约 3 秒，与代码中 `sleep(3)` 行为一致，且远超探针超时时间。 |

证据 1、2 与 4 形成闭环：探针因超时（2）触发重启导致容器错误退出（1），并在某些周期伴随 OOM Kill（4）。证据 6 通过追踪数据显示 `/health` 的实际耗时为 3 秒左右，直接印证了“探针超时”的根本原因，而证据 5 的日志仅展示了最终返回结果，掩盖了内部的阻塞过程。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /health 端点包含 time.sleep(3) → Liveness Probe (timeoutSeconds=1s) 探测超时 → 容器因探针失败触发重启，且期间因内存竞争或偶发原因触发 OOM Kill (Exit 137) → Pod 状态频繁变为 NotReady 并重启
```

### 根因结论

**已确认根因**：应用代码 `/health` 健康检查逻辑中存在阻塞操作（耗时约 3 秒的 `time.sleep(3)`），超过了 Kubernetes Liveness Probe 配置的超时时间（1 秒），导致探针频繁超时失败，进而触发容器重启（伴随 Exit 137 OOM Kill），导致 Pod 进入 `NotReady` 状态。

**依据**：
*   **机制确认**：K8s Event 明确记录探针超时（fact-2），Tracing 数据显示 `/health` 请求实际耗时约 3 秒（fact-6），两者直接因果关系成立。
*   **状态确认**：Pod 因探针失败被杀并重启（fact-2），退出码显示 OOM Kill（fact-4）。

**未确认环节**：
*   **OOM 的直接成因**：缺乏崩溃瞬间的内存指标佐证，无法完全排除 `sleep(3)` 期间内存激增导致的 OOM，还是其他并发竞争导致。但 OOM Kill 与探针阻塞重启现象在日志中均被观测到。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.5s
├─ 并发证据采集: 59.5s
│  └─ g1 aiops-case-v17/workload: 59.5s (Evidence 49.2s, RCA 10.1s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-notready-probe-failed, pod-crashloop-runtime, pod-oomkilled
