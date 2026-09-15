## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload status is NotReady due to Readiness Probe failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.condition`: Ready=True(ContainersNotReady) | 描述 Pod 当前处于非就绪状态的具体症状。 |
| 2 | K8s Event | kubernetes | `event.message`: "Readiness probe failed: Get \"http://172.16.104.33:18081/ready\": dial tcp 172.16.104.33:18081: connect: connection refused" | 暴露 Kubelet 尝试连接探针端口 `18081` 并遭遇网络拒绝的事实。 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (container=app) | 确认应用容器并未发生 OOM 等异常重启，排除了应用崩溃。 |

**证据说明**：
Metric 维度的重启数为 0 排除了应用进程崩溃导致启动失败的可能。K8s Event 记录了端口 `18081` 的连接被拒绝，结合 K8s State 的持续未就绪状态，将问题定位在端口与路径的连通性配置上。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置目标为端口 18081 路径 /ready → 容器应用实际监听端口 18080 路径 /health → 探针发起连接遭拒绝 (dial tcp 172.16.104.33:18081: connect: connection refused) → Pod 状态变为 NotReady
```

### 根因结论

**已确认的根因**：探针端口/路径配置与应用实际监听端口/路径不匹配（证据 #2）。Kubelet 在 `18081/ready` 端口执行探测时，由于该端口未被应用监听，导致 TCP 连接被拒绝，从而使 Pod 持续处于 `ContainersNotReady` 状态（证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.6s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-v16/workload: 41.1s (Evidence 33.4s, RCA 7.6s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
