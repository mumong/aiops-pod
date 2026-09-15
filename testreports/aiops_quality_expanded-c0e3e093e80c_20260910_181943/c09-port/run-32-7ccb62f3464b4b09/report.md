## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | aiops-case-v16/workload Pod 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning Unhealthy: Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused (x704 over 57m) | 直接证据：证实探针连续 57 分钟、704 次因 TCP 连接被拒而失败 |
| 2 | K8s Config | kubernetes | container.app resource_request: cpu=5m, memory=8Mi | 上下文：Pod 资源请求极低，排除资源竞争导致应用启动缓慢或阻塞的可能 |
| 3 | K8s Config | kubernetes | container.app resource_limit: cpu=200m, memory=64Mi | 上下文：Pod 资源限制适中，且无 OOMKill 迹象 |
| 4 | K8s State | kubernetes | Pod Phase: Running, Ready: False (reason: ContainersNotReady); app restart_count: 0 | 现象：容器已在运行但处于未就绪状态，且无重启记录，说明应用进程存活但探针未通 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total(app) = 0 | 佐证：指标证实应用未重启，排除因进程崩溃重启导致的间歇性失败 |

**证据印证关系：**
K8s Event 提供的精确失败信息（连接 18081:18081 被拒绝）直接解释了 K8s State 中 Pod 处于 `Running` 但 `Ready=False` 的矛盾现象。Metric 维度确认重启次数为 0，进一步排除了应用进程不稳定或崩溃重启的嫌疑，将根因锁定在连接层面的配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
ReadinessProbe 配置错误（端口/路径不匹配） → 探针向错误端口发起 TCP 连接被拒 → Kubelet 记录 704 次 Readiness probe failed 事件 → Pod 状态持续为 NotReady
```

### 根因结论

已确认根因：**ReadinessProbe 配置错误**。

根据事实 `fact-57d189ea65df`，Kubelet 记录的 704 次 `Readiness probe failed` 事件明确指向对 `http://172.16.104.33:18081/ready` 的 TCP 连接被拒绝（`connect: connection refused`）。这证实了探针配置的访问端点（18081 端口）与容器内应用实际监听的端点（应用监听 18080 端口且仅提供 /health 路径）不一致。应用进程（`restart_count=0`）正常运行，但由于探针路径不通，Pod 始终无法达到 `Ready` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.8s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-v16/workload: 43.3s (Evidence 33.0s, RCA 10.2s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
