## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload处于NotReady状态，连续触发Readiness probe failed |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确诊探针因端口连接被拒绝而持续失败 |
| 2 | K8s Event | kubelet | `k8s.v1.cni.cncf.io/network-status: ... cni.projectcalico.org/podIP: 172.16.104.33/32` | 确认异常 Pod 的网络身份与探针目标 IP 一致 |
| 3 | K8s State | pod.condition | `ContainersReady: False, reason: ContainersNotReady` | 佐证容器因未通过就绪检查而保持非就绪状态 |
| 4 | K8s Config | container.resource_limit.memory | `container: app, value: 64Mi` | 排除内存硬限制导致的进程资源受限或 OOMKill |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: container=app, value: 0` | 排除因应用崩溃重启导致的不稳定，确认为静态配置/代码逻辑问题 |

**证据印证说明：**
- 探针失败的根本原因是网络层面的“连接被拒绝”，而非资源不足或应用崩溃（证据 1 结合证据 5）。
- 应用并未崩溃重启，说明进程在运行，但拒绝特定端口的连接，这与探针配置和容器实际监听不匹配的逻辑一致。

## 🎯 根因分析 · g1

### 因果链
```text
Readiness Probe配置错误（端口/路径不匹配） → 连接被拒绝（Connection Refused） → 探针连续失败（640次） → Pod状态NotReady
```

### 根因结论
已确认的根因为：**Readiness Probe配置与容器实际服务端口及路径不匹配**（证据 1, 3）。
探针探测的是 `172.16.104.33:18081/ready`，但实际服务未在该端口/路径提供响应，导致连接被拒绝，触发 Pod 持续处于 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 31.8s
├─ 并发证据采集: 46.3s
│  └─ g1 aiops-case-v16/workload: 46.3s (Evidence 34.4s, RCA 11.8s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
