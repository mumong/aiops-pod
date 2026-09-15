## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误（端口 18081 与路径 /ready）与应用实际监听端口 18080 及路径 /health 不匹配，导致 kubelet 探针请求被拒绝，Pod 始终处于 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Phase: Running | 验证容器进程实际启动并维持运行 |
| 2 | K8s State | kubernetes | Ready: False, ContainersReady: False (ContainersNotReady) | 确认容器虽然正在运行，但无法满足就绪条件 |
| 3 | K8s Event | kubernetes | Warning Unhealthy: "Readiness probe failed: Get \"http://172.16.104.33:18081/ready\": dial tcp 172.16.104.33:18081: connect: connection refused" | 直接证据：探针请求被拒绝，指向具体错误的目标端口与路径 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total = 0 | 排除因容器崩溃重启导致就绪失败的可能 |
| 5 | Logging | elasticsearch | "listening on 18080" | 确立应用实际监听端口，与探针配置构成根本冲突 |

**证据印证说明：**
K8s Event (3) 明确指出探针访问 `:18081/ready` 时发生连接被拒绝。结合 Logging (5) 确认应用实际绑定在 `18080`，以及 K8s State (1) 确认应用确在运行中，共同锁定了配置与运行状态不匹配的原因。Metric (4) 证实应用进程稳定，排除了运行时故障。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置端口/路径错误(18081/ready) → kubelet 发起连接被拒绝 → Readiness Probe 持续失败 → Pod 状态标记为 NotReady
```

### 根因结论

已确认根因为 **Readiness Probe 配置错误**。探针被错误配置为探测 `172.16.104.33:18081/ready`，而应用实际在 `18080` 端口监听 `/health` 路径。由于目标端口无服务监听且路径不存在，kubelet 的 TCP/HTTP 探测直接返回“connection refused”（事实 3），导致 `ContainersReady` 条件始终无法满足，Pod 最终处于 `NotReady` 状态（事实 2、4），尽管应用本身正在正常启动和运行（事实 1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.7s
├─ 并发证据采集: 46.1s
│  └─ g1 aiops-case-v16/workload: 46.1s (Evidence 38.3s, RCA 7.7s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
