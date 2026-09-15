## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod workload-79d9f8fd88-bsn84 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason: "CrashLoopBackOff"` (`fact-4615849a2f7e`) | 确认 Pod 当前处于重启循环的异常状态 |
| 2 | K8s Event | kubernetes | `BackOff` 警告: `Back-off restarting failed container app` (`fact-6fb7456cbdfb`) | 记录 Kubelet 因容器反复失败而暂停重启的行为 |
| 3 | K8s Event | kubernetes | `Unhealthy` 警告: `Liveness probe failed: HTTP probe failed with statuscode: 500` (`fact-a78434670aa0`) | 指出导致容器被杀的直接原因是健康检查返回 500 错误 |
| 4 | K8s Config | kubernetes | `container.resource_request.memory: "24Mi"` (`fact-29ae0d961201`) | 确认内存限制宽松，排除 OOM 导致退出的可能 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes: 3469312` (约 3.3 MiB) (`fact-2698be22235d`) | 当前内存使用量极低，佐证异常非资源耗尽引起 |
| 6 | Logging | elasticsearch | 成功请求日志: `http_status: 200` (`fact-4f99442cc71a`) | 证明应用业务逻辑 `/work` 接口本身是可用的 |
| 7 | Tracing | tempo | `application_span`: `GET /work`, `http.response.status_code: 200`, `aiops.observed_mode: "liveness_fail"` (`fact-0a2643cb47d8`) | 结合 Span 属性明确识别出故障模式为“健康检查注入失败” |

**证据关联说明：**
Kubernetes 事件和指标证实了 `liveness` 探针因 HTTP 500 导致容器反复被杀（证据 #2, #3, #5）。
与此同时，业务日志和 Trace 显示应用对 `/work` 的请求均能成功返回 200（证据 #6, #7），但 Trace 中的 `aiops.observed_mode` 明确标记了故障注入点。这些事实共同指向：故障并非应用崩溃，而是探针端点 `/health` 被特定配置强制置为失败。

## 🎯 根因分析 · g1

### 因果链

```text
注入 FAILURE_MODE=liveness_fail 环境变量 (事实 #7) → /health 端点返回 HTTP 500 (事实 #3) → Kubelet 连续探测失败并 Kill 容器 (事实 #2) → Pod 进入 CrashLoopBackOff 状态 (事实 #1)
```

### 根因结论

已确认根因为**故障注入（Fault Injection）导致 Liveness 探针持续失败**。

*   **具体机制**：应用被注入了 `FAILURE_MODE=liveness_fail` 环境变量（证据 #7），这使得 Liveness Probe 的健康检查端点 `/health` 强制返回 HTTP 500 错误，而非应用崩溃。
*   **Kubernetes 行为**：Kubelet 检测到探针连续失败后，按照策略 Kill 了 `app` 容器，由于容器启动后迅速再次返回 500，导致了观察到的 `CrashLoopBackOff` 状态（证据 #1, #2）。
*   **排除干扰**：日志显示业务接口正常（证据 #6），且内存使用极低（证据 #5），排除了应用宕机或 OOM 等常规故障可能。

---

## 📊 性能统计

```text
├─ 总耗时: 4.1m
├─ 问题定位: 20.0s
├─ 并发证据采集: 214.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 214.1s (Evidence 204.1s, RCA 9.8s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
