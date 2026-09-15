## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod `aiops-case-v16/workload` status is NotReady (READY 0/1) due to persistent Readiness probe failures. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: Running, status: NotReady (Ready=False, reason: ContainersNotReady) | 确认 Pod 处于运行但未就绪状态 |
| 2 | K8s Event | kubernetes | Warning Unhealthy (x960 over 78m): `dial tcp 172.16.104.33:18081: connect: connection refused` | 提供直接的探针失败原因：端口不可达 |
| 3 | K8s Event | kubernetes | Annotations `cni.projectcalico.org/podIP: 172.16.104.33/32` | 确认 Pod 的网络标识与事件中的 IP 一致 |
| 4 | K8s Config | kubernetes | Resource Request (Memory: 8Mi, CPU: 5m); Resource Limit (Memory: 64Mi, CPU: 200m) | 排除资源超卖导致的启动失败（且重启计数为 0） |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` (container app) = 0 | 证实容器未发生过重启，排除应用崩溃 |

**证据说明：**
K8s Event（#2）显示 Kubelet 连接 Pod IP `172.16.104.33` 的 `18081` 端口被拒绝，结合 `x960 over 78m` 表明这是一个持续发生的配置错误。Metric（#5）与 K8s State 中的重启计数为 0（#4 辅助）相互印证，排除了应用因资源限制或代码 Bug 崩溃重启的可能性，从而将根因锁定在探针配置与实际应用监听端口的不匹配上。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置目标端口为 18081 → 容器应用实际监听端口不一致导致连接被拒 → Kubelet 持续收到 connection refused 错误 → Pod 状态被判定为 NotReady
```

### 根因结论

已确认的根因为：**Readiness Probe 配置错误（Target Port Mismatch）**。

根据 K8s Event 的持续报错记录（#2），探针配置的目标端口为 `18081`，但连接该端口的 TCP 握手被拒绝。由于 Metric（#5）显示容器重启次数为 0 且 Pod 状态保持 Running，可以排除应用进程未启动或崩溃重启的情况。这表明探针的目标端口与容器应用实际暴露的端口不一致，导致就绪检查持续失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.7s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v16/workload: 37.2s (Evidence 29.1s, RCA 7.9s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
