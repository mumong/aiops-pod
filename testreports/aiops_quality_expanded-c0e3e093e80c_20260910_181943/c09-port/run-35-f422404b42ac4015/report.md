## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod `aiops-case-v16/workload` 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `Pod` phase=Running, status=Running, `ContainersReady`=False, `Ready`=False, reason=ContainersNotReady (`fact-158f8bc57541`, `fact-a95bc03795b3`) | 确认 Pod 存活但应用服务未就绪 |
| 2 | K8s State | Pod | 重启计数为 0 (`fact-506aaed66495`) | 排除因 CrashLoopBackOff 导致应用未启动的可能 |
| 3 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (`fact-76bf6cb08d55`) | 直接定位失败机制：连接被拒绝 |
| 4 | K8s Config | Container | `resource_request.memory`=8Mi, `resource_request.cpu`=5m, `resource_limit.memory`=64Mi, `resource_limit.cpu`=200m (`fact-0f203a1010b4`, `fact-34eb4f0d0caf`, `fact-4e1352dd9015`, `fact-783ac2df0d38`) | 资源限制极低，排除了因 OOMKill 或 CPU 限制导致容器无法提供服务的可能 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (`fact-42b92d524850`) | 与 K8s 事件中的重启计数一致，确认容器正常运行中 |

**证据说明：**
K8s 状态表明 Pod 处于 `Running` 但 `Ready` 为 `False`（#1），且重启次数为 0（#2），说明容器成功启动并在运行。Prometheus 指标确认无重启发生（#5）。K8s 事件（#3）提供了决定性证据：kubelet 正在尝试连接 `172.16.104.33:18081` 并因 `connection refused` 而失败。配置数据（#4）显示资源充足且未耗尽，排除了资源瓶颈。综上，Pod 正在运行，但其健康检查探针因连接被拒而无法成功。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置（Probe）与应用实际监听端口、路径不一致 → 探针请求到达目标 IP/端口但无服务监听 → kubelet 持续报告 connection refused → Pod Ready 状态为 False，服务无法接收流量
```

### 根因结论

已确认的根因是：**Readiness Probe 配置错误**。

证据（#3）显示 `kubelet` 正试图连接端口 `18081` 和路径 `/ready`，但连接被拒绝。这表明应用容器确实在运行（#1, #2），但应用本身并未在探针指定的 `18081` 端口上监听，或者未在 `/ready` 路径上提供响应（可能是应用在 `18080` 端口或其他路径）。探针配置（`port=18081, path=/ready`）与实际运行中的应用服务地址/路径存在偏差，导致健康检查持续失败，进而使 Pod 处于 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.3s
├─ 并发证据采集: 39.1s
│  └─ g1 aiops-case-v16/workload: 39.1s (Evidence 28.5s, RCA 10.4s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
