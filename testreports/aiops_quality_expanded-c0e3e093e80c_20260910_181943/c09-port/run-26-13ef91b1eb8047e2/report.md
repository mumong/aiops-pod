## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误：探针指向端口 18081，但应用实际监听端口为 18080，导致持续连接拒绝。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `phase=Running`, `Ready=False` (`reason: ContainersNotReady`) | 确认 Pod 已调度且容器正在运行，但因未满足就绪条件而被拒绝服务 |
| 2 | K8s State | Kubernetes | `pod.status=Running`, `restart_count=0` | 排除应用启动崩溃或频繁重启的可能性 |
| 3 | K8s Event | Kubernetes | `Warning Unhealthy: Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 直接证明健康检查请求被目标端口拒绝，确认为探针配置错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` | 独立确认容器无异常退出或重启事件，佐证非业务故障 |

证据链表明：Pod 状态稳定在 `Running` 且无重启（证据 1, 2, 4），但 `kubelet` 持续报出连接拒绝错误（证据 3）。由于连接失败而非超时或 5xx 错误，且发生在健康检查阶段，直接指向探针配置（端口或路径）与容器实际监听端口不匹配。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置端口 (18081) ≠ 应用监听端口 (18080) → 连接拒绝 (Connection Refused) → 就绪探针连续失败 (Unhealthy Event) → Pod Ready=False (服务不可见)
```

### 根因结论

**已确认的根因**：`Readiness Probe 配置错误`。

Kubernetes 探针被配置为探测端口 **18081**，但应用实际监听在端口 **18080**。这导致 `kubelet` 发起的健康检查请求（证据 3）不断遭遇连接拒绝，致使容器状态始终不满足 `Ready=True`（证据 1），尽管应用本身运行正常且无崩溃（证据 2, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.4s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-v16/workload: 41.7s (Evidence 36.0s, RCA 5.6s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
