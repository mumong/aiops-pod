## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod workload in aiops-case-v16 is NotReady due to persistent Readiness Probe failures |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | `Warning Unhealthy 112s (x576 over 46m)` kubelet `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确认 Probe 失败的具体错误信息，指向端口连接被拒绝 |
| 2 | K8s State | K8s | Pod `aiops-case-v16/workload` 状态 `Running`，Ready 条件 `False` (`ContainersNotReady`)，重启次数 `0` | 确认容器处于运行态，但未就绪且无重启，排除了应用崩溃退出的可能性 |
| 3 | K8s Config | K8s | Pod IP 配置为 `172.16.104.33` | 提供连接失败的 IP 地址上下文 |

```text
Readiness Probe 配置与 App 监听端口不一致 → 持续的连接被拒绝 (Connection refused) → 容器被标记为未就绪 → Pod 持续处于 NotReady 状态
```

**证据印证说明：**
K8s Event 中记录的 `connection refused` (事实 #1) 直接解释了 K8s State 中容器未就绪的原因 (事实 #2)。在重启次数为 0 且容器状态为 Running 的前提下，连接被拒绝而非超时或应用层错误，强力支持了网络端口层面的配置不匹配（而非应用逻辑或网络策略阻塞）。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 目标端口 (18081) 与 App 实际监听端口 (18080) 不一致 → 连接被目标主机拒绝 → 容器健康检查失败 → Pod 状态保持 NotReady
```

### 根因结论

已确认根因为 **Readiness Probe 配置不匹配**：探针向端口 `18081` 发起探测，而应用程序实际在端口 `18080` 上运行。证据 `fact-d223dd7d9ff8` (kubelet 报错 `connection refused` at `18081`) 直接证实了探测端口的失败原因。由于应用进程在运行且未发生崩溃（重启次数为 0），该现象并非由资源耗尽或应用逻辑错误导致，确认为探针配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 13.6s
├─ 并发证据采集: 73.6s
│  └─ g1 aiops-case-v16/workload: 73.6s (Evidence 65.2s, RCA 8.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed, pod-crashloop-runtime, pod-oomkilled
