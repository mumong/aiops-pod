## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `status: Running` (phase), `containersNotReady: [app]` | 确认 Pod 存活但应用容器不可用，处于异常状态 |
| 2 | K8s Event | K8s Event (kubelet) | `Liveness probe failed: HTTP probe failed with statuscode: 500` (重复 55+ 次) | 直接证实存活探针探测失败，探针返回了 500 错误 |
| 3 | K8s State | K8s Container State | `reason: CrashLoopBackOff`, `back-off 5m0s restarting failed container=app` | 确认容器因探测失败而不断被重启 |
| 4 | K8s Config | K8s Resource Limit | `container resource_limit.memory: 96Mi` | 排除资源限制导致的硬性 OOM (OOMKilled)，配置内存上限并不低 |
| 5 | Metric | Prometheus | `container_memory_usage_bytes`: min `3805184.0`, last `15425536.0`, max `15425536.0` (15.4MB) | 内存使用峰值 (15.4MB) 远低于内存限制 (96Mi)，非内存不足 |
| 6 | K8s State | K8s Container Exit Code | `exit_code: 137` | 确认容器是被信号 (SIGKILL) 强杀终止 |
| 7 | Tracing | Deepflow/Tempo Flow | `GET /work`, `response_code: 200` | 证实业务主要路径 (`/work`) 正常运行，隔离故障至探针检测路径 |

证据表明，Pod 虽然处于 Running 状态，但其应用容器频繁被 kubelet 重启。Kubelet 的 Liveness Probe 连续收到 HTTP 500 错误（证据 #2），进而触发了容器的强制终止（exit code 137，证据 #6）。由于应用的内存使用峰值（15.4MB，证据 #5）远低于 96Mi 的限制（证据 #4），且业务路径 `/work` 能正常返回 200（证据 #7），说明容器是被探针探测失败杀死，而非资源耗尽或应用完全不可用。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 或内部逻辑缺陷 (返回 HTTP 500) → kubelet Liveness Probe 判定失败 → 容器被 SIGKILL (Exit Code 137) 终止 → Pod 状态 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用服务对 Kubelet Liveness Probe 的响应异常导致容器被持续强杀重启。**

诊断证据形成了完整的闭环：
1.  **故障触发机制**：Kubelet 事件明确指出 Liveness Probe 探测失败，且返回 HTTP 500 状态码（证据 #2）。
2.  **终止原因验证**：容器终止的退出码为 137（SIGKILL），符合容器被探针杀死或内部逻辑崩溃后的系统级终止特征（证据 #6）。
3.  **排除资源瓶颈**：Prometheus 内存监控显示使用量（15.4MB）远低于配置的 96Mi 限制（证据 #4、#5），排除了因 OOM 导致容器被系统 kill 的可能性。
4.  **应用可用性隔离**：Tracing 数据证实 `GET /work` 业务路径返回 200（证据 #7），说明应用进程本身并未挂起，而是对探针的健康检查逻辑或特定端点返回了 500 错误。

综上，根因在于应用服务的健康检查逻辑（或探针探测的端点）存在代码缺陷或状态异常，导致其无法向 Kubelet 返回预期的 2xx/3xx 状态码，从而触发了 Kubelet 的保护性重启机制。

---

## 📊 性能统计

```text
├─ 总耗时: 3.5m
├─ 问题定位: 24.8s
├─ 并发证据采集: 172.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 172.0s (Evidence 158.6s, RCA 13.1s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime, pod-oomkilled
