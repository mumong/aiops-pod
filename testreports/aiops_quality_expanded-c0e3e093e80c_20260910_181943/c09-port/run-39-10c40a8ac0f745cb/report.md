## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误（端口与路径均不匹配） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Unhealthy 9s (x832 over 65m) kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-1dbedce0cf62) | 证实读探针持续失败，拒绝建立连接 |
| 2 | K8s State | Pod Condition | `ContainersReady: False`, `Ready: False`, `ContainersNotReady: app` (fact-4de1590c0e7c) | 反映容器虽在运行但未被 K8s 视为就绪 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total` for `app` = `0` (fact-9b9acd5bd899) | 证明应用未崩溃，Pod 状态异常非由 OOM 或 CrashLoop 引起 |

上述证据互相印证：Metric 显示进程存活且未重启，但 K8s 条件显示容器未就绪，Kubelet 日志明确记录了端口 `18081` 连接被拒。结合诊断事实，这是由于读探针配置的端口和路径与容器实际服务不匹配所致。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误（端口与路径均不匹配） → 探针请求被目标拒绝 → kubelet 持续报告 Unhealthy → 容器未被标记为 Ready，影响流量调度
```

### 根因结论

已确认根因为 **Readiness Probe 配置错误（端口与路径均不匹配）**。
- 证据 `fact-1dbedce0cf62` 显示探针尝试连接 `172.16.104.33:18081/ready` 时返回 `connection refused`，且该错误在 65 分钟内发生了 832 次，排除了瞬时网络波动。
- 证据 `fact-9b9acd5bd899` 显示容器重启次数为 0，确证了应用进程本身仍在正常存活，异常仅源于外部健康检查机制的配置不匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 16.7s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-v16/workload: 37.9s (Evidence 32.1s, RCA 5.7s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
