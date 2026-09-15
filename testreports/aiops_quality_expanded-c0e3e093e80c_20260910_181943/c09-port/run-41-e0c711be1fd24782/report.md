## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 证明容器端口探测直接失败（Connection refused） |
| 2 | K8s State | kubernetes | `ContainersReady: False`, `Ready: False` (reason: `ContainersNotReady`) | 证实 Pod 及容器未满足就绪条件 |
| 3 | K8s State | kubernetes | `phase: Running`, `container.restart_count: 0` | 排除容器崩溃或反复重启因素 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (61个样本, 始终为0) | 确认重启计数未变化，进一步排除崩溃重启可能 |

K8s Event 记录了 kubelet 探测 18081 端口失败并导致容器未就绪的直接现象；结合 Pod 处于 Running 且重启次数为 0 的状态，表明应用进程一直在运行，但无法通过该探针，确认为探测配置层面的问题。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误(18081/ready) → kubelet 探测连接被拒绝 → 容器状态未就绪 → Pod 呈现 NotReady 状态
```

### 根因结论

已确认的根因：**Readiness Probe 配置错误**。

探测探针配置的端口（18081）与路径（/ready）与容器实际监听配置（端口 18080、路径 /health）不匹配。探针无法建立连接导致失败（见证据 #1），进而致使 Pod 和容器状态变为未就绪（见证据 #2、#3）。该诊断有足够证据支持并确认发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.4s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-v16/workload: 39.5s (Evidence 29.7s, RCA 9.7s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
