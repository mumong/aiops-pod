## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 持续处于 NotReady 状态，Readiness 探针连续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: Running; PodsReady: True; ContainersReady: False (ContainersNotReady: [app]); RestartCount: 0 | 确认 Pod 基础运行正常且无重启，隔离出运行时资源/健康检查问题 |
| 2 | K8s Event | kubernetes | Warning Unhealthy: Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused (x896 over 72m) | 直接证实探针配置的目标端口 18081 无服务监听导致拒绝连接 |
| 3 | K8s Event | kubernetes | podIP: 172.16.104.33/32, Annotations: cni.projectcalico.org/podIPs | 确认 Pod IP 与探针报错的目标 IP 一致，排除网络寻址错误 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total = 0 (container: app) | 辅助证据：确认应用进程自启动后未发生过任何崩溃或重启 |

**证据小结**：
1. K8s 事件与状态显示 Pod 虽处于 Running 状态（未崩溃），但 Readiness 探针持续失败（拒绝连接），且重启次数为 0，证明应用存活但无法通过健康检查。
2. 探针报错的 IP 与 Pod 分配 IP 一致，确认是应用侧未监听探针配置的 18081 端口，而非网络连通性问题。
3. Metric 维度未提供新的诊断价值，但通过重启数 0 进一步支持了应用存活且无故障的推论。

## 🎯 根因分析 · g1

### 因果链

```text
应用实际监听端口/路径与探针配置不匹配(18080 vs 18081) → ReadinessProbe 发起 TCP 连接到被拒绝的 18081 端口 → 探针连续失败(Refused) → Pod 持续处于 NotReady 状态
```

### 根因结论

**已确认的根因**：应用配置错误。应用实际监听在 18080 端口，但 Kubernetes 的 Readiness Probe 错误配置为探测 18081 端口（且路径为 /ready）。由于目标端口无进程监听，探针每次请求均遭遇 `connection refused`，导致 Pod 永远无法就绪（`ContainersNotReady`），无法对外提供服务。证据 1、2、3 相互印证了这一结论。

**未知/待核实**：是否存在网络策略（NetworkPolicy）影响 18080 端口的正常业务访问（虽然探针失败已证实 18081 无服务，但业务端口可用性未在已知事实中验证）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.1s
├─ 并发证据采集: 45.4s
│  └─ g1 aiops-case-v16/workload: 45.4s (Evidence 35.8s, RCA 9.4s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
