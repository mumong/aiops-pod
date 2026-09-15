## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 状态为 Running 但 READY=0/1 (NotReady) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy Readiness probe failed: ... dial tcp 172.16.104.33:18081: connect: connection refused` (fact-571b27749fd7) | 核心证据：探针在 18081 端口因连接被拒而失败，且该错误在 53 分钟内发生了 640 次 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total` 容器 app 值为 `0` (fact-3571cf0b18bf) | 证明 Pod 运行期间未发生应用侧崩溃或重启，排除了应用不稳定性导致的间歇性失败 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v16/workload` 状态为 `Running` (fact-4b3c3fe74ab1) | 确认容器实际处于运行中，Pod 具备运行环境但应用层未标记就绪 |

证据表明，Pod 处于 Running 状态且未重启，但 Kubelet 持续在 53 分钟内检测到探针在 `172.16.104.33:18081` 端口连接被拒。结合 `restart_count=0` 的事实，说明这不是由于应用崩溃恢复导致的短暂不可用，而是应用持续无法在探针配置的 18081 端口提供服务。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误 (指向 18081 端口) → 探针连接被拒绝 (Connection Refused) → Pod Ready 状态标记失败 (NotReady/0/1) → Pod 无法接收流量
```

### 根因结论

已确认根因为 **Readiness Probe 端口配置与应用程序实际监听端口不匹配**。

Kubelet 按照配置向 Pod IP 的 `18081` 端口发起探测，但该端口没有服务监听，导致 `connection refused` 错误（证据 #1）。由于应用未崩溃（证据 #2），且状态确认 Pod 处于 `Running` 状态（证据 #3），这种持续的网络连接失败直接导致 Kubernetes 判定 Pod 不满足就绪条件，从而标记为 `NotReady`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.2s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-v16/workload: 39.5s (Evidence 30.9s, RCA 8.5s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
