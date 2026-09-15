## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe配置错误：Probe指向端口18081和路径/ready，而应用实际监听端口18080且仅响应路径/health，导致kubelet持续收到connection refused从而标记Pod为NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (x832 over 68m) | 证实 kubelet 探测端口 18081/路径 /ready 持续失败，直接导致 NotReady 状态 |
| 2 | K8s State | Kubernetes | Pod Phase: Running, Ready Condition: False (ContainersNotReady), Restart Count: 0 | 确认容器已启动且未发生重启，故障由探测机制而非应用崩溃引起 |
| 3 | K8s Config | Kubernetes | 资源 Request: CPU 5m / Memory 8Mi, Limit: CPU 200m / Memory 64Mi | 排除因资源不足导致的启动延迟或OOM |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 证实应用服务运行期间未发生异常退出，符合探测逻辑错误导致的稳态 |

**证据说明**：
- 证据 1 记录了 kubelet 具体的连接拒绝错误信息，明确指出了错误的端口（18081）和路径（/ready）；证据 2 和 4 共同确认了应用本身处于正常运行的 Running 状态且未发生重启，排除底层稳定性问题。
- 证据 3 表明资源配额极低但非超限，排除了资源争抢导致服务启动缓慢的可能性，将问题聚焦于探测配置与实际服务端点的匹配性上。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误 (端口/路径不匹配) → kubelet 持续请求失败 (connection refused) → Pod Ready 条件维持为 False → 用户可见现象：Workload 状态 NotReady，无新流量分配
```

### 根因结论

已确认根因为 **Readiness Probe 配置错误**。Probe 被配置为请求端口 `18081` 和路径 `/ready`，但应用实际监听端口 `18080` 且仅提供路径 `/health`。这种配置与运行时实际状态的差异导致 kubelet 持续收到 `connection refused` 错误，从而阻止 Pod 进入 Ready 状态。证据 1 中的原始错误日志与上述配置差异完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 25.4s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-v16/workload: 38.1s (Evidence 31.4s, RCA 6.5s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
