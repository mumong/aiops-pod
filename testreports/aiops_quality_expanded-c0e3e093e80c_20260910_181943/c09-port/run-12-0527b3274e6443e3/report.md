## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 状态为 NotReady（Readiness Probe 持续失败） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` [fact-4ebb82f80ee1] | 证明 kubelet 向 Pod IP 172.16.104.33 的 18081 端口发起连接时被拒绝 |
| 2 | K8s Config | kubernetes | Pod 监听 IP：`172.16.104.33/32` [fact-58965b0c1a80, fact-a0909d53e018] | 确认异常事件中的目标 IP 与 Pod 实际分配 IP 一致，排除网络隔离问题 |
| 3 | Logging | elasticsearch | `listening on 18080` [fact-5dd54cd9b22b] | 显示应用实际在 18080 端口进行监听，证实存在端口配置错位 |
| 4 | K8s State | kubernetes | Pod 状态：`Running`，重启次数：`0` [fact-93bf3f6f7744, fact-11b783223aaf] | 排除容器崩溃或 CrashLoopBackOff 导致的启动失败，确认进程存活 |

**证据分析**
Kubernetes 事件与日志形成了闭环证据：事件明确指向 18081 端口连接失败，而日志显示应用仅在 18080 端口监听。Pod 处于 Running 状态且无重启，排除了应用自身异常。

## 🎯 根因分析 · g1

### 因果链

```text
Probe 配置端口 (18081) 与容器实际监听端口 (18080) 不匹配 → Kubelet 向 18081 发起 HTTP 连接探测 → 目标端口无进程监听，连接被拒绝 (connection refused) → Readiness 探针连续失败，Pod 标记为 NotReady
```

### 根因结论

已确认根因为 **探针端口配置错误**。

证据表明，应用已在 **18080** 端口启动并监听，而 Kubernetes Readiness Probe 被配置为探测 **18081** 端口。由于 18081 端口未监听，kubelet 获取到 `connection refused` 错误，导致探针持续失败，进而将 Pod 状态更新为 NotReady。

*   直接证据：日志显示监听端口为 18080（见证据 #3），K8s 事件显示探测目标端口为 18081 并被拒绝（见证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.7s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-v16/workload: 41.7s (Evidence 32.7s, RCA 8.9s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
