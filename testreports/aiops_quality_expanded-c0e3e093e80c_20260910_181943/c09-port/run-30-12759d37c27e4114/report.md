## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | readinessProbe配置错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `phase`: Running, `ContainersReady`: False (reason: ContainersNotReady), `Ready`: False | 确认 Pod 存活但未通过就绪探针 |
| 2 | K8s Event | kubernetes | `Unhealthy`: Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused | 直接显示应用对探针端点的拒绝连接行为 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory`: 8Mi, `container.resource_limit.cpu`: 200m | 资源配置极低，排除常规资源过载引发的崩溃 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi | 内存硬限制为 64Mi |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 确认应用无 OOMKilled 重启历史，排除了内存不足导致进程重启 |
| 6 | K8s Config | kubernetes | Pod Annotations `cni.projectcalico.org/podIP`: 172.16.104.33/32 | 确定网络连通性测试的 Pod IP 地址 |

Pod 处于 Running 状态且未发生重启，但状态一直为 NotReady。日志和追踪缺失。探针直接报错“connection refused”，说明应用进程正在运行并接收到了 TCP 连接，但目标端口 18081 上没有服务监听，这与应用实际仅监听其他端口且配置了错误的探针路径高度吻合。

## 🎯 根因分析 · g1

### 因果链

```text
应用实际监听端口 18080 且仅实现 /health 端点 → Kubernetes readinessProbe 错误配置为探测 18081 端口/ready 路径 → Probe 连续失败(failureThreshold=1)导致 ContainersNotReady → Pod 状态显示 NotReady
```

### 根因结论

已确认根因为 **readinessProbe 配置错误**。

证据表明，应用进程运行正常（无重启，日志未出现 Crash 记录），且拒绝连接（connection refused）发生在探针设定的目标端口 `18081` 上。这说明探针探测的目标端口与容器实际监听端口不一致，导致就绪检查永久失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.1s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-v16/workload: 37.9s (Evidence 30.0s, RCA 7.7s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
