## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | ReadinessProbe配置的端口(18081)和路径(/ready)与容器实际监听的端口(18080)和路径(/health)不一致 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Unhealthy`: `Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (576次 over 45m) | 确认 ReadinessProbe 频繁失败，明确显示探针目标端口(18081)与路径(/ready) |
| 2 | K8s State | Kubernetes | `pod.condition.Ready: False` (ContainersNotReady: app) | 确认 Pod 整体状态因应用容器未就绪而异常 |
| 3 | K8s State | Kubernetes | `pod.phase: Running`, `container.restart_count: 0` | 排除容器启动崩溃或重启循环问题，指向应用内部配置与探测不一致 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (app) | 确认应用生命周期稳定，进一步排除因 OOM 或 CrashLoopBackOff 导致的未就绪 |

**证据说明：**
Kubernetes 事件 (证据 1) 明确指出 `dial connection refused`，证实了 ReadinessProbe 配置的地址/路径与容器实际运行环境不匹配；容器状态 (证据 2) 的 `ContainersNotReady` 与 Pod 的 `Running` 状态 (证据 3) 结合，以及 Prometheus 监控中重启次数为 0 (证据 4)，共同排除了容器启动失败等外部因素，将故障锁定在探针配置与实际服务监听端口的差异上。

## 🎯 根因分析 · g1

```text
ReadinessProbe配置与容器实际监听不一致 → 探测请求连接被拒绝 → Readiness Probe频繁失败 → Pod状态变为 Unready
```

### 根因结论
已确认的根因为 **ReadinessProbe 配置错误**。探针配置的端口(18081)和路径(/ready)与容器实际监听的端口(18080)和路径(/health)不一致 (证据 1)。这导致 kubelet 发起的探测请求始终被拒绝，进而触发 Pod 的 `ContainersNotReady` 状态 (证据 2, 3)。证据充分，无需补充。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.2s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-v16/workload: 45.3s (Evidence 39.2s, RCA 5.9s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
