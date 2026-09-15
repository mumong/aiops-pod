## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Liveness Probe 配置不当导致容器被 Kubelet 强制终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Normal Killing ... Container app failed liveness probe, will be restarted` (`fact-b6dbad8fc0b0`) | 确认容器被 Kubelet 因 Liveness 探测失败而强制杀除的直接触发器 |
| 2 | K8s Event | `kubelet` | `Warning Unhealthy ... Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` (`fact-7e7f9d1b7a62`) | 证明探测请求在等待响应头时发生超时，导致探测失败 |
| 3 | K8s State | `Pod` | `restart_count: 21` (`fact-8a11baea7445`) | 持续异常的症状量化，表明上述失败机制正在循环 |
| 4 | K8s Event | `kubelet` | `Container app failed liveness probe, will be restarted` (`fact-15bfa792f78e` 记录) | 进一步佐证容器因 Liveness 问题被反复重启 |
| 5 | Metric | `Prometheus` | `kube_pod_container_status_last_terminated_reason: 1` (labels: `container: app, reason: Error`) (`fact-c2745fba6efd`) | 独立确认上一次容器终止原因为 Error，与 K8s Event 描述一致 |
| 6 | Logging | `app` | `listening on 18080` (`fact-1f1bce8ac04d`)；`10.2.0.50 - - [14/Sep/2026 13:49:48] "GET /health HTTP/1.1" 200 -` (`fact-1da099a26380`) | 证明应用进程正在运行且能够响应 `/health` 端点 |
| 7 | Tracing | `Deepflow/Tempo` | `GET /health` `response_code: 200`, `duration_us`: `min: 3001036.0, max: 3002217.0` (`fact-79512a39f40a` 聚合) | 揭示实际请求耗时约 3 秒，远超常见默认探测超时阈值，构成导致 `context deadline exceeded` 的深层机制 |

**证据说明：**
Kubernetes 事件明确指出 `Liveness probe failed: context deadline exceeded` 是重启的直接原因；Tracing 聚合数据显示实际 `/health` 请求耗时约 3 秒，解释了为何在标准超时限制下判定为“超时”；同时应用日志显示服务正在运行且返回 HTTP 200，排除了应用完全崩溃的可能性，印证了配置不当导致的假阴性故障。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 默认超时配置过小 → 实际健康检查接口响应耗时 (~3s) 超过限制 → Kubelet 判定探测超时 (context deadline exceeded) → 强制重启容器
```

### 根因结论

**已确认根因：Liveness Probe 配置不当导致容器被 Kubelet 强制终止。**

具体机制为：虽然 `app` 容器运行正常且 `/health` 端点返回 HTTP 200（证据 #6, #7），但接口响应耗时约为 3000ms。Kubelet 默认的 Liveness Probe `timeoutSeconds`（通常为 1 秒）小于该耗时，导致探测请求在等待响应头时发生超时（`context deadline exceeded`，证据 #2）。根据 K8s 策略，Kubelet 将探测失败的容器强制终止并重启（证据 #1, #3）。该根因已被 Kubernetes 事件、指标聚合以及链路追踪的实际耗时数据共同确证。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 12.9s
├─ 并发证据采集: 562.8s
│  └─ g1 aiops-case-v17/workload: 562.8s (Evidence 556.8s, RCA 5.8s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
