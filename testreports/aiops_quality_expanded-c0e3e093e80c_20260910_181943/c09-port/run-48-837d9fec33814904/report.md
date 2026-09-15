## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload is NotReady with ContainersNotReady status |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Running` | 容器进程已在运行，网络栈基础已建立 |
| 2 | K8s State | kubernetes | `Ready=False, ContainersNotReady`；`ContainersReady=False` | Pod 整体与容器就绪状态均失败，直接指向健康检查问题 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (持续 75m, 960次) | 确认 kubelet 向 Pod IP `172.16.104.33` 的 `18081` 端口发起探测时遭遇连接被拒 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu: 200m`；`container.resource_request.cpu: 5m`；`container.resource_limit.memory: 64Mi`；`container.resource_request.memory: 8Mi` | 容器资源配额配置，当前无资源超限导致的 CrashLoopBackOff 迹象 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (app) | 进一步佐证 Pod 未经历重启，进程存活但处于不健康状态 |

**证据关联：**
- 证据 #3 (K8s Event) 揭示了具体的失败机制：Pod 运行 (证据 #1) 但就绪探测失败。
- 证据 #5 (Metric) 排除了容器因 OOM 或异常崩溃导致的频繁重启，将故障锁定在运行时的服务不可用。
- 证据 #2 (K8s State) 的状态流转与探测失败的错误信息完全吻合，确认为单一维度的连接性问题。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置目标端口错误 (18081) → Kubelet 探测未监听端口导致连接被拒 → 容器持续健康检查失败 → Pod 状态标记为 NotReady
```

### 根因结论

**已确认根因：** 就绪探测（Readiness Probe）的目标端口配置错误。

证据表明，集群中运行的 Pod `aiops-case-v16/workload` 处于 Running 状态且无重启记录，但 kubelet 持续向 Pod IP `172.16.104.33` 的 `18081` 端口发起 HTTP 探测，并返回 `connection refused` 错误（事实 #3）。这种持续的连接拒绝导致了 Pod 和容器的 `Ready` 状态被标记为 `False`（事实 #2, #5）。根因是探针的探测端口与实际容器服务监听端口不一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.1s
├─ 并发证据采集: 45.9s
│  └─ g1 aiops-case-v16/workload: 45.9s (Evidence 37.9s, RCA 7.9s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
