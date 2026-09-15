## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | ReadinessProbe 配置端口与容器监听端口不一致：探针配置为 18081，容器实际监听 18080，导致探针连接被拒且 Pod 持续 NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod condition: Ready=False, reason=ContainersNotReady, message=containers with unready status: [app] (fact-07076a5d4762, fact-cf2e9620db8a) | 证实 Pod 未就绪症状 |
| 2 | K8s Event | kubernetes | Unhealthy Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused (fact-e681286fcdd7) | 直接证据：探针配置端口 18081 连接被拒 |
| 3 | Logging | elasticsearch | Message: "listening on 18080" (fact-5dd54cd9b22b) | 证实容器实际监听端口为 18080，解释探针失败原因 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 (fact-b3ef2eaa40db) | 排除因容器频繁崩溃重启导致的故障 |
| 5 | K8s State | kubernetes | Pod phase/status: Running (fact-21c96a09ce02, fact-be33bb7a6bc8) | 确认容器业务逻辑运行中，非业务进程异常 |

**证据说明：**
Pod 业务进程确实在监听 18080 端口（事实 3、5），但 Kubelet 持续尝试连接 18081 端口导致连接被拒（事实 2），进而致使 Readiness Probe 连续失败（事实 2），最终导致 Pod 状态标记为 NotReady（事实 1）。由于容器重启次数为 0（事实 4），进一步佐证了容器本身并未运行异常，而是探针配置与业务监听端口不匹配。

## 🎯 根因分析 · g1

### 因果链
```text
探针配置端口(18081)与容器监听端口(18080)不匹配 → kubelet 向 18081 发起 HTTP 探测 → 连接被拒绝 (Connection Refused) → Pod Readiness 为 False，状态 NotReady
```

### 根因结论
根因确认为**探针配置与业务监听端口不一致**。
- **事实支撑**：容器日志证实进程监听 18080 端口 (事实 3)，而 Kubelet 报告在探测 18081 端口时遭遇 `connect: connection refused` (事实 2)。
- **结果**：该配置错误导致 Readiness Probe 持续失败，Pod 被 K8s 置为 `NotReady` 状态 (事实 1)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 40.5s
│  └─ g1 aiops-case-v16/workload: 40.5s (Evidence 33.1s, RCA 7.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
