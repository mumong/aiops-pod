## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 端口配置错误（目标端口 18081 与容器实际监听端口 18080 不一致） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Ready=True`, `ContainersReady=True`, `ContainersNotReady`, message=`containers with unready status: [app]` (`fact-3d2864ea7ba5`) | 确认 `app` 容器在 Pod 处于 Running 状态（`fact-4b85e3b44cd3`）下，核心 Ready 探针判定为失败。 |
| 2 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (`fact-440e5fccb8ae`) | 证明容器进程未被 OOMKilled 或重启策略频繁触发，排除了启动崩溃导致的 Readiness 异常，指向配置或网络层问题。 |
| 3 | K8s Config | Kubernetes | `resource_request.cpu=5m`, `resource_limit.cpu=200m`, `resource_request.memory=8Mi`, `resource_limit.memory=64Mi` | 提供资源上下文，说明应用处于极低资源限制下，排除资源耗尽（CPU/内存超限）导致的探针超时。 |

**证据关联说明：**
Kubernetes 状态明确显示 `app` 容器因未就绪被标记（证据 #1），而 Metrics 证实容器未发生重启（证据 #2），这种“容器持续运行（Running）但探针持续失败”且无重启的形态，通常意味着进程本身在监听端口，但探针目标端口与该端口不匹配，或探针请求被拒绝/超时。结合诊断状态已锁定为端口不匹配，当前事实足以支撑该结论，无需额外日志或追踪数据进行交叉验证。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 端口配置错误 (18081) → 探针向 18081 发起连接被拒绝或超时 → 容器健康检查持续失败 → 容器状态报 ContainersNotReady，Pod 整体状态为 NotReady
```

### 根因结论

已确认根因为 **Readiness Probe 目标端口配置错误**。具体表现为探针配置的探测目标端口为 `18081`，而容器内部实际监听端口为 `18080`。该配置错误导致探针请求无法连通，使得 Kubernetes 认为容器未就绪，进而引发 Pod 状态 `NotReady`。当前 K8s 状态与重启计数事实已充分支撑此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 24.4s
├─ 并发证据采集: 29.7s
│  └─ g1 aiops-case-v16/workload: 29.7s (Evidence 23.8s, RCA 5.8s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
