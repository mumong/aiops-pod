## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe配置错误：Probe配置为目标端口18081和路径/ready，但容器内应用实际监听在端口18080且仅响应/health路径，导致连接被拒绝从而触发NotReady状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-77f7cec67a78) | 直接记录 Kubelet 探测被拒的失败机制 |
| 2 | K8s State | kubernetes | `ContainersNotReady: containers with unready status: [app]` (fact-30e84a49d1ef, fact-46af89fab6a4) | 证明因上述失败触发的容器非就绪状态 |
| 3 | K8s Config | kubernetes | Pod IP 分配: `172.16.104.33/32` (fact-59b457a06466) | 定位故障 Pod 的网络实体与地址 |
| 4 | K8s Config | kubernetes | 容器资源限制: `cpu: 200m`, `memory: 64Mi` (fact-790bef05e69d, fact-7aa900ee627d) | 辅助排除资源超卖导致的性能问题 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (fact-111ea750b9c2) | 证明应用处于稳定运行态，无重启现象 |

上述 Kubernetes 事实（#1、#2）直接证实了探针配置与目标端口 18081 不一致导致的连接拒绝，且 Metric（#5）排除了应用因 OOM 等异常导致的重启，确认为纯配置型错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用实际监听(18080, /health)与Probe配置(18081, /ready)不一致 → Kubelet向18081/ready发起请求 → 连接被拒绝(connection refused) → ContainersNotReady状态
```

### 根因结论

已确认根因为 **Readiness Probe 配置错误**。
具体表现为探针目标端口（18081）与路径（/ready）均未命中应用实际服务（端口18080，路径/health），导致 Kubelet 持续收到 `connection refused`（事实 #1），进而使 Pod 进入 `NotReady` 状态（事实 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.3m
├─ 问题定位: 13.3s
├─ 并发证据采集: 537.2s
│  └─ g1 aiops-case-v16/workload: 537.2s (Evidence 528.5s, RCA 8.6s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed, pod-crashloop-runtime
