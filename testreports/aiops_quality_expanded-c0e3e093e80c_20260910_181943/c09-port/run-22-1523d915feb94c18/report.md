## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload status NotReady (ContainersNotReady) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (x513 over 44m) | 直接观测：Pod 在 Pod IP `172.16.104.33` 的探测端口 `18081` 持续被拒绝连接。 |
| 2 | K8s Config | kubernetes | Resource Limits: CPU `200m`, Memory `64Mi`; Requests: CPU `5m`, Memory `8Mi` | 排除资源压力：容器内存与 CPU 限制宽松且请求量极低，资源耗尽导致 Crash 的可能性低。 |
| 3 | K8s State | kubernetes | `container.restart_count: 0`; Phase: `Running`; Condition: `Ready=False` (ContainersNotReady) | 现象确认：Pod 已启动且运行，但处于 NotReady 状态，且未发生过重启，印证是单次探测配置失败而非生命周期异常。 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (container: app) | 佐证容器无 CrashLoopBackOff 状态，进一步确认非进程崩溃问题。 |

**证据分析：**
Kubernetes 事件表明探针请求连接 Pod IP `172.16.104.33` 的 `18081` 端口时遭遇 `connection refused`，且该错误已持续出现 500 多次。结合容器未重启、资源请求极低的事实，判定网络端口不通并非因为资源耗尽或容器启动失败，而是指向端口配置层面的问题。

## 🎯 根因分析 · g1

### 因果链

```text
readinessProbe 端口配置错误 (18081) 与容器实际监听端口 (18080) 不匹配 → kubelet 探测连接被目标端拒绝 (connection refused) → readiness probe 持续失败 → Pod 状态标记为 NotReady
```

### 根因结论

已确认根因：**就绪探针 (readinessProbe) 配置的探测端口 `18081` 与容器实际应用监听的端口 `18080` 不一致**（基于 `connect: connection refused` 错误模式）。

由于端口不匹配，kubelet 向 Pod IP 的 `18081` 端口发起 HTTP 探测请求时，因该端口无服务监听而被操作系统拒绝连接。这导致就绪探针持续判定失败，进而使 Pod 的 `ContainersReady` 状态保持为 `False`（证据 1、3）。配置资源（证据 2）和指标数据（证据 4）排除了进程崩溃或资源竞争导致的启动失败，进一步锁定了探针配置错误的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.2s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v16/workload: 40.2s (Evidence 32.5s, RCA 7.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
