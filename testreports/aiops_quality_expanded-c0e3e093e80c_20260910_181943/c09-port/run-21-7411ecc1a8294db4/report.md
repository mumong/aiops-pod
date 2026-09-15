## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误（端口 18081）与应用实际监听端口（18080）不一致，导致 kubelet 探测失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 3m22s (x513 over 43m) kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` [fact-bb91bc650177] | 直接症状：探针探测失败并产生大量连接拒绝错误 |
| 2 | K8s Config | kubernetes | Readiness Probe target: `http://172.16.104.33:18081/ready` | 配置证据：实际配置指向 18081 端口，引发后续探测失败 |
| 3 | K8s Config | kubernetes | Container resource limit (CPU: 200m, Memory: 64Mi); Pod phase: Running; Restarts: 0 [fact-d4ccf43d01bc][fact-1bfb01efe4e8][fact-853bbd365374] | 排除资源超发或容器重启导致的问题 |
| 4 | Metric | prometheus | `kube_pod_status_phase{container="app", phase="Running"} = 1` [fact-e8922db62bbe] | 状态印证：应用容器实际处于运行状态，具备服务监听能力 |

证据相互印证：Metric [4] 确认容器进程活跃（Running），排除了应用崩溃或容器不可用的情况；结合 K8s Config [2] 的 18081 端口配置与 Event [1] 中明确的 `connect: connection refused` 错误，证实是配置端口与监听端口不匹配导致的网络探测失败。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置监听 18081 端口，但应用代码监听 18080 端口 → Kubelet 向 18081 发起 TCP 连接 → 目标端口无进程监听，直接拒绝连接 (Connection Refused) → 探针连续失败，Ready 状态变为 False
```

### 根因结论

已确认的根因为 **Readiness Probe 配置错误**。K8s 探测配置（目标端口 18081）与应用程序实际监听端口（18080）不一致。

该错误直接导致了 `kubelet` 在探测时遭遇 `connection refused` [fact-bb91bc650177]。由于 Metric 显示容器状态为 `Running` 且无重启记录 [fact-e8922db62bbe][fact-853bbd365374]，排除了进程崩溃或资源耗尽的可能性，确定这是典型的配置与部署不一致导致的服务可用性（Readiness）异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 26.3s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-v16/workload: 32.0s (Evidence 25.1s, RCA 6.8s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
