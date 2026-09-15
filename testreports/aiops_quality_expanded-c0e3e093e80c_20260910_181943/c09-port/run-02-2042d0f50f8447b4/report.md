## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误：Probe 配置的端口（18081）与容器实际监听端口（18080）不一致，且路径（/ready）与代码实现（/health）不匹配。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Unhealthy` (Warning): `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-65dbd45322a7) | 核心异常现象，表明探针请求失败且连接被拒绝，证明 Pod IP 172.16.104.33 在 18081 端口无服务监听。 |
| 2 | K8s Event | Kubernetes | `cni.projectcalico.org/podIP: 172.16.104.33/32` (fact-22dbf0b68043) | 确认发生故障时的 Pod 真实 IP 地址，将探针失败与特定容器绑定。 |
| 3 | Logging | Elasticsearch | `listening on 18080` (fact-5dd54cd9b22b) | 确认应用容器的实际监听端口为 18080，与探针配置的 18081 端口不匹配，直接佐证配置错误。 |
| 4 | K8s State | Kubernetes | `ContainersNotReady` / `pod.phase: Running` (fact-5337a99bcd0b, fact-3b3d94530c69) | 确认 Pod 处于运行状态但未就绪，且重启次数为 0，排除了因容器频繁崩溃重启导致的不稳定因素。 |

**证据互证说明**：
证据 1 (K8s Event) 证明探针在 18081 端口连接被拒，证据 3 (Logging) 证明应用实际上在 18080 端口监听，两者构成了端口不匹配的直接证据。证据 2 提供了关联的 Pod IP，证据 4 排除了容器健康度波动和重启异常，确认问题根源在于探针配置与实际运行的应用不符。

## 🎯 根因分析 · g1

### 因果链
```text
Readiness Probe 配置错误（端口 18081 与实际 18080 不匹配） → 探针向错误端口发送请求 → 连接被拒绝 (connection refused) → 探针判定为失败 → Pod 状态 NotReady
```

### 根因结论
已确认根因为 **Readiness Probe 配置错误**。
证据 1 显示探针配置的目标端口为 `18081` 且路径为 `/ready`，请求 Pod IP `172.16.104.33` 时遭到拒绝；证据 3 的日志记录证实应用实际仅监听在端口 `18080`，且文档指出应用正确的健康路径为 `/health`。探针配置的端口和路径与实际应用运行参数完全不一致，导致探针持续失败，进而使 Pod 进入 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.5s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-v16/workload: 37.9s (Evidence 29.6s, RCA 8.1s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
