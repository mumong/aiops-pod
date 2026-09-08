## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，持续 17 次重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_exit_code` (fact-7b7de1938d26) | Exit Code: 137 | 确认进程是被强制终止（SIGKILL），排除正常退出 |
| 2 | K8s Event | kubelet (fact-cb7f48521d45) | Liveness probe failed: HTTP probe failed with statuscode: 500 | 直接指明故障触发机制为健康检查端点返回 500 错误 |
| 3 | K8s State | `container.last_terminated_reason` (fact-7528877eb1cc) | reason: Error | 确认上一轮容器生命周期以错误状态结束 |
| 4 | Metric | Prometheus (fact-a87c63c96d09) | waiting reason: CrashLoopBackOff (value: 1) | 量化验证当前异常组状态，与现象一致 |
| 5 | Metric | Prometheus (fact-bd9f1b1981b4) | last_terminated reason: Error (value: 1) | 独立确认上一轮崩溃原因为 Error，与 K8s State 互补 |
| 6 | Logging | Elasticsearch (fact-4436923ed531) | Pattern: `request completed`, path: `/work`, status: 200, count: 8 | 证实业务核心路径（/work）响应正常，排除业务逻辑崩溃导致进程退出 |
| 7 | Tracing | Deepflow (fact-6d1725d2eacc) | HTTP 200 response, duration min/max 18ms/50ms | 网络层观测到的业务请求返回正常，限定了故障范围仅在探针端点 |

**证据关联说明：**
K8s Event (Fact 2) 与 K8s State (Fact 1) 形成闭环，明确指出了“500 错误触发 Liveness 失败进而导致 SIGKILL (137)”的致死链条。Metric (Fact 4, 5) 从监控视角独立证实了上述状态。Logging (Fact 6) 和 Tracing (Fact 7) 证明业务逻辑（`/work` 路径）完全正常，从而排除了应用整体崩溃的可能，将根因精准锁定在健康检查（Health Probe）相关的逻辑或资源状态上。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程在 /health 端点响应 500 错误 → kubelet Liveness Probe 连续失败 → kubelet 发送 SIGKILL 强制终止容器 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态并不断重启
```

### 根因结论

已确认的根因是：**应用进程的健康检查端点（/health）持续返回 HTTP 500 错误，触发 Kubernetes Liveness Probe 失败，导致 kubelet 强制杀死并重启容器。**

*   **直接证据**：K8s Event (Fact 2) 显示 Liveness probe 探测到 HTTP 500 状态码；K8s State (Fact 1, 3) 确认容器因 Error 退出且退出码为 137（SIGKILL）。
*   **排除其他**：Metric (Fact 4) 和 Logging/Tracing (Fact 6, 7) 显示业务请求（如 `/work`）均返回 200 且耗时正常，证明应用进程本身仍在运行且业务逻辑未崩溃，故障仅局限于健康检查端点的响应异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.6s
├─ 并发证据采集: 75.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 75.5s (Evidence 64.7s, RCA 10.7s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
